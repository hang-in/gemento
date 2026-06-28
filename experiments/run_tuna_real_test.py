"""실증 테스트: 로컬 tunaCtx 리포지토리 연동 디버깅 테스트.

tunaCtx 내부에서 고의로 발생시킨 unittest 에러 Traceback을
로컬 Redis에 스풀링하고, 제멘토의 Ephemeral Context Router(Hybrid 모드)를
이용하여 에이전트가 에러 원인(파일명, 메소드명, 예외 내용)을 성공적으로 디버깅하는지 검증합니다.
"""
from __future__ import annotations

import json
import os
import subprocess
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

TUNA_DIR = Path("d:/privateProject/tunaCtx")
PYTHON_EXE = Path("d:/privateProject/gemento/.venv/Scripts/python.exe")


def run_tuna_test_and_spool() -> str:
    """tunaCtx 내부의 실패하는 테스트를 가동하고 출력을 Redis에 스풀링합니다."""
    redis_key = "ctx:tuna_ctx_real:stdout"
    r = get_redis_client()
    
    # gemento venv의 python을 이용하여 tunaCtx 폴더에서 unittest 실행
    cmd = [str(PYTHON_EXE), "-m", "unittest", "tests/test_router_error.py"]
    print(f"  [Exec] Running: {' '.join(cmd)} in cwd: {TUNA_DIR}")
    
    proc = subprocess.run(
        cmd,
        cwd=TUNA_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    
    # unittest는 에러 발생 시 stderr로 traceback을 내뿜음
    raw_log = f"=== STDOUT ===\n{proc.stdout}\n\n=== STDERR ===\n{proc.stderr}"
    
    # Redis 적재
    r.set(redis_key, raw_log)
    print(f"  [Setup] Spooled {len(raw_log.encode('utf-8'))} bytes of unittest Traceback to Redis key: {redis_key}")
    return redis_key


def main():
    print("=" * 80)
    print("실증 테스트: tunaCtx 리포지토리 연동 에러 디버깅")
    print("=" * 80)
    
    redis_key = run_tuna_test_and_spool()
    
    # 목표 정의 및 검증용 채점 키워드
    objective = "Find the failing test file name, failing test method name, and the specific Python exception details."
    scoring_keywords = [
        ["test_router_error.py"], 
        ["test_routing_failure_none_config", "test_routing_failure_empty_endpoint"],
        ["AttributeError"]
    ]
    
    # 채점 함수
    def score(ans) -> float:
        if not ans: return 0.0
        if isinstance(ans, dict):
            ans = json.dumps(ans, ensure_ascii=False)
        elif not isinstance(ans, str):
            ans = str(ans)
        matched = sum(1 for grp in scoring_keywords if any(t.lower() in ans.lower() for t in grp))
        return matched / len(scoring_keywords)

    prompt = (
        "We executed the unittest in the tunaCtx repository, and a failure occurred.\n"
        f"The complete Traceback and execution log is cached in Redis key: {redis_key}\n\n"
        "Please use read_context or grep_context to inspect this log. "
        "Find the exact failing test file name, failing test method name, and the specific python exception detail."
    )

    print("\n[Start] Running Gemento Ephemeral Context Router (Hybrid Mode)...")
    start_time = time.time()
    tattoo, logs, ans = run_abc_chain(
        task_id="tuna_ctx_real_debug",
        objective=objective,
        prompt=prompt,
        constraints=["에러가 발생한 테스트 파일과 메소드를 정확히 명시하라", "발생한 Python 예외와 구체적인 메시지를 찾아라"],
        max_cycles=5,
        context_router=True,
        context_handles=[redis_key],
        error_blocks=True, # 하이브리드 슬라이싱 활성화
    )
    duration = time.time() - start_time
    score_val = score(ans)
    
    print("\n" + "=" * 80)
    print("실증 테스트 결과 요약")
    print("=" * 80)
    print(f"Model: {MODEL_NAME}")
    print(f"Status: {'SUCCESS' if score_val == 1.0 else 'FAILED'}")
    print(f"Score: {score_val:.1%}")
    print(f"Duration: {duration:.1f} seconds")
    print(f"Answer: {ans}")
    print("-" * 80)
    
    # 결과 저장
    out_data = {
        "experiment": "tuna_ctx_real_debug",
        "model": MODEL_NAME,
        "score": score_val,
        "duration_seconds": duration,
        "final_answer": ans,
        "cycles": len(logs),
        "tool_calls": [c.tool_calls for c in logs if c.tool_calls]
    }
    
    out_path = RESULTS_DIR / "tuna_ctx_real_test_result.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out_data, f, indent=2, ensure_ascii=False)
    print(f"  → Real-world validation results saved: {out_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
