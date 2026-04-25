---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: role-adapter-phase-1-a-b-c
parallel_group: B
depends_on: [01]
---

# Task 03 — `run_abc_chunked()` 리팩토링

## Changed files

- `experiments/orchestrator.py`
  - `run_abc_chunked()` (line 792~) 본문: chunk iteration 안의 A 호출 + 최종 수렴의 B·C 호출을 어댑터로 교체
  - **함수 시그니처 유지**:
    ```python
    def run_abc_chunked(
        task_id, question, chunks, constraints=None,
        termination="...", logger=None, max_final_cycles=5,
        assertion_soft_cap=64,
    ) -> tuple[Tattoo, list[ABCCycleLog], str | None]:
    ```

## Change description

### Step 1 — Chunk iteration 안의 A 호출 처리

`run_abc_chunked`는 chunk 마다 A를 호출하여 evidence를 누적하고, 모든 chunk 처리 후 최종 B·C 수렴을 1회만 한다. A 호출은 `build_prompt_chunked` + `call_model` + `apply_llm_response` 패턴.

**현재 패턴** (line 822~ 추정):

```python
for chunk in chunks:
    chunk_id = chunk["chunk_id"]
    tattoo.next_directive = ...
    selected = select_assertions(tattoo, soft_cap=assertion_soft_cap)
    display_tattoo = Tattoo(...)  # 토큰 절약용 작은 view
    messages = build_prompt_chunked(
        tattoo_json=json.dumps(display_tattoo.to_dict(), ensure_ascii=False),
        current_chunk=chunk["content"],
        chunk_id=chunk_id,
    )
    raw, _ = call_model(messages)
    parsed = extract_json_from_response(raw)
    if parsed:
        tattoo, answer = apply_llm_response(tattoo, parsed, loop_index=chunk_id, hard_cap=ASSERTION_HARD_CAP * 20)
```

**리팩토링 후 — ProposerAgent 사용**:

```python
from agents import ProposerAgent
proposer = ProposerAgent()  # chunk 루프 외부에서 1회 생성

for chunk in chunks:
    chunk_id = chunk["chunk_id"]
    tattoo.next_directive = ...
    selected = select_assertions(tattoo, soft_cap=assertion_soft_cap)
    display_tattoo = Tattoo(...)
    a_result = proposer.call(
        tattoo_json=json.dumps(display_tattoo.to_dict(), ensure_ascii=False),
        chunked={"current_chunk": chunk["content"], "chunk_id": chunk_id},
        max_retries=0,  # 기존 동작 — chunked는 retry 없음. Step 4 참조
    )
    if a_result.parsed:
        tattoo, answer = apply_llm_response(
            tattoo, a_result.parsed,
            loop_index=chunk_id,
            hard_cap=ASSERTION_HARD_CAP * 20,
        )
```

**주의**: `apply_llm_response`, `select_assertions`, `display_tattoo` 생성, `tattoo.next_directive` 설정 등 **모든 주변 로직은 그대로 유지**. ProposerAgent는 단지 `build_prompt_chunked + call_model + extract_json_from_response`만 wrap.

### Step 2 — Retry 정책 결정 (동작 동치 핵심)

**먼저 기존 코드를 정확히 확인**: `run_abc_chunked`의 chunk iteration A 호출이 retry를 하는지 안 하는지. Developer가 line 845~870 근처를 직접 읽고 결정:

- 기존이 retry 0회면 → `max_retries=0`
- 기존이 retry 1회면 → `max_retries=1`

회귀 게이트(Task 05)는 `run_abc_chain`(Exp08b)을 검증하지 그대로지만, run_abc_chunked는 별도 sanity check가 필요할 수 있음 (Risks 참조).

### Step 3 — 최종 수렴의 B·C 처리

`run_abc_chunked` 끝부분에 모든 chunk 처리 후 B → C 수렴 루프(`max_final_cycles`)가 있다면, Task 02와 동일 패턴으로 어댑터 사용:

```python
from agents import CriticAgent, JudgeAgent

# 최종 B·C 수렴
for final_cycle in range(max_final_cycles):
    assertions_for_b = [a.to_dict() for a in tattoo.active_assertions]
    if not assertions_for_b:
        break
    
    b_result = CriticAgent().call(
        problem=question,
        assertions=assertions_for_b,
        handoff_a2b=tattoo.handoff_a2b.to_dict() if tattoo.handoff_a2b else None,
        max_retries=1,
    )
    # b_result.parsed로 후속 처리 (assertion 무효화, critique_log append 등)
    
    c_result = JudgeAgent().call(
        problem=question,
        current_phase=tattoo.phase.value,
        current_critique=b_result.parsed,
        previous_critique=...,
        assertion_count=len(tattoo.active_assertions),
        handoff_b2c=tattoo.handoff_b2c.to_dict() if tattoo.handoff_b2c else None,
        max_retries=1,
    )
    # c_result.parsed로 수렴 판단
    if c_result.parsed and c_result.parsed.get("converged"):
        break
```

**주의**: 기존 `run_abc_chunked`의 최종 수렴 코드를 line 단위로 정확히 보고 어댑터 호출로 1:1 교체. 후속 처리 (assertion 무효화, phase transition 등)는 그대로.

### Step 4 — 동작 동치 보장 체크

- A 호출의 retry 횟수 보존 (기존 코드 확인 후 결정)
- B·C 호출의 retry 횟수 1회 (기존 동작 유지)
- `apply_llm_response`의 hard_cap 그대로 (`ASSERTION_HARD_CAP * 20`)
- `select_assertions`의 soft_cap 그대로 (파라미터 `assertion_soft_cap=64`)
- `display_tattoo` 생성 로직 (assertion 토큰 절약) 그대로
- 로깅·print 메시지 패턴 보존

### Step 5 — Task 02와의 차이점

- `run_abc_chain`은 cycle 마다 A→B→C 1세트, 여러 cycle 반복
- `run_abc_chunked`는 chunk 마다 A 1회, 모든 chunk 후 B·C는 max_final_cycles 만큼 반복
- 둘 다 같은 어댑터(CriticAgent, JudgeAgent) 사용 — 코드 중복 제거 효과 발생

## Dependencies

- **Task 01 완료**: `experiments/agents/{__init__, base, proposer, critic, judge}.py` 존재해야 함.
- 외부 패키지 추가 없음.
- 본 Task와 Task 02는 같은 파일(`orchestrator.py`)을 수정하지만 **다른 함수**이므로 충돌 가능성 낮음. 단 같은 파일이라 실제 작업은 직렬로 진행 권장 (parallel_group=B 동일하지만 한 사람이 순차적으로).

## Verification

```bash
# 1. 함수 시그니처 유지
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import inspect
from orchestrator import run_abc_chunked
sig = inspect.signature(run_abc_chunked)
required = {'task_id', 'question', 'chunks', 'constraints', 'termination',
            'logger', 'max_final_cycles', 'assertion_soft_cap'}
assert required == set(sig.parameters), f'sig mismatch: {set(sig.parameters)}'
print('OK signature preserved')
"

# 2. 어댑터 import 사용
grep -c "from agents import\|agents.proposer\|agents.critic\|agents.judge\|ProposerAgent\|CriticAgent\|JudgeAgent" experiments/orchestrator.py
# 기대: 4 이상 (Task 02의 import + 본 Task의 추가 import)

# 3. run_abc_chunked 내부에서 직접 call_model 호출 제거
awk '/^def run_abc_chunked\(/,/^def [a-z_]+\(/' experiments/orchestrator.py | grep -c "call_model(.*messages"
# 기대: 0 (어댑터 사용으로 직접 호출 사라짐)

# 4. apply_llm_response 호출은 유지 (ProposerAgent 결과로 호출)
awk '/^def run_abc_chunked\(/,/^def [a-z_]+\(/' experiments/orchestrator.py | grep -c "apply_llm_response"
# 기대: 1 이상 (chunk 처리 시 누적용)

# 5. ASSERTION_HARD_CAP * 20 (또는 동등 값) 보존
awk '/^def run_abc_chunked\(/,/^def [a-z_]+\(/' experiments/orchestrator.py | grep -c "ASSERTION_HARD_CAP\s*\*\s*20\|hard_cap=200"
# 기대: 1 이상 (chunked-specific cap 유지)

# 6. import 회귀 없음
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from orchestrator import run_abc_chain, run_abc_chunked
from agents import ProposerAgent, CriticAgent, JudgeAgent
print('OK no circular import')
"

# 7. Exp09 longctx 분기에서 run_abc_chunked가 호출 가능 (run_experiment.py 영향 없음)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from run_experiment import EXPERIMENTS
assert 'longctx' in EXPERIMENTS
print('OK longctx command intact')
"

# 8. Smoke 테스트 — 빈 chunks로 run_abc_chunked 호출 시 에러 없이 빠르게 종료
#    (실제 LLM 호출 없이 시그니처만 검증)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
# chunks=[]로 호출 시 try/except로 보호되는지만 import-level 확인
import inspect
from orchestrator import run_abc_chunked
src = inspect.getsource(run_abc_chunked)
# select_assertions, display_tattoo 키워드 보존 확인
assert 'select_assertions' in src
print('OK key invariants preserved in source')
"
```

## Risks

- **`run_abc_chunked` 내부 retry 정책**: 본 Task 시작 전 Developer가 line 822~ 의 정확한 retry 동작을 읽고 `max_retries` 값을 결정해야 함. 잘못 추정하면 동치 깨짐.
- **회귀 게이트가 Exp08b만 검증**: Task 05는 Exp08b math-04(=`run_abc_chain` 사용)만 회귀 검증. `run_abc_chunked`는 Exp09에서 사용되는데 Exp09는 아직 결과 없음 → **Task 03의 회귀는 자동 검증되지 않음**. Risks 완화: Task 04 단위 테스트가 ProposerAgent의 `_build_messages(chunked=...)` 분기를 mock으로 검증.
- **동일 파일 변경**: Task 02와 Task 03 모두 `orchestrator.py` 수정. 같은 사람이 순차로 진행 권장 (parallel_group은 B로 같지만 직렬화).
- **`run_loop()` 영향 없음 확인**: `run_abc_chunked`는 `run_abc_chain`과 달리 `run_loop()`을 호출하지 않고 직접 `build_prompt_chunked` + `call_model` 호출. 따라서 ProposerAgent를 직접 사용하는 게 자연스러움.
- **Exp09 진행 영향**: Gemini가 Windows에서 `python run_experiment.py longctx` 실행 중일 수 있음. 단 Gemini는 자기 git checkout에 있는 코드로 돌리므로, main에 push만 안 하면 실행 영향 없음. 본 Task 완료 후 main push는 Task 05 통과 후로 한정.

## Scope boundary

**Task 03에서 절대 수정 금지**:
- `experiments/agents/` (Task 01 영역) — import만
- `experiments/system_prompt.py`, `experiments/schema.py`, `experiments/tools/`, `experiments/tasks/`
- `experiments/run_experiment.py`, `experiments/measure.py`
- `run_abc_chain()` 함수 (Task 02 영역)
- `run_loop()`, `call_model`, `extract_json_from_response`, `select_assertions`, `apply_llm_response`, `create_initial_tattoo` 함수 본문 — 호출만, 수정 금지
- `LONGCTX_*` 상수, `run_longctx` 함수
- `apply_llm_response`의 `hard_cap=ASSERTION_HARD_CAP * 20` 값 — 보존 필수

**허용 범위**: `experiments/orchestrator.py:run_abc_chunked` 함수 본문에서 chunk iteration의 A 호출 + 최종 수렴의 B·C 호출만 어댑터 호출로 교체.
