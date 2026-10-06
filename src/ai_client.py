"""표준 라이브러리로 OpenAI REST API를 한 번 호출합니다."""

import json
import urllib.error
import urllib.request

API_URL = "https://api.openai.com/v1/chat/completions"


def generate(api_key: str, model: str, temperature: float, max_tokens: int,
             messages: list[dict], schema: dict) -> dict:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        # CLI 이름은 과제 예시를 따르고, 실제 요청은 현재 API 파라미터에 연결합니다.
        "max_completion_tokens": max_tokens,
        "store": False,
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "git_draft", "strict": True, "schema": schema},
        },
    }
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        # 자동 재시도 없이 1회만 요청하여 호출 횟수와 비용을 예측할 수 있게 합니다.
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        reasons = {
            400: "요청 설정 오류: 모델의 temperature/JSON 출력 지원 여부와 토큰 한도를 확인해 주세요.",
            401: "인증 실패: AI_API_KEY를 확인해 주세요.",
            403: "접근 거부: 프로젝트 및 모델 사용 권한을 확인해 주세요.",
            404: "모델을 찾을 수 없습니다. --model 값을 확인해 주세요.",
            429: "요청 한도 또는 사용 가능 잔액을 확인해 주세요.",
        }
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
        choice = data["choices"][0]
        if choice["finish_reason"] == "length":
            raise RuntimeError("응답이 토큰 한도에서 잘렸습니다. --max-tokens를 늘려 다시 실행해 주세요.")
        if choice["message"].get("refusal") or choice["finish_reason"] != "stop":
            raise RuntimeError("모델이 초안 생성을 완료하지 못했습니다. 입력과 응답 제한을 확인해 주세요.")
        draft = json.loads(choice["message"]["content"])
        if not isinstance(draft, dict):
            raise ValueError("JSON 객체가 아닙니다.")
        return draft
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("AI 응답 구조가 올바르지 않습니다. JSON 초안을 받지 못했습니다.") from exc
