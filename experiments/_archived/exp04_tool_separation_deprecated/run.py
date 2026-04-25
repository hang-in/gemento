"""실험 4 (deprecated): Tool Separation.

도구 호출을 같은 루프/분리 루프에서 처리할 때의 품질 차이 측정.
**상태**: 결과 파일 0개. 구현 미완성. abc-pipeline (exp04_abc_pipeline)으로 대체됨.

원본 함수: experiments/run_experiment.py:run_tool_separation (line 661 in v1)
격리: experiments-task-05 (2026-04-25). dispatcher 에서 제거됨.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from config import MODEL_NAME

# experiments-task-07 rev — 자체 디렉토리의 results/ 사용 (deprecated)
RESULTS_DIR = Path(__file__).resolve().parent / "results"


def load_tasks() -> list[dict]:
    tasks_path = Path(__file__).resolve().parent.parent.parent / "tasks" / "taskset.json"
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
