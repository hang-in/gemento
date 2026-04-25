---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: exp08b-tool-use-refinement-prompt
parallel_group: A
depends_on: []
---

# Task 02 — SYSTEM_PROMPT tool-use 가이드 강화

## Changed files

- `experiments/system_prompt.py`
  - `SYSTEM_PROMPT` 문자열 상수 (line 7~) 내의 "Tool use (math tasks)" 섹션만 수정.
  - `build_prompt`, `build_prompt_with_phase`, `build_critic_prompt`, `build_judge_prompt` 등 함수 **본문은 전혀 수정하지 않음**.

## Change description

### Step 1 — 기존 섹션 위치 확인

Exp08 Task 03에서 추가된 "Tool use (math tasks)" 섹션은 `SYSTEM_PROMPT` 상수의 하단에 있다. `grep -n "Tool use (math tasks)" experiments/system_prompt.py`로 위치 확인 후 해당 섹션을 통째로 교체.

### Step 2 — 섹션 재작성

기존 섹션을 아래 강화본으로 교체:

```
## Tool use (math tasks)

When the task involves numeric calculation, a linear system, or an optimization (linear programming), you MUST call the appropriate tool rather than computing manually:

- `calculator(expression)` — basic arithmetic. Example: `(13+7)*3.5`.
  - Use `**` for powers (e.g. `2**10`). Python's `^` is bitwise XOR — NEVER use it for exponentiation.
- `solve_linear_system(A, b)` — solve Ax = b for n×n A.
- `linprog(c, A_ub, b_ub, bounds, ...)` — minimize c·x.
  - For MAXIMIZATION, negate c (e.g. to maximize 50x+40y, pass c=[-50,-40]).

### Mandatory rules

1. **LP / optimization problems**: If the problem is a linear programming or optimization task, you MUST call `linprog` on your FIRST tool round. Do not attempt manual LP corner-point enumeration.
2. **Error recovery**: If a tool returns an error, READ the error message and adjust your next call. Do NOT abandon tool use and fall back to manual calculation after one failure.
3. **Integer answers**: LP/linear solvers return floats; round to the nearest integer if the problem expects integers, then verify via `calculator`.
4. **Never fabricate**: Do not invent numeric results. If a tool is available for the calculation, use it.
```

**근거**:
- 기존 섹션은 "MUST call" 지시를 한 문장에만 포함. Exp08 원시 데이터를 보면 math-04 trial 2에서 모델이 tool 호출을 전혀 시도하지 않고 10 cycle을 소모한 사례가 발생 → 규칙화 필요.
- Error recovery 항목 추가: Exp08 calculator BitXor 에러 후 모델이 재시도하지 않고 `None`으로 종료한 패턴 방지.
- `^` 금지는 Task 01의 에러 힌트와 짝으로 작동 — prompt에서 미리 금지하고, 그래도 위반하면 에러 메시지로 재교육.

### Step 3 — 회귀 방지 확인

- `SYSTEM_PROMPT` 문자열 끝에 있는 다른 지시 사항(예: JSON 출력 규칙, next_directive 관련)은 그대로 유지.
- build_prompt 함수는 `{"role": "system", "content": SYSTEM_PROMPT}`로 상수를 주입만 하므로, 상수 변경만으로 모든 A 호출에 자동 반영.
- 변경 후 파일 길이가 너무 짧지는 않은지 (`wc -l`로 확인 — 330~350 라인 범위 유지 예상).

## Dependencies

- 선행 Task 없음.
- 외부 패키지 추가 없음.

## Verification

```bash
# 1. 새 지시 문구가 SYSTEM_PROMPT에 포함
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -c "
import sys; sys.path.insert(0, 'experiments')
from system_prompt import SYSTEM_PROMPT
required = [
    'LP / optimization problems',
    'MUST call `linprog`',
    'first tool round',
    'READ the error message',
    \"Python's '^'\",
    '**',
]
missing = [s for s in required if s not in SYSTEM_PROMPT]
assert not missing, f'missing: {missing}'
print('OK all guidelines present')
"
# 기대: "OK all guidelines present"

# 2. build_prompt 함수 로직은 수정되지 않음
grep -c "messages = \[" experiments/system_prompt.py
# 기대: 최소 4 (build_prompt, build_critic_prompt, build_judge_prompt 등)

# 3. 관련 모듈 import 회귀 없음
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from system_prompt import SYSTEM_PROMPT, build_prompt, build_critic_prompt, build_judge_prompt
from system_prompt import build_prompt_with_phase, build_critic_prompt_with_phase, build_judge_prompt_with_phase
msgs = build_prompt('{}')
assert isinstance(msgs, list) and msgs[0]['role'] == 'system'
print('OK build_prompt still works')
"
# 기대: "OK build_prompt still works"

# 4. 파일 전체 문법 오류 없음
cd /Users/d9ng/privateProject/gemento && .venv/bin/python -m py_compile experiments/system_prompt.py && echo "OK compile"
# 기대: "OK compile"
```

## Risks

- **프롬프트 길이 증가**: SYSTEM_PROMPT가 길어지면 매 A 호출 프롬프트 비용 증가. 추가량은 ~200 토큰 수준이라 무시 가능.
- **지시 충돌 가능성**: 기존 SYSTEM_PROMPT에 JSON 출력 규칙이 있을 수 있음. 새 Mandatory rules가 JSON 형식과 독립적인 내용이라 충돌 없음으로 예상. 실제 수정 후 `grep -n "JSON\|json" experiments/system_prompt.py`로 교차 확인 권장.
- **모델 compliance 편차**: 프롬프트 강화가 항상 기대대로 작동하지 않음. Exp05a에서 "MUST set final_answer" 강화가 실패한 선례가 있음. 그러나 본 변경은 단순 지시 강화가 아닌 **tool_choice=auto + 에러 피드백 루프** 조합이라 작동 가능성이 더 높다. Exp08b 결과로 판정.
- **B/C 경로 영향 없음 확인**: SYSTEM_PROMPT는 A(제안자)만 사용 — `build_critic_prompt`, `build_judge_prompt`는 각자 별도 상수 사용. 교차 확인: `grep -n "SYSTEM_PROMPT" experiments/system_prompt.py`로 사용처 모두 확인.

## Scope boundary

**Task 02에서 절대 수정 금지**:
- `experiments/tools/` 내부 모든 파일 (Task 01 영역)
- `experiments/run_experiment.py` (Task 03 영역)
- `experiments/measure.py` (Task 04 영역)
- `experiments/orchestrator.py` — 본 Task는 prompt 상수만.
- `experiments/system_prompt.py` 내 **build_* 함수들의 본문** — 상수 변경만 허용.
- `CRITIC_PROMPT`, `JUDGE_PROMPT` 등 다른 상수 — 터치 금지.

**허용 범위**: `experiments/system_prompt.py`의 `SYSTEM_PROMPT` 상수 내 "Tool use (math tasks)" 섹션만.
