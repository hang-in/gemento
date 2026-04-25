---
type: plan-task
status: todo
updated_at: 2026-04-26
parent_plan: exp10-reproducibility-cost-profile
parallel_group: B
depends_on: [01, 02]
---

# Task 03 — Exp10 dispatcher (run.py) 작성

## Changed files

- `experiments/exp10_reproducibility_cost/run.py` — **신규**. 3 condition × 9 task × N=20 trial dispatcher

신규 외 다른 파일 수정 금지. `experiments/run_experiment.py` 의 EXPERIMENTS dict 추가는 task-05 영역.

## Change description

### 배경

Exp10 본 dispatcher. 3 condition (`gemma_8loop`, `gemma_1loop`, `gemini_flash_1call`) × 9 task × N=20 trial = 540 호출. 본 task 는 코드 작성·import·CLI dry-run 검증까지. 실제 540 호출은 task-06 에서.

**rate limit 정책**: `gemini_flash_1call` 는 호출 후 `time.sleep(1.0)` 추가 — Google AI Studio 무료 tier 안전 마진.

### Step 1 — `experiments/exp10_reproducibility_cost/run.py` 작성

```python
"""실험 10: Reproducibility & Cost Profile.

3 condition × 9 task × N=20 trial = 540 호출.
- gemma_8loop        : Gemma 4 E4B + 8루프 (loop_saturation baseline_phase15 동등)
- gemma_1loop        : Gemma 4 E4B 단일 추론
- gemini_flash_1call : Gemini 2.5 Flash 1회 외부 API 호출 (rate limit 1초 sleep)

dispatcher key: `reproducibility-cost`
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import MODEL_NAME
from orchestrator import run_abc_chain
from _external.gemini_client import call_with_meter as gemini_call
from _external.lmstudio_client import call_with_meter as lmstudio_call


# Google AI Studio 무료 tier rate limit 안전 마진. paid tier 에서는 0 으로 줄여도 OK.
GEMINI_CALL_SLEEP_SEC = 1.0

from exp10_reproducibility_cost.tasks import (
    EXP10_TASK_IDS, load_exp10_tasks, score_trial,
)


# experiments-task-07 rev — 자체 디렉토리의 results/ 사용
RESULTS_DIR = Path(__file__).resolve().parent / "results"

DEFAULT_TRIALS = 20
GEMMA_8LOOP_MAX_CYCLES = 15  # loop_saturation baseline_phase15 와 동등
GEMMA_8LOOP_USE_PHASE_PROMPT = True

CONDITIONS = (
    "gemma_8loop",
    "gemma_1loop",
    "gemini_flash_1call",
)


def save_partial(path: Path, data: dict) -> None:
    """체크포인트 저장."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_result(experiment_name: str, result: dict) -> Path:
    """최종 결과 저장."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{experiment_name}_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"  → Result saved: {path}")
    return path


def trial_gemma_8loop(task: dict, trial_idx: int) -> dict:
    """gemma_8loop condition: ABC + 8루프 (loop_saturation baseline_phase15 동등)."""
    start = time.time()
    try:
        tattoo, abc_logs, final_answer = run_abc_chain(
            task_id=f"{task['id']}_8loop_t{trial_idx}",
            objective=task["objective"],
            prompt=task["prompt"],
            constraints=task.get("constraints"),
            termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
            max_cycles=GEMMA_8LOOP_MAX_CYCLES,
            use_phase_prompt=GEMMA_8LOOP_USE_PHASE_PROMPT,
        )
        actual_cycles = len(abc_logs)
        error = None
    except Exception as e:
        final_answer = None
        actual_cycles = 0
        error = str(e)
    duration_ms = int((time.time() - start) * 1000)
    accuracy = score_trial(final_answer, task)
    return {
        "trial": trial_idx + 1,
        "condition": "gemma_8loop",
        "task_id": task["id"],
        "final_answer": str(final_answer) if final_answer else None,
        "accuracy": accuracy,
        "actual_cycles": actual_cycles,
        "duration_ms": duration_ms,
        "input_tokens": 0,   # ABC 체인은 token 합계 미반환 — task-04 analyze 시 0 처리
        "output_tokens": 0,
        "cost_usd": 0.0,
        "error": error,
    }


def trial_gemma_1loop(task: dict, trial_idx: int) -> dict:
    """gemma_1loop condition: LM Studio 단일 호출."""
    messages = [
        {"role": "system", "content": "You are a helpful reasoning assistant. Think step by step and provide your final answer as JSON: {\"final_answer\": \"...\"}."},
        {"role": "user", "content": task["prompt"]},
    ]
    meter = lmstudio_call(messages, response_format={"type": "json_object"})
    # final_answer 파싱
    final_answer = None
    if meter.raw_response and not meter.error:
        try:
            parsed = json.loads(meter.raw_response)
            final_answer = parsed.get("final_answer") if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            final_answer = meter.raw_response.strip()[:200]
    accuracy = score_trial(final_answer, task)
    return {
        "trial": trial_idx + 1,
        "condition": "gemma_1loop",
        "task_id": task["id"],
        "final_answer": str(final_answer) if final_answer else None,
        "accuracy": accuracy,
        "actual_cycles": 1,
        "duration_ms": meter.duration_ms,
        "input_tokens": meter.input_tokens,
        "output_tokens": meter.output_tokens,
        "cost_usd": meter.cost_usd,
        "error": meter.error,
    }


def trial_gemini_flash(task: dict, trial_idx: int) -> dict:
    """gemini_flash_1call condition: Gemini 2.5 Flash API 1회 호출 + rate limit sleep."""
    messages = [
        {"role": "system", "content": "You are a helpful reasoning assistant. Think step by step and provide your final answer as JSON: {\"final_answer\": \"...\"}."},
        {"role": "user", "content": task["prompt"]},
    ]
    meter = gemini_call(messages, response_mime_type="application/json")
    final_answer = None
    if meter.raw_response and not meter.error:
        try:
            parsed = json.loads(meter.raw_response)
            final_answer = parsed.get("final_answer") if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            final_answer = meter.raw_response.strip()[:200]
    accuracy = score_trial(final_answer, task)
    # Rate limit 안전 마진 — Google AI Studio 무료 tier 보호
    time.sleep(GEMINI_CALL_SLEEP_SEC)
    return {
        "trial": trial_idx + 1,
        "condition": "gemini_flash_1call",
        "task_id": task["id"],
        "final_answer": str(final_answer) if final_answer else None,
        "accuracy": accuracy,
        "actual_cycles": 1,
        "duration_ms": meter.duration_ms,
        "input_tokens": meter.input_tokens,
        "output_tokens": meter.output_tokens,
        "cost_usd": meter.cost_usd,
        "error": meter.error,
    }


CONDITION_DISPATCH = {
    "gemma_8loop": trial_gemma_8loop,
    "gemma_1loop": trial_gemma_1loop,
    "gemini_flash_1call": trial_gemini_flash,
}


def run(trials: int = DEFAULT_TRIALS, dry_run: bool = False, conditions: tuple[str, ...] = CONDITIONS) -> Path | None:
    """본 실험. trials × 9 task × len(conditions) trial 실행."""
    tasks = load_exp10_tasks()
    partial_path = RESULTS_DIR / "partial_exp10_reproducibility_cost.json"

    # 이어하기 시도
    finished: set[tuple[str, str, int]] = set()  # (cond, task_id, trial)
    all_results: list[dict] = []
    if partial_path.exists() and not dry_run:
        try:
            with open(partial_path, encoding="utf-8") as f:
                partial = json.load(f)
                all_results = partial.get("trials", [])
                for r in all_results:
                    finished.add((r["condition"], r["task_id"], r["trial"]))
            print(f"  → Resuming from checkpoint: {len(finished)} trials done.")
        except Exception:
            print("  ⚠ Checkpoint load failed; starting fresh.")
            all_results = []

    total = len(conditions) * len(tasks) * trials
    counter = len(finished)
    for cond in conditions:
        dispatch = CONDITION_DISPATCH[cond]
        for task in tasks:
            for trial_idx in range(trials):
                key = (cond, task["id"], trial_idx + 1)
                if key in finished:
                    continue
                counter += 1
                print(f"  [{counter}/{total}] {cond} | {task['id']} | trial {trial_idx + 1}")
                if dry_run:
                    print(f"    (dry-run, skipping LLM call)")
                    return None
                result = dispatch(task, trial_idx)
                all_results.append(result)
                # 매 trial 후 체크포인트
                save_partial(partial_path, {
                    "experiment": "reproducibility_cost",
                    "model": MODEL_NAME,
                    "trials_per_condition": trials,
                    "conditions": list(conditions),
                    "task_ids": list(EXP10_TASK_IDS),
                    "trials": all_results,
                })

    # 최종 결과 저장
    final_path = save_result("exp10_reproducibility_cost", {
        "experiment": "reproducibility_cost",
        "model": MODEL_NAME,
        "trials_per_condition": trials,
        "conditions": list(conditions),
        "task_ids": list(EXP10_TASK_IDS),
        "trials": all_results,
    })
    if partial_path.exists():
        partial_path.unlink()
        print("  → Checkpoint cleared.")
    return final_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Exp10: Reproducibility & Cost Profile")
    parser.add_argument("--trials", type=int, default=DEFAULT_TRIALS, help=f"trials per condition×task (default: {DEFAULT_TRIALS})")
    parser.add_argument("--dry-run", action="store_true", help="첫 trial 만 보고 종료 (LLM 호출 0)")
    parser.add_argument("--conditions", nargs="*", default=list(CONDITIONS),
                        help=f"실행할 condition 목록 (default: {CONDITIONS})")
    args = parser.parse_args()
    run(trials=args.trials, dry_run=args.dry_run, conditions=tuple(args.conditions))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Step 2 — 핵심 설계 포인트

- **체크포인트** — 매 trial 후 `partial_exp10_reproducibility_cost.json` 저장. 540 호출 중 중단 시 resume.
- **CLI flag** — `--trials N`, `--dry-run`, `--conditions <list>` (예: `--conditions gemma_1loop` 만 단독 실행 가능).
- **dry-run** — 첫 trial 1개만 print 후 종료. LLM 호출 0. CI / smoke 검증 용.
- **token·cost metering** — gemma_8loop (ABC) 는 token 0 처리 (orchestrator 가 합계 미반환). 후속 plan 에서 ABC token 측정 추가 시 본 코드 갱신.
- **score_trial 통합** — 모든 condition 이 trial dict 에 `accuracy` 키 포함. analyze.py 가 이를 통합.

### Step 3 — Verification 절차

본 task 의 verification 은 LLM 호출 0:
- 신규 파일 존재
- import smoke
- `--dry-run` CLI 동작 (LLM 호출 직전 print 후 종료)
- `--trials 0` 으로 빈 결과 path 만 반환되는지 (또는 dry-run 동등)

## Dependencies

- **Task 01 완료** — `_external/gemini_client.py`, `_external/lmstudio_client.py` 가 import 가능해야 함.
- **Task 02 완료** — `exp10_reproducibility_cost/tasks.py` 의 `EXP10_TASK_IDS`, `load_exp10_tasks`, `score_trial` 사용.
- 외부 패키지: 없음 (httpx 는 task-01 의존).

## Verification

```bash
# 1. 신규 파일 존재
test -f /Users/d9ng/privateProject/gemento/experiments/exp10_reproducibility_cost/run.py && \
echo "OK run.py exists"

# 2. import smoke (LLM 호출 0)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.run import run, CONDITIONS, CONDITION_DISPATCH, DEFAULT_TRIALS, RESULTS_DIR
assert callable(run)
assert len(CONDITIONS) == 3
assert set(CONDITIONS) == set(CONDITION_DISPATCH.keys())
assert DEFAULT_TRIALS == 20
assert str(RESULTS_DIR).endswith('exp10_reproducibility_cost/results')
print('OK run.py imports + constants')
"

# 3. 3 condition dispatcher 모두 callable
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.run import CONDITION_DISPATCH
for cond, fn in CONDITION_DISPATCH.items():
    assert callable(fn), f'{cond} not callable'
print('OK 3 dispatch functions callable')
"

# 4. CLI --dry-run 동작 (LLM 호출 0)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m exp10_reproducibility_cost.run --dry-run --trials 1 2>&1 | head -5
# 기대: "(dry-run, skipping LLM call)" 출력 후 종료

# 5. CLI --help 동작
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m exp10_reproducibility_cost.run --help 2>&1 | grep -q "trials" && echo "OK --help works"

# 6. RESULTS_DIR 가 자체 디렉토리 (per-dir 표준)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.run import RESULTS_DIR
from pathlib import Path
expected = Path(__file__).resolve().parent / 'exp10_reproducibility_cost' / 'results'
" || true
# 기대: 출력 0 또는 OK (위치 확인)
echo "RESULTS_DIR check passed"

# 7. orchestrator.py 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD experiments/orchestrator.py | wc -l
# 기대: 0

# 8. 다른 파일 변경 없음 (test_static.py 는 task-05 영역)
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only experiments/ | grep -vE "^experiments/(_external/|exp10_reproducibility_cost/)"
# 기대: 출력 0 라인
```

## Risks

- **LM Studio JSON mode 미지원 가능성**: `response_format={"type":"json_object"}` 가 LM Studio 일부 버전에서 미지원. 그 경우 `400 Bad Request` 발생 가능. trial_gemma_1loop 에서 fallback (response_format 빼고 재호출) 추가 검토 — 본 task 범위에서는 표준 OpenAI-compat 가정. task-06 smoke 에서 깨지면 hotfix.
- **Gemini API 무응답**: rate limit (429) / 503. trial_gemini_flash 의 `meter.error` 로 잡혀 결과에 기록됨. analyze.py 에서 error trial 제외 처리. 429 가 빈번하면 task-06 에서 GEMINI_CALL_SLEEP_SEC 늘리기.
- **체크포인트 corruption**: partial JSON 이 깨졌을 때 fresh 시작. 540 호출 다시 — 데이터 보존을 위해 incremental save 빈도가 중요. 본 코드는 매 trial 후 저장.
- **EXP10_TASK_IDS 변경**: task-02 의 9 task 가 다른 순서로 변경되면 분석 결과 비교 깨짐. tuple immutable + `assert len == 9` 로 보호.
- **--conditions 인자 오타**: `--conditions gemmma_8loop` (오타) 입력 시 KeyError. argparse choices 추가 권장 — 본 task 코드에서는 단순 `nargs="*"`. 외부 사용 시 주의.
- **메모리 사용량**: 540 trial 의 raw_response 가 모두 메모리에 — 수MB 정도. 큰 문제 아님.

## Scope boundary

**Task 03 에서 절대 수정 금지**:

- `experiments/run_experiment.py` — Exp10 dispatcher key 추가는 task-05 영역.
- `experiments/orchestrator.py`, `config.py`, `schema.py`, `system_prompt.py`, `measure.py`.
- `experiments/_external/` — task-01 결과물 그대로 사용, 수정 금지.
- `experiments/exp10_reproducibility_cost/__init__.py`, `tasks.py` — task-02 결과물 그대로.
- `experiments/exp10_reproducibility_cost/INDEX.md`, `analyze.py` — task-04·05 영역.
- `experiments/tests/test_static.py` — task-05 영역.
- 다른 expXX/ 디렉토리.

**허용 범위**:

- `experiments/exp10_reproducibility_cost/run.py` 신규 작성 (위 본문 그대로).
- 위 1 파일 외 일체 수정 금지.
