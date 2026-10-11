"""표준 라이브러리로 Gemini REST API를 한 번 호출합니다."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

API_URL = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/openai/chat/completions"
)


def generate(
    api_key: str,
    model: str,
    temperature: float,
    max_tokens: int,
    messages: list[dict],
    schema: dict,
) -> dict:
    # main.py에서 전달받은 모델과 옵션을 Gemini 요청에 반영합니다.
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "git_draft",
                "strict": True,
                "schema": schema,
            },
        },
    }

    # 딕셔너리를 JSON으로 변환하고 Gemini API 키를 헤더에 담습니다.
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        # 자동 재시도 없이 한 번만 요청합니다.
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as exc:
        reasons = {
            400: "요청 설정 또는 API 키 오류: 아래 상세 메시지를 확인해 주세요.",
            401: "인증 실패: AI_API_KEY에 Gemini API 키를 설정해 주세요.",
            403: "접근 거부: API 키 권한과 프로젝트의 API 사용 가능 여부를 확인해 주세요.",
            404: "모델을 찾을 수 없거나 접근할 수 없습니다. --model 값을 확인해 주세요.",
            429: "요청량 또는 무료 할당량 제한: 아래 상세 메시지를 확인해 주세요.",
            500: "Gemini 서버 내부 오류가 발생했습니다.",
            503: "Gemini 서비스를 일시적으로 사용할 수 없습니다.",
        }

        # API가 제공한 구체적인 오류 설명을 함께 표시합니다.
        detail = ""
        try:
            error_data = json.loads(exc.read().decode("utf-8"))
            error = error_data.get("error", {})
            if isinstance(error, dict):
                detail = str(error.get("message", ""))
        except (ValueError, TypeError, AttributeError, UnicodeError):
            pass

        reason = reasons.get(exc.code, "Gemini API 요청에 실패했습니다.")
        raise RuntimeError(
            f"HTTP {exc.code}: {reason} {detail}"
        ) from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"네트워크 연결 실패: {exc.reason}"
        ) from exc

    except (TimeoutError, OSError) as exc:
        raise RuntimeError(
            f"API 연결 또는 응답 시간 오류: {exc}"
        ) from exc

    except (ValueError, UnicodeError) as exc:
        raise RuntimeError(
            "API 응답을 JSON으로 읽지 못했습니다."
        ) from exc

    try:
        # 생성 완료 여부를 확인한 뒤 응답 안의 JSON 초안을 추출합니다.
        choice = data["choices"][0]
        message = choice["message"]
        finish_reason = choice["finish_reason"]

        if finish_reason == "length":
            raise RuntimeError(
                "응답이 토큰 한도에서 잘렸습니다. "
                "--max-tokens를 늘려 다시 실행해 주세요."
            )

        if message.get("refusal") or finish_reason != "stop":
            raise RuntimeError(
                f"초안 생성이 완료되지 않았습니다. 종료 사유: {finish_reason}"
            )

        draft = json.loads(message["content"])
        if not isinstance(draft, dict):
            raise ValueError("JSON 객체가 아닙니다.")

        return draft

    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError(
            "AI 응답 구조가 올바르지 않습니다. JSON 초안을 받지 못했습니다."
        ) from exc