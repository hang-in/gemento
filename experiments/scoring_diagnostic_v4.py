"""v4 의미론적 채점 진단 스크립트.

Ollama Cloud의 gpt-oss:120b 모델을 판정관(Judge)으로 사용하여,
Exp13(Reducer) 및 Exp14(Search Tool) 결과에 대해 Scorer v3 키워드 매칭과
v4 의미론적 판정 점수를 비교 분석합니다.

사용:
    python -m scoring_diagnostic_v4 --limit-trials 1
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# gemento/experiments 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent))

from measure import score_answer_v3
from _external.llm_judge import judge_answer

_ROOT = Path(__file__).resolve().parent

TASKS_JSON = _ROOT / "tasks/taskset.json"
LONG_TASKS_JSON = _ROOT / "tasks/longctx_taskset.json"
EXP13_JSON = _ROOT / "exp13_reducer_role/results/exp13_reducer_abc.json"
EXP14_JSON = _ROOT / "exp14_search_tool/results/exp14_search_tool_abc.json"


def load_taskset() -> dict[str, dict]:
    """taskset.json 및 longctx_taskset.json을 로드하여 {task_id: task_entry} 맵 반환."""
    task_map = {}
    
    with open(TASKS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    for t in data["tasks"]:
        task_map[t["id"]] = t
        
    if LONG_TASKS_JSON.exists():
        with open(LONG_TASKS_JSON, encoding="utf-8") as f:
            long_data = json.load(f)
        for t in long_data["tasks"]:
            task_map[t["id"]] = t
            
    return task_map



def evaluate_file(
    file_path: Path,
    task_map: dict[str, dict],
    limit_trials: int | None = None,
) -> dict:
    """JSON 결과 파일을 읽고 v3 스코어와 v4 의미 판정 점수를 비교 연산한다."""
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return {}

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    # exp13/exp14 JSON 구조는 루트에 'trials' 키가 플랫하게 들어있음
    trials = data.get("trials", [])
    eval_records = []
    
    # task_id별 평가된 trial 횟수 제한을 위해 카운터 도입
    task_trial_counts = {}
    
    total_count = 0
    correct_v3_count = 0
    correct_v4_count = 0
    v3_score_sum = 0.0
    v4_score_sum = 0.0

    print(f"\nEvaluating: {file_path.name}")
    print(f"  {'task_id':<15} {'trial':>5} {'v3_score':>8} {'v4_score':>8} {'v4_correct':<10} {'reason':<40}")
    print("  " + "-" * 90)

    for t in trials:
        if t.get("error"):
            continue

        task_id = t["task_id"]
        
        # limit_trials 필터링
        task_trial_counts[task_id] = task_trial_counts.get(task_id, 0) + 1
        if limit_trials is not None and task_trial_counts[task_id] > limit_trials:
            continue

        task_entry = task_map.get(task_id)
        if not task_entry:
            continue
        
        prompt = task_entry.get("prompt", task_entry.get("question", ""))
        expected = task_entry["expected_answer"]
        final_ans = t.get("final_answer")
        if not final_ans:
            continue

        # v3 채점
        v3_score = score_answer_v3(str(final_ans), task_entry)
        
        # v4 의미 판정
        trial_num = t.get("trial_idx", t.get("trial", 0))
        print(f"  ↻ Judging {task_id} trial {trial_num}...", end="\r")
        verdict = judge_answer(
            question=prompt,
            expected_answer=expected,
            candidate_answer=str(final_ans),
            model="gpt-oss:120b",
            provider="ollama"
        )
        
        v4_score = verdict.get("score") if verdict.get("score") is not None else 0.0
        v4_correct = verdict.get("correct") if verdict.get("correct") is not None else False
        reason = verdict.get("reason", "")
        if verdict.get("error"):
            reason = f"ERROR: {verdict.get('error')}"

        # 집계
        total_count += 1
        v3_score_sum += v3_score
        v4_score_sum += v4_score
        if v3_score >= 0.8:  # 키워드 매칭 정답 임계
            correct_v3_count += 1
        if v4_correct:
            correct_v4_count += 1

        # 출력
        reason_trunc = reason[:50] + "..." if len(reason) > 50 else reason
        print(f"  {task_id:<15} {trial_num:>5} {v3_score:>8.2f} {v4_score:>8.1f} {str(v4_correct):<10} {reason_trunc:<40}")

        eval_records.append({
            "task_id": task_id,
            "trial": trial_num,
            "v3_score": v3_score,
            "v4_score": v4_score,
            "v4_correct": v4_correct,
            "reason": reason,
            "final_answer": final_ans,
        })

    # 요약 메트릭 계산
    mean_v3 = v3_score_sum / total_count if total_count else 0.0
    mean_v4 = v4_score_sum / total_count if total_count else 0.0
    acc_v3 = correct_v3_count / total_count if total_count else 0.0
    acc_v4 = correct_v4_count / total_count if total_count else 0.0

    print("  " + "-" * 90)
    print(f"  [Summary] Trials: {total_count}")
    print(f"  V3 Scorer  - Mean: {mean_v3:.3f}, Acc (>=0.8): {acc_v3:.1%}")
    print(f"  V4 Judge   - Mean Score: {mean_v4:.2f}/5.0, Semantic Acc: {acc_v4:.1%}")
    
    return {
        "file": file_path.name,
        "total_trials": total_count,
        "mean_v3": mean_v3,
        "acc_v3": acc_v3,
        "mean_v4": mean_v4,
        "acc_v4": acc_v4,
        "records": eval_records
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-trials", type=int, default=1, help="Limit number of trials per task to evaluate (default: 1)")
    args = parser.parse_args()

    task_map = load_taskset()
    
    print("=" * 100)
    print(f"Starting V4 LLM-as-judge Evaluation (Ollama Cloud gpt-oss:120b)")
    print(f"Limit trials per task: {args.limit_trials}")
    print("=" * 100)

    # 1. Exp13 Reducer 재채점
    r_stats = evaluate_file(EXP13_JSON, task_map, limit_trials=args.limit_trials)

    # 2. Exp14 Search Tool 재채점
    s_stats = evaluate_file(EXP14_JSON, task_map, limit_trials=args.limit_trials)

    # 종합 비교 출력
    print("\n" + "=" * 100)
    print("FINAL COMPARISON: KEYWORD V3 vs SEMANTIC V4")
    print("=" * 100)
    if r_stats:
        delta_r = (r_stats['acc_v4'] - r_stats['acc_v3']) * 100
        print(f"Exp13 (Reducer)   - V3 Acc: {r_stats['acc_v3']:.1%} | V4 Semantic Acc: {r_stats['acc_v4']:.1%} (Delta: {delta_r:+.1f}%p)")
    if s_stats:
        delta_s = (s_stats['acc_v4'] - s_stats['acc_v3']) * 100
        print(f"Exp14 (Search)    - V3 Acc: {s_stats['acc_v3']:.1%} | V4 Semantic Acc: {s_stats['acc_v4']:.1%} (Delta: {delta_s:+.1f}%p)")
    print("=" * 100)



if __name__ == "__main__":
    main()
