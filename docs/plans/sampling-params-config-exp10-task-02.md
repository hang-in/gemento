---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: sampling-params-config-exp10
parallel_group: B
depends_on: [01]
---

# Task 02 — orchestrator.py 가 SAMPLING_PARAMS 참조

## Changed files

- `experiments/orchestrator.py` — **수정**. `call_model()` 의 payload 구성 (line 67-72) 이 SAMPLING_PARAMS 참조하도록 변경. import 1줄 추가.

신규 파일 0. 다른 파일 수정 0.

## Change description

### 배경

현재 `experiments/orchestrator.py:71` 에 `temperature=0.1`, `max_tokens=4096` 이 payload dict 안에 하드코딩되어 있다.

```python
# 현재 (line 67-72):
payload: dict = {
    "model": model,
    "messages": list(messages),
    "max_tokens": 4096,
    "temperature": 0.1,
}
```

본 task 는 `from config import SAMPLING_PARAMS` 를 통해 일원화된 dict 참조로 변경한다. None 값 (top_p, seed) 은 payload 에 미포함 → LM Studio 기본 동작 유지 → 기존 14 실험 결과 동일성 보장.

### Step 1 — import 추가

`experiments/orchestrator.py` 의 기존 `from config import ...` 줄에 `SAMPLING_PARAMS` 추가:

```python
# 기존 (예시):
from config import API_CHAT_URL, API_TIMEOUT, MODEL_NAME, ASSERTION_SOFT_CAP, ...
# →
from config import API_CHAT_URL, API_TIMEOUT, MODEL_NAME, ASSERTION_SOFT_CAP, SAMPLING_PARAMS, ...
```

(실제 import 라인은 파일 상단을 읽어 확인 후 합치기)

### Step 2 — payload 구성 변경

`call_model()` 의 line 67-72 (또는 변경된 위치) 수정:

```python
# 새 형태:
payload: dict = {
    "model": model,
    "messages": list(messages),
}
# SAMPLING_PARAMS 의 None 이 아닌 값만 spread
for k, v in SAMPLING_PARAMS.items():
    if v is not None:
        payload[k] = v
```

또는 dict comprehension:

```python
payload: dict = {
    "model": model,
    "messages": list(messages),
    **{k: v for k, v in SAMPLING_PARAMS.items() if v is not None},
}
```

두 방식 모두 OK. 가독성 우선이면 첫 번째.

### Step 3 — 동일 함수 내 다른 sampling 사용처 검색

`call_model()` 외에 orchestrator.py 의 다른 함수가 sampling param 을 직접 설정하는지 확인. grep 결과 없으면 (현재 검증된 대로) 본 task 범위는 line 67-72 만.

```bash
grep -n "temperature\|max_tokens\|top_p\|seed" experiments/orchestrator.py
```

`call_model()` 외 매치가 있으면 별도 보고 + plan 보강 (rework). 본 verification 의 일부.

## Dependencies

- **task-01 완료** — `from config import SAMPLING_PARAMS` 통과해야 함.
- 외부 패키지: 없음.

## Verification

```bash
# 1. import 통과
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import orchestrator
from config import SAMPLING_PARAMS
print('OK orchestrator + SAMPLING_PARAMS import')
"

# 2. orchestrator.py 본문에 magic number (temperature=0.1, max_tokens=4096) 직접 등장 0건
cd /Users/d9ng/privateProject/gemento/experiments && grep -nE '"(temperature|max_tokens)"\s*:\s*[0-9]' orchestrator.py && echo "FAIL hardcoded sampling found" || echo "OK no hardcoded sampling literals"

# 3. SAMPLING_PARAMS 참조 등장
cd /Users/d9ng/privateProject/gemento/experiments && grep -n "SAMPLING_PARAMS" orchestrator.py | head -3
# 기대: import 라인 + 사용 라인 >=2건

# 4. call_model() payload 가 의도대로 SAMPLING_PARAMS 사용 — dummy 호출로 payload 검증 (네트워크 X)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
# call_model() 본체를 import 후 payload 구성 부분만 reflection 으로 검증
from orchestrator import call_model
import inspect
src = inspect.getsource(call_model)
assert 'SAMPLING_PARAMS' in src, 'call_model must reference SAMPLING_PARAMS'
print('OK call_model references SAMPLING_PARAMS')
"

# 5. 다른 sampling 사용처 없음 — call_model 외에서 temperature/max_tokens 등 직접 등장 검색
cd /Users/d9ng/privateProject/gemento/experiments && grep -nE "(temperature|max_tokens|top_p|seed)\s*[:=]" orchestrator.py | grep -v "SAMPLING_PARAMS" || echo "OK only SAMPLING_PARAMS references"

# 6. 다른 파일 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only experiments/ docs/ | grep -vE "^experiments/(config|orchestrator)\.py$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **import 라인 합치기 실패**: 기존 `from config import ...` 가 multi-line 일 경우 SAMPLING_PARAMS 추가 위치 주의. import 정렬 깨지면 다른 검증 영향 가능.
- **결과 동일성**: SAMPLING_PARAMS 의 `temperature=0.1`, `max_tokens=4096` 가 그대로 적용되면 payload 동일. 단 dict ordering 차이로 wire-level JSON 직렬화 순서 변경 가능 — LM Studio 가 key order 무시하므로 무관 (검증된 OpenAI 호환 동작).
- **None 미포함 정책**: top_p/seed=None 일 때 payload 에서 빠짐. 본 task 의 핵심 동작 — LM Studio 기본값 유지. 향후 None 이 아닌 값 설정 시 자동 적용.
- **call_model() 의 tool loop 영향**: line 83-114 의 tool_calls 루프에서 payload["messages"] append. SAMPLING_PARAMS 와 무관 — sampling 은 첫 dict 구성에서만 적용.

## Scope boundary

**Task 02 에서 절대 수정 금지**:

- `experiments/config.py` — task-01 결과물 그대로.
- `experiments/_external/lmstudio_client.py` — task-03 영역.
- `experiments/_external/gemini_client.py` — 본 plan 범위 밖.
- `experiments/tests/test_static.py` — task-04 영역.
- `docs/reference/researchNotebook.md` — task-05 영역.
- `experiments/orchestrator.py` 의 `call_model()` 외 함수 (`run_abc_chain`, `select_assertions` 등).
- 다른 expXX/ 디렉토리.

**허용 범위**:

- `experiments/orchestrator.py` 의 `from config import` 1줄 갱신.
- `experiments/orchestrator.py:call_model()` payload dict 구성 부분 (현재 line 67-72) 수정.
