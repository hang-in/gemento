---
type: task
status: pending
plan: exp07-loop-saturation
task: 2
parallel_group: A
depends_on: []
updated_at: 2026-04-21
---

# Task 2: Loop-Phase 프롬프트 추가

## Changed files

- `experiments/system_prompt.py` — 새 함수 3개 추가 (기존 함수 변경 없음)

## Change description

`system_prompt.py` 파일 끝에 loop-phase 인식 프롬프트 빌더 3개를 추가한다.
기존 `build_prompt()`, `build_critic_prompt()`, `build_judge_prompt()`는 변경하지 않는다.

### 1. 단계 구분 헬퍼

```python
def _get_phase_mode(cycle: int, max_cycles: int) -> str:
    """현재 사이클에 따라 탐색/정제/커밋 모드를 반환한다."""
    if cycle <= max_cycles * 0.33:
        return "explore"
    elif cycle <= max_cycles * 0.66:
        return "refine"
    else:
        return "commit"
```

비율 기반으로 MAX_CYCLES 변경에 자동 적응.

### 2. `build_prompt_with_phase(tattoo_json, cycle, max_cycles, tool_results=None)`

기존 `build_prompt()`와 동일하되, user 메시지에 phase-mode 컨텍스트 블록을 삽입:

```
## Loop Progress
You are in cycle {cycle}/{max_cycles}. Mode: {mode}.

### Mode instructions
- explore: Generate diverse hypotheses. Explore multiple approaches. Do NOT converge early.
- refine: Narrow down hypotheses. Eliminate weak evidence. Reduce open_questions.
- commit: Finalize your answer. Close ALL remaining open_questions. You MUST set final_answer if possible.
```

SYSTEM_PROMPT 자체는 변경하지 않음 — user 메시지 레벨에서 추가.

### 3. `build_critic_prompt_with_phase(problem, assertions, handoff_a2b, cycle, max_cycles)`

기존 `build_critic_prompt()`와 동일하되, user 메시지에 phase-mode 블록 추가:

```
## Loop Progress
Cycle {cycle}/{max_cycles}. Mode: {mode}.

### Mode instructions for critic
- explore: Focus on finding logical gaps and unstated assumptions. Be aggressive.
- refine: Focus on eliminating remaining uncertainties. Challenge weak assertions.
- commit: Final verification pass. Identify any remaining errors before convergence.
```

### 4. `build_judge_prompt_with_phase(problem, current_phase, current_critique, previous_critique, assertion_count, handoff_b2c, cycle, max_cycles)`

기존 `build_judge_prompt()`와 동일하되, user 메시지에 phase-mode 블록 추가:

```
## Loop Progress
Cycle {cycle}/{max_cycles}. Mode: {mode}.

### Mode instructions for judge
- explore: Resist early convergence. If progress is being made, encourage more exploration.
- refine: Allow convergence if evidence is strong. Push phase transitions when progress stalls.
- commit: Actively push toward CONVERGED. Only reject if there are clear errors remaining.
```

### 구현 순서

1. `_get_phase_mode()` 헬퍼 추가
2. `build_prompt_with_phase()` 추가
3. `build_critic_prompt_with_phase()` 추가
4. `build_judge_prompt_with_phase()` 추가
5. 각 함수는 기존 함수를 호출하지 않고 독립 구현 (기존 함수와 커플링 방지)

## Dependencies

없음 (Task 1, 3과 병렬 가능)

## Verification

```bash
cd /Users/d9ng/privateProject/gemento/experiments
python -c "
from system_prompt import (
    build_prompt, build_critic_prompt, build_judge_prompt,
    build_prompt_with_phase, build_critic_prompt_with_phase, build_judge_prompt_with_phase,
    _get_phase_mode,
)

# 기존 함수 동작 확인
msgs = build_prompt('{\"test\": true}')
assert len(msgs) == 2, 'build_prompt broken'

# phase mode 테스트
assert _get_phase_mode(1, 20) == 'explore'
assert _get_phase_mode(10, 20) == 'refine'
assert _get_phase_mode(18, 20) == 'commit'
assert _get_phase_mode(3, 8) == 'explore'
assert _get_phase_mode(5, 8) == 'refine'
assert _get_phase_mode(7, 8) == 'commit'

# with_phase 함수 출력 확인
msgs_p = build_prompt_with_phase('{\"test\": true}', cycle=1, max_cycles=20)
assert len(msgs_p) == 2
assert 'Loop Progress' in msgs_p[1]['content']
assert 'explore' in msgs_p[1]['content'].lower()

msgs_c = build_critic_prompt_with_phase('problem', [], None, cycle=15, max_cycles=20)
assert 'commit' in msgs_c[1]['content'].lower()

msgs_j = build_judge_prompt_with_phase('problem', 'INVESTIGATE', None, None, 5, None, cycle=10, max_cycles=20)
assert 'Loop Progress' in msgs_j[1]['content']

print('All checks passed')
"
```

## Risks

- Loop-Phase 지시문이 JSON 출력 형식을 방해할 가능성 → user 메시지에만 추가하고 system prompt는 불변
- "commit" 모드에서 C가 너무 빨리 수렴 판정할 위험 → "Only reject if there are clear errors remaining"으로 완화

## Scope boundary

수정 금지:
- `SYSTEM_PROMPT`, `CRITIC_PROMPT`, `JUDGE_PROMPT` 상수 (기존 프롬프트 텍스트)
- `build_prompt()`, `build_critic_prompt()`, `build_judge_prompt()` 기존 함수 시그니처 및 구현
- `experiments/tasks/taskset.json` (Task 1 영역)
- `experiments/orchestrator.py` (Task 3 영역)
