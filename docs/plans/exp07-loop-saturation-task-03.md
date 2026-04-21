---
type: task
status: pending
plan: exp07-loop-saturation
task: 3
parallel_group: A
depends_on: []
updated_at: 2026-04-21
---

# Task 3: 오케스트레이터 max_cycles 파라미터화

## Changed files

- `experiments/orchestrator.py:412` — `run_abc_chain()` 시그니처 확장

## Change description

`run_abc_chain()`에 두 개의 선택적 파라미터를 추가한다. 기존 호출 코드는 기본값으로 동작하므로 하위 호환 유지.

### 변경 사항

1. **시그니처 변경** (orchestrator.py:412)

```python
def run_abc_chain(
    task_id: str,
    objective: str,
    prompt: str,
    constraints: list[str] | None = None,
    termination: str = "모든 비판이 수렴하고 최종 답변이 확정되면 종료",
    logger=None,
    max_cycles: int = MAX_TOTAL_CYCLES,       # 추가
    use_phase_prompt: bool = False,            # 추가
) -> tuple[Tattoo, list[ABCCycleLog], str | None]:
```

2. **루프 범위 변경** (orchestrator.py:439)

```python
# Before:
for cycle in range(1, MAX_TOTAL_CYCLES + 1):
# After:
for cycle in range(1, max_cycles + 1):
```

3. **프롬프트 분기** (orchestrator.py:425, 472, 541)

`use_phase_prompt=True`일 때 `_with_phase` 버전을 import하여 사용:

```python
if use_phase_prompt:
    from system_prompt import (
        build_prompt_with_phase as _build_prompt,
        build_critic_prompt_with_phase as _build_critic,
        build_judge_prompt_with_phase as _build_judge,
    )
else:
    from system_prompt import (
        build_prompt as _build_prompt_base,
        build_critic_prompt as _build_critic_base,
        build_judge_prompt as _build_judge_base,
    )
```

Agent A 호출 부분 (orchestrator.py:451 `run_loop` 호출):
- `run_loop()`은 내부에서 `build_prompt()`를 직접 호출하므로, `use_phase_prompt=True`일 때는 `run_loop()`에도 cycle/max_cycles를 전달해야 함
- `run_loop()` 시그니처에 선택적 파라미터 추가: `phase_prompt_args: tuple[int, int] | None = None`
- `phase_prompt_args`가 주어지면 `build_prompt_with_phase()`를 사용

Agent B 호출 부분 (orchestrator.py:472):
- `use_phase_prompt`일 때 `build_critic_prompt_with_phase(prompt, assertions, handoff_a2b, cycle, max_cycles)` 호출

Agent C 호출 부분 (orchestrator.py:541):
- `use_phase_prompt`일 때 `build_judge_prompt_with_phase(problem, phase, critique, prev_critique, count, b2c, cycle, max_cycles)` 호출

4. **안전장치 경계도 max_cycles 연동** (orchestrator.py:656)

```python
# MAX_CYCLES_PER_PHASE는 그대로 유지 (3)
# max_cycles가 커져도 per-phase 안전장치는 동일하게 동작
```

### 구현 순서

1. `run_loop()` 시그니처에 `phase_prompt_args` 추가
2. `run_loop()` 내부에서 `phase_prompt_args` 존재 시 `build_prompt_with_phase` 사용
3. `run_abc_chain()` 시그니처에 `max_cycles`, `use_phase_prompt` 추가
4. 루프 범위를 `max_cycles`로 변경
5. A/B/C 각 에이전트 프롬프트 빌더 호출을 `use_phase_prompt`에 따라 분기

## Dependencies

없음 (Task 1, 2와 병렬 가능 — 단, Task 2의 함수를 import하므로 실행 시에는 Task 2 완료 필요)

## Verification

```bash
cd /Users/d9ng/privateProject/gemento/experiments
python -c "
import inspect
from orchestrator import run_abc_chain, run_loop

# 시그니처 확인
sig_abc = inspect.signature(run_abc_chain)
params = list(sig_abc.parameters.keys())
assert 'max_cycles' in params, f'max_cycles not in {params}'
assert 'use_phase_prompt' in params, f'use_phase_prompt not in {params}'
assert sig_abc.parameters['max_cycles'].default == 12, 'max_cycles default wrong'
assert sig_abc.parameters['use_phase_prompt'].default == False, 'use_phase_prompt default wrong'

# run_loop 시그니처 확인
sig_loop = inspect.signature(run_loop)
assert 'phase_prompt_args' in sig_loop.parameters, 'phase_prompt_args not in run_loop'
assert sig_loop.parameters['phase_prompt_args'].default is None, 'phase_prompt_args default wrong'

print('All checks passed')
"
```

## Risks

- `run_loop()` 변경은 기존 `run_chain()` (solo 실험)에도 영향 → `phase_prompt_args=None` 기본값으로 기존 동작 보존
- import 순서: `use_phase_prompt=True`일 때 Task 2의 함수가 없으면 ImportError → Task 2 완료가 런타임 전제

## Scope boundary

수정 금지:
- `MAX_TOTAL_CYCLES = 12` 상수값 (기본값으로만 사용)
- `MAX_CYCLES_PER_PHASE = 3` 상수값
- `run_chain()` 함수 (solo 실험용, 이 task에서는 건드리지 않음)
- `experiments/tasks/taskset.json` (Task 1 영역)
- `experiments/system_prompt.py` (Task 2 영역)
