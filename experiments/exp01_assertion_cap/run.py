"""실험 1: Assertion 상한과 추론 품질.

assertion 수가 증가할 때 Gemma 4 E4B의 추론 품질이 어떻게 변하는지 측정한다.

dispatcher key: `assertion-cap`
원본 함수: experiments/run_experiment.py:run_assertion_cap (line 99 in v1)
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
from schema import Phase, create_initial_tattoo
from experiments.run_helpers import classify_trial_error, is_fatal_error


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
    """assertion 수 변화에 따른 추론 품질 변곡점을 탐색한다."""
    tasks = load_tasks()
    cap_values = [2, 4, 6, 8, 10, 12]
    results = []

    aborted = False
    for task in tasks:
        if aborted:
            break
        if not task.get("prefab_assertions"):
            continue
        print(f"\n[Assertion Cap] Task: {task['id']}")

        for cap in cap_values:
            if aborted:
                break
            assertions_to_use = task["prefab_assertions"][:cap]
            task_results = []

            for trial in range(DEFAULT_REPEAT):
                # 사전 제작된 assertion이 포함된 문신 생성
                # objective에 실제 문제(prompt)를 포함하여 모델이 맥락을 알 수 있게 한다
                tattoo = create_initial_tattoo(
                    task_id=f"{task['id']}_cap{cap}",
                    objective=f"{task['objective']}\n\nProblem:\n{task['prompt']}",
                    termination="답변이 완성되면 수렴",
                )
                tattoo.phase = Phase.SYNTHESIZE
                tattoo.next_directive = "주어진 assertions를 종합하여 최종 답을 작성하라."
                for i, a_text in enumerate(assertions_to_use):
                    tattoo.add_assertion(content=a_text, confidence=0.8, source_loop=i + 1)
                tattoo.finalize_integrity()

                from orchestrator import run_loop
                _, log = run_loop(tattoo, cap)
                task_results.append({
                    "trial": trial + 1,
                    "cap": cap,
                    "response": log.raw_response,
                    "parsed": log.parsed_response,
                    "duration_ms": log.duration_ms,
                    "error": log.error,
                })
                print(f"  Cap {cap}, Trial {trial + 1}: {log.duration_ms}ms")

                err_class = classify_trial_error(log.error)
                if is_fatal_error(err_class):
                    print(f"[ABORT] task={task['id']} cap={cap} trial={trial} fatal={err_class.value}: {str(log.error)[:200]}")
                    print("[ABORT] 부분 결과는 보존. 저장 직전 error 비율 검사 진행.")
                    aborted = True
                    break

            results.append({
                "task_id": task["id"],
                "cap": cap,
                "trials": task_results,
            })

        # 태스크 완료 후 중간 저장 (크래시 방어)
        save_result("exp01_assertion_cap_partial", {"experiment": "assertion_cap", "model": MODEL_NAME, "results": results})

    all_trials = [t for r in results for t in r.get("trials", [])]
    bad = sum(1 for t in all_trials if t.get("error") is not None)
    rate = bad / len(all_trials) if all_trials else 0.0
    if rate >= 0.30:
        print(f"[REJECT] error 비율 {rate:.1%} ≥ 30%. 저장 거부 + warning")
        print("[REJECT] 부분 결과는 메모리에 유지 — 사용자가 별도 처리 권고")
        raise SystemExit(1)

    save_result("exp01_assertion_cap", {"experiment": "assertion_cap", "model": MODEL_NAME, "results": results})
