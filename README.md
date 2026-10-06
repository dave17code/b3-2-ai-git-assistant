# B3-2 · AI Git 설명 도우미

Git 변경 사항을 수집해 **커밋 메시지 또는 PR 제목/본문 초안**을 생성하는 Python CLI입니다.
미션의 필수 기능에 집중하며, 웹 화면·DB·실제 커밋·push·GitHub PR 자동 등록 기능은 없습니다.

## 1. 준비 및 설치

- Python **3.10 이상**
- Git 설치 및 `git` 명령 실행 가능
- OpenAI API Key와 API를 사용할 수 있는 계정 상태
- 네트워크 연결

**Python 표준 라이브러리만 사용하므로 `pip install`이 필요하지 않습니다.**
ZIP을 풀고 `main.py`와 `README.md`가 있는 `b3-2-ai-git-assistant` 폴더를 엽니다.

Windows Git Bash 기준:

```bash
cd b3-2-ai-git-assistant
py --version
git --version
```

이 문서의 `py`는 macOS/Linux에서는 `python3`로 바꿉니다.
프로젝트 파일은 UTF-8로 저장되어 있습니다.

## 2. API Key 환경변수 설정

이 프로젝트는 **`AI_API_KEY` 하나만 읽습니다.** 실제 키를 코드나 파일에 넣지 마세요.
키는 [OpenAI API 대시보드](https://platform.openai.com/api-keys)에서 관리합니다.

Windows Git Bash에서는 다음 명령으로 화면과 명령 기록에 키 값을 직접 남기지 않고 입력할 수 있습니다.

```bash
read -rsp "OpenAI API Key: " AI_API_KEY
export AI_API_KEY
printf '\n'
```

입력하는 키는 화면에 표시되지 않습니다. 붙여넣기 후 Enter를 누르세요.

Windows PowerShell:

```powershell
$env:AI_API_KEY = "실제로_발급받은_API_Key"
```

macOS/Linux의 zsh 또는 bash:

```bash
export AI_API_KEY="실제로_발급받은_API_Key"
```

환경변수는 현재 터미널 세션에 적용됩니다. 새 터미널에서는 다시 설정해야 합니다.
`.env` 파일을 자동으로 읽는 기능은 없습니다.

## 3. 처음 실행하는 순서

아래 Git 명령은 **사용자가 직접 실행하는 준비 작업**입니다. CLI 내부에서 실행하지 않습니다.
압축 파일에는 `.git`과 개인 Git 설정이 포함되어 있지 않습니다.

새 프로젝트라면 최초 기준 커밋을 만듭니다. 이미 Git 저장소로 관리 중이면 이 준비는 생략합니다.

```bash
git init
git add .
git commit -m "chore: B3-2 AI Git 설명 도우미 추가"
git branch -M main
git switch -c feature/readme-guide
```

`Author identity unknown` 오류가 나오면 본인 이름과 GitHub용 이메일을 **이 저장소에** 설정하고 커밋을 다시 실행합니다.

```bash
git config user.name "본인 이름"
git config user.email "본인의 GitHub 이메일 또는 noreply 이메일"
```

이제 `README.md` 마지막에 `B3-2 CLI 실행을 확인합니다.` 같은 설명 한 줄을 추가하고 저장합니다.
기준 커밋 이후의 변경을 입력으로 사용하기 위한 단계입니다.

```bash
git status
git diff
py main.py commit --safe-mode
py main.py pr --safe-mode
```

각 명령이 변경 요약과 해당 초안을 출력합니다. 두 번 실행하면 API도 각각 1회씩, 총 2회 요청됩니다.
**실제 커밋 전에 두 초안을 모두 생성**하세요. 커밋 후 작업 폴더가 깨끗하면 변경 사항이 없다고 종료합니다.

이 프로그램은 현재 실행한 Git 루트를 분석합니다. `src` 하위 폴더에서는 실행하지 마세요.

## 4. 명령과 옵션

```bash
py main.py commit
py main.py pr
py main.py commit --model gpt-4.1-mini --temperature 0.2 --max-tokens 1200 --safe-mode
py main.py --help
```

| 옵션 | 기본값 | 역할 |
|---|---|---|
| `--model` | `gpt-4.1-mini` | 사용할 OpenAI 모델 |
| `--temperature` | `0.2` | 출력 변동성 조절. 0~2 범위 |
| `--max-tokens` | `1200` | 생성 토큰 상한. 1 이상의 정수 |
| `--safe-mode` | 끔 | 전송 원문을 처음 200줄/20,000자 이내로 제한 |

미션의 표기 예시인 `-model`, `-temperature`, `-max-tokens`, `-safe-mode`도 지원합니다.
API Key·이메일 등 **패턴 마스킹은 안전 모드 여부와 관계없이 항상 적용**합니다.
안전 모드는 여기에 입력량 제한을 추가합니다. 생략된 부분이 있으면 경고를 출력합니다.

- 낮은 temperature는 비교적 일정한 표현을 유도하지만 정확성을 보장하지 않습니다.
- 토큰 수와 글자 수는 다릅니다. 출력 한도가 너무 작으면 본문이 잘려 오류로 종료할 수 있습니다.
- CLI의 `--max-tokens`는 API의 `max_completion_tokens`로 전달됩니다.
- 모델 변경 시 Chat Completions, temperature, JSON Schema 출력 지원과 계정 접근 권한을 확인하세요.
- 지원하지 않는 모델/파라미터 조합은 API 오류 원인을 출력하며 자동 대체하지 않습니다.

## 5. 어떤 변경을 수집하나요?

| 상태 | 사용하는 Git 명령 |
|---|---|
| 변경 파일 목록 | `git status --porcelain=v1 -z --untracked-files=all` |
| 스테이징된 변경 | `git diff --cached` |
| 스테이징되지 않은 변경 | `git diff` |
| 새 미추적 파일 | `git diff --no-index`로 빈 파일과 비교 |

실제 코드에서는 컬러/외부 diff 프로그램을 끄는 옵션도 추가합니다.
Git 수집에는 `status`와 `diff` 계열만 사용하며 `git add`나 커밋을 자동 실행하지 않습니다.
파일명에 공백이나 한글이 있어도 처리합니다. 바이너리 파일은 Git이 출력한 변경 정보만 사용합니다.
`.gitignore`로 무시된 미추적 파일은 수집하지 않습니다. 이미 추적 중인 파일은 `.gitignore`만으로 제외되지 않습니다.

PR 초안도 **현재 로컬 변경**을 설명합니다. 이미 커밋된 브랜치 전체와 `main`의 차이를 비교하는 기능은 없습니다.
같은 파일에 staged/unstaged 변경이 함께 있으면 두 단계의 변경을 구분해 모델에 전달합니다.

## 6. 출력 예시

아래는 `src/search.py`에서 빈 검색어 처리를 추가했다고 가정한 **설명용 예시**입니다.
이 프로젝트에 검색 기능이 포함되어 있거나 실제 API 호출을 기록한 것은 아닙니다.
실제 문구는 입력과 모델 응답에 따라 달라집니다.

### 커밋

```text
[INFO] Git status 수집 완료: 1개 파일 변경
 M src/search.py
[INFO] Git diff 수집 완료: 12줄
[INFO] API Key·이메일 등 공통 민감정보 패턴 마스킹 적용
[INFO] 안전 모드: 전송 원문 최대 200줄 / 20,000자
[INFO] AI API 요청 중... (모델: gpt-4.1-mini)
[DONE] 초안 생성 및 형식 검증 완료
--- 변경 요약 ---
- src/search.py에서 검색어 앞뒤 공백을 제거합니다.
- 빈 검색어 입력 시 빈 목록을 반환합니다.

--- Commit Message ---
fix: 빈 검색어 처리 추가

- src/search.py에서 검색어 앞뒤 공백을 제거합니다.
- 빈 검색어 입력 시 빈 목록을 반환합니다.
----------------------
[INFO] 내용 검토 후 직접 적용해 주세요. 테스트 실행 및 Git 변경은 수행하지 않았습니다.
[INFO] AI API 요청 횟수: 1
```

### PR

```text
--- 변경 요약 ---
- 빈 검색어 처리와 검색어 공백 제거를 추가합니다.

--- PR Title ---
fix: 빈 검색어 처리 및 공백 제거

--- PR Body ---
## Why
- 불필요한 검색 실행을 줄이려는 변경으로 추정됩니다. 실제 배경은 작성자가 확인해 주세요.

## What
- src/search.py에서 공백을 제거하고 빈 검색어에는 빈 목록을 반환합니다.

## How to Test
- 빈 문자열과 공백 문자열 입력 시 빈 목록이 반환되는지 확인합니다.
- 정상 검색어의 검색 결과가 기존과 동일한지 확인합니다.

----------------------
```

`How to Test`는 실행할 테스트의 **제안**입니다. 도구가 테스트를 실행하거나 통과를 확인하지 않습니다.
변경 배경을 diff로 확정할 수 없으면 추정임을 밝히도록 지시합니다. 실제 배경에 맞게 수정하세요.

## 7. 출력 검증과 후처리

- API에 JSON Schema를 보내 제목과 문자열 배열 형태로 결과를 요청합니다.
- 필수 내용이 없거나 배열 형식이 잘못되면 오류로 종료합니다.
- 제목/불릿의 줄바꿈과 제어 문자를 제거하고 공백을 정리합니다.
- 커밋 제목은 **최대 72자**, PR 제목은 **최대 80자**로 자르고 경고를 표시합니다.
- 커밋 제목이 권장 길이 50자를 넘으면 검토 안내를 표시합니다.
- 커밋 본문은 핵심 변경 요약 **1~2개 불릿**으로 구성합니다.
- PR 본문은 Python이 `Why`, `What`, `How to Test` 헤더와 각 섹션의 불릿을 붙입니다.
- 제목을 줄인 경우 의미가 자연스러운지 반드시 검토하세요.

형식 다듬기는 **후처리 방식**입니다. 결과 재생성이나 네트워크 자동 재시도는 하지 않으며,
실행당 API 요청은 0회 또는 1회입니다. 제목/본문 내용의 사실성은 사용자가 검토합니다.

## 8. 보안 및 비용

- API Key는 환경변수에서 읽어 인증 헤더에 사용합니다. 프롬프트에 넣지 않습니다.
- diff와 파일 목록에서 실제 API Key, 일반적인 키/토큰 패턴, 이메일, 비밀키 블록 등을 마스킹합니다.
- 패턴으로 탐지하지 못하는 비밀값·개인정보가 있을 수 있으므로 **실행 전에 `git diff`, `git diff --cached`, 새 파일 내용을 직접 확인**하세요.
- `.env`, 인증키, 개인정보를 Git에 넣지 마세요. `.gitignore`에는 일반적인 민감 파일 패턴을 포함했습니다.
- `--safe-mode`는 원문을 200줄/20,000자로 제한합니다. 생략 안내 문장은 제한된 원문 뒤에 추가됩니다.
- 기본 모드도 마스킹 후 원문이 100,000자를 넘으면 API를 호출하지 않고 안전 모드 사용을 안내합니다.
- 입력 일부를 생략한 초안은 전체 변경을 설명하지 못합니다. 작은 단위의 변경으로 나눠 사용하세요.
- API 호출에 사용량 비용이 발생할 수 있습니다. `max_tokens`는 출력 상한이며 입력 토큰도 비용에 영향을 줍니다.
- 코드에 `store: false`를 지정하지만 이것이 서비스의 모든 보관 정책을 해제한다는 의미는 아닙니다.

## 9. 오류 및 종료 코드

| 상황 | 처리 |
|---|---|
| 변경 없음 | `변경 사항이 없습니다` 출력, API 0회, 정상 종료 |
| Git 루트 아님 / Git 없음 / 충돌 | 원인 안내 후 종료 |
| Key 미설정 | `AI_API_KEY` 안내, API 0회 |
| HTTP 401 / 403 | 인증 / 권한 오류 안내 |
| HTTP 400 / 404 | 모델과 파라미터 확인 안내 |
| HTTP 429 | 요청 한도 또는 잔액 확인 안내 |
| 네트워크 / 시간 초과 | 원인을 포함한 오류 출력 |
| 출력 잘림 | `--max-tokens`를 늘리도록 안내 |
| JSON / 필수 내용 오류 | 형식 오류로 종료, 자동 재요청 없음 |

종료 코드는 성공 또는 변경 없음 `0`, 실행 오류 `1`, CLI 인자 오류 `2`, 사용자 중단 `130`입니다.
정상/오류 로그에 API 요청 횟수를 표시합니다. 명령 인자 자체가 틀리면 argparse의 사용법 안내로 종료합니다.

## 10. 검증

API Key와 네트워크 없이 테스트할 수 있습니다.

```bash
py -m unittest discover -s tests -v
```

테스트는 임시 Git 저장소를 만들고, API 통신 부분만 모의 응답으로 대체합니다.
실제 프로젝트의 Git 상태를 바꾸거나 외부 API를 호출하지 않습니다.
새 파일·스테이징·미스테이징·이름 변경·삭제, 빈 저장소, 오류 처리,
프롬프트 마스킹, 제목 길이, PR 섹션, 호출 횟수와 요청 파라미터를 확인합니다.

**실제 OpenAI 연결과 생성 품질은 본인 API Key로 3절의 두 명령을 실행해 별도로 확인해야 합니다.**

## 11. GitHub 업로드 및 브랜치 작업 흐름

GitHub에서 본인 계정에 빈 저장소 `b3-2-ai-git-assistant`를 만듭니다.
이미 로컬 README가 있으므로 GitHub에서 README를 추가 생성하지 않습니다.
아래 `YOUR_GITHUB_ID`는 본인 계정명으로 바꾸세요.

```bash
git remote add origin https://github.com/YOUR_GITHUB_ID/b3-2-ai-git-assistant.git
git push -u origin main
```

3절에서 변경한 README를 검토하고, 생성된 커밋 메시지를 사용해 작업 브랜치에 커밋합니다.

```bash
git add README.md
git commit
git push -u origin feature/readme-guide
```

`git commit`이 여는 편집기에 생성된 제목과 본문을 붙여넣고 저장·종료합니다.
GitHub에서 `feature/readme-guide` → `main` PR을 열고, 앞서 생성한 PR 제목/본문을 검토해 붙여넣습니다.
PR을 병합하면 최종 코드와 브랜치 작업 기록을 함께 확인할 수 있습니다.
원격 저장소 생성·인증·push·PR 등록은 사용자가 직접 수행해야 미션 제출 조건이 완료됩니다.

## 12. 파일별 역할 및 요구사항 연결

| 파일 | 역할 |
|---|---|
| `main.py` | 옵션 해석, 환경변수 읽기, 전체 실행, 오류와 결과 출력 |
| `src/git_reader.py` | `subprocess`로 Git 상태와 diff 수집 |
| `src/safety.py` | 민감정보 마스킹과 안전 모드 입력 제한 |
| `src/prompts.py` | 커밋/PR 지시문과 JSON Schema 구성 |
| `src/ai_client.py` | HTTPS POST, 응답 파싱, 인증/네트워크 오류 처리 |
| `src/output.py` | 제목 길이 검증, 후처리, PR 템플릿 출력 |
| `tests/test_app.py` | 임시 Git 저장소 및 모의 API 기반 자동 검증 |

실행 순서: **명령 해석 → Git 수집 → 입력 보호 → 프롬프트 구성 → API 1회 호출 → 검증/후처리 → 초안 출력**.

| 미션 필수 항목 | 구현 위치 |
|---|---|
| Git 루트 및 변경 없음 처리 | `git_reader.py`, `main.py` |
| 환경변수 Key / REST 요청 / API 오류 | `main.py`, `ai_client.py` |
| 모델·temperature·토큰 옵션 | `main.py`, `ai_client.py` |
| 커밋 제목 및 본문 | `prompts.py`, `output.py` |
| PR 제목 및 Why/What/How to Test | `prompts.py`, `output.py` |
| 제목 길이 및 형식 후처리 | `output.py` |
| 안전 모드 및 호출 횟수 | `safety.py`, `main.py` |
| 설치·예시·주의사항 | 이 README |
| 실제 API 확인 / GitHub push | 본인 계정에서 3절 / 11절 수행 |

### API 규격 참고

- [OpenAI Chat Completions API](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create)
- [GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini)

구현 시 공식 문서에서 endpoint, temperature, max_completion_tokens, JSON Schema 지원을 확인했습니다.
