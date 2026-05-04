---
type: plan-task
status: pending
updated_at: 2026-05-05
parent_plan: exp14-search-tool
parallel_group: B
depends_on: [01]
---

# Task 02 — `run_abc_chain` 의 search_tool hook + corpus 주입

## Changed files

- `experiments/orchestrator.py` — **수정**. `run_abc_chain` 에 `search_tool: bool = False` + `corpus: list[dict] | None = None` 인자 추가 + tool_function 결합 로직 (5-15 라인)

수정 1.

## Change description

### 배경

task-01 의 `SEARCH_TOOL_SCHEMA` + `make_search_chunks_tool` 위에서 orchestrator hook. ABC cycle 의 `run_loop` 호출 시 `use_tools=True` 활성화 + Search Tool 의 schema/function 주입.

backward compat: `search_tool=False` (default) 시 기존 동작 유지. Exp08 의 use_tools (math) 와 본 plan 의 search_tool 의 *공존* 보장.

### Step 1 — 시그니처 정찰

```bash
.venv/Scripts/python -c "
import inspect
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
print(f'  signature: {sig}')
" 2>&1 | head
```

(experiments 디렉토리에서 실행 — orchestrator.py 가 `from schema import ...` 사용)

기대: `(task_id, objective, prompt, constraints, termination, max_cycles, use_phase_prompt, c_caller, extractor_pre_stage, reducer_post_stage)` (Exp11/12/13 누적).

### Step 2 — 새 인자 추가

`run_abc_chain` 의 시그니처:

```python
def run_abc_chain(
    task_id, objective, prompt,
    constraints=None, termination="...",
    max_cycles=8, use_phase_prompt=True,
    c_caller=None,
    extractor_pre_stage=False,
    reducer_post_stage=False,
    search_tool: bool = False,   # 신규
    corpus: list[dict] | None = None,  # 신규
) -> tuple[Tattoo, list, str | None]:
    ...
```

### Step 3 — tool_functions / tools 결합

`run_abc_chain` 의 cycle 루프에서 A 의 호출 부분 (현재 `use_tools` 처리 영역) 에 search_tool 결합:

기존 패턴 (Exp08):
```python
# A 호출 시
if use_tools:
    from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS
    tool_fns_a = TOOL_FUNCTIONS
    tools_a = TOOL_SCHEMAS
```

본 plan 변경 — search_tool 활성 시 schema 와 function 추가 결합:

```python
# A (그리고 옵션으로 B/C) 호출 시
_extra_tools = []
_extra_fns = {}
if search_tool and corpus is not None:
    from tools import SEARCH_TOOL_SCHEMA, make_search_chunks_tool
    _extra_tools.append(SEARCH_TOOL_SCHEMA)
    _extra_fns["search_chunks"] = make_search_chunks_tool(corpus)

# 기존 use_tools (math) 와 결합
if use_tools or _extra_tools:
    from tools import TOOL_FUNCTIONS, TOOL_SCHEMAS
    tool_fns_a = {**(TOOL_FUNCTIONS if use_tools else {}), **_extra_fns}
    tools_a = (TOOL_SCHEMAS if use_tools else []) + _extra_tools
else:
    tool_fns_a = None
    tools_a = None
```

**중요 — Sonnet 진행 시**:
- 기존 `run_loop` 의 `use_tools` 분기 정확히 read 후 위 패턴 적용
- A 호출에만 search_tool 노출 (B/C 는 미적용 — A 의 reasoning 보조가 본 plan 가설)
- 단 사용자 / Architect 가 후속 plan 에서 B/C 도 공개 가능 — 본 plan = A 한정
- math TOOL_FUNCTIONS 와 SEARCH 의 dict merge 시 키 충돌 없음 검증 (search_chunks 는 신규 키)

### Step 4 — Search Tool 호출 로그

`run_abc_chain` 의 return 또는 ABCCycleLog 에 `search_calls: list[dict]` 추가 가능. 본 plan = 최소 변경 — 기존 `tool_call_log` 가 자동으로 search 호출 capture (call_model 의 tool_call_log 매핑 활용). run.py (task-03) 에서 trial 결과에 함께 저장.

### Step 5 — backward compat 검증

```bash
.venv/Scripts/python -c "
import inspect
import sys; sys.path.insert(0, 'experiments')
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
params = sig.parameters
for opt in ('c_caller', 'extractor_pre_stage', 'reducer_post_stage', 'search_tool', 'corpus'):
    assert opt in params, f'{opt} 부재'
assert params['search_tool'].default is False
assert params['corpus'].default is None
print('verification ok: 5 hook 공존 + search_tool/corpus default')
"
```

## Dependencies

- task-01 마감 (`SEARCH_TOOL_SCHEMA` + `make_search_chunks_tool`)
- 기존 `experiments/orchestrator.py:run_loop` 의 `use_tools` 분기 (Exp08 영역) — read-only

## Verification

```bash
# experiments 디렉토리에서 실행
cd D:/privateProject/gemento/experiments

# 1) syntax
../.venv/Scripts/python -m py_compile orchestrator.py

# 2) search_tool 인자 + default
../.venv/Scripts/python -c "
import inspect
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
assert 'search_tool' in sig.parameters
assert 'corpus' in sig.parameters
assert sig.parameters['search_tool'].default is False
assert sig.parameters['corpus'].default is None
print('verification 2 ok: search_tool + corpus 인자 + default')
"

# 3) 5 hook 공존 (Exp11 c_caller + Exp12 extractor + Exp13 reducer + 본 plan search_tool/corpus)
../.venv/Scripts/python -c "
import inspect
from orchestrator import run_abc_chain
sig = inspect.signature(run_abc_chain)
for opt in ('c_caller', 'extractor_pre_stage', 'reducer_post_stage', 'search_tool', 'corpus'):
    assert opt in sig.parameters, f'{opt} 부재'
print('verification 3 ok: 5 hook 공존')
"

# 4) source 의 결합 로직 키워드 확인
../.venv/Scripts/python -c "
import inspect
from orchestrator import run_abc_chain
src = inspect.getsource(run_abc_chain)
assert 'search_tool' in src
assert 'corpus' in src
assert 'SEARCH_TOOL_SCHEMA' in src or 'make_search_chunks_tool' in src
print('verification 4 ok: search_tool 결합 로직')
"

# 5) Exp08 use_tools 회귀 검증 (math 라인 보존)
../.venv/Scripts/python -c "
import inspect
from orchestrator import run_abc_chain
src = inspect.getsource(run_abc_chain)
assert 'use_tools' in src, 'Exp08 use_tools 사라짐'
print('verification 5 ok: use_tools 보존')
"
```

5 명령 모두 정상.

## Risks

- **Risk 1 — A 호출 분기에 search_tool 미주입**: `run_loop` 의 use_tools 분기가 A/B/C 어느 쪽인지 정확히 read 후 *A 만* 에 추가. B/C 호출 분기는 변경 금지. dry-run 시 tool_call_log 가 A 호출에서만 발생하는지 검증
- **Risk 2 — math TOOL_FUNCTIONS 와 키 충돌**: math 의 `calculator/solve_linear_system/linprog` vs search 의 `search_chunks` — 키 다름. 단 dict merge 순서 주의 (search 가 math 를 덮어쓰지 않도록)
- **Risk 3 — `_extra_tools` 가 빈 list 일 때 None vs []**: call_model 은 `tools=None` 또는 `tools=[]` 모두 허용해야. 본 task 의 결합 로직에서 빈 list 가 None 으로 변환되는지 검증
- **Risk 4 — ABCCycleLog 의 schema 불일치**: 본 task = ABCCycleLog 변경 0. tool_call_log 는 기존 schema 의 자유 list 필드로 저장 (run_loop 가 이미 처리). run.py (task-03) 에서 결과 JSON 에 통째로 저장
- **Risk 5 — Sonnet 이 cycle 루프 *밖* 에 search_tool 추가**: Reducer 와 다른 — 본 plan 의 Search Tool 은 *cycle 안* 에서 A 가 호출하는 것이 본질. Reducer post-stage 와 혼동 주의

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/tools/bm25_tool.py` (task-01 영역) — read-only import
- `experiments/tools/__init__.py` (task-01 영역)
- `experiments/exp14_search_tool/run.py` (task-03 영역, 미존재)
- `experiments/measure.py` / `score_answer_v*`
- `experiments/run_helpers.py` (Stage 2A)
- `experiments/schema.py`
- `experiments/system_prompt.py`
- `experiments/_external/gemini_client.py` (Exp11 영역)
- 모든 기존 `experiments/exp**/run.py`
- `experiments/exp14_search_tool/run.py` (task-03 영역)
- 결과 JSON

orchestrator.py 에서 변경 금지 영역:
- `run_chain` (Stage 2C bug fix 적용된 starred unpacking 보존)
- `run_loop` 의 핵심 로직 (단 use_tools 분기 *내부* 의 tool dict merge 만 본 task 영역, 시그니처는 변경 금지)
- `call_model` 본체
- Exp11 의 `c_caller` 분기 + Exp12 의 `extractor_pre_stage` 분기 + Exp13 의 `reducer_post_stage` 분기 — 보존
- 기존 `_apply_reducer` 의 Exp13 bug fix (commit `cf057b6`) 보존
