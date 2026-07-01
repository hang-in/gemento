"""per-attempt 실패 sub-mode 진단 — emission gap vs retrieval gap (공유 코드 무변경).

트랙 질문(§20 후속): per-attempt finalization ≈49% 실패가
  (a) emission/finalize gap — tool 이 정답(gohttpserver)을 띄웠는데 chain 이 assertion/
      final_answer 로 커밋 못 함 → **프롬프트로 고칠 수 있음** (Exp16b 전사규칙류 유효).
  (b) retrieval gap — 어떤 grep 도 정답 라인을 못 띄움(under-query/능력 바닥) →
      **프롬프트로 못 고침, retry 가 천장.**
이 비율이 트랙 방향을 가른다. narrow-query nudge(H22)는 이미 반증 — (a) 여야 새 레버 가치.

방법: native_ollama_caller 는 tool 을 내부 실행해 결과를 노출 안 함(micro_diag tool_call_log=[] 한계).
그래서 여기 **tracing caller 를 자체 구현**(CONTEXT_TOOL_FUNCTIONS 재사용, native 와 동형 loop +
tool 호출/결과 캡처). control(grep_only+router+mandatory), task A, single-attempt, n=20.

chain 별 분류:
  finalized+correct                         → success
  not finalized, answer_retrieved_by_tool   → emission_gap   (a, 프롬프트로 고침 가능)
  not finalized, not retrieved              → retrieval_gap  (b, 능력 바닥)

실행 (boxie 터널 필요):
  python -u experiments/exp15_context_router/diagnostics/per_attempt_diag.py
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_DIR.parent.parent))                 # experiments/
sys.path.insert(0, str(_DIR.parent))                        # exp15_context_router/

import httpx

import run_v21_facet_ab as drv
from orchestrator import run_abc_chain
from tools.context_tools import CONTEXT_TOOL_FUNCTIONS

BASE_URL, MODEL, NUM_CTX, REDIS_KEY = drv.BASE_URL, drv.MODEL, drv.NUM_CTX, drv.REDIS_KEY
MAX_CYCLES = 8
N = 20
TASK_ID = "exp21a_crashloop"
CORRECT_KW = "gohttpserver"
OUT = _DIR / "per_attempt_diag_result.json"
MAX_TOOL_ITERS = 8

TASK = next(t for t in drv.TASKS if t["id"] == TASK_ID)


def make_tracing_caller(trace: list):
    """native_ollama_caller 와 동형 loop + tool 호출/결과를 trace 에 캡처.
    trace 항목: {name, pattern, result_has_kw}. 공유 native_ollama_caller.py 무변경.
    """
    url = BASE_URL.rstrip("/") + "/api/chat"
    _exec = dict(CONTEXT_TOOL_FUNCTIONS)                      # grep_only (facet 무)

    def _post(messages, tools):
        payload = {
            "model": MODEL, "messages": messages, "stream": False, "keep_alive": "10m",
            "options": {"num_ctx": NUM_CTX, "temperature": 0.1, "num_predict": 4096},
        }
        if tools:
            payload["tools"] = tools
        with httpx.Client(timeout=600) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()

    def _caller(messages, tools=None, **kwargs):
        convo = list(messages)
        final_content = ""
        for _ in range(MAX_TOOL_ITERS + 1):
            try:
                data = _post(convo, list(tools) if tools else None)
            except Exception as e:
                trace.append({"error": str(e)})
                break
            msg = data.get("message") or {}
            tool_calls = msg.get("tool_calls") or []
            content = msg.get("content") or ""
            if not tool_calls:
                final_content = content
                break
            convo.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
            for tc in tool_calls:
                fn = tc.get("function") or {}
                name = fn.get("name")
                raw = fn.get("arguments")
                args = (json.loads(raw) if isinstance(raw, str) else raw) or {}
                if isinstance(args, str):
                    args = {}
                func = _exec.get(name)
                if func is None:
                    result = {"error": f"unknown tool: {name}"}
                else:
                    try:
                        result = func(**args)
                    except Exception as ex:
                        result = {"error": f"tool execution failed: {ex}"}
                rjson = json.dumps(result, ensure_ascii=False)
                trace.append({
                    "name": name,
                    "pattern": args.get("pattern") if isinstance(args, dict) else None,
                    "result_has_kw": CORRECT_KW.lower() in rjson.lower(),
                })
                convo.append({"role": "tool", "tool_name": name, "content": rjson})
        return final_content, {"error": None, "tool_rounds": 0, "cost_usd": 0.0,
                               "input_tokens": 0, "output_tokens": 0, "reasoning_tokens": 0}

    return _caller


def one_chain():
    prompt = (f"A diagnostic request for server test9ng. The full systemd journal (30-day window, "
              f"very large) is cached in Redis.\nContext Handle: {REDIS_KEY}\n\n" + TASK["objective"])
    trace = []
    caller = make_tracing_caller(trace)
    tt, logs, ans = run_abc_chain(
        task_id=TASK["id"], objective=TASK["objective"], prompt=prompt,
        constraints=TASK["constraints"], max_cycles=MAX_CYCLES, model_caller=caller,
        context_router=True, error_blocks=False, context_handles=[REDIS_KEY],
        mandatory_tool_prompt=True,
    )
    synth = " ".join(str(getattr(a, "content", "")) for a in tt.active_assertions
                     if getattr(a, "content", None)).lower()
    retrieved = any(t.get("result_has_kw") for t in trace)
    finalized = ans is not None
    correct = (CORRECT_KW in str(ans).lower()) if ans else False
    if finalized and correct:
        bucket = "success"
    elif finalized and not correct:
        bucket = "finalized_wrong"
    elif retrieved:
        bucket = "emission_gap"                              # tool 이 띄웠으나 커밋 실패 (promptable)
    else:
        bucket = "retrieval_gap"                             # 못 띄움 (능력 바닥)
    return {
        "finalized": finalized, "correct": correct,
        "answer_retrieved_by_tool": retrieved,
        "answer_in_tattoo": CORRECT_KW in synth,
        "n_assertions": len(tt.active_assertions),
        "n_tool_calls": len(trace),
        "n_grep_hit_kw": sum(1 for t in trace if t.get("result_has_kw")),
        "patterns": [t.get("pattern") for t in trace if t.get("pattern")][:12],
        "bucket": bucket,
    }


def main():
    print("=" * 80, flush=True)
    print(f"per-attempt 진단 — emission gap vs retrieval gap | control task A, single-attempt n={N}", flush=True)
    print("=" * 80, flush=True)
    if not drv._healthcheck():
        sys.exit(1)
    drv._load_megalog_to_redis()

    out = {"experiment": "per_attempt_submode_diag", "model": MODEL, "task": TASK_ID,
           "n": N, "max_cycles": MAX_CYCLES, "samples": []}
    t0 = time.time()
    samples = []
    for i in range(1, N + 1):
        r = one_chain()
        samples.append(r)
        out["samples"] = samples
        out["buckets"] = dict(Counter(x["bucket"] for x in samples))
        out["agg"] = {
            "n": len(samples),
            "finalized_rate": round(sum(1 for x in samples if x["finalized"]) / len(samples), 3),
            "retrieved_rate": round(sum(1 for x in samples if x["answer_retrieved_by_tool"]) / len(samples), 3),
            "emission_gap": sum(1 for x in samples if x["bucket"] == "emission_gap"),
            "retrieval_gap": sum(1 for x in samples if x["bucket"] == "retrieval_gap"),
        }
        out["elapsed_sec"] = round(time.time() - t0, 1)
        OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  [{i}/{N}] {r['bucket']:15s} finalized={r['finalized']} retrieved={r['answer_retrieved_by_tool']} "
              f"tool_calls={r['n_tool_calls']} grep_hit={r['n_grep_hit_kw']} asrt={r['n_assertions']}", flush=True)

    print("\n" + "=" * 80, flush=True)
    print("per-attempt sub-mode 분포:", flush=True)
    print(f"  buckets = {out['buckets']}", flush=True)
    a = out["agg"]
    print(f"  finalized={a['finalized_rate']:.0%} | retrieved_by_tool={a['retrieved_rate']:.0%}", flush=True)
    fails = a["emission_gap"] + a["retrieval_gap"]
    if fails:
        print(f"  실패 {fails}건 중: emission_gap(promptable)={a['emission_gap']} / "
              f"retrieval_gap(능력바닥)={a['retrieval_gap']}", flush=True)
    print(f"  → {OUT}", flush=True)
    print("=" * 80, flush=True)


if __name__ == "__main__":
    main()
