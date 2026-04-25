---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: role-adapter-phase-1-a-b-c
parallel_group: B
depends_on: [01]
---

# Task 02 — `run_abc_chain()` 리팩토링

## Changed files

- `experiments/orchestrator.py`
  - `run_abc_chain()` 본문 (line 485 ~ 약 line 780): 인라인 A/B/C 처리 블록을 `CriticAgent` / `JudgeAgent` 어댑터 호출로 교체
  - **함수 시그니처는 유지** (line 485-495):
    ```python
    def run_abc_chain(
        task_id, objective, prompt, constraints=None,
        termination="...", logger=None, max_cycles=MAX_TOTAL_CYCLES,
        use_phase_prompt=False, use_tools=False,
    ) -> tuple[Tattoo, list[ABCCycleLog], str | None]:
    ```
  - **반환 튜플 그대로** — `(tattoo, logs, final_answer)`

## Change description

### Step 1 — A 역할 처리는 그대로 유지

A 역할은 현재 `run_loop()` 함수가 담당 (line 533~ 호출). `run_loop`은 별도 함수이고 chunk 처리·tool_calls 처리 등 복잡한 로직을 가짐. **이번 Task에서는 `run_loop()`를 건드리지 않음**:

```python
# 기존 (유지)
tattoo, a_log, answer, a_tool_calls = run_loop(
    tattoo, cycle, phase_prompt_args=phase_args,
    use_tools=use_tools, tool_functions=_tool_fns,
)
```

ProposerAgent는 단위 테스트(Task 04)에서만 검증. 통합은 Phase 2로 연기.

### Step 2 — B 역할 인라인 블록 교체 (line 549~624)

**원본 (인라인)**:

```python
# ── B: 비판자 ──
b_start = time.time()
b_error = None
b_parsed = None
b_raw = ""

assertions_for_b = [a.to_dict() for a in tattoo.active_assertions]
if assertions_for_b:
    if use_phase_prompt:
        from system_prompt import build_critic_prompt_with_phase
        b_messages = build_critic_prompt_with_phase(...)
    else:
        b_messages = build_critic_prompt(...)
    for attempt in range(2):
        try:
            b_raw, _ = call_model(b_messages)
            b_parsed = extract_json_from_response(b_raw)
        except Exception as e:
            b_raw = ""
            b_error = str(e)
        if b_parsed:
            b_error = None
            break
        if attempt == 0:
            print(f"    B ↻ retry")
    if not b_parsed and not b_error:
        b_error = "JSON parse failed"
else:
    b_error = "no assertions to critique"

b_duration = int((time.time() - b_start) * 1000)
```

**리팩토링 후 (어댑터)**:

```python
# ── B: 비판자 ──
from agents import CriticAgent

assertions_for_b = [a.to_dict() for a in tattoo.active_assertions]
if assertions_for_b:
    b_result = CriticAgent().call(
        problem=prompt,
        assertions=assertions_for_b,
        handoff_a2b=tattoo.handoff_a2b.to_dict() if tattoo.handoff_a2b else None,
        phase_args=(cycle, max_cycles) if use_phase_prompt else None,
        max_retries=1,
    )
    b_raw = b_result.raw
    b_parsed = b_result.parsed
    b_error = b_result.error
    b_duration = b_result.duration_ms
else:
    b_raw = ""
    b_parsed = None
    b_error = "no assertions to critique"
    b_duration = 0
```

**주의**: 이후 line 591~624의 후속 처리 (HandoffB2C 파싱, `tattoo.invalidate_assertion`, `tattoo.critique_log` append, logger 호출)는 **그대로 유지**. b_parsed/b_raw/b_duration/b_error 변수가 어댑터 결과에서 채워지므로 후속 코드는 수정 불필요.

### Step 3 — C 역할 인라인 블록 교체 (line 629~)

**원본 (인라인, line 629~672)**:

```python
# ── C: 판정자 ──
c_start = time.time()
c_error = None
c_parsed = None
c_raw = ""
phase_transition = None

if use_phase_prompt:
    from system_prompt import build_judge_prompt_with_phase
    c_messages = build_judge_prompt_with_phase(...)
else:
    c_messages = build_judge_prompt(...)

for attempt in range(2):
    try:
        c_raw, _ = call_model(c_messages)
        c_parsed = extract_json_from_response(c_raw)
    except Exception as e:
        c_raw = ""
        c_error = str(e)
    if c_parsed:
        c_error = None
        break
    if attempt == 0:
        print(f"    C ↻ retry")
if not c_parsed and not c_error:
    c_error = "JSON parse failed"

c_duration = int((time.time() - c_start) * 1000)
```

**리팩토링 후**:

```python
# ── C: 판정자 ──
from agents import JudgeAgent

phase_transition = None  # 후속 처리에서 사용

c_result = JudgeAgent().call(
    problem=prompt,
    current_phase=phase_str,
    current_critique=current_critique,
    previous_critique=previous_critique,
    assertion_count=len(tattoo.active_assertions),
    handoff_b2c=tattoo.handoff_b2c.to_dict() if tattoo.handoff_b2c else None,
    phase_args=(cycle, max_cycles) if use_phase_prompt else None,
    max_retries=1,
)
c_raw = c_result.raw
c_parsed = c_result.parsed
c_error = c_result.error
c_duration = c_result.duration_ms
```

이후 line 674~ 의 C 결정 처리 (`converged`, `next_phase_str`, phase transition validation, ABCCycleLog 생성 등)는 **그대로 유지**.

### Step 4 — 동작 동치 보장 체크

- retry 횟수: 1회 (`max_retries=1` → 총 2번 시도). 기존 `for attempt in range(2)`와 동일.
- retry 메시지: `print(f"    {role_name} ↻ retry")` — 어댑터가 출력. 기존 `print(f"    B ↻ retry")` 와 같은 형태.
- Error 메시지: `"JSON parse failed"`, `str(e)` — 어댑터가 동일하게 채움.
- assertions_for_b 비어있을 때: 어댑터 호출 자체를 안 하고 `b_error = "no assertions to critique"` 셋. 기존 동작 유지.
- 모든 후속 처리 (`tattoo.handoff_b2c = ...`, `tattoo.invalidate_assertion(...)`, ABCCycleLog 생성) — **그대로 유지**.

### Step 5 — Import 추가

`run_abc_chain` 내부 또는 파일 상단 (순환 import 가능성 검토 후 결정):

```python
# 함수 내 lazy import (권장 — 순환 회피)
from agents import CriticAgent, JudgeAgent
```

orchestrator.py 모듈 레벨 import는 agents가 orchestrator를 import하므로 순환 발생 가능성. 함수 내 import가 안전.

### Step 6 — 라인 수 비교 (참고)

- 리팩토링 전: `run_abc_chain` 약 300줄 (B 인라인 ~75줄 + C 인라인 ~80줄)
- 리팩토링 후: 약 150~200줄 (B 어댑터 호출 ~15줄 + C 어댑터 호출 ~15줄)
- **순 감소량**: 약 100~150줄

## Dependencies

- **Task 01 완료**: `experiments/agents/{__init__, base, critic, judge}.py` 존재해야 import 가능.
- 외부 패키지 추가 없음.

## Verification

```bash
# 1. 함수 시그니처 유지
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import inspect
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
required = {'task_id', 'objective', 'prompt', 'constraints', 'termination',
            'logger', 'max_cycles', 'use_phase_prompt', 'use_tools'}
assert required == set(sig.parameters), f'sig mismatch: {set(sig.parameters)}'
print('OK signature preserved')
"

# 2. 어댑터 import가 코드에 포함됨
grep -c "from agents import" experiments/orchestrator.py
# 기대: 1 이상 (CriticAgent, JudgeAgent import)

# 3. B/C 인라인 블록 제거됨 — call_model 호출 횟수 감소
grep -c "call_model(b_messages\|call_model(c_messages" experiments/orchestrator.py
# 기대: 0 (어댑터 사용으로 직접 call_model 호출 제거)

# 4. retry print 메시지 — 어댑터에서 출력하므로 인라인에는 없어야
grep -c '"    B ↻\|"    C ↻' experiments/orchestrator.py
# 기대: 0 (어댑터로 이동)

# 5. import 회귀 없음 (CriticAgent, JudgeAgent 호출 가능)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from orchestrator import run_abc_chain
from agents import CriticAgent, JudgeAgent
# import 시점에 순환이 없는지 확인
assert callable(run_abc_chain) and callable(CriticAgent) and callable(JudgeAgent)
print('OK no circular import')
"

# 6. ABCCycleLog 후속 처리 보존 — log 생성 코드 줄 수 변화 적어야
grep -c "ABCCycleLog(" experiments/orchestrator.py
# 기대: 1 이상 (기존과 동일 — log 생성 로직 보존)

# 7. 함수 라인 수 감소 확인 (정성 — 검증 명령은 아니지만 참고용)
awk '/^def run_abc_chain\(/,/^def [a-z_]+\(/' experiments/orchestrator.py | wc -l
# 기대: 200 미만 (기존 300+에서 감소)
```

## Risks

- **변수 스코프 차이**: 인라인 패턴은 `b_raw`, `b_parsed`, `b_error`, `b_duration` 변수를 함수 스코프에 직접 둠. 어댑터 결과를 이 변수들에 unpack해야 후속 처리 코드(line 591~624)가 깨지지 않음. **반드시 unpack 라인을 명시적으로 작성** (Step 2 코드 참조).
- **순환 import**: `agents/base.py`가 `from orchestrator import call_model`을 함수 내부 import로 하므로, orchestrator.py가 모듈 레벨에서 `from agents import ...`해도 순환 안 발생. 단 lazy import(함수 내부)가 더 안전.
- **logger 호출 보존**: B 처리 후 `logger.agent_b(...)`, C 처리 후 `logger.agent_c(...)` 호출은 그대로 유지. 어댑터는 logger 사용 안 함 — 기존 인라인 logger 호출이 그대로 작동해야 함.
- **`current_critique`, `previous_critique` 변수**: C 어댑터 호출 후에도 후속 phase transition 처리에서 사용됨 — 변수 유지 필수.
- **회귀 게이트 (Task 05)에서 동치 깨질 위험**: 어댑터가 retry 횟수·메시지 형식을 정확히 재현해야 함. **Verification 4번이 중요**.

## Scope boundary

**Task 02에서 절대 수정 금지**:
- `experiments/agents/` 내 모든 파일 (Task 01 영역) — import만 허용
- `experiments/system_prompt.py` — 어댑터가 wrap하므로 호출만
- `experiments/schema.py`
- `experiments/run_experiment.py`, `experiments/measure.py`, `experiments/tools/`, `experiments/tasks/`
- `run_loop()` 함수 — A 역할 처리, 본 Task 범위 외
- `run_abc_chunked()` 함수 — Task 03 영역
- `call_model`, `extract_json_from_response`, `select_assertions`, `apply_llm_response`, `create_initial_tattoo` — 호출만, 수정 금지
- ABCCycleLog 생성 로직, logger 호출 — 그대로 유지
- HandoffB2C 파싱, `tattoo.invalidate_assertion`, `tattoo.critique_log` append, phase transition validation 등 후속 처리 — 그대로 유지

**허용 범위**: `experiments/orchestrator.py:run_abc_chain`의 line 549~624 (B 인라인) 및 line 629~672 (C 인라인) 부분만 어댑터 호출로 교체.
