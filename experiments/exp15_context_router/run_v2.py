"""Exp15 v2 — Context Router Stress Test (canonical gemma4:e4b via SSH tunnel).

Full-factorial: 5 task × 4 arm × num_ctx{4096,32768} × n=5 trial = 200 ABC chains.

판별 논리:
- pytrace(작은 로그): 4K·32K 모두 stuffing 정상 → router 무이점이 정상 (통제).
- rust_35k: 4K stuffing 실패 / 32K stuffing 회복 → 원본 "router 우위" = num_ctx artifact 증거.
- overflow_60k: 양 ctx 모두 stuffing 실패 / router 성공 → 부하>용량 영역에서 router 진짜 유효 (H15 좁은 참).

GEMENTO_API_BASE_URL 불필요 — native caller 가 직접 터널 base_url 로 /api/chat 호출.
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx

from tools.context_tools import get_redis_client
from orchestrator import run_abc_chain
from native_ollama_caller import make_ollama_native_caller

BASE_URL = "http://127.0.0.1:11435"   # SSH 터널 → 지인 서버 ollama
MODEL = sys.argv[1] if len(sys.argv) > 1 else "gemma4:e4b"   # 인자로 모델 지정 (e2b 재실행)
CTX_LEVELS = [4096, 32768]
N_TRIALS = 5
MAX_CYCLES = 5
ARMS = ["stuffing", "router_basic", "error_blocks_only", "hybrid"]

_DIR = Path(__file__).resolve().parent
RESULTS_DIR = _DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = RESULTS_DIR / f"exp15_v2_stress_{MODEL.replace(':', '_').replace('-', '_')}.json"


# ── 타스크셋 생성 (합성 로그, 재현 가능) ──────────────────────────────────────

def _build_logs() -> dict:
    """5종 로그를 생성. 반환: {task_id: {lines, objective, keywords, note}}."""
    tasks = {}

    # 1. rust_35k — 1-needle, ~11K tok (4K 초과, 32K fit)
    lines = []
    for i in range(1, 801):
        if i == 342:
            lines.append("error[E0432]: unresolved import `crate::router::SemanticRouter` in src/main.rs:342")
        elif i == 512:
            lines.append("warning: unused import `std::collections::HashMap` in src/utils.rs:12")
        else:
            lines.append(f"[INFO] 2026-06-28 10:15:{i % 60:02d} - Building crate gemento v1.0.0 (step {i}/800)... ok")
    tasks["rust_35k"] = dict(
        lines=lines,
        objective="Find the exact file name, line number, and the unresolved import module that caused the Rust compilation failure.",
        keywords=[["src/main.rs"], ["342"], ["SemanticRouter"]],
        note="~11K tok: exceeds 4096, fits 32768. artifact-판별 핵심.",
    )

    # 2. pytrace — small (~1K tok), fits both → 통제 (stuffing 정상이어야)
    lines = [
        "[INFO] starting payment worker pid=4412",
        "[INFO] received POST /charge body_len=58",
        "Traceback (most recent call last):",
        '  File "app/server.py", line 210, in handle_request',
        "    result = process_payment(req)",
        '  File "app/payment.py", line 88, in process_payment',
        '    amount = payload["amount"]',
        "KeyError: 'amount'",
        "[ERROR] worker 4412 failed to handle request, returning 500",
    ]
    tasks["pytrace"] = dict(
        lines=lines,
        objective="Find the file and line of the root cause, and the exact Python exception type and missing key.",
        keywords=[["payment.py"], ["88"], ["KeyError"], ["amount"]],
        note="~1K tok: fits both ctx. 통제군 — stuffing 정상 기대.",
    )

    # 3. caddy_5xx — ~9K tok, find offending IP + path among 500s
    lines = []
    for i in range(1, 601):
        if i in (220, 437):
            lines.append('10.0.0.7 - - [28/Jun/2026:14:52:20 +0900] "GET /api/v2/payment/checkout HTTP/1.1" 500 512')
        else:
            ip = f"10.0.{i % 5}.{i % 50}"
            lines.append(f'{ip} - - [28/Jun/2026:14:5{i % 6}:{i % 60:02d} +0900] "GET /health HTTP/1.1" 200 12')
    tasks["caddy_5xx"] = dict(
        lines=lines,
        objective="Find the client IP, the request URL path, and the HTTP status code of the failing (5xx) requests in this Caddy access log.",
        keywords=[["10.0.0.7"], ["/api/v2/payment/checkout"], ["500"]],
        note="~9K tok. n100 caddy 시나리오 재현 (실로그 아님, 합성).",
    )

    # 4. multihop — needle = 2 correlated lines (early config + late error)
    lines = []
    for i in range(1, 701):
        if i == 95:
            lines.append("[INFO] config loaded: db_pool_size=0 (overridden by env DB_POOL)")
        elif i == 642:
            lines.append("ERROR: connection pool exhausted: requested 1 but pool size is 0 at internal/db/conn.go:88")
        else:
            lines.append(f"[INFO] 2026-06-28 svc=api req={i} latency_ms={(i*7) % 40} ok")
    tasks["multihop"] = dict(
        lines=lines,
        objective="Explain the ROOT CAUSE of the pool exhaustion error: which config value caused it, and at which file:line the error surfaced. Correlate the config line with the error line.",
        keywords=[["db_pool"], ["conn.go"], ["88"]],
        note="~9K tok. 2-hop 상관 필요 (config@95 + error@642).",
    )

    # 5. overflow_60k — needle in ~65K tok log (exceeds even 32768)
    lines = []
    for i in range(1, 5001):
        if i == 2600:
            lines.append("thread 'auth-worker' panicked: ExpiredSignature at src/auth/jwt.rs:1873")
        else:
            lines.append(f"[INFO] 2026-06-28 auth heartbeat seq={i} session_active=true ttl={(i*13) % 3600}s ok")
    tasks["overflow_60k"] = dict(
        lines=lines,
        objective="Find the exact file, line number, and panic reason of the worker crash in this large auth log.",
        keywords=[["jwt.rs"], ["1873"], ["ExpiredSignature"]],
        note="~65K tok: exceeds BOTH 4096 and 32768. 결정적 부하>용량 영역.",
    )

    return tasks


def _score_text(ans, tattoo, keyword_groups) -> float:
    """final_answer + 최종 tattoo assertions 합집합으로 채점.

    E4B 는 검색한 needle 을 final_answer 대신 assertion 에만 기록하는 경우가 잦다
    (final_answer=None fragility). 이는 arm 무관 공통 노이즈이므로, "needle 이 시스템
    최종 상태(answer 또는 assertion) 어디든 도달했는가"로 채점하면 검색/라우팅 신호를
    모든 arm 에 동일하게 측정할 수 있다 (truncated stuffing 은 needle 자체가 없어 여전히 0).
    """
    parts = []
    if ans:
        parts.append(ans if isinstance(ans, str) else json.dumps(ans, ensure_ascii=False))
    try:
        for a in tattoo.active_assertions:
            c = getattr(a, "content", None)
            if c:
                parts.append(str(c))
    except Exception:
        pass
    if not parts:
        return 0.0
    low = " \n ".join(parts).lower()
    matched = sum(1 for grp in keyword_groups if all(t.lower() in low for t in grp))
    return matched / len(keyword_groups)


def _healthcheck():
    try:
        with httpx.Client(timeout=30) as c:
            tags = c.get(BASE_URL.rstrip("/") + "/api/tags").json()
        names = [m.get("name") for m in tags.get("models", [])]
        if MODEL not in names:
            print(f"  [ABORT] model {MODEL} not on server. available={names}")
            return False
        print(f"  [Healthcheck] tunnel OK, model present: {names}")
        return True
    except Exception as e:
        print(f"  [ABORT] healthcheck failed: {e}")
        return False


def main():
    print("=" * 80)
    print(f"Exp15 v2 Context Router Stress Test — {MODEL} via tunnel {BASE_URL}")
    print(f"matrix: {len(['rust_35k','pytrace','caddy_5xx','multihop','overflow_60k'])} task × {len(ARMS)} arm × {len(CTX_LEVELS)} ctx × n={N_TRIALS}")
    print("=" * 80)

    if not _healthcheck():
        sys.exit(1)

    tasks = _build_logs()
    r = get_redis_client()
    results: dict = {"experiment": "exp15_v2_stress", "model": MODEL,
                     "provider": "ollama_native_via_ssh_tunnel",
                     "n_trials": N_TRIALS, "max_cycles": MAX_CYCLES,
                     "ctx_levels": CTX_LEVELS, "results": {}}
    # resume: 기존 부분 결과 로드 → 완료 셀(len(scores)==N_TRIALS) skip
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
            if prev.get("results"):
                results["results"] = prev["results"]
                print(f"  [Resume] loaded existing partial results from {OUT_PATH.name}")
        except Exception as e:
            print(f"  [Resume] could not load prev ({e}); starting fresh")

    def _done(task_id, ctx, arm) -> bool:
        cell = results["results"].get(task_id, {}).get("ctx", {}).get(str(ctx), {}).get(arm)
        return bool(cell and len(cell.get("scores", [])) == N_TRIALS)

    t0 = time.time()
    for task_id, spec in tasks.items():
        log_content = "\n".join(spec["lines"])
        redis_key = f"ctx:exp15v2_{task_id}:stdout"
        r.set(redis_key, log_content)
        approx_tok = len(log_content) // 4
        print(f"\n{'#'*70}\n# TASK {task_id} | {len(spec['lines'])} lines, ~{approx_tok} tok | {spec['note']}\n{'#'*70}")
        results["results"].setdefault(task_id, {"approx_tokens": approx_tok, "note": spec["note"], "ctx": {}})

        for ctx in CTX_LEVELS:
            results["results"][task_id]["ctx"].setdefault(str(ctx), {})
            for arm in ARMS:
                if _done(task_id, ctx, arm):
                    c = results["results"][task_id]["ctx"][str(ctx)][arm]
                    print(f"  [skip done] {task_id} ctx={ctx} {arm} mean_score={c['mean_score']:.0%}")
                    continue
                scores, durs, cyc, trounds, intoks = [], [], [], [], []
                answers = []
                for trial in range(1, N_TRIALS + 1):
                    stats: dict = {}
                    caller = make_ollama_native_caller(BASE_URL, MODEL, num_ctx=ctx, stats=stats)
                    if arm == "stuffing":
                        prompt = ("Here is the raw log:\n\n```text\n" + log_content + "\n```\n\n" + spec["objective"])
                        kw = dict(context_router=False, error_blocks=False)
                    else:
                        prompt = (f"A failure occurred. The raw log is cached in Redis.\nContext Handle: {redis_key}\n\n"
                                  + spec["objective"])
                        if arm == "router_basic":
                            kw = dict(context_router=True, error_blocks=False, context_handles=[redis_key])
                        elif arm == "error_blocks_only":
                            kw = dict(context_router=False, error_blocks=True, context_handles=[redis_key])
                        else:  # hybrid
                            kw = dict(context_router=True, error_blocks=True, context_handles=[redis_key])

                    start = time.time()
                    try:
                        _t, logs, ans = run_abc_chain(
                            task_id=f"exp15v2_{task_id}_{ctx}_{arm}_{trial}",
                            objective=spec["objective"], prompt=prompt,
                            constraints=["정확한 파일/라인/식별자를 기재하라"],
                            max_cycles=MAX_CYCLES, model_caller=caller, **kw,
                        )
                        dur = time.time() - start
                        sc = _score_text(ans, _t, spec["keywords"])
                        scores.append(sc); durs.append(dur); cyc.append(len(logs))
                        trounds.append(stats.get("tool_rounds", 0))
                        intoks.append(stats.get("in_tok", 0))
                        answers.append(ans if not isinstance(ans, str) else ans[:300])
                    except Exception as e:
                        scores.append(0.0); durs.append(time.time() - start); cyc.append(0)
                        trounds.append(stats.get("tool_rounds", 0)); intoks.append(stats.get("in_tok", 0))
                        answers.append(f"<ERROR: {e}>")
                    print(f"  [{task_id} ctx={ctx} {arm} t{trial}] score={scores[-1]:.0%} "
                          f"dur={durs[-1]:.1f}s cyc={cyc[-1]} tool_rounds={trounds[-1]} in_tok~{intoks[-1]}")

                cell = {
                    "scores": scores,
                    "mean_score": round(statistics.mean(scores), 3),
                    "mean_dur": round(statistics.mean(durs), 1),
                    "mean_cycles": round(statistics.mean(cyc), 1),
                    "mean_tool_rounds": round(statistics.mean(trounds), 2),
                    "mean_in_tok": int(statistics.mean(intoks)),
                    "answers": answers,
                }
                results["results"][task_id]["ctx"][str(ctx)][arm] = cell
                # 증분 저장 (터널 끊김 대비)
                with open(OUT_PATH, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2, ensure_ascii=False)
                print(f"  → [{task_id} ctx={ctx} {arm}] mean_score={cell['mean_score']:.0%} "
                      f"mean_dur={cell['mean_dur']}s mean_tool_rounds={cell['mean_tool_rounds']} (saved)")

    results["total_elapsed_sec"] = round(time.time() - t0, 1)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # ── 요약 매트릭스 출력 ──
    print("\n" + "=" * 80)
    print("SUMMARY — mean_score [mean_tool_rounds] per task × ctx × arm")
    print("=" * 80)
    for task_id, td in results["results"].items():
        print(f"\n{task_id} (~{td['approx_tokens']} tok)")
        for ctx, arms in td["ctx"].items():
            row = " | ".join(f"{a}={arms[a]['mean_score']:.0%}[{arms[a]['mean_tool_rounds']}]" for a in ARMS)
            print(f"  ctx={ctx:>5}: {row}")
    print(f"\ntotal elapsed: {results['total_elapsed_sec']}s → {OUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()
