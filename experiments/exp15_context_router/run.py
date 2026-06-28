"""실험 15: Ephemeral Context Router vs Stuffing (A/B/C/D Test).

소형 LLM(gemma4:e4b) 환경에서 35KB 크기의 대용량 빌드 로그를 대상으로,
다양한 컨텍스트 라우팅 보완 전략(Stuffing, Router-Basic, ErrorBlocks-Only, Hybrid)의
입력 지연(Latency), JSON 안정성 및 정답률(Score)을 측정하여 비교합니다.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# gemento/experiments 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.context_tools import get_redis_client
from orchestrator import run_abc_chain
from config import MODEL_NAME

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# 1. 35KB 크기의 가상 Rust 빌드 에러 로그 생성 및 Redis 적재
def setup_redis_log() -> str:
    redis_key = "ctx:exp15_debug_log:stdout"
    r = get_redis_client()
    
    lines = []
    for i in range(1, 801):
        if i == 342:
            lines.append("error[E0432]: unresolved import `crate::router::SemanticRouter` in src/main.rs:342")
        elif i == 512:
            lines.append("warning: unused import: `std::collections::HashMap` in src/utils.py:12")
        elif i == 789:
            lines.append("error: aborting due to previous error; 1 warning emitted")
        else:
            lines.append(f"[INFO] 2026-06-28 10:15:{i:02d} - Building crate gemento v1.0.0 (step {i}/800)... success")
            
    log_content = "\n".join(lines)
    r.set(redis_key, log_content)
    print(f"  [Setup] 35KB mock compilation log uploaded to Redis key: {redis_key}")
    return redis_key


def main():
    print("=" * 80)
    print("실험 15: Ephemeral Context Router A/B/C/D Cross-Comparison")
    print("=" * 80)
    
    redis_key = setup_redis_log()
    r = get_redis_client()
    raw_log = r.get(redis_key)
    
    # 공통 문제 정의
    objective = "Find the exact file name, line number, and unresolved import module that caused the compilation failure."
    expected_answer = "src/main.rs, line 342, unresolved import `crate::router::SemanticRouter`"
    scoring_keywords = [["src/main.rs"], ["342"], ["SemanticRouter"]]
    
    # 채점 함수
    def score(ans) -> float:
        if not ans: return 0.0
        if isinstance(ans, dict):
            ans = json.dumps(ans, ensure_ascii=False)
        elif not isinstance(ans, str):
            ans = str(ans)
        matched = sum(1 for grp in scoring_keywords if all(t.lower() in ans.lower() for t in grp))
        return matched / len(scoring_keywords)


    results = {}

    # ── Arm A: Stuffing ──
    print("\n" + "-" * 50)
    print("[Arm A] Running Stuffing (Log insertion directly into prompt)...")
    print("-" * 50)
    prompt_stuffing = (
        "Here is the raw compilation output log:\n\n"
        f"```text\n{raw_log}\n```\n\n"
        "Find the file name, line number, and the module import error details."
    )
    start_time = time.time()
    tattoo_a, logs_a, ans_a = run_abc_chain(
        task_id="exp15_stuffing",
        objective=objective,
        prompt=prompt_stuffing,
        constraints=["에러가 발생한 파일과 라인을 정확히 기재하라", "unresolved import 모듈명을 적어라"],
        max_cycles=5,
        context_router=False,
        error_blocks=False,
    )
    duration_a = time.time() - start_time
    score_a = score(ans_a)
    results["stuffing"] = {
        "score": score_a,
        "duration": duration_a,
        "answer": ans_a,
        "cycles": len(logs_a),
    }

    # ── Arm B: Router-Basic ──
    print("\n" + "-" * 50)
    print("[Arm B] Running Router-Basic (Redis Handle + Tool use instructions)...")
    print("-" * 50)
    prompt_router = (
        "A compilation error occurred during build. The raw output is cached in Redis.\n"
        f"Available Context Handle: {redis_key}\n\n"
        "Please inspect the log and find the exact file name, line number, and unresolved import module error."
    )
    start_time = time.time()
    tattoo_b, logs_b, ans_b = run_abc_chain(
        task_id="exp15_router_basic",
        objective=objective,
        prompt=prompt_router,
        constraints=["에러가 발생한 파일과 라인을 정확히 기재하라", "unresolved import 모듈명을 적어라"],
        max_cycles=5,
        context_router=True,
        context_handles=[redis_key],
        error_blocks=False,
    )
    duration_b = time.time() - start_time
    score_b = score(ans_b)
    results["router_basic"] = {
        "score": score_b,
        "duration": duration_b,
        "answer": ans_b,
        "cycles": len(logs_b),
    }

    # ── Arm C: ErrorBlocks-Only ──
    print("\n" + "-" * 50)
    print("[Arm C] Running ErrorBlocks-Only (Pre-sliced snippets, No tools)...")
    print("-" * 50)
    start_time = time.time()
    tattoo_c, logs_c, ans_c = run_abc_chain(
        task_id="exp15_error_blocks_only",
        objective=objective,
        prompt=prompt_router,
        constraints=["에러가 발생한 파일과 라인을 정확히 기재하라", "unresolved import 모듈명을 적어라"],
        max_cycles=5,
        context_router=False,
        context_handles=[redis_key],
        error_blocks=True,
    )
    duration_c = time.time() - start_time
    score_c = score(ans_c)
    results["error_blocks_only"] = {
        "score": score_c,
        "duration": duration_c,
        "answer": ans_c,
        "cycles": len(logs_c),
    }

    # ── Arm D: Hybrid ──
    print("\n" + "-" * 50)
    print("[Arm D] Running Hybrid (Pre-sliced snippets + Tool use instructions)...")
    print("-" * 50)
    start_time = time.time()
    tattoo_d, logs_d, ans_d = run_abc_chain(
        task_id="exp15_hybrid",
        objective=objective,
        prompt=prompt_router,
        constraints=["에러가 발생한 파일과 라인을 정확히 기재하라", "unresolved import 모듈명을 적어라"],
        max_cycles=5,
        context_router=True,
        context_handles=[redis_key],
        error_blocks=True,
    )
    duration_d = time.time() - start_time
    score_d = score(ans_d)
    results["hybrid"] = {
        "score": score_d,
        "duration": duration_d,
        "answer": ans_d,
        "cycles": len(logs_d),
    }

    # ── 종합 리포트 출력 ──
    print("\n" + "=" * 80)
    print("종합 실험 결과 보고서 (A/B/C/D Cross-Comparison)")
    print("=" * 80)
    print(f"Arm A (Stuffing)          - Score: {score_a:.1%} | Duration: {duration_a:.1f}s | Answer: {ans_a}")
    print(f"Arm B (Router-Basic)      - Score: {score_b:.1%} | Duration: {duration_b:.1f}s | Answer: {ans_b}")
    print(f"Arm C (ErrorBlocks-Only)  - Score: {score_c:.1%} | Duration: {duration_c:.1f}s | Answer: {ans_c}")
    print(f"Arm D (Hybrid)            - Score: {score_d:.1%} | Duration: {duration_d:.1f}s | Answer: {ans_d}")
    print("-" * 80)
    
    # JSON 영속 저장
    out_data = {
        "experiment": "exp15_context_router_v2",
        "model": MODEL_NAME,
        "results": results
    }
    
    out_path = RESULTS_DIR / "exp15_ab_test_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)
    print(f"  → Comprehensive results saved: {out_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
