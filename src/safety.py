"""외부로 보낼 텍스트에서 흔한 민감정보 패턴을 가립니다."""

import re


def mask_sensitive(text: str, api_key: str = "") -> str:
    if api_key:
        text = text.replace(api_key, "[MASKED_API_KEY]")
    # 패턴 기반 보호이므로 모든 종류의 개인정보나 비밀값을 탐지하지는 못합니다.
    text = re.sub(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        "[MASKED_PRIVATE_KEY]", text, flags=re.DOTALL,
    )
    patterns = [
        (r"\bsk-[A-Za-z0-9_-]{8,}", "[MASKED_API_KEY]"),
        (r"\b(?:gh[pousr]_[A-Za-z0-9_]{10,}|github_pat_[A-Za-z0-9_]+)", "[MASKED_TOKEN]"),
        (r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b", "[MASKED_ACCESS_KEY]"),
        (r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[MASKED_EMAIL]"),
    ]
    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)
    text = re.sub(r"(?i)\bBearer\s+[^\s\"']+", "Bearer [MASKED_TOKEN]", text)
    return re.sub(
        r'''(?im)(\b(?:[a-z_]*api_key|access_token|password|secret_key)\b["']?\s*[:=]\s*)'''
        r'''(?:"[^"\r\n]*"|'[^'\r\n]*'|[^\s,;}]+)''',
        r"\1[MASKED_SECRET]", text,
    )


def prepare_input(text: str, api_key: str, safe_mode: bool) -> tuple[str, bool]:
    # 먼저 마스킹하여, 줄 수 제한으로 잘린 비밀키 조각도 전송하지 않게 합니다.
    protected = mask_sensitive(text, api_key)
    if safe_mode:
        limited = "".join(protected.splitlines(keepends=True)[:200])[:20000]
        truncated = len(limited) < len(protected)
        if truncated:
            limited += "\n[入力の残りは省略。表示された変更だけを要約してください。]"
        return limited, truncated
    if len(protected) > 100000:
        raise RuntimeError("変更入力が大きすぎます。--safe-modeを指定して再実行してください。")
    return protected, False
