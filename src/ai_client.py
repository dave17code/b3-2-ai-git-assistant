"""표준 라이브러리로 GPT-5.6 Sol REST API를 한 번 호출합니다."""

import json
import urllib.error
import urllib.request

API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = "gpt-5.6-sol"


def generate(api_key: str, model: str, temperature: float, max_tokens: int,
             messages: list[dict], schema: dict) -> dict:
    # 기존 main.py의 호출 방식은 유지하되, 다른 모델 지정은 명확하게 거부합니다.
    if model != MODEL:
        raise RuntimeError(
            f"이 프로젝트는 {MODEL}만 사용합니다. "
            f"main.py의 --model 기본값을 '{MODEL}'로 설정해 주세요."
        )

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        # 간단한 변경 요약에서는 별도의 추론에 사용하는 토큰을 줄입니다.
        "reasoning_effort": "none",
        "max_completion_tokens": max_tokens,
        "store": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "git_draft",
                "strict": True,
                "schema": schema,
            },
        },
    }

    # Python 딕셔너리를 JSON으로 변환하여 POST 요청 본문에 넣습니다.
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
            400: "요청 설정 오류: API 파라미터와 JSON 출력 형식을 확인해 주세요.",
            401: "인증 실패: AI_API_KEY를 확인해 주세요.",
            403: "접근 거부: 프로젝트 및 모델 사용 권한을 확인해 주세요.",
            404: "모델 또는 API 경로를 찾을 수 없습니다.",
            429: "요청 한도 또는 사용 가능 잔액을 확인해 주세요.",
        }

        # API가 제공한 오류 설명을 함께 표시합니다.
        detail = ""
        try:
            detail = json.loads(exc.read().decode("utf-8"))["error"]["message"]
        except (ValueError, KeyError, TypeError, UnicodeError):
            pass

        reason = reasons.get(exc.code, "API 서버 오류가 발생했습니다.")
        raise RuntimeError(f"HTTP {exc.code}: {reason} {detail}") from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(f"네트워크 연결 실패: {exc.reason}") from exc

    except (TimeoutError, OSError) as exc:
        raise RuntimeError(f"API 연결 또는 응답 시간 오류: {exc}") from exc

    except (ValueError, UnicodeError) as exc:
        raise RuntimeError("API 응답을 JSON으로 읽지 못했습니다.") from exc

    try:
        # 생성이 정상적으로 끝났는지 확인한 뒤 JSON 초안을 추출합니다.
        choice = data["choices"][0]
        message = choice["message"]

        if choice["finish_reason"] == "length":
            raise RuntimeError(
                "응답이 토큰 한도에서 잘렸습니다. "
                "--max-tokens를 늘려 다시 실행해 주세요."
            )

        if message.get("refusal") or choice["finish_reason"] != "stop":
            raise RuntimeError(
                "모델이 초안 생성을 완료하지 못했습니다. "
                "입력과 응답 제한을 확인해 주세요."
            )

        draft = json.loads(message["content"])
        if not isinstance(draft, dict):
            raise ValueError("JSON 객체가 아닙니다.")

        return draft

    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError(
            "AI 응답 구조가 올바르지 않습니다. JSON 초안을 받지 못했습니다."
        ) from exc