"""Exp21 — Facet 도구 A/B: grep-only vs grep+facet, megalog 2-task × 2 arm × n=5.

두 arm 의 유일한 차이는 aggregate_context 도구(FACET_TOOL_SCHEMAS/FUNCTIONS)
주입 여부. 1차 지표 = non-null ans rate(finalization), 2차 = keyword score.

run_v20_megalog.py 패턴 복제 + arm 차원 추가.
차이: ① ARMS 루프(2 arm × 2 task × n=5 = 20 체인),
      ② max_cycles=8 (진단상 5→8, 양 arm 에 finalization 기회 부여),
      ③ non_null_rate 1차 지표 추적,
      ④ grep_facet arm 에서 aggregate_context 호출 수(facet_calls) 캡처.

실행 가이드 (드라이버 주석):
  - boxie 원격 → 에이전트 직접 실행 가능.
  - `python -u run_v21_facet_ab.py`  (stdout block-buffer 회피)
  - 순서: arm × task × n=5 = 4 cell × 5 = 20 chain (각 ≤3 attempt).
    megalog grep ~2-3초/호출 → cell 당 수 분.
  - 진척: results/exp21_facet_ab_gemma4_e4b.json 의 arms.*.* non_null_rate 확인.
  - 환경변수 EXP20_LOG_PATH 로 megalog 파일 경로 오버라이드 가능.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from tools.context_tools import get_redis_client
from tools import FACET_TOOL_SCHEMAS, FACET_TOOL_FUNCTIONS
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

BASE_URL = "http://127.0.0.1:11435"   # boxie ollama (tunnel)
MODEL = "gemma4:e4b"
NUM_CTX = 32768
N_TRIALS = 5
MAX_CYCLES = 8
MAX_RETRIES = 2
REDIS_KEY = "ctx:test9ng_journal_30d:stdout"

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULTS_DIR / "exp21_facet_ab_gemma4_e4b.json"

# 로컬 메가로그 파일 (스크래치패드는 세션별 → 매 세션 재pull).
# 환경변수로 오버라이드 가능: EXP20_LOG_PATH.
_DEFAULT_LOG = (r"C:\Users\사자\AppData\Local\Temp\claude\D--privateProject-gemento"
                r"\e0e17d5d-1940-4371-902a-107212495699\scratchpad\test9ng_journal_30d.raw")
LOG_PATH = Path(os.environ.get("EXP20_LOG_PATH", _DEFAULT_LOG))

# ── arm 정의 (facet 주입 여부만 다름) ────────────────────────────────────────
ARMS = [
    {"id": "grep_only",  "extra_schemas": None,               "extra_fns": None},
    {"id": "grep_facet", "extra_schemas": FACET_TOOL_SCHEMAS,  "extra_fns": FACET_TOOL_FUNCTIONS},
]

# ── 2 task 정의 (run_v20 TASKS 와 동일, id 만 exp21a_*/exp21b_*) ─────────────
TASKS = [
    {
        "id": "exp21a_crashloop",
        "label": "A:gohttpserver-crashloop (single needle, cap-robust)",
        "objective": ("This is the systemd journal from server test9ng (a long-running box). "
                      "A systemd service has been repeatedly crash-looping (start → fail → restart). "
                      "Identify which service unit is crash-looping (exact unit name) and report "
                      "recent failure evidence."),
        "constraints": ["크래시루프 중인 서비스의 정확한 unit 이름과 실패 근거를 기재하라"],
        "keywords": [["gohttpserver"], ["failed"]],
    },
    {
        "id": "exp21b_bruteforce",
        "label": "B:ssh-bruteforce-aggregate (high-match-volume, cap-stress)",
        "objective": ("This is the systemd journal from server test9ng. The SSH daemon has been "
                      "hit by a brute-force attack with thousands of failed login attempts. "
                      "Identify the single source IP address responsible for the MOST failed "
                      "attempts, and report how many attempts came from it."),
        "constraints": ["가장 많은 실패 로그인을 시도한 단일 source IP 주소와 그 횟수를 기재하라"],
        "keywords": [["45.144.212.75"]],   # 최다 brute-force IP (×286 / 총 5093건)
    },
]


def _synth(tattoo):
    try:
        return " \n ".join(
            str(getattr(a, "content", ""))
            for a in tattoo.active_assertions
            if getattr(a, "content", None)
        )
    except Exception:
        return None


def _score(ans, tattoo, keywords) -> float:
    parts = []
    if ans:
        parts.append(ans if isinstance(ans, str) else json.dumps(ans, ensure_ascii=False))
    s = _synth(tattoo)
    if s:
        parts.append(s)
    if not parts:
        return 0.0
    low = " \n ".join(parts).lower()
    return sum(1 for g in keywords if all(t.lower() in low for t in g)) / len(keywords)


def _run_with_retry(task: dict, arm: dict, facet_counter: list) -> tuple:
    """task 를 주어진 arm 으로 실행. facet_counter[0] 에 aggregate_context 호출 수 누적.

    facet_calls 캡처 방법:
      grep_facet arm 에서 extra_fns 의 aggregate_context 를 카운팅 래퍼로 교체.
      래퍼는 호출마다 facet_counter[0] += 1 후 원본 함수에 위임.
      카운터는 동일 task 의 모든 trial × retry 에 걸쳐 누적된다.
    """
    prompt = (
        f"A diagnostic request for server test9ng. The full systemd journal (30-day window, "
        f"very large) is cached in Redis.\nContext Handle: {REDIS_KEY}\n\n"
        + task["objective"]
    )
    attempts = 0
    last_ans = last_tt = None

    # grep_facet arm: aggregate_context 를 카운팅 래퍼로 교체
    extra_fns = arm["extra_fns"]
    if arm["id"] == "grep_facet" and extra_fns is not None:
        orig_agg = extra_fns.get("aggregate_context")
        if orig_agg is not None:
            def _counting_agg(*a, _orig=orig_agg, **kw):
                facet_counter[0] += 1
                return _orig(*a, **kw)
            extra_fns = {**extra_fns, "aggregate_context": _counting_agg}

    while attempts <= MAX_RETRIES:
        attempts += 1
        caller = make_ollama_native_caller(
            BASE_URL, MODEL, num_ctx=NUM_CTX,
            extra_tool_schemas=arm["extra_schemas"],
            extra_tool_fns=extra_fns,
        )
        tt, logs, ans = run_abc_chain(
            task_id=task["id"], objective=task["objective"], prompt=prompt,
            constraints=task["constraints"],
            max_cycles=MAX_CYCLES, model_caller=caller,
            context_router=True, error_blocks=False, context_handles=[REDIS_KEY],
            mandatory_tool_prompt=True,
        )
        last_ans, last_tt = ans, tt
        if ans:
            break
    return _score(last_ans, last_tt, task["keywords"]), attempts, last_ans


def _healthcheck() -> bool:
    try:
        with httpx.Client(timeout=30) as c:
            names = [
                m.get("name")
                for m in c.get(BASE_URL.rstrip("/") + "/api/tags").json().get("models", [])
            ]
        if MODEL not in names:
            print(f"  [ABORT] {MODEL} missing {names}"); return False
        print(f"  [Healthcheck] boxie ollama OK {names}"); return True
    except Exception as e:
        print(f"  [ABORT] tunnel/ollama: {e}"); return False


def _load_megalog_to_redis() -> str:
    """로컬 메가로그 파일 → Redis SET (1회 스냅샷, 재현 위해 reuse)."""
    r = get_redis_client()
    if r.exists(REDIS_KEY):
        log = r.get(REDIS_KEY)
        print(f"  [Redis] reuse existing snapshot: {len(log.encode('utf-8'))//(1024*1024)} MB, "
              f"{log.count(chr(10))+1} lines")
        return log
    if not LOG_PATH.exists():
        print(
            f"  [ABORT] megalog not found: {LOG_PATH}\n"
            f"    → re-pull: ssh test9ng.ddns.net \"journalctl --since '30 days ago' --no-pager\""
            f" > {LOG_PATH}"
        )
        sys.exit(1)
    log = LOG_PATH.read_text(encoding="utf-8", errors="ignore")
    # fish init noise 필터 (test9ng 원격 셸이 fish)
    if "source:" in log or "openclaw.fish" in log:
        log = "\n".join(
            ln for ln in log.splitlines()
            if not ln.startswith("source:") and "openclaw.fish" not in ln
        )
    if not log or len(log) < 100000:
        print(f"  [ABORT] megalog too small ({len(log)} chars) — pull likely truncated")
        sys.exit(1)
    r.set(REDIS_KEY, log)
    print(f"  [Redis] spooled megalog: {len(log.encode('utf-8'))//(1024*1024)} MB, "
          f"{log.count(chr(10))+1} lines (~{len(log)//4} tok)")
    return log


def main():
    print("=" * 80)
    print(
        f"Exp21 facet A/B — test9ng 30d journald → boxie {MODEL} | "
        f"n={N_TRIALS} per arm×task, max_cycles={MAX_CYCLES}"
    )
    print("  arms: grep_only vs grep_facet | 1차 지표: non-null ans rate")
    print("=" * 80)
    if not _healthcheck():
        sys.exit(1)

    log = _load_megalog_to_redis()
    low = log.lower()
    print(f"  [sanity] 'gohttpserver' lines={low.count('gohttpserver')}, "
          f"'45.144.212.75' lines={low.count('45.144.212.75')}, "
          f"'failed password' lines={low.count('failed password')}")

    results = {
        "experiment": "exp21_facet_ab",
        "model": MODEL,
        "approx_tokens": len(log) // 4,
        "n_lines": log.count("\n") + 1,
        "n_trials": N_TRIALS,
        "max_cycles": MAX_CYCLES,
        "max_retries": MAX_RETRIES,
        "arms": {},
    }

    t0 = time.time()
    for arm in ARMS:
        arm_id = arm["id"]
        results["arms"][arm_id] = {}
        facet_total = [0]   # arm 전체 aggregate_context 총 호출 수 (grep_facet 용)

        for task in TASKS:
            tid = task["id"]
            print(f"\n  ── Arm={arm_id}  Task {task['label']} ──")
            scores, attempts_list, answers = [], [], []
            task_facet = [0]    # 이 arm×task 셀의 aggregate_context 호출 수

            for trial in range(1, N_TRIALS + 1):
                sc, att, ans = _run_with_retry(task, arm, task_facet)
                scores.append(sc)
                attempts_list.append(att)
                answers.append(ans if not isinstance(ans, str) else ans[:300])

                non_null = sum(1 for a in answers if a is not None)
                print(f"  [{arm_id}|{tid} trial {trial}] "
                      f"score={sc:.0%} attempts={att} "
                      f"non_null={non_null}/{trial}"
                      + (f" facet_calls={task_facet[0]}" if arm_id == "grep_facet" else "")
                      + f" | ans={str(ans)[:120]}")

                # trial 마다 flush (중단 내성)
                cell: dict = {
                    "non_null_rate": round(non_null / trial, 3),
                    "mean_score": round(statistics.mean(scores), 3),
                    "mean_attempts": round(statistics.mean(attempts_list), 2),
                    "answers": answers[:],
                }
                if arm_id == "grep_facet":
                    cell["facet_calls"] = task_facet[0]   # 누적 호출 수 (per task)
                results["arms"][arm_id][tid] = cell
                results["elapsed_sec"] = round(time.time() - t0, 1)
                with open(OUT_PATH, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)

            facet_total[0] += task_facet[0]

        # arm 레벨 total facet_calls (grep_facet 만, 양 task 합산)
        if arm_id == "grep_facet":
            results["arms"][arm_id]["facet_calls"] = facet_total[0]
            with open(OUT_PATH, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"Exp21 facet A/B done — log ~{results['approx_tokens']} tok / {results['n_lines']} lines")
    for arm_id, arm_data in results["arms"].items():
        for tid, cell in arm_data.items():
            if not isinstance(cell, dict):
                continue
            facet_info = (f" facet_calls={cell.get('facet_calls','?')}"
                          if arm_id == "grep_facet" else "")
            print(f"  {arm_id}|{tid}: non_null_rate={cell.get('non_null_rate','?')} "
                  f"mean_score={cell.get('mean_score','?')}{facet_info}")
    if "grep_facet" in results["arms"]:
        total_fc = results["arms"]["grep_facet"].get("facet_calls", "?")
        print(f"  grep_facet total facet_calls (both tasks): {total_fc}")
    print(f"  → {OUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
