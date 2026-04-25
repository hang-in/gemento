---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: exp10-reproducibility-cost-profile
parallel_group: A
depends_on: []
---

# Task 01 — 외부 API 클라이언트 + metering wrapper (Gemini Flash)

## Changed files

- `experiments/_external/__init__.py` — **신규**. 빈 파일 + `.env` 파일 로더 helper (`load_env_file`) export
- `experiments/_external/gemini_client.py` — **신규**. Google AI Studio (Gemini API) wrapper. token·time·cost USD metering
- `experiments/_external/lmstudio_client.py` — **신규**. LM Studio (OpenAI-compatible at `config.py:API_CHAT_URL`) wrapper. token·time metering, cost는 0
- `.gitignore` — **수정**. `.env` 추가 (보안 권장 — 사용자 노출 안 시키려면)
- `.env.example` — **신규**. 사용자가 복사해서 `gemento/.env` 만들 수 있는 템플릿

신규 외 다른 파일 수정 금지. 특히 `experiments/orchestrator.py`, `experiments/config.py` 는 import 만 가능, 수정 금지.

## Change description

### 배경

Exp10 는 3 condition 비교 실험이다 — `gemma_8loop`, `gemma_1loop`, `gemini_flash_1call`. 그 중 `gemini_flash_1call` 은 외부 API (Google AI Studio Gemini Flash). metering (호출당 input/output token, USD cost, wallclock) 이 결과 분석의 핵심 데이터.

OpenAI 가 아닌 Gemini 를 쓰는 이유: 사용자가 Google Cloud $300 무료 크레딧 보유 + secall 프로젝트에 이미 `SECALL_GEMINI_API_KEY` 가 있음.

### Step 1 — `.env` 파일 정책

본 plan 은 `gemento/.env` 를 표준 키 저장소로 사용. 사용자가 직접 생성·관리:

```
GEMINI_API_KEY=AIza...
```

또는 secall 키를 그대로 쓰고 싶으면:

```
SECALL_GEMINI_API_KEY=AIza...
```

코드는 두 변수 모두 우선순위로 시도:
1. `os.environ.get("GEMINI_API_KEY")` — 1순위
2. `os.environ.get("SECALL_GEMINI_API_KEY")` — 2순위
3. `gemento/.env` 파일 직접 파싱 (export 형식 지원)
4. `../secall/.env` 파일 직접 파싱 (형제 디렉토리 fallback)

### Step 2 — `.gitignore` 갱신

기존 `.gitignore` 에 `.env` 라인 추가 (이미 있으면 skip).

```
.env
.env.local
```

`.env.example` 신규 — git tracked 가능 (값 없는 템플릿):

```
# Gemini API key — Google AI Studio (https://aistudio.google.com/apikey)
GEMINI_API_KEY=

# Optional: secall 프로젝트의 키를 그대로 사용 시 (gemini_client 가 자동 fallback)
# SECALL_GEMINI_API_KEY=
```

### Step 3 — `experiments/_external/__init__.py` 작성

```python
"""External API clients for Exp10 (Gemini Flash, LM Studio)."""
from __future__ import annotations

import os
import re
from pathlib import Path


def load_env_file(path: Path) -> dict[str, str]:
    """`.env` 파일 (export KEY=VALUE 또는 KEY=VALUE) 파싱. 따옴표 제거.
    
    secall 의 `export FOO=bar` 형식과 표준 dotenv `FOO=bar` 형식 모두 지원.
    파일 없거나 권한 오류 시 빈 dict 반환.
    """
    if not path.exists():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # 'export ' prefix 제거
        if line.startswith("export "):
            line = line[len("export "):]
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$", line)
        if not m:
            continue
        key, value = m.group(1), m.group(2).strip()
        # 양 끝 따옴표 제거 (single 또는 double)
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]
        out[key] = value
    return out


def resolve_gemini_key() -> str | None:
    """Gemini API 키 우선순위: env > gemento/.env > ../secall/.env."""
    # 1. env 변수
    for env_name in ("GEMINI_API_KEY", "SECALL_GEMINI_API_KEY"):
        v = os.environ.get(env_name)
        if v:
            return v
    # 2. gemento/.env
    here = Path(__file__).resolve()
    gemento_env = here.parent.parent.parent / ".env"  # .../gemento/.env
    env1 = load_env_file(gemento_env)
    for k in ("GEMINI_API_KEY", "SECALL_GEMINI_API_KEY"):
        if env1.get(k):
            return env1[k]
    # 3. ../secall/.env
    secall_env = here.parent.parent.parent.parent / "secall" / ".env"
    env2 = load_env_file(secall_env)
    for k in ("GEMINI_API_KEY", "SECALL_GEMINI_API_KEY"):
        if env2.get(k):
            return env2[k]
    return None
```

### Step 4 — `experiments/_external/gemini_client.py` 작성

```python
"""Google AI Studio (Gemini API) client with token/time/cost metering for Exp10.

Endpoint: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
default model: gemini-2.5-flash
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass

import httpx

from . import resolve_gemini_key


# 2025-04 기준 Gemini 2.5 Flash 공시 가격 (per 1M tokens)
# https://ai.google.dev/pricing — 사용자가 실험 시점에 재확인 필요
GEMINI_25_FLASH_INPUT_COST_PER_1M = 0.075
GEMINI_25_FLASH_OUTPUT_COST_PER_1M = 0.30

DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_TIMEOUT = 120
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


@dataclass
class CallMeter:
    """단일 LLM 호출의 측정 결과."""
    raw_response: str          # text content
    input_tokens: int
    output_tokens: int
    duration_ms: int
    cost_usd: float
    model: str
    error: str | None = None


def _convert_messages_to_gemini(messages: list[dict]) -> tuple[str | None, list[dict]]:
    """OpenAI 스타일 messages → Gemini API 형식 변환.
    
    Returns:
        (system_instruction_text or None, contents list)
    
    Gemini 는 system 을 별도 필드로 받음. messages 의 첫 번째가 system 이면 분리.
    """
    system_text = None
    contents = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "system":
            # 여러 system 있으면 합침
            system_text = (system_text + "\n" + content) if system_text else content
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
        elif role == "assistant":
            contents.append({"role": "model", "parts": [{"text": content}]})
    return system_text, contents


def call_with_meter(
    messages: list[dict],
    model: str = DEFAULT_MODEL,
    timeout: int = DEFAULT_TIMEOUT,
    api_key: str | None = None,
    response_mime_type: str | None = "application/json",
    input_cost_per_1m: float = GEMINI_25_FLASH_INPUT_COST_PER_1M,
    output_cost_per_1m: float = GEMINI_25_FLASH_OUTPUT_COST_PER_1M,
) -> CallMeter:
    """Gemini API 호출 + metering. response_mime_type='application/json' 으로 JSON 응답 강제 가능."""
    key = api_key or resolve_gemini_key()
    if not key:
        return CallMeter(
            raw_response="", input_tokens=0, output_tokens=0,
            duration_ms=0, cost_usd=0.0, model=model,
            error="GEMINI_API_KEY not found in env/gemento/.env/secall/.env"
        )

    system_text, contents = _convert_messages_to_gemini(messages)

    payload: dict = {"contents": contents}
    generation_config: dict = {}
    if response_mime_type:
        generation_config["responseMimeType"] = response_mime_type
    if generation_config:
        payload["generationConfig"] = generation_config
    if system_text:
        payload["systemInstruction"] = {"parts": [{"text": system_text}]}

    url = f"{GEMINI_BASE_URL}/{model}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}

    start = time.time()
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        return CallMeter(
            raw_response="", input_tokens=0, output_tokens=0,
            duration_ms=int((time.time() - start) * 1000),
            cost_usd=0.0, model=model, error=str(e),
        )

    duration_ms = int((time.time() - start) * 1000)

    # Gemini 응답 파싱 — candidates[0].content.parts[].text 합침
    content_text = ""
    candidates = data.get("candidates") or []
    if candidates:
        parts = (candidates[0].get("content") or {}).get("parts") or []
        content_text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))

    usage = data.get("usageMetadata") or {}
    in_tok = usage.get("promptTokenCount", 0)
    out_tok = usage.get("candidatesTokenCount", 0)
    cost = (
        in_tok * input_cost_per_1m / 1_000_000
        + out_tok * output_cost_per_1m / 1_000_000
    )
    return CallMeter(
        raw_response=content_text, input_tokens=in_tok, output_tokens=out_tok,
        duration_ms=duration_ms, cost_usd=cost, model=model, error=None,
    )
```

### Step 5 — `experiments/_external/lmstudio_client.py` 작성

```python
"""LM Studio client with token/time metering for Exp10.

config.py 의 API_CHAT_URL 을 호출. metering 은 OpenAI 와 동일 인터페이스.
LM Studio 는 로컬이라 cost_usd=0.
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path

# experiments/ 를 sys.path 에 추가하여 config import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from config import API_CHAT_URL, API_TIMEOUT, MODEL_NAME


@dataclass
class LMStudioMeter:
    """단일 LM Studio 호출의 측정 결과."""
    raw_response: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    cost_usd: float            # 항상 0.0 (로컬)
    model: str
    error: str | None = None


def call_with_meter(
    messages: list[dict],
    model: str = MODEL_NAME,
    timeout: int = API_TIMEOUT,
    response_format: dict | None = None,
) -> LMStudioMeter:
    """LM Studio API 호출 + metering."""
    payload: dict = {"model": model, "messages": messages}
    if response_format is not None:
        payload["response_format"] = response_format

    headers = {"Content-Type": "application/json"}

    start = time.time()
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(API_CHAT_URL, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        return LMStudioMeter(
            raw_response="", input_tokens=0, output_tokens=0,
            duration_ms=int((time.time() - start) * 1000),
            cost_usd=0.0, model=model, error=str(e),
        )

    duration_ms = int((time.time() - start) * 1000)
    content = data["choices"][0]["message"]["content"] or ""
    usage = data.get("usage", {})
    return LMStudioMeter(
        raw_response=content,
        input_tokens=usage.get("prompt_tokens", 0),
        output_tokens=usage.get("completion_tokens", 0),
        duration_ms=duration_ms, cost_usd=0.0, model=model, error=None,
    )
```

### Step 6 — 검증 패턴

두 wrapper 모두 import smoke + dummy fallback 검증. 실제 API 호출은 task-06 까지 보류 (Reviewer 가드).

`resolve_gemini_key` 는 env 미설정·.env 미존재 시 None 반환 — fallback 동작 검증.

## Dependencies

- 선행 Task 없음 (`depends_on: []`)
- 외부 패키지: `httpx` (이미 프로젝트 의존성)
- env: `GEMINI_API_KEY` 또는 `SECALL_GEMINI_API_KEY` (실행 시점만, 본 task verification 에서는 미설정 허용)

## Verification

```bash
# 1. 신규 5 파일 존재
test -f /Users/d9ng/privateProject/gemento/experiments/_external/__init__.py && \
test -f /Users/d9ng/privateProject/gemento/experiments/_external/gemini_client.py && \
test -f /Users/d9ng/privateProject/gemento/experiments/_external/lmstudio_client.py && \
test -f /Users/d9ng/privateProject/gemento/.env.example && \
echo "OK 4 files exist"
# .gitignore 는 수정이라 별도 검증

# 2. .gitignore 에 .env 포함
grep -E "^\.env$" /Users/d9ng/privateProject/gemento/.gitignore && echo "OK .gitignore has .env"

# 3. gemini_client import smoke (LLM 호출 0)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from _external.gemini_client import call_with_meter, CallMeter, DEFAULT_MODEL, GEMINI_25_FLASH_INPUT_COST_PER_1M
assert callable(call_with_meter)
assert DEFAULT_MODEL == 'gemini-2.5-flash'
assert GEMINI_25_FLASH_INPUT_COST_PER_1M == 0.075
print('OK gemini_client imports')
"

# 4. lmstudio_client import smoke (LLM 호출 0)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from _external.lmstudio_client import call_with_meter, LMStudioMeter
assert callable(call_with_meter)
print('OK lmstudio_client imports')
"

# 5. 키 미설정 시 fallback (error 필드 set)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import os
os.environ.pop('GEMINI_API_KEY', None)
os.environ.pop('SECALL_GEMINI_API_KEY', None)
# 본 검증은 gemento/.env 가 없는 상태에서만 의미. 사용자가 키 입력했으면 SKIP.
from _external import resolve_gemini_key
key = resolve_gemini_key()
# 키가 있으면 정상 (사용자 .env 로드 성공) — 없으면 None
print(f'OK resolve_gemini_key fallback: {\"key found\" if key else \"None (no .env)\"}')"

# 6. cost 계산 unit (1000 in token + 500 out token = $0.000075 + $0.00015 = $0.000225)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from _external.gemini_client import GEMINI_25_FLASH_INPUT_COST_PER_1M, GEMINI_25_FLASH_OUTPUT_COST_PER_1M
expected = 1000 * GEMINI_25_FLASH_INPUT_COST_PER_1M / 1_000_000 + 500 * GEMINI_25_FLASH_OUTPUT_COST_PER_1M / 1_000_000
assert abs(expected - 0.000225) < 1e-9, f'expected 0.000225, got {expected}'
print(f'OK cost calc: {expected:.6f} USD for 1000 in + 500 out')
"

# 7. message 변환 — system 이 systemInstruction 필드로 분리됨
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from _external.gemini_client import _convert_messages_to_gemini
sys_text, contents = _convert_messages_to_gemini([
    {'role': 'system', 'content': 'You are helpful'},
    {'role': 'user', 'content': 'hi'},
])
assert sys_text == 'You are helpful'
assert len(contents) == 1 and contents[0]['role'] == 'user'
print('OK system/user message conversion')
"

# 8. .env 파일 파싱 (export 형식 지원)
cd /Users/d9ng/privateProject/gemento && _ZO_DOCTOR=0 .venv/bin/python -c "
import tempfile, os
from pathlib import Path
from experiments._external import load_env_file
with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
    f.write('export FOO=bar\nBAZ=qux\n# comment\nQUOTED=\"hello world\"\n')
    p = Path(f.name)
result = load_env_file(p)
assert result['FOO'] == 'bar'
assert result['BAZ'] == 'qux'
assert result['QUOTED'] == 'hello world'
p.unlink()
print('OK load_env_file parses export + standard + comments + quotes')
"

# 9. orchestrator.py 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD experiments/orchestrator.py | wc -l
# 기대: 0

# 10. config.py 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD experiments/config.py | wc -l
# 기대: 0
```

## Risks

- **Gemini API spec 변경**: v1beta endpoint 가 deprecate 될 수 있음. v1 로 변경 시 `GEMINI_BASE_URL` 만 수정.
- **3.x 모델 등장 시**: 사용자가 언급한 "3.1 플래시" — 현재 (2026-04 기준) 명확치 않음. `DEFAULT_MODEL` 상수만 변경하면 적용. 또는 `call_with_meter(model="...")` 인자로 override 가능.
- **httpx 환경 의존**: 이미 프로젝트 의존성. 미설치 시 import error.
- **token usage 미반환 가능성**: Gemini 응답에 `usageMetadata` 없으면 0 fallback. metering 부정확. 안전을 위해 본 코드는 `.get(..., 0)` 패턴.
- **system message 처리**: Gemini 가 `systemInstruction` 필드를 별도로 받음. message 변환 함수 (`_convert_messages_to_gemini`) 가 핵심. 잘못 구현하면 system 이 user 로 합쳐짐.
- **rate limit**: Gemini Free Tier 는 ~15 RPM. Exp10 의 180 호출은 task-06 에서 1초 sleep 으로 약 60 RPM 시도 — 무료 거부 가능. 사용자가 $300 크레딧이라 paid tier 이면 1500 RPM 이상이라 OK. **task-06 에서 429 발생 시 sleep 늘리기 fallback 명시.**
- **.env 파일 보안**: `.gitignore` 에 추가하지만 사용자가 수동 commit 시 노출. CLAUDE.md 또는 README 에 경고 추가 — 본 task 범위 밖.
- **`secall/.env` 의존성**: 형제 디렉토리 위치 hardcode. 다른 환경에서 실행 시 fallback 실패 — gemento/.env 에 직접 키 입력하면 해결.
- **양 끝 따옴표 처리**: `load_env_file` 가 단일/이중 따옴표 모두 제거. 키 안에 `=` 가 들어가면 split 깨질 수 있음 — Gemini API 키는 `=` 없으니 안전.

## Scope boundary

**Task 01 에서 절대 수정 금지**:

- `experiments/orchestrator.py` — 본문 일체.
- `experiments/config.py` — `API_CHAT_URL`, `MODEL_NAME` 등 import 만, 수정 금지.
- `experiments/run_experiment.py` — Exp10 dispatcher 추가는 task-05 영역.
- `experiments/exp10_reproducibility_cost/` — task-02·03·04·05·06 영역.
- 다른 expXX/ 디렉토리.
- `experiments/tests/test_static.py` — task-05 영역.

**허용 범위**:

- `experiments/_external/__init__.py`, `gemini_client.py`, `lmstudio_client.py` 신규.
- `gemento/.gitignore` 에 `.env` 한 줄 추가.
- `gemento/.env.example` 신규 (템플릿, 값 없음).
- 위 외 일체 수정 금지. 사용자가 직접 `gemento/.env` 생성 + `GEMINI_API_KEY` 입력 (본 task 범위 밖).
