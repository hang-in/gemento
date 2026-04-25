---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: exp08-math-tool-use-calculator-linalg-lp-exp07
parallel_group: C
depends_on: [02]
---

# Task 03 — Orchestrator tool 통합 (call_model + A 경로)

## Changed files

- `experiments/orchestrator.py`
  - `call_model()` (line 50~63): `tools` 인자 추가 + tool_calls 루프
  - `run_abc_chain()` 또는 하위 헬퍼 (line 414~): A 경로에서만 tools 주입 (B/C는 현상 유지)
  - (선택) `ABCCycleLog` 확장 고려 — tool_calls 기록 필드. 필요하면 `experiments/schema.py` 터치.
- `experiments/system_prompt.py`
  - `SYSTEM_PROMPT` (line 7~): math 태스크에서 수치 계산은 반드시 tool 사용 지시 문구 추가
  - `build_prompt()` (line 89~): tools 활용 안내를 user content에 포함 (조건부: tool_results 없이 초기 호출일 때)
- `experiments/schema.py` (필요 시): `ABCCycleLog`에 `tool_calls: list` 필드 추가 (기본값 `field(default_factory=list)`). 200줄 초과 시 Grep으로 필드 정의부 타겟 Read.

## Change description

### 1. `call_model()` 시그니처 확장

```python
def call_model(
    messages: list[dict],
    model: str = MODEL_NAME,
    tools: list[dict] | None = None,
    tool_functions: dict | None = None,
    max_tool_rounds: int = 5,
) -> tuple[str, list[dict]]:
    """OpenAI-compatible chat API 호출. tools 제공 시 tool_calls 루프 자동 처리.

    반환: (final_content, tool_call_log)
      - final_content: 최종 assistant 메시지 content (str)
      - tool_call_log: [{"name": str, "arguments": dict, "result": Any, "error": str|None}, ...]

    기존 호출부는 tools=None이므로 반환값 언팩 필요. 내부에서 str만 쓰던 호출부는
    first-element 인덱싱으로 수정한다.
    """
```

**Step 1**: tools 인자 없음 → 기존 동작 유지 (tuple 반환하되 두 번째는 빈 리스트).

**Step 2**: tools 인자 있음 → 다음 루프:
1. payload에 `"tools": tools, "tool_choice": "auto"` 추가. JSON mode는 tool_calls와 충돌할 수 있으므로 tools 사용 시 `response_format` 제거 — 최종 content 파싱 실패 시 `extract_json_from_response()`에 폴백.
2. API 호출 → 응답 message의 `tool_calls` 확인.
3. `tool_calls` 존재 시: 각 tool_call을 `tool_functions[name](**json.loads(arguments))`로 실행. 예외는 기록하되 loop 중단 금지 (도구 에러도 모델에게 피드백).
4. assistant 메시지(+tool_calls) + 각 tool role 메시지를 messages에 append.
5. 다시 API 호출 → tool_calls 없으면 loop 종료, content 반환.
6. `max_tool_rounds` 초과 시 `RuntimeError("tool loop exceeded")`.

**참고**: llama.cpp OpenAI 호환 엔드포인트는 `tool_calls` 필드와 `finish_reason='tool_calls'`를 표준대로 반환한다 (`/props`에서 `supports_tool_calls: true` 확인됨).

### 2. 기존 call_model 호출부 수정

- grep 한 뒤 (예: `grep -n 'call_model(' experiments/*.py`) 모든 호출부를 tuple 언팩으로 조정.
- 대부분 호출부는 tool 없이 쓰므로 `raw, _ = call_model(messages)` 패턴.

### 3. `run_abc_chain()` — A 경로만 tool 주입

`run_abc_chain()` 안에서 A를 호출하는 `run_loop(tattoo, cycle, phase_prompt_args=phase_args)` 경로에만 tool을 주입한다. B/C 경로는 그대로.

**구현 방식** (권장):
- `run_abc_chain`에 `use_tools: bool = False` 인자 추가.
- `run_loop`를 수정해서 `call_model` 호출부에 조건부 tools 주입:
  ```python
  if use_tools:
      from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS
      raw, tool_call_log = call_model(messages, tools=TOOL_SCHEMAS, tool_functions=TOOL_FUNCTIONS)
  else:
      raw, tool_call_log = call_model(messages)
  ```
- `tool_call_log`를 `ABCCycleLog` 또는 `a_log`에 기록. Task 05에서 집계.

**대안**: `run_loop`에 직접 `use_tools` 전달하지 않고, `run_abc_chain`에서 flag를 thread-local 또는 함수 인자 체인으로 전달. 현 시점 구조(run_loop는 A 이외에는 호출 안 됨)에서는 인자 추가가 단순.

### 4. `system_prompt.py` — A의 tool-use 가이드

`SYSTEM_PROMPT`(line 7) 맨 아래에 다음 블록을 추가:

```
## Tool use (math tasks)

When the task involves numeric calculation, a linear system, or an optimization (linear programming), you MUST call the appropriate tool rather than computing manually:

- `calculator(expression)` — basic arithmetic. Example: `(13+7)*3.5`.
- `solve_linear_system(A, b)` — solve Ax = b for n×n A.
- `linprog(c, A_ub, b_ub, bounds, ...)` — minimize c·x. For MAXIMIZATION, negate c (e.g. to maximize 50x+40y, pass c=[-50,-40]).

Integer answers: LP/linear solvers return floats; round to nearest integer if the problem expects integers, then verify via `calculator`.

Do not fabricate numeric results. If a tool is available, use it.
```

**주의**: 기존 JSON 스키마 지시와 충돌하지 않도록 tool-use 섹션은 끝에 추가. build_prompt는 tools 주입 여부와 무관하게 동일 SYSTEM_PROMPT를 쓰므로, 모델이 tool을 호출할지는 tool 파라미터의 유무가 결정한다 (baseline arm에서는 tools 없음 → 도구 호출 불가).

### 5. ABCCycleLog 확장 (선택)

`schema.py`의 `ABCCycleLog` dataclass에 `tool_calls: list[dict] = field(default_factory=list)` 추가 — Task 05의 분석용. 기존 필드는 터치 금지.

## Dependencies

- **Task 02 완료**: `experiments/tools/` 모듈이 존재해야 import 가능.
- 외부 패키지 추가 없음 (scipy/numpy는 Task 02에서 이미 도입).

## Verification

```bash
# 1. call_model에 tools 파라미터 존재
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
import inspect
from orchestrator import call_model
sig = inspect.signature(call_model)
assert 'tools' in sig.parameters and 'tool_functions' in sig.parameters
print('OK tools param')
"
# 기대: "OK tools param"

# 2. run_abc_chain에 use_tools 인자 존재
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
import inspect
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
assert 'use_tools' in sig.parameters
print('OK use_tools param')
"
# 기대: "OK use_tools param"

# 3. SYSTEM_PROMPT에 tool-use 섹션 추가됨
grep -c "Tool use (math tasks)" experiments/system_prompt.py
# 기대: 1

# 4. 기존 호출부 회귀 없음 — import 한 번으로 전 파일 syntax 확인
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
import orchestrator, run_experiment, measure, schema, system_prompt
print('all imports OK')
"
# 기대: "all imports OK"

# 5. tool 미주입 시 기존 동작 유지 — 기존 실험 시그니처 호출 가능성
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
import inspect
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
assert sig.parameters['use_tools'].default is False, 'use_tools must default False'
print('OK default False')
"
# 기대: "OK default False"
```

## Risks

- **기존 call_model 호출부**: 반환값을 str에서 tuple로 변경했기 때문에 grep 누락 시 `TypeError: 'tuple' not iterable` 등 즉시 에러. 그래프 기반 영향 확인 필요: `run_loop`, `run_chain`, `run_abc_chain`, B/C 경로 등. (code-review-graph 리포트가 이 4개 함수 test gap을 보고했음 — 본 Task가 이들 영향 경로에 진입.)
- **response_format 제거**: tools 사용 시 JSON mode 강제 해제. 최종 content가 plain text일 경우 `extract_json_from_response()`의 폴백 파싱이 작동해야 함. baseline arm에는 영향 없음 (tools=None, response_format 유지).
- **tool 예외 전파**: `tool_functions[name](**args)`에서 예외 시 해당 tool_call 결과를 `{"error": str(e)}` 로 기록. 전체 루프는 유지. silent 하지 않음.
- **라이브러리 종속 순서**: orchestrator가 tools를 import하므로 tools/ 패키지 오류 시 orchestrator 전체 임포트 실패. Task 02 smoke 통과가 전제.
- **MAX_LOOPS vs max_tool_rounds**: 서로 다른 루프. tool loop는 단일 A 호출 내부, MAX_LOOPS는 cycle 수준. 혼동 방지 주석 필수.

## Scope boundary

**Task 03에서 절대 수정 금지**:
- `experiments/tools/` 내부 파일 (Task 02 영역)
- `experiments/run_experiment.py` (Task 04 영역 — 새 분기 추가는 다음 Task)
- `experiments/measure.py` (Task 01/05 영역)
- `experiments/config.py` — 본 Task에서는 touch 금지
- `docs/reference/handoff-to-gemini-exp7-final.md` (Task 01 영역)

**허용 범위**: orchestrator.py, system_prompt.py, schema.py (ABCCycleLog 필드 1개 추가 한정).
