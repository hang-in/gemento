"""Exp20 — 초대형 실로그 router 검증: test9ng 30일 저널(~29.3M tok) → boxie gemma4:e4b.

아키텍처: test9ng(d9ng-i3-laptop, 외부 노트북 서버)의 30일 journald(112MB / ~1.1M줄 /
~29.3M tok = 컨텍스트의 ~900배, n100 Exp19 의 25배)를 로컬 파일로 1회 pull → 로컬 Redis
SET → boxie(외부 GPU 서버)의 gemma4:e4b 가 router(grep_context)로 진단.

v19(n100 SSH-pull) 패턴 복제. 차이: ① SSH-pull 대신 로컬 파일 로드(거대 로그라 스냅샷),
② 2-task (단일 needle vs 집계 needle) 로 16KB 캡 약점을 실증.

두 task:
  A) gohttpserver.service 크래시루프 — 단일 needle, 16KB 캡 robust → size-invariance 재확인.
  B) SSH brute-force 집계(최다 IP 45.144.212.75 ×286, 총 5093건) — grep_context 가
     total_matches(전체 카운트)는 주지만 matches 텍스트는 16KB 로 잘림 → 시간순 매치
     앞부분만 보여 top-IP 집계가 막힌다. 실패해도 그 자체가 facet 도구 필요성의 실증 데이터.

스택: router + mandatory + retry (Exp16b/16c/19 검증). n=5. 검증 실행은 cloud/SSH(로컬 VRAM 무관).
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
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

BASE_URL = "http://127.0.0.1:11435"   # boxie ollama (tunnel)
MODEL = "gemma4:e4b"
NUM_CTX = 32768
N_TRIALS = 5
MAX_CYCLES = 5
MAX_RETRIES = 2
REDIS_KEY = "ctx:test9ng_journal_30d:stdout"

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULTS_DIR / "exp20_test9ng_megalog_gemma4_e4b.json"

# 로컬 메가로그 파일 (스크래치패드는 세션별 → 매 세션 재pull).
# 환경변수로 오버라이드 가능: EXP20_LOG_PATH.
_DEFAULT_LOG = (r"C:\Users\사자\AppData\Local\Temp\claude\D--privateProject-gemento"
                r"\e0e17d5d-1940-4371-902a-107212495699\scratchpad\test9ng_journal_30d.raw")
LOG_PATH = Path(os.environ.get("EXP20_LOG_PATH", _DEFAULT_LOG))

# ── 2 task 정의 (같은 메가로그를 공유) ────────────────────────────────────
TASKS = [
    {
        "id": "exp20a_crashloop",
        "label": "A:gohttpserver-crashloop (single needle, cap-robust)",
        "objective": ("This is the systemd journal from server test9ng (a long-running box). "
                      "A systemd service has been repeatedly crash-looping (start → fail → restart). "
                      "Identify which service unit is crash-looping (exact unit name) and report "
                      "recent failure evidence."),
        "constraints": ["크래시루프 중인 서비스의 정확한 unit 이름과 실패 근거를 기재하라"],
        "keywords": [["gohttpserver"], ["failed"]],
    },
    {
        "id": "exp20b_bruteforce",
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
        return " \n ".join(str(getattr(a, "content", "")) for a in tattoo.active_assertions if getattr(a, "content", None))
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


def _run_with_retry(task):
    prompt = (f"A diagnostic request for server test9ng. The full systemd journal (30-day window, "
              f"very large) is cached in Redis.\nContext Handle: {REDIS_KEY}\n\n" + task["objective"])
    attempts = 0
    last_ans = last_tt = None
    while attempts <= MAX_RETRIES:
        attempts += 1
        caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)
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


def _healthcheck():
    try:
        with httpx.Client(timeout=30) as c:
            names = [m.get("name") for m in c.get(BASE_URL.rstrip("/") + "/api/tags").json().get("models", [])]
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
        print(f"  [ABORT] megalog not found: {LOG_PATH}\n"
              f"    → re-pull: ssh test9ng.ddns.net \"journalctl --since '30 days ago' --no-pager\" > {LOG_PATH}")
        sys.exit(1)
    log = LOG_PATH.read_text(encoding="utf-8", errors="ignore")
    # fish init noise 필터 (test9ng 원격 셸이 fish)
    if "source:" in log or "openclaw.fish" in log:
        log = "\n".join(ln for ln in log.splitlines()
                        if not ln.startswith("source:") and "openclaw.fish" not in ln)
    if not log or len(log) < 100000:
        print(f"  [ABORT] megalog too small ({len(log)} chars) — pull likely truncated"); sys.exit(1)
    r.set(REDIS_KEY, log)
    print(f"  [Redis] spooled megalog: {len(log.encode('utf-8'))//(1024*1024)} MB, "
          f"{log.count(chr(10))+1} lines (~{len(log)//4} tok)")
    return log


def main():
    print("=" * 80)
    print(f"Exp20 megalog router validation — test9ng 30d journald → boxie {MODEL}")
    print("=" * 80)
    if not _healthcheck():
        sys.exit(1)

    log = _load_megalog_to_redis()
    low = log.lower()
    # sanity: needle 존재 확인 (검증 정직성)
    print(f"  [sanity] 'gohttpserver' lines={low.count('gohttpserver')}, "
          f"'45.144.212.75' lines={low.count('45.144.212.75')}, "
          f"'failed password' lines={low.count('failed password')}")

    results = {"experiment": "exp20_test9ng_megalog_realdata", "model": MODEL,
               "analyzer": "boxie(14.58.110.187) gemma4:e4b", "log_source": "test9ng journald (30d)",
               "approx_tokens": len(log) // 4, "n_lines": log.count("\n") + 1,
               "n_trials": N_TRIALS, "max_retries": MAX_RETRIES, "stack": "router+mandatory+retry",
               "tasks": {}}

    t0 = time.time()
    for task in TASKS:
        print(f"\n  ── Task {task['label']} ──")
        scores, attempts_list, answers = [], [], []
        for trial in range(1, N_TRIALS + 1):
            sc, att, ans = _run_with_retry(task)
            scores.append(sc); attempts_list.append(att)
            answers.append(ans if not isinstance(ans, str) else ans[:300])
            print(f"  [{task['id']} trial {trial}] score={sc:.0%} attempts={att} | ans={str(ans)[:120]}")
            results["tasks"][task["id"]] = {
                "label": task["label"], "keywords": task["keywords"],
                "scores": scores, "mean_score": round(statistics.mean(scores), 3),
                "mean_attempts": round(statistics.mean(attempts_list), 2), "answers": answers,
            }
            results["elapsed_sec"] = round(time.time() - t0, 1)
            with open(OUT_PATH, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"Exp20 megalog validation — log ~{results['approx_tokens']} tok / {results['n_lines']} lines")
    for tid, t in results["tasks"].items():
        print(f"  {tid}: mean_score={t['mean_score']:.0%} (mean_attempts={t['mean_attempts']})")
    print(f"  → {OUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
