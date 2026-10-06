"""AI 결과를 검증하고 길이 및 Markdown 형식을 후처리합니다."""

import re

from src.safety import mask_sensitive


def one_line(text: str) -> str:
    # 줄바꿈 및 터미널 제어 문자를 제거하고 공백을 정리합니다.
    return " ".join(re.sub(r"[\x00-\x1f\x7f]", " ", text).split()).strip("` ")


def normalize_draft(draft: dict, command: str, api_key: str = "") -> tuple[dict, list[str]]:
    title = draft.get("title")
    if not isinstance(title, str) or not one_line(title):
        raise RuntimeError("AI 응답에 유효한 제목이 없습니다.")
    # 마스킹 문구가 길어질 수 있으므로 보호 처리를 먼저 하고 제목 길이를 검사합니다.
    result = {"title": one_line(mask_sensitive(title, api_key))}
    notices = []
    limit = 72 if command == "commit" else 80
    if len(result["title"]) > limit:
        result["title"] = result["title"][:limit - 1].rstrip() + "…"
        notices.append(f"제목을 {limit}자 이내로 줄였습니다. 의미가 자연스러운지 검토해 주세요.")
    if command == "commit" and len(result["title"]) > 50:
        notices.append("커밋 제목이 권장 길이 50자를 넘습니다. 최대 72자 규칙은 충족합니다.")

    fields = ["summary"] if command == "commit" else ["summary", "why", "what", "how_to_test"]
    for name in fields:
        value = draft.get(name)
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise RuntimeError(f"AI 응답의 {name} 항목이 문자열 배열이 아닙니다.")
        items = [one_line(mask_sensitive(re.sub(r"^\s*[-*•]\s*", "", item), api_key)) for item in value]
        items = [item for item in items if item]
        if not items:
            raise RuntimeError(f"AI 응답의 {name} 항목이 비어 있습니다.")
        result[name] = items[:2] if name == "summary" else items
    return result, notices


def render_draft(draft: dict, command: str) -> str:
    def bullets(name: str) -> str:
        return "\n".join(f"- {item}" for item in draft[name])

    lines = ["--- 변경 요약 ---", bullets("summary"), ""]
    if command == "commit":
        lines += ["--- Commit Message ---", draft["title"], "", bullets("summary")]
    else:
        # 섹션 헤더와 불릿 기호를 Python에서 붙여 출력 구조를 일정하게 유지합니다.
        lines += ["--- PR Title ---", draft["title"], "", "--- PR Body ---"]
        for heading, name in [("Why", "why"), ("What", "what"), ("How to Test", "how_to_test")]:
            lines += [f"## {heading}", bullets(name), ""]
    lines += ["----------------------"]
    return "\n".join(lines)
