---
type: plan-task
status: pending
updated_at: 2026-06-30
parent_plan: exp21-facet-aggregate-tool
parallel_group: A
depends_on: []
---

# Task 01 — facet 도구 + caller opt-in 플러밍

## Changed files

- `experiments/tools/context_tools.py` (수정) — `aggregate_context()` 함수 + `FACET_TOOL_SCHEMAS` 리스트 + `FACET_TOOL_FUNCTIONS` dict 추가. **기존 `read_context`/`grep_context`/`CONTEXT_TOOL_SCHEMAS`/`CONTEXT_TOOL_FUNCTIONS` 무변경.**
- `experiments/exp15_context_router/native_ollama_caller.py` (수정) — `make_ollama_native_caller(..., extra_tool_schemas=None, extra_tool_fns=None)` 파라미터 추가. default None → 기존 거동 동치.

> 신규 0, 수정 2.

## Change description

### 배경
Exp20 진단: grep_context 16KB 라인 덤프가 high-volume 매치에서 모델 finalization 을 막음. 절단 없는 결정론적 집계 도구를 **순수 opt-in** 으로 추가하되, 글로벌 도구 표면을 불변으로 유지해 타 실험 회귀를 차단한다.

### Step 1 — `aggregate_context` 함수 (context_tools.py, grep_context 정의 아래)
```python
def aggregate_context(handle: str, pattern: str, group_by: str | None = None,
                      top_n: int = 10) -> dict:
    """Redis 로그에서 pattern 매치 라인을 전수 집계한다 (16KB 라인덤프 대신 카운트).

    group_by 가 capture group 을 가진 regex 면 그 그룹값별 카운트를 top_n 으로 반환.
    group_by 가 None 이면 매치 총수 + 소수 sample 라인만 반환.
    절단 없음 — top_n 행만 반환하므로 출력이 항상 작다.

    Args:
        handle: Redis key
        pattern: 매치 대상 문자열/정규식 (grep_context 와 동일 의미, IGNORECASE)
        group_by: (선택) capture group 1 개를 가진 정규식.
                  예: r"from (\\d+\\.\\d+\\.\\d+\\.\\d+)"  → IP 별 카운트.
                  예: r"(\\S+\\.service)"  → systemd unit 별 카운트.
        top_n: 반환할 상위 그룹 수 (기본 10)
    """
    try:
        r = get_redis_client()
        content = r.get(handle)
        if content is None:
            return {"error": f"Context handle '{handle}' not found in Redis."}
        lines = content.splitlines()
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return {"error": f"invalid pattern regex: {e}"}
        matched = [ln for ln in lines if regex.search(ln)]
        total = len(matched)

        if group_by:
            try:
                grp = re.compile(group_by, re.IGNORECASE)
            except re.error as e:
                return {"error": f"invalid group_by regex: {e}"}
            from collections import Counter
            counts: "Counter[str]" = Counter()
            for ln in matched:
                m = grp.search(ln)
                if m and m.groups():
                    counts[m.group(1)] += 1
            top = [{"value": v, "count": c} for v, c in counts.most_common(top_n)]
            return {"handle": handle, "pattern": pattern, "group_by": group_by,
                    "total_matches": total, "unique_groups": len(counts),
                    "top": top, "truncated": False}
        # group_by 없음 → 총수 + sample (절단 아님: sample 개수만 의도적으로 제한)
        sample = matched[:5]
        return {"handle": handle, "pattern": pattern, "group_by": None,
                "total_matches": total, "sample": sample,
                "note": "Use group_by (regex with one capture group) to aggregate by field.",
                "truncated": False}
    except Exception as e:
        return {"error": f"Redis connection or aggregate error: {e}"}
```

### Step 2 — FACET 도구 정의 (context_tools.py, `CONTEXT_TOOL_FUNCTIONS` 정의 아래, 별도 구조)
```python
FACET_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "aggregate_context",
            "description": (
                "Aggregate ALL matching lines in a cached log by count, with NO 16KB "
                "truncation. Use this instead of grep_context when a pattern has many "
                "matches and you need totals or the top contributors. If you give "
                "'group_by' (a regex with ONE capture group), it returns the top values "
                "by frequency. Examples: to find the IP with the most failed SSH logins, "
                "pattern='Failed password', group_by='from (\\\\d+\\\\.\\\\d+\\\\.\\\\d+\\\\.\\\\d+)'. "
                "To find which systemd unit fails most, pattern='Failed with result', "
                "group_by='(\\\\S+\\\\.service)'. Without group_by it returns the total "
                "match count plus a few sample lines."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "handle": {"type": "string", "description": "The Redis key handle"},
                    "pattern": {"type": "string", "description": "Text/regex to match lines (IGNORECASE)"},
                    "group_by": {"type": "string", "description": "Optional regex with ONE capture group to aggregate by"},
                    "top_n": {"type": "integer", "description": "How many top groups to return (default 10)"},
                },
                "required": ["handle", "pattern"],
            },
        },
    },
]

FACET_TOOL_FUNCTIONS = {
    "aggregate_context": aggregate_context,
}
```

### Step 3 — `tools/__init__.py` export (FACET 가 import 가능하도록)
`experiments/tools/__init__.py` 가 `CONTEXT_TOOL_SCHEMAS` 를 export 하듯 `FACET_TOOL_SCHEMAS`/`FACET_TOOL_FUNCTIONS`/`aggregate_context` 도 export. (기존 export 라인 무변경, 추가만.)

### Step 4 — native_ollama_caller opt-in 파라미터
```python
def make_ollama_native_caller(base_url, model, num_ctx, stats=None,
                              max_tokens=4096, temperature=0.1,
                              extra_tool_schemas=None, extra_tool_fns=None):
    ...
    _exec = {**CONTEXT_TOOL_FUNCTIONS, **(extra_tool_fns or {})}   # 실행 lookup
    def _caller(messages, tools=None, **kwargs):
        eff_tools = list(tools or [])
        if extra_tool_schemas:
            eff_tools = eff_tools + list(extra_tool_schemas)
        ... _post(convo, eff_tools or None) ...
        func = _exec.get(name)   # CONTEXT_TOOL_FUNCTIONS 직접 참조 → _exec 로 교체
```
- `tools` 가 None 이고 extra 도 없으면 `eff_tools or None` 으로 기존과 동일하게 None 전달 → **byte-identical**.
- 실행 lookup 을 모듈 전역 `CONTEXT_TOOL_FUNCTIONS` 대신 `_exec`(= 전역 + extra) 로.

## Dependencies

- 외부 패키지: `collections.Counter`(표준), 기존 `re`/`redis`.
- 기존 파일(read-only 이해): `experiments/tools/__init__.py`(export 패턴), `orchestrator.py:776-779`(context_router 도구 주입 경로 — **수정 금지**, 이해만).

## Verification

```bash
# 1) syntax + import
cd experiments && python -c "import ast; ast.parse(open('tools/context_tools.py',encoding='utf-8').read()); print('context_tools OK')"
cd experiments && python -c "import ast; ast.parse(open('exp15_context_router/native_ollama_caller.py',encoding='utf-8').read()); print('caller OK')"

# 2) FACET export + 글로벌 불변(회귀)
cd experiments && python -c "
from tools import CONTEXT_TOOL_SCHEMAS, CONTEXT_TOOL_FUNCTIONS, FACET_TOOL_SCHEMAS, FACET_TOOL_FUNCTIONS, aggregate_context
names=[s['function']['name'] for s in CONTEXT_TOOL_SCHEMAS]
assert names==['read_context','grep_context'], names           # 글로벌 불변
assert list(CONTEXT_TOOL_FUNCTIONS)==['read_context','grep_context']
assert [s['function']['name'] for s in FACET_TOOL_SCHEMAS]==['aggregate_context']
assert 'aggregate_context' in FACET_TOOL_FUNCTIONS
print('FACET separated, global unchanged OK')
"

# 3) aggregate_context 기능 (fixture)
cd experiments && python -c "
from tools.context_tools import get_redis_client, aggregate_context
r=get_redis_client()
r.set('ctx:facet_smoke:stdout','\n'.join(['Failed password from 1.1.1.1']*3+['Failed password from 2.2.2.2']*1+['ok line']))
g=aggregate_context('ctx:facet_smoke:stdout','Failed password', group_by=r'from (\d+\.\d+\.\d+\.\d+)')
assert g['total_matches']==4, g
assert g['top'][0]=={'value':'1.1.1.1','count':3}, g['top']
n=aggregate_context('ctx:facet_smoke:stdout','Failed password')
assert n['total_matches']==4 and 'sample' in n, n
r.delete('ctx:facet_smoke:stdout'); print('aggregate_context OK', g['top'])
"

# 4) caller default 동치 (extra None → tools 그대로)
cd experiments && python -c "
from exp15_context_router.native_ollama_caller import make_ollama_native_caller
c=make_ollama_native_caller('http://127.0.0.1:11435','gemma4:e4b',32768)   # extra None
print('caller default constructs OK')
"
```

## Risks

1. `tools/__init__.py` 가 `*` export 가 아니라 명시 export 면 FACET 추가 누락 → import 실패. 대응: Verification 2 로 즉시 검출.
2. native caller 의 `CONTEXT_TOOL_FUNCTIONS` 직접 참조를 `_exec` 로 바꿀 때 다른 참조 빠뜨림. 대응: grep 으로 `CONTEXT_TOOL_FUNCTIONS` 참조 전수 확인.
3. group_by regex 에 capture group 없으면 `m.group(1)` IndexError. 대응: `m.groups()` 체크 후 접근(코드 반영됨).

## Scope boundary

- **수정 금지**: `orchestrator.py`, `grep_context`/`read_context` 본문, `CONTEXT_TOOL_SCHEMAS`/`CONTEXT_TOOL_FUNCTIONS` 기존 원소, 드라이버(`run_v*.py`), 테스트.
- 본 task 는 도구 정의 + caller 파라미터까지. A/B 드라이버는 task-03.
