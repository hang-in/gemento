---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: sampling-params-config-exp10
parallel_group: B
depends_on: [01]
---

# Task 03 — lmstudio_client.py 가 SAMPLING_PARAMS 참조

## Changed files

- `experiments/_external/lmstudio_client.py` — **수정**. `call_with_meter()` 가 SAMPLING_PARAMS default 사용 + `sampling_overrides` 인자 추가. import 1줄 추가.

신규 파일 0. 다른 파일 수정 0.

## Change description

### 배경

현재 `experiments/_external/lmstudio_client.py:33-67` 의 `call_with_meter()` 는 sampling param 을 아예 전달하지 않는다. payload 는:

```python
# 현재 (line 40):
payload: dict = {"model": model, "messages": messages}
if response_format is not None:
    payload["response_format"] = response_format
```

LM Studio 가 sampling 미지정 시 자체 기본값 사용 — 비결정성 + reproducibility appendix 의 sampling 필드 진실성 훼손. 본 task 는 SAMPLING_PARAMS 를 default 로 사용하고, 호출자가 필요 시 `sampling_overrides` dict 로 부분 덮어쓰기 가능하게 한다.

### Step 1 — import 추가

`experiments/_external/lmstudio_client.py:18` 의 기존 `from config import API_CHAT_URL, API_TIMEOUT, MODEL_NAME` 에 `SAMPLING_PARAMS` 추가:

```python
from config import API_CHAT_URL, API_TIMEOUT, MODEL_NAME, SAMPLING_PARAMS
```

### Step 2 — call_with_meter() 시그니처 + payload 변경

함수 시그니처에 `sampling_overrides: dict | None = None` 추가:

```python
def call_with_meter(
    messages: list[dict],
    model: str = MODEL_NAME,
    timeout: int = API_TIMEOUT,
    response_format: dict | None = None,
    sampling_overrides: dict | None = None,
) -> LMStudioMeter:
```

payload 구성을 다음과 같이 변경:

```python
# Step 2 본체:
sampling = dict(SAMPLING_PARAMS)
if sampling_overrides:
    sampling.update(sampling_overrides)

payload: dict = {"model": model, "messages": messages}
for k, v in sampling.items():
    if v is not None:
        payload[k] = v
if response_format is not None:
    payload["response_format"] = response_format
```

### Step 3 — Exp10 의 호출 지점 영향 확인

`experiments/exp10_reproducibility_cost/run.py:107` 의 `lmstudio_call(messages, response_format={"type": "json_object"})` 는 sampling_overrides 미사용 → SAMPLING_PARAMS 그대로 적용 → 결과 동일성 유지.

본 task 에서 `exp10_reproducibility_cost/run.py` 는 **수정 금지** (Scope boundary).

### Step 4 — gemini_client 변경 금지

`experiments/_external/gemini_client.py` 는 별도 모델·별도 sampling 정책. 본 task 범위 밖. 수정 금지.

## Dependencies

- **task-01 완료** — `from config import SAMPLING_PARAMS` 통과 필요.
- 외부 패키지: 없음.

## Verification

```bash
# 1. import 통과 + 시그니처 확인
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from _external.lmstudio_client import call_with_meter
import inspect
sig = inspect.signature(call_with_meter)
assert 'sampling_overrides' in sig.parameters, f'missing sampling_overrides: {list(sig.parameters)}'
default = sig.parameters['sampling_overrides'].default
assert default is None, f'sampling_overrides default must be None, got {default}'
print('OK call_with_meter has sampling_overrides=None default')
"

# 2. SAMPLING_PARAMS 참조 등장
cd /Users/d9ng/privateProject/gemento/experiments && grep -n "SAMPLING_PARAMS" _external/lmstudio_client.py | head -3
# 기대: import 1 + 사용 1 = 2건 이상

# 3. payload 구성 정합성 — call_with_meter 본체에 SAMPLING_PARAMS 사용 확인
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from _external.lmstudio_client import call_with_meter
import inspect
src = inspect.getsource(call_with_meter)
assert 'SAMPLING_PARAMS' in src, 'call_with_meter must reference SAMPLING_PARAMS'
print('OK call_with_meter references SAMPLING_PARAMS')
"

# 4. lmstudio_client.py 본문에 magic number 직접 0건
cd /Users/d9ng/privateProject/gemento/experiments && grep -nE '"(temperature|max_tokens|top_p|seed)"\s*:\s*[0-9]' _external/lmstudio_client.py && echo "FAIL hardcoded sampling found" || echo "OK no hardcoded sampling literals"

# 5. gemini_client.py 미수정 확인
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only experiments/_external/ | grep "gemini_client.py" && echo "FAIL gemini_client modified" || echo "OK gemini_client.py unchanged"

# 6. exp10 run.py 미수정 확인
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only experiments/exp10_reproducibility_cost/ && echo "FAIL exp10 modified" || echo "OK exp10 unchanged"

# 7. 다른 파일 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only experiments/ docs/ | grep -vE "^experiments/(config\.py|_external/lmstudio_client\.py)$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **call_with_meter() 시그니처 확장**: `sampling_overrides` 신규 인자. 기존 호출자 (`exp10_reproducibility_cost/run.py:107`) 는 키워드 미사용 → 호환 유지. 단 향후 호출자가 시그니처 의존하면 영향.
- **dict copy 비용**: `dict(SAMPLING_PARAMS)` 매 호출 1회 — micro 비용, 무시 가능.
- **None 처리 정책**: top_p/seed=None 일 때 payload 에서 제외. 명시적으로 None 으로 override 하면 어떻게 처리할지 ambiguous — 본 task 는 단순화: None 값 모두 제외. 향후 "None override 가 명시적으로 unset 의도" 라면 별도 sentinel 필요. 현재 범위 밖.
- **결과 동일성**: 호출자 (`exp10_reproducibility_cost/run.py`) 가 sampling_overrides 미사용 → SAMPLING_PARAMS 그대로 → temperature=0.1, max_tokens=4096 적용 → 결과 동일. 단 본 task 도입 전 LM Studio 기본값과 0.1/4096 이 다르면 **결과가 달라짐**. 본 plan Constraints 의 "결과 동일성 보장" 위반 가능. → Risk 인식하나 본 task 는 "진실한 sampling 명시" 가 핵심 가치이므로 받아들임. Exp10 본격 실행 전 baseline 이 변경 가능성 명시 (researchNotebook 메모 — task-05).

## Scope boundary

**Task 03 에서 절대 수정 금지**:

- `experiments/config.py` — task-01 결과물 그대로.
- `experiments/orchestrator.py` — task-02 영역.
- `experiments/_external/gemini_client.py` — 본 plan 범위 밖.
- `experiments/_external/__init__.py` — 환경 helper, 본 task 무관.
- `experiments/tests/test_static.py` — task-04 영역.
- `docs/reference/researchNotebook.md` — task-05 영역.
- `experiments/exp10_reproducibility_cost/` 모든 파일.
- 다른 expXX/ 디렉토리.

**허용 범위**:

- `experiments/_external/lmstudio_client.py` 의 import 1줄 갱신.
- `experiments/_external/lmstudio_client.py:call_with_meter()` 의 시그니처 + payload 구성 수정.
