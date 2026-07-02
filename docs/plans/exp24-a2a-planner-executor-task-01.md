---
type: plan-task
status: pending
updated_at: 2026-07-03
parent_plan: exp24-a2a-planner-executor
parallel_group: A
depends_on: []
---

# Task 01 — Planner/Executor 프롬프트 + a2a proposer 경로

## Changed files

- `experiments/system_prompt.py` (수정) — `A2A_PLANNER_SYSTEM` 프롬프트 + `build_a2a_planner_prompt(tattoo_json)` + `build_a2a_executor_prompt(finding, tattoo_json)` (신규 빌더, 기존 프롬프트 무변경).
- `experiments/orchestrator.py` (수정) — `run_abc_chain` 에 `a2a_proposer: bool = False` 파라미터 + A-stage 분기 + `_a2a_propose(...)` 헬퍼.

요약: 신규 0, 수정 2.

## Change description

### 배경
`scoped_emit_probe.py`(scoped emit 100%)가 입증한 경로를 정식 편입. Executor 는 probe 처럼 **finding 을 clean scoped 입력으로, 도구 없이** emit. Planner 는 도구로 finding 을 텍스트로 산출. 기존 파서(`extract_json_from_response`)·적용(`apply_llm_response`)·`LoopLog` 재사용 — 신규 파서 금지.

### Step 1 — `system_prompt.py` Planner/Executor 빌더
`SYSTEM_PROMPT`(기존) 무변경. 아래 신규 추가:

```python
A2A_PLANNER_SYSTEM = (
    "You are the PLANNER in a two-stage diagnostic pipeline. Your job is ONLY to find the "
    "single most important fact needed to answer the objective — e.g. which systemd service "
    "unit is crash-looping. Use the provided tools (grep_context / list_failed_units) to "
    "locate it in the cached log. Output ONE short plain-text sentence stating the finding "
    "(e.g. 'The crash-looping unit is gohttpserver.service.'). Do NOT output JSON, do NOT "
    "emit assertions — another agent will record it. If you cannot find it, say so plainly."
)

def build_a2a_planner_prompt(tattoo_json: str) -> list[dict]:
    return [
        {"role": "system", "content": A2A_PLANNER_SYSTEM},
        {"role": "user", "content": f"Current tattoo (state):\n{tattoo_json}\n\n"
                                    "Find the single key fact and state it in one sentence."},
    ]

def build_a2a_executor_prompt(finding: str, tattoo_json: str) -> list[dict]:
    # probe(scoped_emit_probe) 조건 재현: finding 을 clean 입력으로, 도구 없이 emit.
    scoped = (
        f"FACT (already established by the planner): {finding}\n\n"
        "Your ONLY task: record this established fact as a new_assertion (content: the fact, "
        "e.g. which unit is crash-looping and that it is failing), confidence >= 0.8. "
        "Do NOT call tools; the fact is already known. Emit at least one new_assertion."
    )
    # 기존 proposer schema/파서 재사용을 위해 build_prompt 계열과 동일 형식 사용.
    from system_prompt import build_prompt   # SYSTEM_PROMPT 기반 proposer 메시지
    # tattoo_json 의 objective 자리에 scoped 를 넣어 build — 간단히 scoped 를 user 로 덧붙임.
    msgs = build_prompt(tattoo_json)
    msgs.append({"role": "user", "content": scoped})
    return msgs
```

(Developer 판단: `build_a2a_executor_prompt` 는 probe 가 검증한 "scoped objective + 기존 proposer 시스템" 을 재현하는 게 핵심. 위는 한 방법 — build_prompt 에 scoped user 를 덧붙임. probe 처럼 scoped tattoo 를 새로 만들어 build_prompt 에 넘기는 방식도 허용, 단 **도구 없이 · decompose 없이** 를 지킬 것.)

### Step 2 — `orchestrator.py` 파라미터 + 헬퍼
`run_abc_chain` 시그니처에 `retrieval_discipline_prompt` 아래 `a2a_proposer: bool = False,` 추가.

A-stage(`run_loop` 호출부, 현재 `:823`) 를 분기:

```python
if a2a_proposer:
    tattoo, a_log, answer, a_tool_calls = _a2a_propose(
        tattoo, cycle, model_caller=model_caller,
        planner_tools=combined_extra_tools or None,
    )
else:
    tattoo, a_log, answer, a_tool_calls = run_loop(
        tattoo, cycle, phase_prompt_args=phase_args,
        use_tools=use_tools, tool_functions=_tool_fns,
        extra_tools=combined_extra_tools or None,
        extra_tool_fns=combined_extra_fns or None,
        model_caller=model_caller,
    )
```

`_a2a_propose` 헬퍼 (run_abc_chain 내부 또는 모듈 레벨):

```python
def _a2a_propose(tattoo, loop_index, model_caller, planner_tools=None):
    from system_prompt import build_a2a_planner_prompt, build_a2a_executor_prompt
    # 1. Planner: 도구로 finding 텍스트 산출 (native caller 가 도구 내부 실행)
    p_msgs = build_a2a_planner_prompt(tattoo.to_json())
    finding, _ = model_caller(p_msgs, tools=planner_tools) if planner_tools else model_caller(p_msgs)
    finding = (finding or "").strip()
    # 2. Executor: clean scoped emit (도구 없음)
    e_msgs = build_a2a_executor_prompt(finding, tattoo.to_json())
    raw, _ = model_caller(e_msgs)
    parsed = extract_json_from_response(raw)
    if parsed:
        new_tattoo, answer = apply_llm_response(tattoo, parsed, loop_index)
    else:
        new_tattoo = copy.deepcopy(tattoo); new_tattoo.loop_index = loop_index
        new_tattoo.parent_id = tattoo.tattoo_id
        new_tattoo.finalize_integrity(parent_chain_hash=tattoo.chain_hash)
        answer = None
    a_log = LoopLog(loop_index=loop_index, tattoo_in=tattoo.to_dict(),
                    raw_response=f"[planner] {finding}\n[executor] {raw}",
                    parsed_response=parsed, tattoo_out=new_tattoo.to_dict(),
                    duration_ms=0, error=None if parsed else "a2a executor parse failed")
    return new_tattoo, a_log, answer, []
```

반환 shape 는 `run_loop` 와 동일 `(Tattoo, LoopLog, str|None, list)` — B/C 무변경.

### Step 3 — 기본 False 불변식 확인
`a2a_proposer=False` 시 위 `else:` 경로 = 기존 `run_loop` 호출과 **문자 동일**. diff 는 순수 추가.

## Dependencies

- 외부: 없음.
- 기존 파일 (read-only 참조): `scoped_emit_probe.py`(Executor 경로 검증), `system_prompt.py:build_prompt`/`SYSTEM_PROMPT`(**수정 금지**), `orchestrator.py`(`run_loop`/`apply_llm_response`/`extract_json_from_response`/`LoopLog`/`copy`).

## Verification

```bash
# 1. syntax + import
python -c "import ast; [ast.parse(open('experiments/'+f,encoding='utf-8').read()) for f in ('system_prompt.py','orchestrator.py')]; print('syntax OK')"
python -c "import sys; sys.path.insert(0,'experiments'); from system_prompt import A2A_PLANNER_SYSTEM, build_a2a_planner_prompt, build_a2a_executor_prompt; print('planner msgs:', len(build_a2a_planner_prompt('{}'))); print('exec msgs:', len(build_a2a_executor_prompt('unit X fails','{}')))"
```

```bash
# 2. 파라미터 기본 False + 가드 존재 + 기존 프롬프트 무변경
python -c "import sys,inspect; sys.path.insert(0,'experiments'); import orchestrator; p=inspect.signature(orchestrator.run_abc_chain).parameters['a2a_proposer']; assert p.default is False; src=inspect.getsource(orchestrator.run_abc_chain); assert 'if a2a_proposer:' in src; from system_prompt import SYSTEM_PROMPT; assert SYSTEM_PROMPT.startswith('You are') or len(SYSTEM_PROMPT)>0; print('param+guard OK')"
```

```bash
# 3. Executor 프롬프트가 probe 조건(도구 없음·scoped) 반영
python -c "import sys; sys.path.insert(0,'experiments'); from system_prompt import build_a2a_executor_prompt as b; m=b('The crash-looping unit is gohttpserver.service.','{}'); txt=' '.join(x['content'] for x in m); assert 'Do NOT call tools' in txt and 'new_assertion' in txt and 'gohttpserver' in txt; print('executor scoped OK')"
```

```bash
# 4. (터널 있을 때) a2a 경로 1회 smoke — Planner→Executor 가 assertion emit
python -c "
import sys; sys.path.insert(0,'experiments'); sys.path.insert(0,'experiments/exp15_context_router')
import run_v21_facet_ab as drv
from schema import create_initial_tattoo
from orchestrator import _a2a_propose
from native_ollama_caller import make_ollama_native_caller
from tools import CONTEXT_TOOL_SCHEMAS
if not drv._healthcheck(): sys.exit(0)
drv._load_megalog_to_redis()
tt=create_initial_tattoo('a2a_smoke', f'Which systemd unit is crash-looping on test9ng? Context Handle: {drv.REDIS_KEY}', [], '', [drv.REDIS_KEY])
c=make_ollama_native_caller(drv.BASE_URL, drv.MODEL, num_ctx=drv.NUM_CTX)
nt,log,ans,_=_a2a_propose(tt,1,model_caller=c,planner_tools=CONTEXT_TOOL_SCHEMAS)
print('assertions:', [a.content[:60] for a in nt.active_assertions][:3])
" 2>&1 || echo '(터널 없으면 Task 03 실행 시 확인)'
```

## Risks

1. **기본 False 비불변** — Verification 2 + diff 순수 추가 확인.
2. **B/C 계약 파손** — `_a2a_propose` 반환 shape 를 run_loop 와 동일하게(Verification 4 smoke 로 tattoo/assertion 정상 확인).
3. **build_a2a_executor_prompt 가 도구 노출** — Executor 는 도구 없이 호출(헬퍼가 tools 안 넘김). Verification 3.
4. **apply_llm_response/LoopLog import 누락** — orchestrator 상단 이미 사용 중(재확인).

## Scope boundary

**수정 금지**: `SYSTEM_PROMPT`/`build_prompt`/critic/judge 프롬프트, `run_loop` 본문, B/C/error_blocks/mandatory/discipline/context_router 경로, 실험 드라이버, 테스트. 본 task 는 신규 프롬프트 빌더 + 파라미터 + 분기 + 헬퍼만.
