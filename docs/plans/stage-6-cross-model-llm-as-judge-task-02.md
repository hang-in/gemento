---
type: plan-task
status: pending
updated_at: 2026-05-05
parent_plan: stage-6-cross-model-llm-as-judge
parallel_group: B
depends_on: []
---

# Task 02 — Local Qwen 셋업 + orchestrator `model_caller` hook

## Changed files

- `experiments/orchestrator.py` — **수정**. `run_abc_chain` 에 `model_caller: Callable | None = None` 인자 추가 + Exp11 c_caller 의 *상위 일반화* 로 A/B/C 모두 외부 모델로 교체 가능
- (사용자 직접) Local LM Studio 에 Qwen 2.5 7B Q4_K_M 로딩 — 별도 endpoint 또는 동일 endpoint switch

수정 1 (코드).

## Change description

### 배경

Stage 6 의 cross-model 재현은 *전체 ABC chain 을 다른 모델로 교체*. Exp11 의 `c_caller` (Judge C 만 외부 모델) 와 다른 패턴 — 본 plan = A/B/C 모두 동일 외부 모델.

가장 깔끔한 design = `model_caller` hook (모든 LLM 호출의 함수 주입). default = None (기존 LM Studio 호출). model_caller 제공 시 *모든 ABC role 호출* 이 외부 함수로 routing.

### Step 1 — `run_abc_chain` 시그니처 확장

```python
def run_abc_chain(
    task_id, objective, prompt,
    constraints=None, termination="...",
    max_cycles=8, use_phase_prompt=True,
    c_caller=None,                      # Exp11 — Judge C 만 외부 (legacy hook)
    extractor_pre_stage=False,           # Exp12
    reducer_post_stage=False,            # Exp13
    search_tool=False, corpus=None,      # Exp14
    model_caller: Callable | None = None,  # 신규 (Stage 6) — 모든 role 외부
) -> tuple[Tattoo, list, str | None]:
    ...
```

`model_caller(messages, **kwargs) -> (str, dict)` callable. 내부 `call_model` 의 substitute.

### Step 2 — 호출 routing 로직

`run_loop` 의 `call_model(messages, ...)` 호출 위치를 *조건부 routing*:

```python
def _route_model_call(messages, **kwargs):
    if model_caller is not None:
        return model_caller(messages, **kwargs)
    return call_model(messages, **kwargs)
```

**중요 — c_caller 와의 관계**:
- `c_caller` 가 명시되면 Judge C 만 c_caller 호출 (Exp11 hook 보존)
- `model_caller` 가 명시되면 *전체 chain* 외부 → c_caller 우선순위 결정 필요

**Architect 결정**:
- `c_caller` is not None → 기존 Exp11 동작 (C 만 외부, A/B 는 internal)
- `model_caller` is not None and c_caller is None → 모든 role 외부 (Stage 6)
- 둘 다 None → 기존 internal LM Studio (default)
- 둘 다 명시 → **에러** ("c_caller and model_caller are mutually exclusive")

### Step 3 — Local Qwen 2.5 7B Q4_K_M LM Studio 셋업

**사용자 직접 작업** (Sonnet 수행 금지):

1. LM Studio 에 Qwen 2.5 7B Q4_K_M 모델 다운로드 (~4.5GB)
2. context 32K 설정
3. GPU offload max
4. 별도 endpoint port 사용 (예: `http://localhost:1235`) — 동시에 Gemma 도 운영 가능 (메모리 충분 시) 또는 model swap

**옵션** — 단일 endpoint switch:
- LM Studio 의 model swap 기능 사용
- 실행 시점에 `MODEL_NAME = "qwen-2.5-7b-q4"` 로 config 변경
- 한 번에 한 모델만 로드 가능 (3060 Ti 8GB 한계)

### Step 4 — `model_caller` 구현 예시 (cross_model/run.py 에서 사용 예정)

task-03 영역이지만 본 task 의 hook 검증 위해 stub 작성:

```python
# experiments/cross_model/run.py 에서 사용 예시
from experiments._external.groq_client import call_with_meter_retry, LLAMA_3_1_8B

def make_groq_caller(model_id: str):
    def _caller(messages, **kwargs):
        result = call_with_meter_retry(messages, model=model_id, **kwargs)
        # CallMeter → (str, dict) 변환
        meta = {
            "input_tokens": result.input_tokens,
            "output_tokens": result.output_tokens,
            "duration_ms": result.duration_ms,
            "cost_usd": result.cost_usd,
            "error": result.error,
        }
        return result.raw_response, meta
    return _caller

# 사용: run_abc_chain(..., model_caller=make_groq_caller(LLAMA_3_1_8B))
```

### Step 5 — backward compat 검증

```bash
.venv/Scripts/python -c "
import inspect
import sys; sys.path.insert(0, 'experiments')
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
params = sig.parameters
for opt in ('c_caller', 'extractor_pre_stage', 'reducer_post_stage',
            'search_tool', 'corpus', 'model_caller'):
    assert opt in params, f'{opt} 부재'
assert params['model_caller'].default is None
print('verification ok: 6 hook 공존 + model_caller default')
"
```

## Dependencies

- 패키지: 없음 (httpx 기존 사용)
- 기존 `experiments/orchestrator.py:run_loop` (Exp11 c_caller 분기 영역) — read-only 패턴 참조
- 기존 `experiments/_external/groq_client.py` — read-only import
- 사용자 hardware: LM Studio + Qwen 2.5 7B Q4_K_M

## Verification

```bash
# experiments 디렉토리에서 실행
cd D:/privateProject/gemento/experiments

# 1) syntax
../.venv/Scripts/python -m py_compile orchestrator.py

# 2) model_caller 인자 + default
../.venv/Scripts/python -c "
import inspect
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
assert 'model_caller' in sig.parameters
assert sig.parameters['model_caller'].default is None
print('verification 2 ok: model_caller 인자 + default')
"

# 3) 6 hook 공존
../.venv/Scripts/python -c "
import inspect
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
for opt in ('c_caller', 'extractor_pre_stage', 'reducer_post_stage',
            'search_tool', 'corpus', 'model_caller'):
    assert opt in sig.parameters, f'{opt} 부재'
print('verification 3 ok: 6 hook 공존')
"

# 4) c_caller / model_caller mutual exclusion (논리 검증)
../.venv/Scripts/python -c "
import inspect
from orchestrator import run_abc_chain
src = inspect.getsource(run_abc_chain)
assert 'mutually exclusive' in src or ('c_caller' in src and 'model_caller' in src)
print('verification 4 ok: mutual exclusion 로직 또는 routing')
"

# 5) (사용자 직접) Local Qwen 2.5 7B Q4_K_M LM Studio 로드 + endpoint 응답 확인
# curl http://localhost:1235/v1/models  (또는 사용 endpoint)
# Qwen 2.5 7B 모델 ID 확인
```

5 검증 — 1-4 자동, 5 사용자 직접.

## Risks

- **Risk 1 — c_caller / model_caller 우선순위 design conflict**: 두 hook 의 의도 차이 — Exp11 = C 만, Stage 6 = 전체. mutual exclusion 또는 명확한 우선순위 명시. Architect 결정: mutual exclusion (둘 다 명시 → ValueError)
- **Risk 2 — Local Qwen 의 tool-calling 호환성**: Q4_K_M quantization 의 OpenAI tool_calls 신뢰도. dry-run 시 H7/H8 패턴 확인 (calculator 호출 발생 여부). 호환 안 되면 H10/H11/H12 만 cross-model 재현 + H13 은 Local Qwen 미적용
- **Risk 3 — 메모리 부족 (3060 Ti 8GB)**: Qwen 2.5 7B Q4 + 32K context = ~7GB. 경계 영역. context overflow 시 16K 로 축소 또는 model swap (Gemma 와 동시 운영 안 함)
- **Risk 4 — Sonnet 이 model_caller 의 Internal call_model 대체 위치 잘못**: A/B/C 모든 호출이 routing 되어야 — `run_loop` 의 call_model 호출 위치 정확히 식별 후 적용
- **Risk 5 — Exp11 c_caller 회귀**: 본 task 의 routing 로직 변경이 c_caller 분기 깨면 Exp11 재현 불가. mutual exclusion 명시 + Exp11 결과 JSON 의 재실행 시 동등 결과 검증

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/_external/groq_client.py` (task-01 영역) — read-only import
- `experiments/_external/llm_judge.py` (task-01 영역)
- `experiments/cross_model/run.py` (task-03 영역, 미존재)
- `experiments/measure.py` / `score_answer_v*`
- `experiments/run_helpers.py`
- `experiments/schema.py`
- `experiments/system_prompt.py`
- 모든 기존 `experiments/exp**/run.py`
- 결과 JSON

orchestrator.py 에서 변경 금지 영역:
- `run_chain` (Stage 2C bug fix 보존)
- `call_model` 본체 (model_caller routing 만 추가, 함수 본체 변경 0)
- Exp11 의 `c_caller` 분기 + Exp12/13/14 의 hook 분기 — 보존
- `run_loop` 의 핵심 로직 (단 call_model 호출 위치만 routing wrapper 적용)
