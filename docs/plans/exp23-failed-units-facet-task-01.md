---
type: plan-task
status: pending
updated_at: 2026-07-02
parent_plan: exp23-failed-units-facet
parallel_group: A
depends_on: []
---

# Task 01 — 도구 구현 + export

## Changed files

- `experiments/tools/context_tools.py` (수정) — `list_failed_units(handle, top_n=10)` 함수 + `FAILED_UNITS_TOOL_SCHEMAS` / `FAILED_UNITS_TOOL_FUNCTIONS` (글로벌 분리 opt-in). `aggregate_context`/`FACET_TOOL_*` 정의 바로 아래.
- `experiments/tools/__init__.py` (수정) — `list_failed_units`, `FAILED_UNITS_TOOL_SCHEMAS`, `FAILED_UNITS_TOOL_FUNCTIONS` import + `__all__` 추가. 기존 export 무변경.

요약: 신규 0, 수정 2.

## Change description

### 배경
`aggregate_context`(H21, `context_tools.py:149`)는 실패 unit 집계가 가능하나 모델이 `pattern`/`group_by`를 formulate 해야 한다. per_attempt_diag(retrieval_gap 7/7)가 보여준 병목이 바로 그 formulate 이므로, **인자 없는 preset** 을 만든다. FACET_TOOL 패턴(`:257~289`)을 그대로 미러.

### Step 1 — `list_failed_units` 함수
`aggregate_context` 정의(`:149~200`) 바로 아래에 추가. 내부에서 systemd 실패 신호를 전수 스캔해 unit 별 카운트 top-N 반환 (untruncated):

```python
def list_failed_units(handle: str, top_n: int = 10) -> dict:
    """실패/재시작 중인 systemd unit 을 전수 집계해 top-N 반환 (인자 없는 preset).

    grep_context 로 검색어를 formulate 할 필요 없이, 표준 systemd 실패 신호
    ('Failed with result' / 'Main process exited' / 'start-limit' / '.service' churn)
    를 내부에서 스캔해 unit 별 실패-신호 카운트를 untruncated 로 돌려준다.
    per-attempt retrieval_gap(모델이 넓은 grep 후 포기) 우회용.

    Args:
        handle: Redis key
        top_n: 반환할 상위 unit 수 (기본 10)
    """
    try:
        r = get_redis_client()
        content = r.get(handle)
        if content is None:
            return {"error": f"Context handle '{handle}' not found in Redis."}
        lines = content.splitlines()
        signal = re.compile(
            r"Failed with result|Main process exited|start-limit|entered failed state|Failed to start",
            re.IGNORECASE,
        )
        unit = re.compile(r"(\S+\.service)", re.IGNORECASE)
        from collections import Counter
        counts: "Counter[str]" = Counter()
        for ln in lines:
            if signal.search(ln):
                m = unit.search(ln)
                if m:
                    counts[m.group(1)] += 1
        top = [{"unit": u, "failure_signals": c} for u, c in counts.most_common(top_n)]
        return {"handle": handle, "signal_lines": sum(counts.values()),
                "unique_units": len(counts), "top": top, "truncated": False}
    except Exception as e:
        return {"error": f"Redis connection or scan error: {e}"}
```

### Step 2 — 스키마 + 함수 dict
`FACET_TOOL_FUNCTIONS`(`:287~289`) 바로 아래에 추가 (글로벌/FACET 무변경):

```python
FAILED_UNITS_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_failed_units",
            "description": (
                "List the systemd units that are FAILING or crash-looping in a cached log, "
                "as an untruncated top-N count — NO search pattern needed. Call this FIRST "
                "when diagnosing a service crash/failure: it scans standard systemd failure "
                "signals ('Failed with result', 'Main process exited', start-limit, entered "
                "failed state) and returns the units with the most failure signals. Use it "
                "instead of guessing grep patterns. Returns {top:[{unit,failure_signals}], ...}."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {"type": "string", "description": "The Redis key handle"},
                    "top_n": {"type": "integer", "description": "How many top units to return (default 10)"},
                },
                "required": ["handle"],
            },
        },
    },
]

FAILED_UNITS_TOOL_FUNCTIONS = {
    "list_failed_units": list_failed_units,
}
```

### Step 3 — `tools/__init__.py` export
`FACET_TOOL_*` export 라인(`:5`) 아래에 추가, `__all__`(`:13` 인근)에 3개 이름 추가. 기존 라인 무변경.

## Dependencies

- 외부: `re`, `collections.Counter` (이미 import 됨 / 함수 내 import).
- 기존 파일 (read-only 참조): `context_tools.py:149` `aggregate_context`, `:257` `FACET_TOOL_SCHEMAS` (미러 패턴), `:203` `CONTEXT_TOOL_SCHEMAS` (**수정 금지**).

## Verification

```bash
# 1. syntax + import (repo root)
python -c "import sys; sys.path.insert(0,'experiments'); from tools import list_failed_units, FAILED_UNITS_TOOL_SCHEMAS, FAILED_UNITS_TOOL_FUNCTIONS; print('import OK'); print('fn:', list(FAILED_UNITS_TOOL_FUNCTIONS.keys()))"
```

```bash
# 2. 글로벌/FACET 불변 확인
python -c "import sys; sys.path.insert(0,'experiments'); from tools import CONTEXT_TOOL_FUNCTIONS, FACET_TOOL_FUNCTIONS; assert list(CONTEXT_TOOL_FUNCTIONS.keys())==['read_context','grep_context']; assert list(FACET_TOOL_FUNCTIONS.keys())==['aggregate_context']; print('globals intact')"
```

```bash
# 3. fixture 집계 정확성 (Redis 없이 — 함수 단위, 실패 신호 unit 반환 확인)
python -c "
import sys; sys.path.insert(0,'experiments')
from unittest import mock
import tools.context_tools as ct
fake=['Jan 1 gohttpserver.service: Main process exited, code=exited',
      'Jan 1 gohttpserver.service: Failed with result exit-code',
      'Jan 1 sshd.service: Started',
      'Jan 1 gohttpserver.service: start-limit hit']
class R:
    def get(self,k): return chr(10).join(fake)
with mock.patch.object(ct,'get_redis_client',lambda: R()):
    out=ct.list_failed_units('h')
    print(out)
    assert out['top'][0]['unit']=='gohttpserver.service', out
    assert out['top'][0]['failure_signals']==3, out
    assert out['truncated'] is False
print('fixture OK')
"
```

```bash
# 4. (터널+Redis 있을 때) 실제 메가로그로 gohttpserver 반환 확인 — Risk 4
python -c "
import sys; sys.path.insert(0,'experiments')
from tools import list_failed_units
out=list_failed_units('ctx:test9ng_journal_30d:stdout')
print('units:', [u['unit'] for u in out.get('top',[])][:5])
assert any('gohttpserver' in u['unit'] for u in out.get('top',[])), out
print('real-log OK')
" 2>&1 || echo '(Redis/터널 없으면 skip — Task 03 실행 시 확인)'
```

## Risks

1. **글로벌 오염** — Verification 2 로 CONTEXT/FACET 목록 무변경 확인.
2. **실패 신호가 test9ng 저널과 불일치** — Verification 4 로 실제 로그서 gohttpserver 반환 확인 (Redis 있을 때). 없으면 Task 03 실행 시점에 확인.
3. **unit 정규식이 과포착** (`.service` 없는 라인) — signal + unit 동시 조건이라 완화. fixture(Verification 3)로 검증.

## Scope boundary

**수정 금지**: `CONTEXT_TOOL_SCHEMAS/FUNCTIONS`, `FACET_TOOL_SCHEMAS/FUNCTIONS`, `aggregate_context`/`grep_context`/`read_context` 본문, `orchestrator.py`, `system_prompt.py`, 실험 드라이버. 본 task 는 신규 함수 1 + 스키마/함수 dict 2 + export 만.
