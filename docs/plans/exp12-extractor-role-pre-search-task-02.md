---
type: plan-task
status: todo
updated_at: 2026-05-03
parent_plan: exp12-extractor-role-pre-search
parallel_group: B
depends_on: [01]
---

# Task 02 — `run_abc_chain` 의 extractor pre-stage hook

## Changed files

- `experiments/orchestrator.py` — **수정**. `run_abc_chain` 에 `extractor_pre_stage: bool = False` 옵션 추가 (1-2 라인) + pre-stage 호출 로직 (5-10 라인)

수정 1.

## Change description

### 배경

task-01 의 `EXTRACTOR_PROMPT` + `build_extractor_prompt()` 위에서 orchestrator 에 pre-stage hook 추가. `run_abc_chain` 호출 시 `extractor_pre_stage=True` 면 trial 시작 시 1회 Extractor 호출 → 결과 claims/entities 를 task prompt 에 prefix 로 주입.

backward compat: `extractor_pre_stage=False` (default) 시 기존 동작 그대로.

### Step 1 — `run_abc_chain` 시그니처 정찰

```bash
.venv/Scripts/python -c "
import inspect
from experiments.orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
print(f'  signature: {sig}')
"
```

기대: `(task_id, objective, prompt, constraints, termination, max_cycles, use_phase_prompt, c_caller)` (Exp11 의 c_caller 추가 후 시그니처).

### Step 2 — `extractor_pre_stage` 옵션 추가

`run_abc_chain` 의 시그니처 끝에 추가:

```python
def run_abc_chain(
    task_id: str,
    objective: str,
    prompt: str,
    constraints: list[str] | None = None,
    termination: str = "...",
    max_cycles: int = 8,
    use_phase_prompt: bool = True,
    c_caller: Callable[[list[dict]], tuple[str, dict]] | None = None,
    extractor_pre_stage: bool = False,  # 신규 (default=False=기존 동작)
) -> tuple[Tattoo, list, str | None]:
    ...
```

### Step 3 — Extractor 호출 + prompt prefix 주입 로직

`run_abc_chain` 의 본격 cycle 루프 *전* 에 Extractor 호출 추가:

```python
# Step 3 의 코드 stub:
extractor_result_text = None
if extractor_pre_stage:
    from system_prompt import build_extractor_prompt
    extractor_messages = build_extractor_prompt(prompt)
    extractor_response, _meta = call_model(extractor_messages)
    extractor_result_text = extractor_response.strip()
    # prompt 에 prefix 주입
    if extractor_result_text:
        prompt = (
            "## Pre-extracted structure (from Extractor agent):\n"
            f"{extractor_result_text}\n\n"
            "## Original task prompt:\n"
            f"{prompt}"
        )
    print(f"  [Extractor] result preview: {extractor_result_text[:200]}{'...' if len(extractor_result_text or '') > 200 else ''}")
```

**중요**:
- Extractor 호출은 trial 시작 시 1회만 (cycle 루프 *밖*)
- prefix 주입 후 `prompt` 변수 자체가 prefix 포함된 새 prompt
- 기존 cycle 루프는 변경 0 — A/B/C 가 prefix 포함된 prompt 받음
- Extractor JSON parse 실패 / 빈 응답 시 prefix 미주입 (graceful fallback)

### Step 4 — extractor 결과 결과 dict 에 보존 (선택)

본 plan 의 task-03 의 run.py 가 Extractor 결과 raw text 를 trial 결과 JSON 에 보존하면 분석 시 도움. 단 orchestrator 변경 최소 정책 — task-03 의 run.py 가 별도 호출하여 보존하는 패턴이 더 정합.

**Architect 결정**: orchestrator 는 print 만, 결과 JSON 저장은 task-03 의 run.py 가 별도 처리. 본 task 의 변경 = `extractor_pre_stage` 옵션 + 호출 + prefix 주입 + print.

### Step 5 — backward compat 검증

기존 도구 (Exp10 / Exp11 / Stage 2C) 의 `run_abc_chain` 호출이 `extractor_pre_stage` 인자 미지정 시 기존 동작 보장:

```bash
.venv/Scripts/python -c "
from experiments.orchestrator import run_abc_chain
import inspect
sig = inspect.signature(run_abc_chain)
params = sig.parameters
assert 'extractor_pre_stage' in params
assert params['extractor_pre_stage'].default is False
# c_caller 도 보존
assert 'c_caller' in params
print('verification 1 ok: extractor_pre_stage + c_caller 보존')
"
```

## Dependencies

- task-01 마감 (`EXTRACTOR_PROMPT` + `build_extractor_prompt()`)
- 패키지: 없음
- 다른 subtask: 없음 (parallel_group B)

## Verification

```bash
# 1) syntax
.venv/Scripts/python -m py_compile experiments/orchestrator.py
echo "ok: syntax"

# 2) extractor_pre_stage 인자 + default
.venv/Scripts/python -c "
from experiments.orchestrator import run_abc_chain
import inspect
sig = inspect.signature(run_abc_chain)
assert 'extractor_pre_stage' in sig.parameters
assert sig.parameters['extractor_pre_stage'].default is False
print('verification 2 ok: extractor_pre_stage 인자 + default=False')
"

# 3) Exp11 의 c_caller + 본 plan 의 extractor_pre_stage 공존
.venv/Scripts/python -c "
from experiments.orchestrator import run_abc_chain
import inspect
sig = inspect.signature(run_abc_chain)
params = sig.parameters
assert 'c_caller' in params and 'extractor_pre_stage' in params
print('verification 3 ok: c_caller + extractor_pre_stage 공존')
"

# 4) source 안의 build_extractor_prompt import 패턴
.venv/Scripts/python -c "
import inspect
from experiments.orchestrator import run_abc_chain
src = inspect.getsource(run_abc_chain)
assert 'extractor_pre_stage' in src
assert 'build_extractor_prompt' in src or 'EXTRACTOR' in src
print('verification 4 ok: extractor 호출 로직')
"
```

4 명령 모두 정상.

## Risks

- **Risk 1 — orchestrator import 차이**: `from system_prompt import ...` (현 패턴) vs `from .system_prompt import ...`. 정찰 후 패턴 따름
- **Risk 2 — prompt prefix 주입이 너무 김**: Extractor 결과 + 원 prompt 합쳐 SYSTEM_PROMPT 의 max context 초과 가능 (4096 max_tokens 한도 vs 8K context). Gemma E4B context 131K — 영향 작음. 단 dry-run 시 첫 cycle 의 A 응답 길이 / format 확인
- **Risk 3 — Extractor JSON parse 실패 시 fallback**: graceful fallback (prefix 미주입) 으로 baseline 동작. trial 단위 fail 0
- **Risk 4 — Sonnet 이 cycle 루프 안에 Extractor 추가**: 본 plan = trial 시작 시 1회만. 잘못된 위치는 비용 8배

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/system_prompt.py` (task-01 영역) — read-only import 만
- `experiments/measure.py` / `score_answer_v*` — 본 plan 영역 외
- `experiments/run_helpers.py` (Stage 2A) — 변경 금지
- `experiments/schema.py` — 변경 금지
- `experiments/_external/gemini_client.py` — 변경 금지 (Exp11 영역)
- 모든 기존 `experiments/exp**/run.py` — 변경 금지
- `experiments/exp12_extractor_role/run.py` (task-03 영역)
- 결과 JSON / docs

orchestrator.py 에서 변경 금지 영역:
- `run_chain` (Stage 2C bug fix 적용된 starred unpacking 보존)
- `run_loop` / `call_model` / 다른 함수 — 변경 금지
- `run_abc_chain` 의 ABC 로직 자체 — pre-stage hook 만 추가
- Exp11 의 `c_caller` 분기 — 변경 금지 (보존)
