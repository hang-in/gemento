"""실험 3.5: Cross-Validation Gate.

B(비판자)가 A의 결함 assertion을 교차 검증으로 감지할 수 있는지 테스트한다.
게이트 실험: A-B-C 파이프라인 구축 전에 B 단독 능력을 확인.

dispatcher key: `cross-validation`
원본 함수: experiments/run_experiment.py:run_cross_validation (line 306 in v1)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DEFAULT_REPEAT, MODEL_NAME

# experiments-task-07 rev — 자체 디렉토리의 results/ 사용
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def load_tasks() -> list[dict]:
    tasks_path = Path(__file__).resolve().parent.parent / "tasks" / "taskset.json"
    with open(tasks_path) as f:
        return json.load(f)["tasks"]


def save_result(experiment_name: str, result: dict) -> Path:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{experiment_name}_{timestamp}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"  → Result saved: {path}")
    return path


def run():
    """B(비판자)가 A의 결함 assertion을 교차 검증으로 감지할 수 있는지 테스트한다.

    게이트 실험: A-B-C 파이프라인 구축 전에 B 단독 능력을 확인.
    """
    from system_prompt import build_critic_prompt
    from orchestrator import call_ollama, extract_json_from_response
    from experiments.run_helpers import classify_trial_error, is_fatal_error

    tasks = load_tasks()
    skip_tasks = {"logic-01", "logic-02"}
    results = []

    aborted = False
    for task in tasks:
        if aborted:
            break
        if task["id"] in skip_tasks:
            print(f"\n[Cross-Validation] Task: {task['id']} — SKIPPED")
            continue
        if not task.get("fault_injections"):
            continue
        if not task.get("prefab_assertions"):
            continue

        print(f"\n[Cross-Validation] Task: {task['id']}")

        for fault in task["fault_injections"]:
            if aborted:
                break
            # prefab assertion 목록에서 결함 주입
            clean_assertions = []
            for i, a_text in enumerate(task["prefab_assertions"][:8]):
                clean_assertions.append({
                    "id": f"a{i+1:02d}",
                    "content": a_text,
                    "confidence": 0.8,
                })

            # 결함 주입할 대상 assertion 결정
            corrupted_assertions = [dict(a) for a in clean_assertions]
            corrupted_id = None

            if fault["type"] == "corrupt_content":
                # 첫 번째 관련 assertion을 오염
                target_idx = min(2, len(corrupted_assertions) - 1)
                corrupted_id = corrupted_assertions[target_idx]["id"]
                corrupted_assertions[target_idx]["content"] = fault["corrupted_value"]
            elif fault["type"] == "inflate_confidence":
                target_idx = 0
                corrupted_id = corrupted_assertions[target_idx]["id"]
                corrupted_assertions[target_idx]["confidence"] = 0.99
            elif fault["type"] == "contradiction":
                corrupted_id = "a_injected"
                corrupted_assertions.append({
                    "id": corrupted_id,
                    "content": fault["contradicting_assertion"],
                    "confidence": 0.85,
                })

            task_results = []
            for trial in range(DEFAULT_REPEAT):
                print(f"  Fault={fault['type']}, Trial {trial + 1}: ", end="", flush=True)

                # B(비판자)에게 오염된 assertions 전달
                messages = build_critic_prompt(
                    problem=task["prompt"],
                    assertions=corrupted_assertions,
                )

                start = time.time()
                error = None
                parsed = None
                raw = ""
                detected = False

                for attempt in range(2):
                    try:
                        raw = call_ollama(messages)
                        parsed = extract_json_from_response(raw)
                    except Exception as e:
                        raw = ""
                        error = str(e)
                    if parsed:
                        error = None
                        break
                    if attempt == 0:
                        print("↻ ", end="", flush=True)

                duration_ms = int((time.time() - start) * 1000)

                # 감지 여부 판정
                if parsed and "judgments" in parsed:
                    for j in parsed["judgments"]:
                        if j.get("assertion_id") == corrupted_id:
                            if j.get("status") in ("suspect", "invalid"):
                                detected = True
                                break

                status_str = "✓ DETECTED" if detected else "✗ missed"
                print(f"{duration_ms}ms — {status_str}")

                task_results.append({
                    "trial": trial + 1,
                    "fault_type": fault["type"],
                    "corrupted_id": corrupted_id,
                    "detected": detected,
                    "judgments": parsed.get("judgments") if parsed else None,
                    "raw_response": raw[:500],
                    "duration_ms": duration_ms,
                    "error": error,
                })

                err_class = classify_trial_error(error)
                if is_fatal_error(err_class):
                    print(f"[ABORT] task={task['id']} fault={fault['type']} trial={trial} fatal={err_class.value}: {str(error)[:200]}")
                    print("[ABORT] 부분 결과는 보존. 저장 직전 error 비율 검사 진행.")
                    aborted = True
                    break

            results.append({
                "task_id": task["id"],
                "fault": fault,
                "corrupted_id": corrupted_id,
                "trials": task_results,
            })

    # 요약 출력
    total = sum(len(r["trials"]) for r in results)
    detected_count = sum(
        1 for r in results for t in r["trials"] if t["detected"]
    )
    print(f"\n{'═' * 50}")
    print(f"  교차 검증 감지율: {detected_count}/{total} = {detected_count/total:.1%}" if total else "  No data")
    print(f"{'═' * 50}")

    all_trials = [t for r in results for t in r.get("trials", [])]
    bad = sum(1 for t in all_trials if t.get("error") is not None)
    rate = bad / len(all_trials) if all_trials else 0.0
    if rate >= 0.30:
        print(f"[REJECT] error 비율 {rate:.1%} ≥ 30%. 저장 거부 + warning")
        print("[REJECT] 부분 결과는 메모리에 유지 — 사용자가 별도 처리 권고")
        raise SystemExit(1)

    save_result("exp035_cross_validation", {
        "experiment": "cross_validation",
        "model": MODEL_NAME,
        "results": results,
    })
