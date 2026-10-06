"""B3-2 미션: Git 변경 사항으로 커밋 메시지와 PR 초안을 생성합니다."""

import argparse
import os
import sys

from src.ai_client import generate
from src.git_reader import collect_changes
from src.output import normalize_draft, render_draft
from src.prompts import build_request
from src.safety import mask_sensitive, prepare_input


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Git 변경 사항 기반 커밋/PR 초안 생성기")
    parser.add_argument("command", choices=["commit", "pr"], help="생성할 초안 종류")
    parser.add_argument("--model", "-model", default="gpt-4.1-mini", help="모델명 (기본: gpt-4.1-mini)")
    parser.add_argument("--temperature", "-temperature", type=float, default=0.2, help="0~2 (기본: 0.2)")
    parser.add_argument("--max-tokens", "-max-tokens", type=int, default=1200, help="생성 토큰 상한 (기본: 1200)")
    parser.add_argument("--safe-mode", "-safe-mode", action="store_true", help="전송 입력을 최대 200줄/20,000자로 제한")
    args = parser.parse_args(argv)
    if not 0 <= args.temperature <= 2:
        parser.error("--temperature는 0 이상 2 이하이어야 합니다.")
    if args.max_tokens < 1:
        parser.error("--max-tokens는 1 이상의 정수이어야 합니다.")
    if not args.model.strip():
        parser.error("--model은 비어 있을 수 없습니다.")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    api_key = os.environ.get("AI_API_KEY", "").strip()
    calls = 0
    try:
        changes = collect_changes()
        if not changes.files:
            print("[INFO] 변경 사항이 없습니다. 초안을 생성하지 않고 종료합니다.")
            return 0
        print(f"[INFO] Git status 수집 완료: {len(changes.files)}개 파일 변경")
        print(mask_sensitive(changes.status, api_key))
        print(f"[INFO] Git diff 수집 완료: {len(changes.diff.splitlines())}줄")
        if not api_key:
            raise RuntimeError("AI_API_KEY 환경변수가 설정되지 않았습니다. README의 설정 방법을 확인해 주세요.")

        context, truncated = prepare_input(
            f"[Git diff]\n{changes.diff}\n\n[Git status]\n{changes.status}",
            api_key, args.safe_mode,
        )
        print("[INFO] API Key·이메일 등 공통 민감정보 패턴 마스킹 적용")
        if args.safe_mode:
            print("[INFO] 안전 모드: 전송 원문 최대 200줄 / 20,000자")
        if truncated:
            print("[WARN] 안전 모드로 입력 일부를 생략했습니다. 초안은 전송한 부분만 설명합니다.")
        messages, schema = build_request(args.command, context)
        print(f"[INFO] AI API 요청 중... (모델: {args.model})")
        calls = 1
        draft = generate(api_key, args.model, args.temperature, args.max_tokens, messages, schema)
        draft, notices = normalize_draft(draft, args.command, api_key)
        for notice in notices:
            print(f"[WARN] {notice}")
        print("[DONE] 초안 생성 및 형식 검증 완료")
        print(render_draft(draft, args.command))
        print("[INFO] 내용 검토 후 직접 적용해 주세요. 테스트 실행 및 Git 변경은 수행하지 않았습니다.")
        return 0
    except (RuntimeError, OSError) as exc:
        print(f"[ERROR] {mask_sensitive(str(exc), api_key)}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[INFO] 사용자가 실행을 중단했습니다.")
        return 130
    finally:
        print(f"[INFO] AI API 요청 횟수: {calls}")


if __name__ == "__main__":
    raise SystemExit(main())
