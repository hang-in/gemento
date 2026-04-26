---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: sampling-params-config-exp10
parallel_group: A
depends_on: []
---

# Task 01 — config.py 에 SAMPLING_PARAMS 추가

## Changed files

- `experiments/config.py` — **수정**. 끝에 `SAMPLING_PARAMS: dict` 추가.

신규 파일 0. 다른 파일 수정 0.

## Change description

### 배경

현재 `experiments/config.py` (28 라인) 는 `MODEL_NAME`, `API_BASE_URL`, `ASSERTION_SOFT_CAP` 등 실험 상수를 담고 있으나 LLM sampling 설정은 부재. orchestrator·lmstudio_client 가 각자 다른 방식으로 sampling 을 처리하고 있어 일원화가 필요하다.

### Step 1 — config.py 끝에 dict 추가

`experiments/config.py` 28 라인 (`MAX_LOOPS = 15` 다음) 에 다음 영역을 추가:

```python


# ── Sampling (LLM 추론 결정성 통제) ──
# 본 dict 가 모든 LLM 호출의 sampling source-of-truth.
# orchestrator.call_model() 와 _external/lmstudio_client.call_with_meter() 가 참조한다.
# 값이 None 이면 payload 에 미포함 (LM Studio 기본 동작).
# 결과 동일성 보장 — 기존 14 실험 재현성 유지를 위해 temperature/max_tokens 변경 금지.
SAMPLING_PARAMS: dict = {
    "temperature": 0.1,
    "max_tokens": 4096,
    "top_p": None,    # 미지정 — LM Studio 기본값 사용
    "seed": None,     # 비결정성 유지 — Exp10 본격 실행 전 별도 결정
}
```

### Step 2 — 기존 상수 변경 금지 검증

`MODEL_NAME`, `API_BASE_URL`, `ASSERTION_SOFT_CAP` 등 다른 상수는 건드리지 않는다. 본 task 는 **새 dict 추가만** 수행.

## Dependencies

- 없음. 본 task 는 plan 의 foundation.
- 외부 패키지: 없음 (stdlib `dict` 만 사용).

## Verification

```bash
# 1. 파일 라인 수 — 28 → ~38 라인 (10 줄 추가)
wc -l /Users/d9ng/privateProject/gemento/experiments/config.py

# 2. SAMPLING_PARAMS import + 4 필드 존재 확인
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from config import SAMPLING_PARAMS
expected = {'temperature', 'max_tokens', 'top_p', 'seed'}
actual = set(SAMPLING_PARAMS.keys())
assert actual == expected, f'expected {expected}, got {actual}'
assert SAMPLING_PARAMS['temperature'] == 0.1, f'temperature must be 0.1, got {SAMPLING_PARAMS[\"temperature\"]}'
assert SAMPLING_PARAMS['max_tokens'] == 4096, f'max_tokens must be 4096, got {SAMPLING_PARAMS[\"max_tokens\"]}'
assert SAMPLING_PARAMS['top_p'] is None
assert SAMPLING_PARAMS['seed'] is None
print('OK SAMPLING_PARAMS has 4 fields with expected values')
"

# 3. 다른 상수 미변경 확인
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import config
assert config.MODEL_NAME == 'gemma4-e4b'
assert config.API_BASE_URL == 'http://yongseek.iptime.org:8005'
assert config.ASSERTION_SOFT_CAP == 8
assert config.MAX_LOOPS == 15
print('OK existing constants unchanged')
"

# 4. 다른 파일 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only experiments/ docs/ | grep -vE "^experiments/config\.py$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **dict 추가 후 type hint** : `SAMPLING_PARAMS: dict` 는 broad. 향후 TypedDict 로 강화 가능하나 본 task 범위 밖 (over-engineering).
- **None 값 의미**: payload 에 포함 안 함 의도. orchestrator/lmstudio_client 가 None 처리 책임 부담 (task-02·03 에서 처리).
- **import 시점**: orchestrator·lmstudio_client 가 `from config import SAMPLING_PARAMS` 로 import 하므로 module-level dict mutation 금지. dict 자체를 다른 곳에서 수정하면 영향 전파 — task-04 에서 immutability 검증.
- **기존 결과 동일성**: temperature=0.1, max_tokens=4096 값 변경 시 14 실험 재현성 깨짐. 본 task 에서 두 값 변경 금지 (Verification 2 에서 강제).

## Scope boundary

**Task 01 에서 절대 수정 금지**:

- `experiments/orchestrator.py` — task-02 영역.
- `experiments/_external/lmstudio_client.py` — task-03 영역.
- `experiments/_external/gemini_client.py` — 본 plan 범위 밖.
- `experiments/tests/test_static.py` — task-04 영역.
- `docs/reference/researchNotebook.md` — task-05 영역.
- `experiments/config.py` 의 기존 상수 (`MODEL_NAME` ~ `MAX_LOOPS`).
- 다른 expXX/ 디렉토리.

**허용 범위**:

- `experiments/config.py` 끝에 SAMPLING_PARAMS dict 1개 추가 (~10 줄).
