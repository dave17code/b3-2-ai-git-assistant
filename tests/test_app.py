"""실제 임시 Git 저장소와 모의 HTTP 응답으로 필수 동작을 검증합니다."""

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from main import main, parse_args
from src.ai_client import API_URL, generate
from src.git_reader import collect_changes
from src.output import normalize_draft, render_draft
from src.prompts import build_request
from src.safety import mask_sensitive, prepare_input


COMMIT = {"title": "fix: 빈 검색어 처리", "summary": ["src/search.py에서 빈 검색어를 처리합니다."]}
PR = {
    **COMMIT,
    "why": ["불필요한 검색을 줄이려는 변경으로 추정됩니다. 작성자가 배경을 확인해 주세요."],
    "what": ["빈 검색어에 대한 처리 추가"],
    "how_to_test": ["빈 문자열을 입력하여 빈 목록이 반환되는지 확인합니다."],
}


def response(draft: dict = COMMIT, finish: str = "stop", refusal=None) -> io.BytesIO:
    body = {"choices": [{"finish_reason": finish,
                         "message": {"content": json.dumps(draft), "refusal": refusal}}]}
    return io.BytesIO(json.dumps(body).encode())


class GitAndCliTests(unittest.TestCase):
    def setUp(self):
        self.old_cwd = Path.cwd()
        self.temp = tempfile.TemporaryDirectory()
        os.chdir(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "B3-2 Test")
        self.git("config", "user.email", "test@example.invalid")

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], check=True, capture_output=True,
                              encoding="utf-8", timeout=30).stdout

    def baseline(self):
        Path("sample.txt").write_text("old\n", encoding="utf-8")
        self.git("add", "sample.txt")
        self.git("commit", "-qm", "baseline")

    def run_cli(self, args, key="test-only-value"):
        out, err = io.StringIO(), io.StringIO()
        # API Key는 테스트 프로세스의 환경변수에만 임시로 설정합니다.
        with patch.dict(os.environ, {"AI_API_KEY": key}):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                code = main(args)
        return code, out.getvalue() + err.getvalue()

    def test_clean_repository_skips_api_even_without_key(self):
        with patch("src.ai_client.urllib.request.urlopen") as request:
            code, text = self.run_cli(["commit"], key="")
        self.assertEqual(code, 0)
        self.assertIn("변경 사항이 없습니다", text)
        self.assertIn("요청 횟수: 0", text)
        request.assert_not_called()

    def test_new_unicode_and_space_filename_without_staging(self):
        name = "한글 파일.txt"
        Path(name).write_text("새 내용\n", encoding="utf-8")
        before = self.git("status", "--porcelain")
        changes = collect_changes()
        self.assertEqual(changes.files, [name])
        self.assertIn("+새 내용", changes.diff)
        self.assertEqual(before, self.git("status", "--porcelain"))

    def test_staged_changes_before_first_commit(self):
        Path("new.txt").write_text("new\n", encoding="utf-8")
        self.git("add", "new.txt")
        self.assertIn("+new", collect_changes().diff)

    def test_staged_and_unstaged_are_both_collected(self):
        self.baseline()
        Path("sample.txt").write_text("staged\n", encoding="utf-8")
        self.git("add", "sample.txt")
        Path("sample.txt").write_text("working\n", encoding="utf-8")
        changes = collect_changes()
        self.assertEqual(changes.files, ["sample.txt"])
        self.assertIn("+staged", changes.diff)
        self.assertIn("+working", changes.diff)

    def test_rename_and_deletion(self):
        self.baseline()
        self.git("mv", "sample.txt", "renamed.txt")
        changes = collect_changes()
        self.assertEqual(changes.files, ["renamed.txt"])
        self.assertIn("sample.txt -> renamed.txt", changes.status)
        self.git("commit", "-qm", "rename")
        Path("renamed.txt").unlink()
        self.assertIn("-old", collect_changes().diff)

    def test_empty_and_binary_new_files(self):
        Path("empty.txt").touch()
        Path("binary.bin").write_bytes(b"\x00\x01\xff")
        changes = collect_changes()
        self.assertEqual(len(changes.files), 2)
        self.assertIn("binary.bin", changes.diff)
        self.assertIn("empty.txt", changes.diff)

    def test_root_requirement(self):
        Path("child").mkdir()
        os.chdir("child")
        with self.assertRaisesRegex(RuntimeError, "루트"):
            collect_changes()

    def test_ignored_file_is_not_collected(self):
        Path(".gitignore").write_text(".env\n", encoding="utf-8")
        self.git("add", ".gitignore")
        self.git("commit", "-qm", "ignore")
        Path(".env").write_text("SECRET=private", encoding="utf-8")
        self.assertEqual(collect_changes().files, [])

    def test_missing_key_skips_api(self):
        Path("new.txt").write_text("new", encoding="utf-8")
        with patch("src.ai_client.urllib.request.urlopen") as request:
            code, text = self.run_cli(["commit"], key="")
        self.assertEqual(code, 1)
        self.assertIn("AI_API_KEY 환경변수", text)
        request.assert_not_called()

    def test_commit_flow_and_cli_parameters(self):
        Path("new.txt").write_text("new", encoding="utf-8")
        with patch("src.ai_client.urllib.request.urlopen", return_value=response()) as request:
            code, text = self.run_cli(["commit", "--model", "gpt-4.1-mini",
                                       "--temperature", "0.4", "--max-tokens", "900"])
        self.assertEqual(code, 0, text)
        self.assertIn("--- Commit Message ---", text)
        self.assertIn(COMMIT["title"], text)
        self.assertIn("요청 횟수: 1", text)
        self.assertEqual(request.call_count, 1)
        http_request = request.call_args.args[0]
        payload = json.loads(http_request.data)
        self.assertEqual(http_request.full_url, API_URL)
        self.assertEqual(http_request.get_method(), "POST")
        self.assertEqual(http_request.get_header("Authorization"), "Bearer test-only-value")
        self.assertEqual(payload["temperature"], 0.4)
        self.assertEqual(payload["max_completion_tokens"], 900)
        self.assertTrue(payload["response_format"]["json_schema"]["strict"])

    def test_pr_flow_does_not_change_git(self):
        self.baseline()
        Path("sample.txt").write_text("changed", encoding="utf-8")
        before = self.git("status", "--porcelain")
        with patch("src.ai_client.urllib.request.urlopen", return_value=response(PR)) as request:
            code, text = self.run_cli(["pr", "--safe-mode"])
        self.assertEqual(code, 0, text)
        for heading in ["Why", "What", "How to Test"]:
            self.assertIn(f"## {heading}\n- ", text)
        self.assertEqual(request.call_count, 1)
        self.assertEqual(before, self.git("status", "--porcelain"))

    def test_secrets_are_masked_in_request_and_errors(self):
        secret = "test-only-value"
        Path("new.txt").write_text(f"{secret}\na@example.com\nsk-example123456789", encoding="utf-8")
        with patch("src.ai_client.urllib.request.urlopen", return_value=response()) as request:
            code, text = self.run_cli(["commit"])
        payload = json.loads(request.call_args.args[0].data)
        context = payload["messages"][1]["content"]
        self.assertEqual(code, 0, text)
        for value in [secret, "a@example.com", "sk-example123456789"]:
            self.assertNotIn(value, context)
        error = urllib.error.HTTPError(API_URL, 401, "Unauthorized", {},
                                       io.BytesIO(json.dumps({"error": {"message": secret}}).encode()))
        with patch("src.ai_client.urllib.request.urlopen", side_effect=error):
            code, text = self.run_cli(["pr"])
        self.assertEqual(code, 1)
        self.assertIn("HTTP 401", text)
        self.assertNotIn(secret, text)


class FormattingAndSafetyTests(unittest.TestCase):
    def test_title_limits_and_bullet_format(self):
        for command, limit, draft in [("commit", 72, COMMIT), ("pr", 80, PR)]:
            with self.subTest(command=command):
                fixed, notices = normalize_draft({**draft, "title": "가" * 120 + "\n제목"}, command)
                self.assertLessEqual(len(fixed["title"]), limit)
                self.assertNotIn("\n", fixed["title"])
                self.assertTrue(notices)
                self.assertIn("\n- ", render_draft(fixed, command))

    def test_masking_precedes_length_check(self):
        fixed, _ = normalize_draft({**PR, "title": "가" * 71 + " a@b.co"}, "pr")
        self.assertLessEqual(len(fixed["title"]), 80)
        self.assertNotIn("a@b.co", fixed["title"])

    def test_commit_has_one_or_two_body_bullets(self):
        fixed, _ = normalize_draft({**COMMIT, "summary": ["- 첫째", "* 둘째", "셋째"]}, "commit")
        self.assertEqual(fixed["summary"], ["첫째", "둘째"])

    def test_empty_or_invalid_fields_are_rejected(self):
        for value in [[], ["  "], "text", [None]]:
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                normalize_draft({**PR, "why": value}, "pr")
        with self.assertRaises(RuntimeError):
            normalize_draft({**COMMIT, "title": ""}, "commit")

    def test_safe_mode_limits_lines_and_single_large_line(self):
        text, clipped = prepare_input("\n".join(f"line {i}" for i in range(400)), "", True)
        self.assertTrue(clipped)
        self.assertIn("line 199", text)
        self.assertNotIn("line 200", text)
        text, clipped = prepare_input("x" * 30000, "", True)
        self.assertTrue(clipped)
        self.assertEqual(text.count("x"), 20000)
        with self.assertRaisesRegex(RuntimeError, "safe-mode"):
            prepare_input("x" * 100001, "", False)

    def test_private_key_and_secret_assignments(self):
        text = 'API_KEY="value123"\npassword: secret123\n-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----'
        protected = mask_sensitive(text)
        for value in ["value123", "secret123", "abc"]:
            self.assertNotIn(value, protected)
        self.assertIn("[MASKED_PRIVATE_KEY]", protected)

    def test_cli_validation_and_single_dash_aliases(self):
        args = parse_args(["pr", "-model", "gpt-4.1-mini", "-temperature", "0", "-max-tokens", "500", "-safe-mode"])
        self.assertTrue(args.safe_mode)
        self.assertEqual(args.temperature, 0)
        for args in [["commit", "--temperature", "nan"], ["commit", "--temperature", "3"],
                     ["commit", "--max-tokens", "0"], ["commit", "--model", ""]]:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                parse_args(args)


class ApiTests(unittest.TestCase):
    def invoke(self):
        messages, schema = build_request("commit", "sample diff")
        return generate("test-only-value", "gpt-4.1-mini", 0.2, 1200, messages, schema)

    def test_http_errors_do_not_retry(self):
        for status in [400, 401, 403, 404, 429, 500]:
            error = urllib.error.HTTPError(API_URL, status, "error", {}, io.BytesIO(b"{}"))
            with self.subTest(status=status), patch("src.ai_client.urllib.request.urlopen", side_effect=error) as request:
                with self.assertRaisesRegex(RuntimeError, f"HTTP {status}"):
                    self.invoke()
                self.assertEqual(request.call_count, 1)

    def test_network_and_timeout(self):
        for error in [urllib.error.URLError("offline"), TimeoutError("timeout")]:
            with patch("src.ai_client.urllib.request.urlopen", side_effect=error) as request:
                with self.assertRaises(RuntimeError):
                    self.invoke()
                self.assertEqual(request.call_count, 1)

    def test_truncated_refused_and_malformed_response(self):
        cases = [response(finish="length"), response(refusal="refused"),
                 io.BytesIO(b"not json"), io.BytesIO(b'{}'), response(draft=[])]
        for result in cases:
            with patch("src.ai_client.urllib.request.urlopen", return_value=result):
                with self.assertRaises(RuntimeError):
                    self.invoke()


if __name__ == "__main__":
    unittest.main()
