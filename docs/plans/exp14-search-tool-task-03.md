---
type: plan-task
status: pending
updated_at: 2026-05-05
parent_plan: exp14-search-tool
parallel_group: C
depends_on: [01, 02]
---

# Task 03 — `exp14_search_tool/run.py` + 2 condition + tattoo_history

## Changed files

- `experiments/exp14_search_tool/__init__.py` — **신규**
- `experiments/exp14_search_tool/run.py` — **신규**. 2 condition (baseline_abc_chunked + abc_search_tool) + cycle-by-cycle tattoo_history (Stage 2C 결함 fix 보존, Exp12/13 패턴) + longctx_taskset 로드 + corpus chunked 주입
- `experiments/exp14_search_tool/results/.gitkeep` — **신규**

신규 3.

## Change description

### 배경

task-01 의 `SEARCH_TOOL_SCHEMA` + task-02 의 `search_tool` hook 위에서 Exp14 실험 도구. **Exp12/13 `run.py` 패턴 그대로** — `run_baseline_abc_chunked` (search_tool=False) + `run_abc_search_tool` (search_tool=True, corpus 주입). longctx_taskset.json 의 10 task 사용.

`gemento-experiment-scaffold` 스킬 활용 권장 — 직전 Exp12 또는 Exp13 의 run.py 패턴 정확 복제 후 변경 부분만 적용.

### Step 1 — 디렉토리 신규

```bash
mkdir -p experiments/exp14_search_tool/results
touch experiments/exp14_search_tool/__init__.py
touch experiments/exp14_search_tool/results/.gitkeep
```

### Step 2 — taskset 로드 함수 (longctx 전용)

main `taskset.json` 과 다름 — longctx_taskset 의 task 는 `document_path`, `gold_evidence_chunks` 등 추가 필드.

```python
def _load_longctx_taskset(taskset_path: str) -> list[dict]:
    """longctx_taskset.json 로드. 각 task 에 chunked corpus 주입."""
    with open(taskset_path, "r", encoding="utf-8") as f:
        ts = json.load(f)
    tasks = ts["tasks"]

    # 각 task 의 document 로드 + chunk
    from tools import chunk_document
    base_dir = Path(taskset_path).parent
    for task in tasks:
        doc_path = base_dir / task["document_path"]
        with open(doc_path, "r", encoding="utf-8") as f:
            doc_text = f.read()
        chunks = chunk_document(doc_text, size=500, overlap=50)
        task["_chunks"] = [c.to_dict() for c in chunks]
    return tasks
```

### Step 3 — `run_baseline_abc_chunked`

Exp09 의 `abc_chunked` 패턴 — sequential chunk → A 의 Tattoo 누적. 단 본 plan 영역 = 새 함수 (Exp09 코드 의존 없이). 가장 간단한 구현 = ABC + corpus 미주입 + search_tool=False:

```python
def run_baseline_abc_chunked(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """A/B/C 모두 Gemma + Search Tool 없음. corpus 는 prompt 에 직접 포함."""
    start = time.time()
    final_answer = None; error = None; actual_cycles = 0
    tattoo_history = []
    try:
        # corpus 를 prompt 에 통째로 포함
        corpus_text = "\n\n".join(c["content"] for c in task["_chunks"])
        full_prompt = f"{task['question']}\n\nDocument:\n{corpus_text}"
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_baseline_chunked_t{trial_idx}",
            objective=task.get("question", ""),
            prompt=full_prompt,
            constraints=None,
            termination="...",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=False,
            reducer_post_stage=False,
            search_tool=False,  # ⭐ baseline = 미주입
            corpus=None,
        )
        actual_cycles = len(abc_logs)
        tattoo_history = _extract_tattoo_history(abc_logs, tattoo)
        if not final_answer:
            error = f"baseline_abc_chunked: no final_answer after {actual_cycles} cycles"
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history if tattoo_history else None,
    }
```

**중요 — context 한계**: longctx-large (20K word) 가 prompt 에 통째로 들어가면 LM Studio 의 context window 초과 가능. 단 Exp09 의 ABC chunked arm 도 같은 한계 (Exp09 결과: large 에서 chunked 처리). 본 baseline 은 *Search Tool 없이 어떻게든 답을 내는지* 측정 — context overflow 는 Exp09 결과와 정합.

대안 baseline: Exp09 의 abc_chunked 함수 직접 import. Sonnet 결정 (참조 Exp09 의 run.py 와 cross-reference).

### Step 4 — `run_abc_search_tool`

```python
def run_abc_search_tool(task: dict, trial_idx: int, max_cycles: int = DEFAULT_MAX_CYCLES) -> dict:
    """A/B/C 모두 Gemma + A 가 search_chunks 호출 가능."""
    start = time.time()
    final_answer = None; error = None; actual_cycles = 0
    tattoo_history = []
    try:
        # corpus 는 별도 — prompt 에 포함 안 함
        full_prompt = task["question"]
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_search_tool_t{trial_idx}",
            objective=task.get("question", ""),
            prompt=full_prompt,
            constraints=None,
            termination="...",
            max_cycles=max_cycles,
            use_phase_prompt=True,
            extractor_pre_stage=False,
            reducer_post_stage=False,
            search_tool=True,   # ⭐ Search Tool 활성
            corpus=task["_chunks"],
        )
        actual_cycles = len(abc_logs)
        tattoo_history = _extract_tattoo_history(abc_logs, tattoo)
        if not final_answer:
            error = f"abc_search_tool: no final_answer after {actual_cycles} cycles"
    except Exception as e:
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    return {
        "final_answer": str(final_answer) if final_answer else None,
        "error": error,
        "cycles": actual_cycles,
        "duration_ms": duration_ms,
        "tattoo_history": tattoo_history if tattoo_history else None,
    }
```

### Step 5 — CONDITION_DISPATCH + run_experiment + main

Exp12/13 패턴 그대로. CONDITION_DISPATCH:

```python
CONDITION_DISPATCH = {
    "baseline_abc_chunked": run_baseline_abc_chunked,
    "abc_search_tool": run_abc_search_tool,
}
```

`run_experiment` / `main` 은 Exp12 또는 Exp13 의 동일 함수 그대로 재사용. 변경:
- taskset loader = `_load_longctx_taskset` (위 Step 2)
- default conditions = `("baseline_abc_chunked", "abc_search_tool")`
- default trials = 5
- default max_cycles = 8
- default `--taskset` = `experiments/tasks/longctx_taskset.json`

**중요**: `gemento-experiment-scaffold` 스킬 활용. 직전 Exp 의 run.py read 후 변형 — 임의 단순화 금지.

### Step 6 — Stage 2A/2B/2C 인프라 보존

Exp12/13 패턴 그대로:
- Stage 2A healthcheck/abort + 결과 JSON meta v1.0
- Stage 2B FailureLabel
- Stage 2C tattoo_history cycle-by-cycle (`_extract_tattoo_history`)

## Dependencies

- task-01 (SEARCH_TOOL_SCHEMA + make_search_chunks_tool)
- task-02 (orchestrator search_tool hook)
- 기존 `experiments/run_helpers.py` (Stage 2A) — read-only
- 기존 `experiments/measure.py:score_answer_v3` — read-only
- 기존 `experiments/tools/chunker.py:chunk_document` — read-only
- 기존 `experiments/tasks/longctx_taskset.json` — read-only
- 기존 `experiments/tasks/longctx_docs/*.txt` — read-only

## Verification

```bash
# 1) syntax + import + help
.venv/Scripts/python -m py_compile experiments/exp14_search_tool/run.py
.venv/Scripts/python -m experiments.exp14_search_tool.run --help

# 2) condition dispatch
.venv/Scripts/python -c "
from experiments.exp14_search_tool.run import CONDITION_DISPATCH
assert 'baseline_abc_chunked' in CONDITION_DISPATCH
assert 'abc_search_tool' in CONDITION_DISPATCH
print('verification 2 ok: 2 condition dispatch')
"

# 3) abc_search_tool 가 search_tool=True 호출 패턴
.venv/Scripts/python -c "
import inspect
from experiments.exp14_search_tool.run import run_abc_search_tool
src = inspect.getsource(run_abc_search_tool)
assert 'search_tool=True' in src
assert 'corpus=task[' in src or 'corpus=task.get' in src
print('verification 3 ok: search_tool=True + corpus 주입')
"

# 4) longctx_taskset 로드 동작
.venv/Scripts/python -c "
from experiments.exp14_search_tool.run import _load_longctx_taskset
tasks = _load_longctx_taskset('experiments/tasks/longctx_taskset.json')
assert len(tasks) == 10, f'expected 10 tasks, got {len(tasks)}'
assert all('_chunks' in t for t in tasks), 'chunks 미주입'
sample = tasks[0]
assert len(sample['_chunks']) >= 1
print(f'verification 4 ok: 10 tasks loaded, sample chunks={len(sample[\"_chunks\"])}')
"

# 5) baseline_abc_chunked 가 search_tool=False 호출 패턴
.venv/Scripts/python -c "
import inspect
from experiments.exp14_search_tool.run import run_baseline_abc_chunked
src = inspect.getsource(run_baseline_abc_chunked)
assert 'search_tool=False' in src
print('verification 5 ok: baseline search_tool=False 명시')
"
```

5 명령 모두 정상 + (사용자 직접) dry-run 1 task × 1 trial × abc_search_tool 검증 (Step 7 = task-04 진입 직전).

## Risks

- **Risk 1 — Exp12/13 패턴 복사 실패**: Sonnet 이 Exp12 또는 Exp13 run.py 정확히 read 후 변형. 임의 단순화 금지 — `gemento-experiment-scaffold` 스킬 활용
- **Risk 2 — context overflow** (longctx-large 의 baseline): 20K word 가 prompt 에 통째로 들어가면 LM Studio 한계 가능. 본 plan 의 baseline = "Search Tool 없이 어떻게든" 측정 — overflow 발생 시 Exp09 결과와 정합. 만약 healthcheck/abort 가 발화하면 사용자 보고
- **Risk 3 — Search Tool 미호출 (tool_neglect)**: Exp08 의 tool_neglect 회귀. dry-run 첫 trial 의 tool_call_log 가 비어있으면 사용자 보고 (prompt 강화 별도 plan)
- **Risk 4 — _chunks 메모리 폭증**: longctx-large 의 chunked corpus = ~200KB × 10 task. python 메모리 OK, 단 task dict 의 결과 JSON 직렬화에서는 `_chunks` 제외 (corpus 는 결과에 저장 안 함)
- **Risk 5 — Reducer/Extractor 와의 동시 활성화 가능성**: Sonnet 이 search_tool=True 와 reducer_post_stage=True 동시 활성화 시도 가능. 본 plan = search_tool 만, 다른 hook 명시적 False
- **Risk 6 — `chunk_document` 의 size 파라미터**: Exp09 default = 500 word, overlap = 50. 본 plan 도 동일 사용 — 임의 변경 금지

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/tools/bm25_tool.py` (task-01 영역) — read-only import
- `experiments/orchestrator.py` (task-02 영역) — read-only 호출만
- `experiments/measure.py` / `score_answer_v*`
- `experiments/run_helpers.py` (Stage 2A) — read-only
- `experiments/schema.py`
- `experiments/system_prompt.py`
- `experiments/tools/chunker.py` — read-only
- `experiments/tasks/longctx_taskset.json` — read-only
- `experiments/tasks/longctx_docs/*.txt` — read-only
- 모든 기존 `experiments/exp**/run.py` — 변경 금지 (Exp12/13 패턴 read-only 참조만)
- 결과 JSON
