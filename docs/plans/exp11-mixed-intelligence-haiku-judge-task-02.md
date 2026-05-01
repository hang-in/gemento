---
type: plan-task
status: done
updated_at: 2026-05-02
parent_plan: exp11-mixed-intelligence-haiku-judge
parallel_group: B
depends_on: []
---

# Task 02 — `run_abc_chain` c_caller 인자 + tattoo_history fix

## Changed files

- `experiments/orchestrator.py` — **수정**. `run_abc_chain` 에 `c_caller` 인자 추가 (1-2 라인) + Stage 2C 의 cycle-by-cycle tattoo history 저장 결함 fix (Mixed plan 자체 영역, orchestrator 변경은 c_caller 만)

> 단 tattoo_history fix 는 `exp11_mixed_intelligence/run.py` (task-03) 측에서 처리 — 본 task 는 c_caller 인자 추가만.

수정 1.

## Change description

### 배경

Mixed Intelligence 의 Judge C 호출만 Haiku 사용. orchestrator 의 `run_abc_chain` 이 C 호출 함수를 customizable 하게 받도록 1-2 라인 patch.

backward compat 정책: `c_caller=None` (기본) 시 기존 `call_model` 사용 — 모든 기존 도구 (Exp10 등) 영향 0.

### Step 1 — 현 `run_abc_chain` 시그니처 정찰

```bash
.venv/Scripts/python -c "
import inspect
from experiments.orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
print(f'  signature: {sig}')
"
```

기대: `run_abc_chain(task_id, objective, prompt, constraints, termination, max_cycles, use_phase_prompt)` 형태. 정확한 시그니처는 정찰 결과로.

### Step 2 — `c_caller` 인자 추가 (default=None)

`run_abc_chain` 의 시그니처 끝에 `c_caller` 추가:

```python
def run_abc_chain(
    task_id: str,
    objective: str,
    prompt: str,
    constraints: list[str] | None = None,
    termination: str = "...",
    max_cycles: int = 8,
    use_phase_prompt: bool = True,
    c_caller: Callable[[list[dict]], tuple[str, dict]] | None = None,  # 신규 (default=None=기존 동작)
) -> tuple[Tattoo, list, str | None]:
    ...
```

`c_caller` 의 시그니처: `(messages: list[dict]) -> tuple[str, dict]` — 기존 `call_model` 과 호환. response text + meta dict 반환.

`Callable` import (필요 시 `from typing import Callable`):

```python
from typing import Callable  # 기존 import 영역에 추가
```

### Step 3 — `run_abc_chain` 내부의 C 호출 부분 수정

`run_abc_chain` 의 C role 호출 부분 (Judge prompt 호출):

```python
# Before (대략):
c_response, c_meta = call_model(c_messages)

# After:
if c_caller is not None:
    c_response, c_meta = c_caller(c_messages)
else:
    c_response, c_meta = call_model(c_messages)
```

**중요**: `c_meta` 의 schema 호환 — `call_model` 의 meta 와 c_caller 의 meta 가 같은 구조여야. task-03 의 Mixed run.py 가 c_caller 작성 시 호환 보장.

### Step 4 — backward compat 검증

기존 도구 (Exp10) 의 run_abc_chain 호출이 영향 받는지 검증:

```bash
.venv/Scripts/python -c "
from experiments.orchestrator import run_abc_chain
import inspect
sig = inspect.signature(run_abc_chain)
# c_caller 가 keyword-only / default=None 이면 기존 호출 호환
params = sig.parameters
assert 'c_caller' in params
assert params['c_caller'].default is None
print('verification 1 ok: c_caller default=None')
"
```

### Step 5 — Stage 2C tattoo_history 결함 disclosure (orchestrator 변경 0)

Stage 2C 의 결함 = `exp_h4_recheck/run.py:115` 의 `tattoo_history = [tattoo.to_dict()] if tattoo else None` (final tattoo 1 개만).

**본 task 영역 외**: orchestrator.py 의 `run_abc_chain` 자체는 cycle-by-cycle tattoo 관리 — 단 본 도구가 어떻게 history 를 추출하는지가 문제. task-03 의 `exp11_mixed_intelligence/run.py` 가 cycle-by-cycle 저장 로직 작성.

본 task 는 c_caller 추가 + disclosure 만. 실제 tattoo_history 저장 fix 는 task-03.

## Dependencies

- 패키지: 없음
- 다른 subtask: 없음 (parallel_group B, 첫 노드)
- task-03 가 본 task 의 c_caller 사용

## Verification

```bash
# 1) syntax + run_abc_chain 시그니처
.venv/Scripts/python -m py_compile experiments/orchestrator.py
echo "ok: syntax"

# 2) c_caller 인자 + default=None
.venv/Scripts/python -c "
from experiments.orchestrator import run_abc_chain
import inspect
sig = inspect.signature(run_abc_chain)
params = sig.parameters
assert 'c_caller' in params, 'c_caller 인자 부재'
assert params['c_caller'].default is None, 'c_caller default 가 None 이 아님'
print('verification 2 ok: c_caller 인자 추가')
"

# 3) 기존 호출 호환 (Exp10 의 run_abc_chain 호출 패턴)
.venv/Scripts/python -c "
import inspect
from experiments.orchestrator import run_abc_chain
src = inspect.getsource(run_abc_chain)
# 핵심: c_caller=None 시 call_model 사용
assert 'c_caller' in src
print('verification 3 ok: backward compat 보존')
"

# 4) (사용자 직접) Exp10 의 run_abc_chain 사용 도구 회귀 — Task 04 직전 dry-run
# 본 task 시점에 정적 검증만 — 실제 호출 회귀는 Task 04 의 실험 시점
```

## Risks

- **Risk 1 — `c_caller` 의 시그니처가 c_meta schema 와 mismatch**: task-03 의 Mixed run.py 가 c_caller 작성 시 호환 보장. dry-run 시 검증
- **Risk 2 — `run_abc_chain` 의 C 호출 부분이 여러 곳**: 정찰 후 모든 C 호출 위치에 patch. 단 `run_abc_chain` 내부의 단일 호출 영역이 일반적
- **Risk 3 — Sonnet 이 c_caller 외 다른 부분 변경**: 본 task = c_caller 인자 추가만. 기존 로직 변경 금지 (Scope boundary)

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/anthropic_client.py` (task-01 영역)
- `experiments/measure.py` / `score_answer_v*` — 본 plan 영역 외
- `experiments/schema.py` / `run_helpers.py` / `config.py` — 변경 금지
- 모든 기존 `experiments/exp**/run.py` — 변경 금지
- `experiments/exp_h4_recheck/run.py` — Stage 2C 영역, read-only
- `experiments/exp11_mixed_intelligence/run.py` (task-03 영역)
- 결과 JSON / docs/reference / docs/plans

orchestrator.py 에서 변경 금지 영역:
- `run_chain` (Stage 2C bug fix 적용된 starred unpacking 보존)
- `run_loop` / `call_model` / 다른 함수 — 변경 금지
- `run_abc_chain` 의 ABC 로직 자체 — c_caller 분기만 추가
