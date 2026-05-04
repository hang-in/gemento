---
type: plan-task
status: done
updated_at: 2026-05-04
parent_plan: exp13-reducer-role
parallel_group: B
depends_on: [01]
---

# Task 02 — `run_abc_chain` 의 reducer post-stage hook

## Changed files

- `experiments/orchestrator.py` — **수정**. `run_abc_chain` 에 `reducer_post_stage: bool = False` 옵션 추가 (1-2 라인) + post-stage 호출 로직 (5-10 라인)

수정 1.

## Change description

### 배경

task-01 의 `REDUCER_PROMPT` + `build_reducer_prompt()` 위에서 orchestrator post-stage hook 추가. ABC chain 종료 후 final tattoo + final_answer 를 Reducer 에게 전달 → 정리된 final_answer 로 교체.

backward compat: `reducer_post_stage=False` (default) 시 기존 동작.

### Step 1 — 시그니처 정찰

```bash
.venv/Scripts/python -c "
import inspect
from experiments.orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
print(f'  signature: {sig}')
"
```

기대: `(task_id, objective, prompt, constraints, termination, max_cycles, use_phase_prompt, c_caller, extractor_pre_stage)` (Exp11/Exp12 누적).

### Step 2 — `reducer_post_stage` 인자 추가 + 호출 로직

`run_abc_chain` 의 시그니처:

```python
def run_abc_chain(
    task_id, objective, prompt,
    constraints=None, termination="...",
    max_cycles=8, use_phase_prompt=True,
    c_caller=None,
    extractor_pre_stage=False,
    reducer_post_stage: bool = False,  # 신규 (default=False)
) -> tuple[Tattoo, list, str | None]:
    ...
```

ABC cycle 루프 종료 후 `return tattoo, abc_logs, final_answer` 직전:

```python
# Reducer post-stage (옵션)
if reducer_post_stage and final_answer:
    from system_prompt import build_reducer_prompt
    # active assertions 추출 (Tattoo 의 active_assertions 또는 동등)
    assertions = []
    if hasattr(tattoo, "active_assertions"):
        assertions = [
            {"claim": a.claim, "confidence": getattr(a, "confidence", None)}
            for a in tattoo.active_assertions
        ]
    elif hasattr(tattoo, "assertions"):
        assertions = [
            {"claim": a.claim, "confidence": getattr(a, "confidence", None)}
            for a in tattoo.assertions
            if getattr(a, "status", None) and getattr(a.status, "value", "") == "active"
        ] if hasattr(tattoo, "assertions") else []
    reducer_messages = build_reducer_prompt(assertions, final_answer)
    reduced_response, _meta = call_model(reducer_messages)
    reduced = reduced_response.strip()
    if reduced:
        # 새 final_answer 로 교체 (graceful fallback: 빈 응답 시 원본 유지)
        print(f"  [Reducer] candidate (orig {len(final_answer)} chars) → reduced ({len(reduced)} chars)")
        print(f"  [Reducer] preview: {reduced[:200]}{'...' if len(reduced) > 200 else ''}")
        final_answer = reduced
```

**중요**:
- post-stage = ABC cycle 루프 종료 *후*
- final_answer 가 있을 때만 호출 (None 또는 빈 경우 skip)
- Reducer 응답 빈 경우 원본 보존 (graceful fallback)
- assertions 추출 — Tattoo schema 의 정확한 필드명은 정찰 후 결정 (active_assertions / assertions / 다른 필드)

### Step 3 — backward compat 검증

```bash
.venv/Scripts/python -c "
from experiments.orchestrator import run_abc_chain
import inspect
sig = inspect.signature(run_abc_chain)
params = sig.parameters
assert 'reducer_post_stage' in params
assert params['reducer_post_stage'].default is False
# Exp11/Exp12 의 c_caller / extractor_pre_stage 도 보존
assert 'c_caller' in params
assert 'extractor_pre_stage' in params
print('verification ok: reducer_post_stage + 기존 옵션 보존')
"
```

## Dependencies

- task-01 마감 (`REDUCER_PROMPT` + `build_reducer_prompt()`)
- 패키지: 없음
- Tattoo schema 의 active_assertions / assertions 필드 정찰

## Verification

```bash
# 1) syntax
.venv/Scripts/python -m py_compile experiments/orchestrator.py

# 2) reducer_post_stage 인자 + default
.venv/Scripts/python -c "
from experiments.orchestrator import run_abc_chain
import inspect
sig = inspect.signature(run_abc_chain)
assert 'reducer_post_stage' in sig.parameters
assert sig.parameters['reducer_post_stage'].default is False
print('verification 2 ok: reducer_post_stage 인자')
"

# 3) Exp11 c_caller + Exp12 extractor_pre_stage + 본 plan reducer_post_stage 공존
.venv/Scripts/python -c "
from experiments.orchestrator import run_abc_chain
import inspect
sig = inspect.signature(run_abc_chain)
for opt in ('c_caller', 'extractor_pre_stage', 'reducer_post_stage'):
    assert opt in sig.parameters, f'{opt} 부재'
print('verification 3 ok: 3 옵션 공존')
"

# 4) Reducer 호출 로직 확인
.venv/Scripts/python -c "
import inspect
from experiments.orchestrator import run_abc_chain
src = inspect.getsource(run_abc_chain)
assert 'reducer_post_stage' in src
assert 'build_reducer_prompt' in src or 'REDUCER' in src
print('verification 4 ok: reducer 호출 로직')
"
```

4 명령 모두 정상.

## Risks

- **Risk 1 — Tattoo schema 의 active_assertions 필드명 차이** — `tattoo.active_assertions` vs `tattoo.assertions` (with status filter) vs 다른 패턴. 정찰 후 정확한 필드 사용. fallback: 모든 assertions 사용 (status filter 안 함)
- **Risk 2 — assertions 의 confidence 필드 부재** — None 처리 (Step 2 의 코드 stub 에 `getattr(..., None)` 으로 graceful)
- **Risk 3 — Reducer 응답이 너무 김 / max_tokens 초과** — final answer 가 짧아야 함. SAMPLING_PARAMS 의 max_tokens=4096 한도 충분
- **Risk 4 — Sonnet 이 cycle 루프 *안* 에 Reducer 추가** — 본 plan = post-stage (cycle 루프 *밖*) 만. 잘못 위치 시 비용 8배

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/system_prompt.py` (task-01 영역) — read-only import
- `experiments/measure.py` / `score_answer_v*` — 본 plan 영역 외
- `experiments/run_helpers.py` (Stage 2A) — 변경 금지
- `experiments/schema.py` — 변경 금지
- `experiments/_external/gemini_client.py` — 변경 금지
- 모든 기존 `experiments/exp**/run.py` — 변경 금지
- `experiments/exp13_reducer_role/run.py` (task-03 영역)
- 결과 JSON

orchestrator.py 에서 변경 금지 영역:
- `run_chain` (Stage 2C bug fix 적용된 starred unpacking 보존)
- `run_loop` / `call_model` / 다른 함수
- `run_abc_chain` 의 ABC 로직 자체 — post-stage hook 만 추가
- Exp11 의 `c_caller` 분기 + Exp12 의 `extractor_pre_stage` 분기 — 보존
