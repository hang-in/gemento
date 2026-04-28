---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: exp10-v3-scorer-false-positive-abc-json-parse
parallel_group: B
depends_on: []
---

# Task 04 — ABC JSON parse 4 fail 진단

## Changed files

- `experiments/exp10_reproducibility_cost/diagnose_json_fails.py` — **신규**. v2 final JSON 의 4 fail trial 의 `_debug.abc_logs` 마지막 cycle 분석 + 분류.
- `docs/reference/exp10-v3-abc-json-fail-diagnosis.md` — **신규**. 진단 결과 문서.

신규 파일 2, 다른 파일 수정 0.

## Change description

### 배경

v2 final 540 trial 중 gemma_8loop 의 4 trial 이 ABC chain JSON parse fail:

| condition | task | trial | error |
|-----------|------|------:|-------|
| gemma_8loop | math-03 | 13 | `A: JSON parse failed` |
| gemma_8loop | synthesis-01 | 14 | `B: JSON parse failed` |
| gemma_8loop | logic-04 | 2 | `A: JSON parse failed` |
| gemma_8loop | logic-04 | 6 | `A: JSON parse failed` |

각 trial 의 `_debug.abc_logs` 에 `a_raw`/`b_raw`/`c_raw` 가 4KB truncate 본으로 저장됨 (`experiments/exp10_reproducibility_cost/run.py:_truncate_raw`, line 44). truncate 시 끝에 `... (truncated, original_len=N)` 표시.

본 task 는 4 trial 의 마지막 cycle 의 fail 발생 raw 를 분석하여 원인을 분류:

- **(a) Truncate 원인** — raw 끝에 `... (truncated, original_len=N)` 가 보유 → 모델 응답이 4KB 초과 → max_tokens 한계 또는 모델 폭주
- **(b) Markdown fence 미닫힘** — raw 가 ` ```json\n{...` 로 시작하지만 ``` 닫는 fence 없음 → 모델이 응답 도중 멈춤
- **(c) JSON 자체 malformed** — fence 닫혔지만 brace count 안 맞거나 control char 등 lenient parser 도 못 처리

### 신규 파일: `experiments/exp10_reproducibility_cost/diagnose_json_fails.py`

```python
"""v2 final 의 ABC JSON parse 4 fail 진단.

각 fail trial 의 마지막 cycle 의 a_raw/b_raw/c_raw 중 error 가 발생한 항목을
분석하여 원인을 분류한다.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from exp10_reproducibility_cost.run import RESULTS_DIR


DEFAULT_INPUT = RESULTS_DIR / "exp10_v2_final_20260429_033922.json"

TRUNCATE_TAIL = re.compile(r"\.\.\. \(truncated, original_len=(\d+)\)\s*$")
FENCE_OPEN = re.compile(r"```(?:json)?\s*$|```(?:json)?\s*\n", re.IGNORECASE)
FENCE_CLOSE = re.compile(r"```\s*$")


def classify(raw: str) -> dict:
    """Raw 를 분류. 반환 키: kind, original_len, has_open_fence, has_close_fence, brace_open, brace_close, tail50."""
    if not raw:
        return {"kind": "empty"}
    m = TRUNCATE_TAIL.search(raw)
    truncated = bool(m)
    original_len = int(m.group(1)) if m else len(raw)
    body = raw[: m.start()] if truncated else raw
    has_open = bool(re.search(r"```(?:json)?", body, re.IGNORECASE))
    # 닫는 fence 는 시작 fence 다음 위치부터 검색
    has_close = False
    if has_open:
        # 첫 fence 다음부터
        first = re.search(r"```(?:json)?", body, re.IGNORECASE)
        rest = body[first.end():] if first else ""
        has_close = "```" in rest
    brace_open = body.count("{")
    brace_close = body.count("}")
    tail50 = body[-50:] if len(body) > 50 else body

    if truncated:
        kind = "truncate"
    elif has_open and not has_close:
        kind = "fence_unclosed"
    elif brace_open != brace_close:
        kind = "brace_mismatch"
    else:
        kind = "other"

    return {
        "kind": kind,
        "original_len": original_len,
        "stored_len": len(body),
        "has_open_fence": has_open,
        "has_close_fence": has_close,
        "brace_open": brace_open,
        "brace_close": brace_close,
        "tail50": tail50,
    }


TARGETS = [
    ("gemma_8loop", "math-03", 13),
    ("gemma_8loop", "synthesis-01", 14),
    ("gemma_8loop", "logic-04", 2),
    ("gemma_8loop", "logic-04", 6),
]


def diagnose(input_path: Path) -> list[dict]:
    with open(input_path, encoding="utf-8") as f:
        d = json.load(f)
    by_key = {(t["condition"], t["task_id"], t["trial"]): t for t in d["trials"]}
    rows = []
    for key in TARGETS:
        t = by_key.get(key)
        if t is None:
            rows.append({"key": key, "missing": True})
            continue
        debug = t.get("_debug") or {}
        logs = debug.get("abc_logs") or []
        if not logs:
            rows.append({"key": key, "no_debug_logs": True})
            continue
        last = logs[-1]
        # 어느 phase 가 fail 인지
        if last.get("a_error"):
            phase = "A"
            raw = last.get("a_raw", "")
        elif last.get("b_error"):
            phase = "B"
            raw = last.get("b_raw", "")
        elif last.get("c_error"):
            phase = "C"
            raw = last.get("c_raw", "")
        else:
            phase = "?"
            raw = ""
        cls = classify(raw)
        rows.append({
            "key": key,
            "trial_error": t.get("error"),
            "fail_phase": phase,
            "last_cycle": last.get("cycle"),
            "last_phase_name": last.get("phase"),
            **cls,
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose ABC JSON parse 4 fail")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    args = parser.parse_args()
    rows = diagnose(Path(args.input))
    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    # 분류 요약
    kinds = {}
    for r in rows:
        k = r.get("kind", "unknown")
        kinds[k] = kinds.get(k, 0) + 1
    print("\n--- summary ---")
    for k, v in sorted(kinds.items()):
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### 신규 파일: `docs/reference/exp10-v3-abc-json-fail-diagnosis.md`

진단 스크립트 실행 후, 그 결과를 본 문서에 표 형태로 기록:

```markdown
---
type: reference
status: done
updated_at: 2026-04-29
author: <agent>
---

# Exp10 v2 final ABC JSON parse 4 fail 진단

## 배경
v2 final 540 trial 중 gemma_8loop 4 trial 이 `extract_json_from_response` 실패. 본 문서는 각 trial 의 `_debug.abc_logs` 마지막 cycle 분석 결과.

## 진단 결과

| condition | task | trial | fail_phase | kind | original_len | tail50 (raw 끝) |
|-----------|------|------:|-----------:|------|-------------:|-----------------|
| gemma_8loop | math-03 | 13 | <FILL> | <FILL> | <FILL> | <FILL> |
| gemma_8loop | synthesis-01 | 14 | <FILL> | <FILL> | <FILL> | <FILL> |
| gemma_8loop | logic-04 | 2 | <FILL> | <FILL> | <FILL> | <FILL> |
| gemma_8loop | logic-04 | 6 | <FILL> | <FILL> | <FILL> | <FILL> |

## 분류 요약

- truncate: <N>
- fence_unclosed: <N>
- brace_mismatch: <N>
- other: <N>

## 함의 (Task 05 patch 방향)

(diagnose 결과에 따라 작성. 예: "4건 모두 truncate → max_tokens 4096 한계로 응답 짤림. orchestrator 의 partial JSON 복구 fallback 추가 필요" 또는 "4건 fence_unclosed → 마크다운 fence 시작 후 닫힘 못 찾는 경우 raw 끝까지 잘라 lenient 시도")

## 본 v2 final 의 4 fail 재산정 가능 여부

- raw 원본 4KB truncate 후만 `_debug` 에 저장. original_len > 4096 인 경우 원본 손실 → retry 만이 결정적.
- original_len ≤ 4096 인 경우 본 stored body 가 곧 원본. orchestrator patch (Task 05) 적용 후 `extract_json_from_response` 재호출로 final_answer 복구 가능 여부 별도 점검.
```

`<FILL>` / `<N>` 자리는 진단 스크립트 실행 결과로 대체.

## Dependencies

- 패키지: 표준 `json`, `re`, `argparse`. 신규 의존성 0.
- v2 final JSON: 이미 존재.
- 다른 subtask: 없음. Group B 의 시작점.

## Verification

```bash
# 1) 정적 import 통과 + 도움말 출력
.venv/bin/python -m experiments.exp10_reproducibility_cost.diagnose_json_fails --help

# 2) 4 trial 진단 실행 — 4 row 출력 + summary
.venv/bin/python -m experiments.exp10_reproducibility_cost.diagnose_json_fails 2>&1 | tee /tmp/diag.log

# 3) 진단 문서가 작성되었는지 + <FILL> 자리가 모두 채워졌는지
grep -c "<FILL>" docs/reference/exp10-v3-abc-json-fail-diagnosis.md
# 기대: 0 (모두 실제 값으로 치환됨)
```

3 명령 모두 정상 + 4 trial 모두 분류 완료 + 문서의 placeholder 0개.

## Risks

- **`_debug` 필드 누락**: gemma_8loop 의 v2 final trial 일부에 `_debug.abc_logs` 가 비어 있을 가능성 (Exp10 v2 재실행 시점이 debug logging plan 완료 직후라 schema 미준수 trial 가능). diagnose 스크립트가 `no_debug_logs` 경고로 처리. 만약 4 trial 중 일부가 누락되면 별도 raw 복구 불가 — Task 05 patch 는 미래 run 으로만 적용 가능 (본 plan constraint 준수).
- **`a_raw` 의 원본 길이 추정**: `... (truncated, original_len=N)` 표시가 있는 경우 N 으로 추정 가능. 표시 없으면 stored_len 이 곧 original_len. 분류 스크립트가 두 케이스 모두 처리.
- **fence_open 정규식 false positive**: 응답 본문에 ``` 가 단순 인용으로 등장한 경우 has_open_fence=True 로 잡힐 수 있음. 본 plan 의 분류는 진단 목적이라 정확도 100% 필요 없음 — Task 05 patch 의 priority 결정 정도면 충분.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- v2 final JSON — read-only.
- `experiments/orchestrator.py` — Task 05 영역. 본 task 는 진단만.
- `experiments/measure.py` / `experiments/tasks/taskset.json` — Task 01·02 영역.
- 다른 결과 JSON (`exp10_logic04_flash_retry_*.json`, `exp10_math04_8loop_debug_*.json`) — 본 task 분석 대상 아님.
