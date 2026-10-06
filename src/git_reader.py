"""현재 프로젝트의 Git 상태와 변경 내용을 수집합니다."""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class GitChanges:
    files: list[str]
    status: str
    diff: str


def run_git(*args: str, allow_difference: bool = False) -> str:
    try:
        result = subprocess.run(
            ["git", "--no-pager", "-c", "core.quotepath=false", *args],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            check=False,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("Git을 찾을 수 없습니다. Git 설치와 PATH를 확인해 주세요.") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("Git 명령 실행 시간이 초과되었습니다.") from exc

    # --no-index는 차이가 있으면 정상적으로 종료 코드 1을 반환합니다.
    allowed = (0, 1) if allow_difference else (0,)
    if result.returncode not in allowed:
        reason = result.stderr.strip() or f"종료 코드 {result.returncode}"
        raise RuntimeError(f"Git 명령 실행 실패: {reason}")
    return result.stdout


def collect_changes() -> GitChanges:
    # worktree에서는 .git이 디렉터리가 아닌 파일이므로 exists()로 확인합니다.
    if not Path(".git").exists():
        raise RuntimeError("Git 프로젝트 루트에서 실행해 주세요. 최초 사용 시 git init이 필요합니다.")

    raw = run_git("status", "--porcelain=v1", "-z", "--untracked-files=all")
    if not raw:
        return GitChanges([], "", "")

    entries = raw.split("\0")
    files, status_lines, untracked = [], [], []
    index = 0
    while index < len(entries) and entries[index]:
        entry = entries[index]
        state, path = entry[:2], entry[3:]
        index += 1
        files.append(path)
        if "R" in state or "C" in state:
            # -z 출력에서 이름 변경은 새 경로 뒤에 기존 경로가 이어집니다.
            old_path = entries[index]
            index += 1
            status_lines.append(f"{state} {old_path} -> {path}")
        else:
            status_lines.append(f"{state} {path}")
        if state == "??":
            untracked.append(path)
        if "U" in state or state in {"AA", "DD"}:
            raise RuntimeError("병합 충돌이 있습니다. 충돌을 해결하고 git add한 뒤 실행해 주세요.")

    flags = ("--no-ext-diff", "--no-textconv", "--no-color")
    pieces = []
    # 두 영역은 같은 파일도 서로 다른 중간 상태를 담을 수 있어 구분해 전달합니다.
    for label, args in [
        ("스테이징된 변경", ("diff", "--cached", *flags)),
        ("스테이징되지 않은 변경", ("diff", *flags)),
    ]:
        patch = run_git(*args)
        if patch.strip():
            pieces.append(f"[{label}]\n{patch}")

    # 미추적 파일은 일반 diff에 나오지 않아 빈 파일과 비교합니다. Git 상태는 바꾸지 않습니다.
    for path in untracked:
        patch = run_git(
            "diff", "--no-index", *flags, "--", os.devnull, path,
            allow_difference=True,
        )
        pieces.append(f"[새 파일: {path}]\n{patch or '(빈 파일)'}")

    return GitChanges(files, "\n".join(status_lines), "\n".join(pieces))
