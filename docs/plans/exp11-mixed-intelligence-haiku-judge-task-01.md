---
type: plan-task
status: todo
updated_at: 2026-05-02
parent_plan: exp11-mixed-intelligence-haiku-judge
parallel_group: A
depends_on: []
---

# Task 01 — Gemini Flash client 재사용 검증 + config 보강

## Changed files

- `experiments/config.py` — **수정 (추가만)**. `GEMINI_FLASH_MODEL_ID` 상수 추가 (또는 gemini_client 의 `DEFAULT_MODEL` 재사용 — 본 task 결정)
- (선택) `experiments/_external/__init__.py` — 변경 0 (read-only 검증만)
- (선택) `experiments/_external/gemini_client.py` — 변경 0 (read-only 검증만)

수정 1 또는 0 (검증만). 신규 0.

## Change description

### 배경

v2 (2026-05-02) — Judge 모델 Haiku → Gemini Flash. 기존 `experiments/_external/gemini_client.py` (Exp10 영역) 재사용. 본 task = 재사용 가능성 검증 + 필요 시 작은 config 추가.

### Step 1 — 기존 gemini_client 정찰

```bash
.venv/Scripts/python -c "
from experiments._external import resolve_gemini_key
from experiments._external.gemini_client import (
    call_with_meter, CallMeter, DEFAULT_MODEL, DEFAULT_TIMEOUT,
    GEMINI_25_FLASH_INPUT_COST_PER_1M, GEMINI_25_FLASH_OUTPUT_COST_PER_1M,
)
print(f'  DEFAULT_MODEL = {DEFAULT_MODEL}')
print(f'  input cost = \${GEMINI_25_FLASH_INPUT_COST_PER_1M}/MTok')
print(f'  output cost = \${GEMINI_25_FLASH_OUTPUT_COST_PER_1M}/MTok')
print(f'  GEMINI_API_KEY 발견: {bool(resolve_gemini_key())}')
"
```

기대:
- `DEFAULT_MODEL = gemini-2.5-flash`
- input $0.075 / output $0.30 / MTok
- API key 발견 ✓ (사용자 이미 보유)

### Step 2 — `experiments/config.py` 보강 (선택)

`config.py` 가 이미 `MODEL_NAME = "gemma4-e4b"` 등 정의. Mixed plan 의 신규 도구가 import 시 명시적 상수 있으면 가독성 ↑.

```python
# config.py 끝에 추가:
# ── Mixed Intelligence (Exp11) ──
GEMINI_FLASH_MODEL_ID = "gemini-2.5-flash"  # gemini_client 의 DEFAULT_MODEL 과 동일
```

또는 추가 안 함 — `gemini_client.DEFAULT_MODEL` 직접 import.

**Architect 결정**: 추가 안 함 (over-engineering). task-03 의 run.py 가 `from experiments._external.gemini_client import call_with_meter, DEFAULT_MODEL as GEMINI_FLASH_MODEL` 패턴.

### Step 3 — system prompt 분리 검증

기존 `gemini_client._convert_messages_to_gemini` 가 OpenAI 스타일 messages 의 system role 을 자동 분리하여 Gemini API 의 `systemInstruction` 필드로 전달 — 본 plan 의 c_caller 가 그대로 활용 가능.

```python
# 검증
from experiments._external.gemini_client import _convert_messages_to_gemini
sys_text, contents = _convert_messages_to_gemini([
    {"role": "system", "content": "You are a Judge."},
    {"role": "user", "content": "Approve or reject."},
])
assert sys_text == "You are a Judge."
assert len(contents) == 1
assert contents[0]["role"] == "user"
```

### Step 4 — 짧은 호출 dry-run (사용자 직접, ~$0.0001)

**사용자 실행 의무** (메모리 정책: Architect/Developer 가 모델 호출 금지):

```powershell
.\.venv\Scripts\python.exe -c "
from experiments._external.gemini_client import call_with_meter
result = call_with_meter([
    {'role': 'system', 'content': 'You are a verdict judge. Reply with JSON only.'},
    {'role': 'user', 'content': 'Should we accept the answer 13 apples and 7 oranges? Reply: {\"verdict\":\"accept\"|\"reject\"}'},
], response_mime_type='application/json')
print(f'  text={result.raw_response!r}')
print(f'  tokens=in:{result.input_tokens} out:{result.output_tokens}')
print(f'  cost=\${result.cost_usd:.6f}')
print(f'  err={result.error}')
"
```

기대:
- text = `{"verdict":"accept"}` 또는 비슷한 JSON
- tokens 적음 (~50 in + 30 out)
- cost ~$0.00001
- err = None

→ 통과 시 본 task 마감. 실패 시 사용자 호출 (API key 확인 / 네트워크 / SDK 차이).

## Dependencies

- 패키지: 표준 + `httpx` (이미 설치)
- 다른 subtask: 없음 (parallel_group A)
- 기존 `experiments/_external/gemini_client.py` (Exp10 영역) — read-only

## Verification

```bash
# 1) gemini_client import + DEFAULT_MODEL
.venv/Scripts/python -c "
from experiments._external.gemini_client import call_with_meter, DEFAULT_MODEL
assert DEFAULT_MODEL == 'gemini-2.5-flash'
print('verification 1 ok: gemini_client import')
"

# 2) resolve_gemini_key — API key 발견 (사용자 환경)
.venv/Scripts/python -c "
from experiments._external import resolve_gemini_key
key = resolve_gemini_key()
assert key, 'GEMINI_API_KEY not found in env / gemento/.env / secall/.env'
print(f'verification 2 ok: API key 발견 (length={len(key)})')
"

# 3) _convert_messages_to_gemini 동작
.venv/Scripts/python -c "
from experiments._external.gemini_client import _convert_messages_to_gemini
sys_text, contents = _convert_messages_to_gemini([
    {'role': 'system', 'content': 'sys'},
    {'role': 'user', 'content': 'q'},
])
assert sys_text == 'sys'
assert len(contents) == 1 and contents[0]['role'] == 'user'
print('verification 3 ok: messages 변환')
"

# 4) (사용자 직접) 짧은 dry-run — Step 4 의 명령
```

3 명령 (1-3 본 task 검증) + 4 (사용자 dry-run).

## Risks

- **Risk 1 — API key 부재**: `resolve_gemini_key()` 가 None 반환 시 사용자 호출 (env 또는 .env 확인)
- **Risk 2 — Gemini API 가격 변동**: `GEMINI_25_FLASH_INPUT_COST_PER_1M` 의 정의된 값 (2025-04 시점) 이 2026-05 시점에 변동 가능. 단 큰 변동 안 — disclosure 만 (실험 시점 사용자 재확인 권고)
- **Risk 3 — system prompt 분리 호환**: 기존 `_convert_messages_to_gemini` 가 OpenAI 호환. ABC chain 의 system prompt 가 잘 분리되는지 dry-run 검증
- **Risk 4 — JSON mime type 응답이 Tattoo schema 와 호환 안 됨**: gemini_client 의 `response_mime_type='application/json'` 이 default. Judge 응답이 JSON 안 일 수도 — task-03 에서 mime type 결정 (text 또는 json)

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/_external/gemini_client.py` — read-only (Exp10 영역, 기존 코드 보존)
- `experiments/_external/__init__.py` — read-only
- `experiments/orchestrator.py` (task-02 영역)
- `experiments/measure.py` / `score_answer_v*` — 본 plan 영역 외
- `experiments/run_helpers.py` (Stage 2A) — 변경 금지
- `experiments/schema.py` — 변경 금지
- 모든 기존 `experiments/exp**/run.py` — 변경 금지

## 폐기 사항 (v1 → v2)

- ❌ `experiments/anthropic_client.py` 신규 — 폐기 (gemini_client 재사용)
- ❌ `experiments/config.py` 의 `HAIKU_MODEL_ID` / `HAIKU_PRICING` — 폐기 (gemini_client 의 DEFAULT_MODEL / cost 상수 재사용)
- ❌ `anthropic` Python SDK 설치 — 폐기 (httpx 직접, gemini_client 가 내부 사용)
- ❌ ANTHROPIC_API_KEY 환경 변수 — 폐기 (GEMINI_API_KEY 사용, 사용자 이미 보유)
