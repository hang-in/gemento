"""Exp19 — 실데이터 router 검증: n100 journald → boxie gemma4:e4b 진단.

아키텍처: n100(내부 장기운영 서버, journald 9.8M줄)의 실 저널을 Windows 에서 SSH-pull →
로컬 Redis 스풀 → boxie(외부 GPU 서버)의 gemma4:e4b 가 router(grep_context)로 진단.
= "n100 로그를 GPU 서버로 분석" (소형 모델이 다른 박스의 대형 실 로그를 진단).

mock(이전 caddy fallback) 대체 — 진짜 대형 운영 로그(7일 ~34.5K줄 ~860K tok, stuffing 불가)
에서 실제 장애(certbot.service 반복 Failed to start)를 router 로 찾아낸다.

스택: router + mandatory + retry (큰 로그 1-needle 전사 영역, Exp16b 검증). n=5.
검증 실행은 cloud/SSH(로컬 VRAM 무관).
"""
from __future__ import annotations

import json
import statistics
import subprocess
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
N100_SSH_HOST = "n100"                 # ~/.ssh/config alias → 192.168.1.121:9207
JOURNAL_SINCE = "7 days ago"
REDIS_KEY = "ctx:n100_journald:stdout"

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULTS_DIR / "exp19_n100_journald_gemma4_e4b.json"

OBJECTIVE = ("This is the systemd journal from server n100 (a long-running internal box). "
             "A service has been repeatedly FAILING to start recently. "
             "Identify which service is failing (exact unit name) and report recent failure timestamps.")
KEYWORDS = [["certbot"], ["failed to start"]]   # 실제 needle: certbot.service 반복 실패


def pull_n100_journal() -> str:
    """n100 에서 journalctl(최근 윈도우)을 SSH-pull. stdout 만(fish init 에러는 stderr)."""
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", N100_SSH_HOST,
           f"journalctl --since '{JOURNAL_SINCE}' --no-pager"]
    print(f"  [SSH-pull] {' '.join(cmd)}")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          text=True, encoding="utf-8", errors="ignore", timeout=180)
    lines = [ln for ln in proc.stdout.splitlines()
             if ln and not ln.startswith("source:") and "openclaw.fish" not in ln]
    return "\n".join(lines)


def _synth(tattoo):
    try:
        return " \n ".join(str(getattr(a, "content", "")) for a in tattoo.active_assertions if getattr(a, "content", None))
    except Exception:
        return None


def _score(ans, tattoo) -> float:
    parts = []
    if ans:
        parts.append(ans if isinstance(ans, str) else json.dumps(ans, ensure_ascii=False))
    s = _synth(tattoo)
    if s:
        parts.append(s)
    if not parts:
        return 0.0
    low = " \n ".join(parts).lower()
    return sum(1 for g in KEYWORDS if all(t.lower() in low for t in g)) / len(KEYWORDS)


def _run_with_retry():
    prompt = (f"A failure occurred on server n100. The full systemd journal (recent window) is cached in Redis.\n"
              f"Context Handle: {REDIS_KEY}\n\n" + OBJECTIVE)
    attempts = 0
    last_ans = last_tt = None
    while attempts <= MAX_RETRIES:
        attempts += 1
        caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=NUM_CTX)
        tt, logs, ans = run_abc_chain(
            task_id="exp19", objective=OBJECTIVE, prompt=prompt,
            constraints=["실패한 서비스의 정확한 unit 이름과 최근 시각을 기재하라"],
            max_cycles=MAX_CYCLES, model_caller=caller,
            context_router=True, error_blocks=False, context_handles=[REDIS_KEY],
            mandatory_tool_prompt=True,
        )
        last_ans, last_tt = ans, tt
        if ans:
            break
    return _score(last_ans, last_tt), attempts, last_ans


def _healthcheck():
    try:
        with httpx.Client(timeout=30) as c:
            names = [m.get("name") for m in c.get(BASE_URL.rstrip("/") + "/api/tags").json().get("models", [])]
        if MODEL not in names:
            print(f"  [ABORT] {MODEL} missing {names}"); return False
        print(f"  [Healthcheck] boxie ollama OK {names}"); return True
    except Exception as e:
        print(f"  [ABORT] tunnel/ollama: {e}"); return False


def main():
    print("=" * 80)
    print(f"Exp19 real-data router validation — n100 journald → boxie {MODEL}")
    print("=" * 80)
    if not _healthcheck():
        sys.exit(1)

    # 1. n100 저널 pull + Redis 스풀 (1회, 재현 위해 스냅샷)
    r = get_redis_client()
    if r.exists(REDIS_KEY):
        log = r.get(REDIS_KEY)
        print(f"  [Redis] reuse existing snapshot: {len(log.encode('utf-8'))//1024} KB, {log.count(chr(10))+1} lines")
    else:
        log = pull_n100_journal()
        if not log or len(log) < 1000:
            print(f"  [ABORT] journal pull failed/empty ({len(log)} chars)"); sys.exit(1)
        r.set(REDIS_KEY, log)
        print(f"  [Redis] spooled n100 journal: {len(log.encode('utf-8'))//1024} KB, {log.count(chr(10))+1} lines (~{len(log)//4} tok)")
    # sanity: needle 존재 확인 (검증 정직성)
    print(f"  [sanity] 'Failed to start' lines={log.lower().count('failed to start')}, 'certbot' lines={log.lower().count('certbot')}")

    results = {"experiment": "exp19_n100_journald_realdata", "model": MODEL,
               "analyzer": "boxie(14.58.110.187) gemma4:e4b", "log_source": "n100 journald (7d)",
               "approx_tokens": len(log) // 4, "n_lines": log.count("\n") + 1,
               "n_trials": N_TRIALS, "max_retries": MAX_RETRIES, "stack": "router+mandatory+retry"}
    scores, attempts_list, answers = [], [], []
    t0 = time.time()
    for trial in range(1, N_TRIALS + 1):
        sc, att, ans = _run_with_retry()
        scores.append(sc); attempts_list.append(att)
        answers.append(ans if not isinstance(ans, str) else ans[:300])
        print(f"  [trial {trial}] score={sc:.0%} attempts={att} | ans={str(ans)[:120]}")
        results.update({"scores": scores, "mean_score": round(statistics.mean(scores), 3),
                        "mean_attempts": round(statistics.mean(attempts_list), 2), "answers": answers,
                        "elapsed_sec": round(time.time() - t0, 1)})
        with open(OUT_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"Exp19 n100 real-data validation — mean_score={results['mean_score']:.0%} "
          f"(n={N_TRIALS}, mean_attempts={results['mean_attempts']}, log ~{results['approx_tokens']} tok / {results['n_lines']} lines)")
    print(f"  → {OUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
