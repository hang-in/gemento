"""제멘토 실험 실행기.

Usage:
    python run_experiment.py baseline          # 실험 0: 기준선
    python run_experiment.py assertion-cap     # 실험 1: assertion 상한
    python run_experiment.py multiloop         # 실험 2: 다단계 루프
    python run_experiment.py error-propagation # 실험 3: 오류 전파
    python run_experiment.py tool-separation   # 실험 4: 도구 분리
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

# experiments/ 디렉토리를 기준으로 import
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    RESULTS_DIR, DEFAULT_REPEAT, MODEL_NAME,
    OLLAMA_GENERATE_URL, OLLAMA_TIMEOUT,
)
from schema import Tattoo, Phase, create_initial_tattoo
from orchestrator import run_chain, call_ollama, LoopLog


def load_tasks() -> list[dict]:
    """태스크셋을 로드한다."""
    tasks_path = Path(__file__).parent / "tasks" / "taskset.json"
    with open(tasks_path) as f:
        return json.load(f)["tasks"]


def save_result(experiment_name: str, result: dict) -> Path:
    """실험 결과를 저장한다."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{experiment_name}_{timestamp}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"  → Result saved: {path}")
    return path


# ── 실험 0: Baseline ──

def run_baseline():
    """문신 없이 단일 추론으로 답변 품질을 측정한다."""
    tasks = load_tasks()
    results = []

    for task in tasks:
        print(f"\n[Baseline] Task: {task['id']} — {task['objective']}")
        task_results = []

        for trial in range(DEFAULT_REPEAT):
            messages = [
                {"role": "system", "content": "You are a helpful reasoning assistant. Think step by step and provide your final answer."},
                {"role": "user", "content": task["prompt"]},
            ]
            start = time.time()
            try:
                raw = call_ollama(messages)
                error = None
            except Exception as e:
                raw = ""
                error = str(e)
            duration_ms = int((time.time() - start) * 1000)

            task_results.append({
                "trial": trial + 1,
                "response": raw,
                "duration_ms": duration_ms,
                "error": error,
            })
            print(f"  Trial {trial + 1}: {duration_ms}ms")

        results.append({
            "task_id": task["id"],
            "objective": task["objective"],
            "expected_answer": task.get("expected_answer"),
            "trials": task_results,
        })

    save_result("exp00_baseline", {"experiment": "baseline", "model": MODEL_NAME, "results": results})


# ── 실험 1: Assertion Cap ──

def run_assertion_cap():
    """assertion 수 변화에 따른 추론 품질 변곡점을 탐색한다."""
    tasks = load_tasks()
    cap_values = [2, 4, 6, 8, 10, 12]
    results = []

    for task in tasks:
        if not task.get("prefab_assertions"):
            continue
        print(f"\n[Assertion Cap] Task: {task['id']}")

        for cap in cap_values:
            assertions_to_use = task["prefab_assertions"][:cap]
            task_results = []

            for trial in range(DEFAULT_REPEAT):
                # 사전 제작된 assertion이 포함된 문신 생성
                tattoo = create_initial_tattoo(
                    task_id=f"{task['id']}_cap{cap}",
                    objective=task["objective"],
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

            results.append({
                "task_id": task["id"],
                "cap": cap,
                "trials": task_results,
            })

    save_result("exp01_assertion_cap", {"experiment": "assertion_cap", "model": MODEL_NAME, "results": results})


# ── 실험 2: Multi-loop Quality ──

def run_multiloop():
    """다단계 루프에서 품질이 누적되는지 검증한다."""
    tasks = load_tasks()
    loop_counts = [1, 2, 4, 8]
    results = []

    for task in tasks:
        print(f"\n[Multiloop] Task: {task['id']}")

        for max_loops in loop_counts:
            task_results = []

            for trial in range(DEFAULT_REPEAT):
                final_tattoo, logs = run_chain(
                    task_id=f"{task['id']}_loops{max_loops}_t{trial}",
                    objective=task["objective"],
                    constraints=task.get("constraints", []),
                    max_loops=max_loops,
                )

                # 최종 답변 추출
                final_answer = None
                if logs and logs[-1].parsed_response:
                    final_answer = logs[-1].parsed_response.get("final_answer")

                task_results.append({
                    "trial": trial + 1,
                    "max_loops": max_loops,
                    "actual_loops": len(logs),
                    "final_phase": final_tattoo.phase.value,
                    "final_confidence": final_tattoo.confidence,
                    "total_assertions": len(final_tattoo.active_assertions),
                    "final_answer": final_answer,
                    "loop_details": [
                        {
                            "loop": l.loop_index,
                            "phase": l.tattoo_out["state"]["phase"],
                            "assertions": len([
                                a for a in l.tattoo_out["state"]["assertions"]
                                if a["status"] == "active"
                            ]),
                            "confidence": l.tattoo_out["integrity"]["confidence"],
                            "duration_ms": l.duration_ms,
                            "error": l.error,
                        }
                        for l in logs
                    ],
                })
                print(f"  Loops={max_loops}, Trial {trial + 1}: "
                      f"phase={final_tattoo.phase.value}, "
                      f"conf={final_tattoo.confidence:.2f}, "
                      f"assertions={len(final_tattoo.active_assertions)}")

            results.append({
                "task_id": task["id"],
                "max_loops": max_loops,
                "expected_answer": task.get("expected_answer"),
                "trials": task_results,
            })

    save_result("exp02_multiloop", {"experiment": "multiloop", "model": MODEL_NAME, "results": results})


# ── 실험 3: Error Propagation ──

def run_error_propagation():
    """결함 주입 후 오류 전파를 측정한다."""
    tasks = load_tasks()
    results = []

    for task in tasks:
        print(f"\n[Error Propagation] Task: {task['id']}")
        fault_types = task.get("fault_injections", [])
        if not fault_types:
            continue

        for fault in fault_types:
            task_results = []
            for trial in range(DEFAULT_REPEAT):
                # 정상 체인 2루프 실행
                tattoo, pre_logs = run_chain(
                    task_id=f"{task['id']}_fault_{fault['type']}_t{trial}",
                    objective=task["objective"],
                    max_loops=fault.get("inject_at_loop", 2),
                )

                # 결함 주입
                if fault["type"] == "corrupt_content" and tattoo.active_assertions:
                    target = tattoo.active_assertions[0]
                    target.content = fault.get("corrupted_value", "CORRUPTED: incorrect fact")
                elif fault["type"] == "inflate_confidence" and tattoo.active_assertions:
                    target = tattoo.active_assertions[0]
                    target.confidence = 0.95
                elif fault["type"] == "contradiction":
                    tattoo.add_assertion(
                        content=fault.get("contradicting_assertion", "This contradicts everything."),
                        confidence=0.85,
                        source_loop=tattoo.loop_index,
                    )

                tattoo.finalize_integrity(parent_chain_hash=tattoo.chain_hash)

                # 결함 주입 후 추가 루프 실행
                post_logs: list[LoopLog] = []
                for i in range(tattoo.loop_index + 1, tattoo.loop_index + 7):
                    tattoo, log = __import__("orchestrator").run_loop(tattoo, i)
                    post_logs.append(log)
                    if tattoo.phase == Phase.CONVERGED:
                        break

                task_results.append({
                    "trial": trial + 1,
                    "fault_type": fault["type"],
                    "inject_at_loop": fault.get("inject_at_loop", 2),
                    "post_injection_loops": len(post_logs),
                    "final_confidence": tattoo.confidence,
                    "final_phase": tattoo.phase.value,
                    "confidence_trajectory": [
                        l.tattoo_out["integrity"]["confidence"] for l in post_logs
                    ],
                })

            results.append({
                "task_id": task["id"],
                "fault": fault,
                "trials": task_results,
            })

    save_result("exp03_error_propagation", {"experiment": "error_propagation", "model": MODEL_NAME, "results": results})


# ── 실험 4: Tool Loop Separation ──

def run_tool_separation():
    """도구 호출을 같은 루프/분리 루프에서 처리할 때의 품질 차이를 측정한다."""
    tasks = load_tasks()
    results = []

    for task in tasks:
        if not task.get("requires_tool"):
            continue
        print(f"\n[Tool Separation] Task: {task['id']}")

        # 이 실험은 실험 2 이후에 구현을 완성한다.
        # 현재는 구조만 잡아둔다.
        results.append({
            "task_id": task["id"],
            "status": "not_implemented_yet",
            "note": "실험 2 결과 이후 구현 예정",
        })

    save_result("exp04_tool_separation", {"experiment": "tool_separation", "model": MODEL_NAME, "results": results})


# ── CLI ──

EXPERIMENTS = {
    "baseline": run_baseline,
    "assertion-cap": run_assertion_cap,
    "multiloop": run_multiloop,
    "error-propagation": run_error_propagation,
    "tool-separation": run_tool_separation,
}


def main():
    parser = argparse.ArgumentParser(description="제멘토 실험 실행기")
    parser.add_argument("experiment", choices=EXPERIMENTS.keys(), help="실행할 실험")
    args = parser.parse_args()

    print(f"═══ 제멘토 실험: {args.experiment} ═══")
    print(f"모델: {MODEL_NAME}")
    print()

    EXPERIMENTS[args.experiment]()
    print("\n═══ 완료 ═══")


if __name__ == "__main__":
    main()
