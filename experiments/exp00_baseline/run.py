"""실험 0: Baseline.

가정: Gemma 4 E4B 단독 실행 (Tattoo·ABC 없음). 단순 prompt → response.

dispatcher key: `baseline`
원본 함수: experiments/run_experiment.py:run_baseline (line 56-94 in v1)
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# experiments/ 디렉토리를 import 경로에 추가 (공용 모듈 접근)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import DEFAULT_REPEAT, MODEL_NAME

# experiments-task-07 rev — 자체 디렉토리의 results/ 사용
RESULTS_DIR = Path(__file__).resolve().parent / "results"
from orchestrator import call_model


def load_tasks() -> list[dict]:
    """태스크셋을 로드한다. (run_experiment.py 와 동일 — 본 plan task-07 정리 대상)"""
    tasks_path = Path(__file__).resolve().parent.parent / "tasks" / "taskset.json"
    with open(tasks_path) as f:
        return json.load(f)["tasks"]


def save_result(experiment_name: str, result: dict) -> Path:
    """실험 결과를 저장한다. (run_experiment.py 와 동일 — 본 plan task-07 정리 대상)"""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = RESULTS_DIR / f"{experiment_name}_{timestamp}.json"
    with open(path, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"  → Result saved: {path}")
    return path


def run():
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
                raw = call_model(messages)
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
