"""Exp10 9 task subset + 채점 함수.

3 condition (gemma_8loop, gemma_1loop, gemini_flash_1call) 비교 실험에서
공통으로 사용할 task ID 와 채점 helper.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# experiments/ 를 import 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from measure import score_answer_v2  # 기존 채점 함수


EXP10_TASK_IDS = (
    # math (4)
    "math-01",
    "math-02",
    "math-03",
    "math-04",
    # synthesis (3) — synthesis-02 제외 (Exp05a final_answer=None 이력)
    "synthesis-01",
    "synthesis-03",
    "synthesis-04",
    # logic (2) — logic-01·02 제외 (JSON 파싱 불안정 이력)
    "logic-03",
    "logic-04",
)


def load_exp10_tasks() -> list[dict]:
    """Exp10 9 task 만 로드. order 보존."""
    tasks_path = Path(__file__).resolve().parent.parent / "tasks" / "taskset.json"
    with open(tasks_path, encoding="utf-8") as f:
        all_tasks = json.load(f)["tasks"]
    by_id = {t["id"]: t for t in all_tasks}
    missing = [tid for tid in EXP10_TASK_IDS if tid not in by_id]
    if missing:
        raise RuntimeError(f"Exp10 tasks missing in taskset.json: {missing}")
    return [by_id[tid] for tid in EXP10_TASK_IDS]


def score_trial(final_answer: str | None, task: dict) -> float:
    """단일 trial 채점. measure.score_answer_v2 로 위임."""
    return score_answer_v2(str(final_answer or ""), task)
