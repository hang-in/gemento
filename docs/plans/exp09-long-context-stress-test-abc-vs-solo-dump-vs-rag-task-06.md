---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: exp09-long-context-stress-test-abc-vs-solo-dump-vs-rag
parallel_group: C
depends_on: [01, 02, 03, 05]
---

# Task 06 — Exp09 실행 분기 (`longctx` 커맨드, 3 arm)

## Changed files

- `experiments/run_experiment.py`
  - 기존 `run_tool_use_refined()` (line 1126~) 뒤에 `run_longctx()` 추가
  - 관련 상수 (`LONGCTX_*`) 추가
  - `EXPERIMENTS` 딕셔너리(line 1242)에 `"longctx": run_longctx` 항목 추가

## Change description

### Step 1 — 상수 정의

```python
# ── Exp09 (longctx) ──
LONGCTX_TRIALS = 3  # MVP
LONGCTX_TASKSET_PATH = TASKS_DIR / "longctx_taskset.json"
LONGCTX_ARMS = [
    {"label": "solo_dump",    "description": "document 전체를 A에 단일 투입"},
    {"label": "rag_baseline", "description": "BM25 top-K chunks만 A에 투입"},
    {"label": "abc_tattoo",   "description": "ABC + Tattoo + chunk iteration"},
]
LONGCTX_CHUNK_SIZE = 500   # words per chunk
LONGCTX_CHUNK_OVERLAP = 50
LONGCTX_RAG_TOP_K = 5
LONGCTX_MAX_FINAL_CYCLES = 5  # ABC arm: 모든 chunk 처리 후 B→C 루프 상한
```

### Step 2 — `run_longctx()` 함수 구조

```python
def run_longctx():
    """실험 9: Long-Context Stress Test (ABC vs Solo-dump vs RAG).
    
    3 arm × 10 tasks × 3 trials = 90 runs. 체크포인트 지원.
    """
    from tools.chunker import chunk_document
    from tools.bm25_tool import bm25_retrieve
    from orchestrator import run_abc_chunked, call_model
    
    # 태스크셋 로드
    with open(LONGCTX_TASKSET_PATH) as f:
        d = json.load(f)
    tasks = d["tasks"]
    
    # document는 path 참조 → 실제 내용 로드
    for t in tasks:
        doc_path = TASKS_DIR / t["document_path"]
        with open(doc_path) as f:
            t["_document"] = f.read()
    
    # 체크포인트
    partial_path = RESULTS_DIR / "partial_longctx.json"
    results: dict = {"solo_dump": [], "rag_baseline": [], "abc_tattoo": []}
    finished: set[tuple[str, str]] = set()
    if partial_path.exists():
        try:
            with open(partial_path) as f:
                partial = json.load(f)
                results = partial.get("results_by_arm", results)
                for arm_label, task_list in results.items():
                    for tr in task_list:
                        finished.add((arm_label, tr["task_id"]))
            print(f"  → Resuming: {len(finished)} (arm, task) pairs done.")
        except Exception:
            print("  ⚠ Checkpoint load failed; starting fresh.")
    
    for arm in LONGCTX_ARMS:
        label = arm["label"]
        for task in tasks:
            if (label, task["id"]) in finished:
                continue
            print(f"\n[LongCtx] arm={label} | task={task['id']} ({task['size_class']}, {task['hop_type']})")
            task_results = []
            for trial in range(LONGCTX_TRIALS):
                print(f"  Trial {trial + 1}/{LONGCTX_TRIALS}...")
                trial_result = _run_longctx_trial(arm, task, trial)
                task_results.append(trial_result)
            results.setdefault(label, []).append({
                "task_id": task["id"],
                "size_class": task["size_class"],
                "hop_type": task["hop_type"],
                "expected_answer": task["expected_answer"],
                "gold_evidence_chunks": task.get("gold_evidence_chunks", []),
                "trials": task_results,
            })
            # 체크포인트 저장
            with open(partial_path, "w", encoding="utf-8") as f:
                json.dump({
                    "experiment": "longctx",
                    "model": MODEL_NAME,
                    "arms": LONGCTX_ARMS,
                    "results_by_arm": results,
                }, f, ensure_ascii=False, indent=2)
    
    # 최종 저장
    final = {
        "experiment": "longctx",
        "model": MODEL_NAME,
        "arms": LONGCTX_ARMS,
        "trials_per_task": LONGCTX_TRIALS,
        "chunk_size": LONGCTX_CHUNK_SIZE,
        "chunk_overlap": LONGCTX_CHUNK_OVERLAP,
        "rag_top_k": LONGCTX_RAG_TOP_K,
        "results_by_arm": results,
    }
    save_result("exp09_longctx", final)
    if partial_path.exists():
        partial_path.unlink()
```

### Step 3 — Arm별 trial 실행 함수

```python
def _run_longctx_trial(arm, task, trial_idx):
    """단일 arm × task × trial 실행. arm label에 따라 분기."""
    from tools.chunker import chunk_document
    from tools.bm25_tool import bm25_retrieve
    from orchestrator import run_abc_chunked, call_model
    
    label = arm["label"]
    question = task["question"]
    document = task["_document"]
    
    if label == "solo_dump":
        # Document 전체 + 질문을 A에 한 번에 투입
        # n_ctx 8K 초과 시 llama.cpp가 truncation (의도적)
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Answer based on the provided document."},
            {"role": "user", "content": f"## Document\n\n{document}\n\n## Question\n\n{question}\n\nProvide the answer as a JSON object: {{\"final_answer\": \"...\"}}."},
        ]
        try:
            raw, _ = call_model(messages)
            final_answer = _extract_answer(raw)
        except Exception as e:
            final_answer = None
            error = str(e)
        return {
            "trial": trial_idx + 1,
            "arm": label,
            "final_answer": final_answer,
            "error": locals().get("error"),
            "doc_word_count": len(document.split()),
        }
    
    elif label == "rag_baseline":
        # BM25 top-K chunks만 A에 투입
        chunks = [c.to_dict() for c in chunk_document(document, size=LONGCTX_CHUNK_SIZE, overlap=LONGCTX_CHUNK_OVERLAP)]
        top = bm25_retrieve(question, chunks, top_k=LONGCTX_RAG_TOP_K)
        top_text = "\n\n---\n\n".join(f"[chunk {c['chunk_id']}]\n{c['content']}" for c in top)
        messages = [
            {"role": "system", "content": "You are a helpful assistant. Answer based on the retrieved chunks."},
            {"role": "user", "content": f"## Retrieved Chunks\n\n{top_text}\n\n## Question\n\n{question}\n\nProvide the answer as a JSON object: {{\"final_answer\": \"...\"}}."},
        ]
        try:
            raw, _ = call_model(messages)
            final_answer = _extract_answer(raw)
        except Exception as e:
            final_answer = None
            error = str(e)
        return {
            "trial": trial_idx + 1,
            "arm": label,
            "final_answer": final_answer,
            "error": locals().get("error"),
            "retrieved_chunk_ids": [c["chunk_id"] for c in top],
            "top_k": LONGCTX_RAG_TOP_K,
        }
    
    elif label == "abc_tattoo":
        chunks = [c.to_dict() for c in chunk_document(document, size=LONGCTX_CHUNK_SIZE, overlap=LONGCTX_CHUNK_OVERLAP)]
        try:
            tattoo, logs, final_answer = run_abc_chunked(
                task_id=f"{task['id']}_t{trial_idx}",
                question=question,
                chunks=chunks,
                max_final_cycles=LONGCTX_MAX_FINAL_CYCLES,
            )
            error = None
            evidence_refs_used = [
                a.evidence_ref for a in tattoo.active_assertions if a.evidence_ref
            ]
        except Exception as e:
            tattoo = None; logs = []; final_answer = None; evidence_refs_used = []
            error = str(e)
        return {
            "trial": trial_idx + 1,
            "arm": label,
            "final_answer": final_answer,
            "error": error,
            "num_chunks": len(chunks),
            "num_assertions": len(tattoo.active_assertions) if tattoo else 0,
            "evidence_refs_used": evidence_refs_used,
        }
    
    raise ValueError(f"unknown arm label: {label}")


def _extract_answer(raw: str) -> str | None:
    """solo_dump / rag_baseline 용 — {"final_answer": "..."} 파싱."""
    from orchestrator import extract_json_from_response
    parsed = extract_json_from_response(raw)
    if parsed and isinstance(parsed, dict):
        return parsed.get("final_answer")
    # 폴백: 원문 자체를 final_answer로
    return raw.strip() if raw else None
```

### Step 4 — EXPERIMENTS 등록

```python
EXPERIMENTS = {
    # ... 기존 ...
    "tool-use-refined": run_tool_use_refined,
    "longctx": run_longctx,  # ← 추가
}
```

### Step 5 — 수정하지 않는 부분

- 기존 `run_tool_use_refined`, `run_tool_use`, `run_abc_pipeline` 등 모든 함수
- `TOOL_USE_*` 상수
- `CONDITIONS`, `LOOP_SAT_REPEAT` 등

## Dependencies

- **Task 01 완료**: `longctx_taskset.json` + `longctx_docs/*.md` 존재해야 태스크 로드.
- **Task 02 완료**: `chunker.chunk_document` 필요.
- **Task 03 완료**: `bm25_tool.bm25_retrieve` 필요.
- **Task 05 완료**: `orchestrator.run_abc_chunked` 필요.
- **Task 04 완료**: `Assertion.evidence_ref` 필드 — ABC arm 결과 기록에 사용.

## Verification

```bash
# 1. longctx 커맨드 등록
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from run_experiment import EXPERIMENTS
assert 'longctx' in EXPERIMENTS
print('OK longctx registered')
"

# 2. argparse --help에 포함
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python run_experiment.py --help 2>&1 | grep -o 'longctx'
# 기대: 'longctx' 출력

# 3. 상수 값 확인
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from run_experiment import LONGCTX_TRIALS, LONGCTX_ARMS, LONGCTX_CHUNK_SIZE, LONGCTX_CHUNK_OVERLAP, LONGCTX_RAG_TOP_K
assert LONGCTX_TRIALS == 3
labels = {a['label'] for a in LONGCTX_ARMS}
assert labels == {'solo_dump', 'rag_baseline', 'abc_tattoo'}
assert LONGCTX_CHUNK_SIZE == 500
assert LONGCTX_CHUNK_OVERLAP == 50
assert LONGCTX_RAG_TOP_K == 5
print('OK constants')
"

# 4. _run_longctx_trial 함수 존재 (arm 분기)
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
from run_experiment import _run_longctx_trial
print('OK helper function present')
"

# 5. Dry-run: 태스크셋 로드 + chunking만 확인 (LLM 호출 없이)
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
import json
from run_experiment import LONGCTX_TASKSET_PATH, TASKS_DIR, LONGCTX_CHUNK_SIZE, LONGCTX_CHUNK_OVERLAP
from tools.chunker import chunk_document
with open(LONGCTX_TASKSET_PATH) as f:
    data = json.load(f)
print(f'loaded {len(data[\"tasks\"])} tasks')
for t in data['tasks'][:3]:
    with open(TASKS_DIR / t['document_path']) as f:
        doc = f.read()
    chunks = chunk_document(doc, size=LONGCTX_CHUNK_SIZE, overlap=LONGCTX_CHUNK_OVERLAP)
    print(f'  {t[\"id\"]}: {len(doc.split())} words → {len(chunks)} chunks')
# 기대: 각 태스크의 words + chunks 출력
"

# 6. 기존 실험 회귀 없음 — import
cd /Users/d9ng/privateProject/gemento/experiments && ../.venv/bin/python -c "
import run_experiment
assert hasattr(run_experiment, 'run_tool_use')
assert hasattr(run_experiment, 'run_tool_use_refined')
assert hasattr(run_experiment, 'run_longctx')
print('OK no regression')
"
```

## Risks

- **n_ctx 8K 초과 방어**: Solo-dump arm에서 Large(20K) 문서는 n_ctx 초과 → llama.cpp가 truncation. **이게 실험 포인트**. 단 truncation이 서버에서 에러로 처리되면 실험 실패. 에러를 `final_answer=None + error=...`로 기록하고 진행하도록 반드시 try/except.
- **Assertion 수 폭증 (ABC arm)**: Task 05에서 지적한 대로 20K 문서는 수십~수백 assertions 생성 가능. Tattoo JSON이 매 chunk 호출마다 주입되면 token 폭증. **완화**: `select_assertions`의 soft_cap을 ABC chunked에서는 훨씬 크게 (혹은 chunk 처리 단계에선 active assertion 요약본만 주입).
- **체크포인트 호환**: 실행 중 긴 문서 load로 시간 오래 걸리므로 체크포인트 필수. `partial_longctx.json` 이름 충돌 없음.
- **실행 시간**: 90 runs + 긴 문서 처리 → ABC arm은 chunk당 1번씩 A 호출 = Large 20K/500 words 기준 40 chunk × 3 trials × 4 tasks = ~480 A calls만 해도 많음. **수 시간 예상**. 체크포인트로 분할 실행.
- **JSON 결과 크기**: tattoo와 chunks 정보 포함 시 거대해짐. 결과 JSON에 `_document` 원문은 저장 금지 (task_id와 document_path로 역참조).
- **evidence_refs_used 필드**: ABC arm에서만 의미 있음. solo/rag arm에는 None 또는 []. Measure analyzer(Task 07)가 arm별로 다른 필드 처리.

## Scope boundary

**Task 06에서 절대 수정 금지**:
- `experiments/orchestrator.py` (Task 05 영역) — import만 허용
- `experiments/schema.py` (Task 04 영역)
- `experiments/tools/` (Task 02, 03 영역) — import만 허용
- `experiments/tasks/` (Task 01 영역) — 로드만 허용
- `experiments/measure.py`, `experiments/system_prompt.py`, `experiments/config.py`
- 기존 `run_*` 함수 (모든 것)

**허용 범위**: `experiments/run_experiment.py`에만 상수 블록 + `run_longctx` 함수 + `_run_longctx_trial` + `_extract_answer` 헬퍼 + `EXPERIMENTS` 딕셔너리 1줄 추가.
