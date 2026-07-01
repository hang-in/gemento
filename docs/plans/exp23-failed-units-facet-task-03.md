---
type: plan-task
status: pending
updated_at: 2026-07-02
parent_plan: exp23-failed-units-facet
parallel_group: C
depends_on: [01]
---

# Task 03 — A/B 드라이버 (3 arm)

## Changed files

- `experiments/exp15_context_router/run_v23_failed_units_ab.py` (신규) — control(grep_only) / fu_offered(+list_failed_units) / fu_mandatory(+도구 +"먼저 호출" constraint) × task A × n=15. 실행은 사용자/에이전트.

요약: 신규 1, 수정 0.

## Change description

### 배경
`run_v21_facet_ab.py`(H21 facet A/B) 인프라를 재사용. arm 차이는 (a) caller 에 넘기는 `extra_tool_schemas/fns` (b) fu_mandatory 만 constraint 주입. per-attempt(retrieval_gap) 측정이 목적이므로 **single-attempt**(retry 없음), task A.

### Step 1 — 드라이버 작성
`run_v21_facet_ab.py` 인프라(`BASE_URL`/`MODEL`/`NUM_CTX`/`REDIS_KEY`/`TASKS`/`_healthcheck`/`_load_megalog_to_redis`) 재사용. 3 arm:

```python
from tools import FAILED_UNITS_TOOL_SCHEMAS, FAILED_UNITS_TOOL_FUNCTIONS

FU_MANDATORY_HINT = (
    "For a service crash/failure diagnosis, FIRST call `list_failed_units` on the handle "
    "to get the failing systemd units directly — do NOT start by grepping for 'error'. "
    "Then confirm the top unit with grep_context and record it as a new_assertion."
)

ARMS = [
    {"id": "control",      "schemas": None,                      "fns": None,                        "hint": None},
    {"id": "fu_offered",   "schemas": FAILED_UNITS_TOOL_SCHEMAS, "fns": FAILED_UNITS_TOOL_FUNCTIONS, "hint": None},
    {"id": "fu_mandatory", "schemas": FAILED_UNITS_TOOL_SCHEMAS, "fns": FAILED_UNITS_TOOL_FUNCTIONS, "hint": FU_MANDATORY_HINT},
]
```

- caller: `make_ollama_native_caller(..., extra_tool_schemas=arm["schemas"], extra_tool_fns=arm["fns"])` (native caller 가 이미 `extra_tool_*` 지원 — `native_ollama_caller.py:28`).
- fu_mandatory: `constraints = list(TASK["constraints"]) + [arm["hint"]]`.
- `run_abc_chain(..., mandatory_tool_prompt=True, context_router=True, context_handles=[REDIS_KEY])` (양 arm 공통, single-attempt).
- task = `exp21a_crashloop` 만. n=15/arm.
- 측정: `finalized`(ans not None), `correct`(gohttpserver in ans), `n_assertions`, `used_fu`(스키마 arm 에서 caller stats 로 도구 호출 여부 — stats dict 또는 tool_rounds 로 근사). durable 저장 `diagnostics/v23_failed_units_result.json`, 매 trial 증분 write.

### Step 2 — used_fu 계측
native caller 의 `stats` dict 를 arm 별로 넘겨 `tool_rounds` 를 받거나, fu 도구 호출 카운트를 위해 `FAILED_UNITS_TOOL_FUNCTIONS` 를 wrap 해 카운터 증가(진단 스크립트 방식). 간단히: stats dict 전달 후 `calls`/`tool_rounds` 기록 + fu 도구 wrap 카운터(`used_fu` bool).

### Step 3 — 실행 안내 docstring
```
# 사용자/에이전트 실행 (boxie 터널 필요):
#   python -u experiments/exp15_context_router/run_v23_failed_units_ab.py
#   EXP20_LOG_PATH 로 메가로그 경로 오버라이드 가능.
```

## Dependencies

- Task 01 완료 (`FAILED_UNITS_TOOL_*` 존재 — 없으면 fu arm 이 control 과 동일).
- 외부(실행 시점): boxie e4b 터널(11435) + Redis 메가로그 키.
- 기존 파일 (read-only): `run_v21_facet_ab.py`(인프라), `native_ollama_caller.py`(`extra_tool_*`), `orchestrator.py:run_abc_chain`.

## Verification

```bash
# 1. syntax (LLM/터널 없이 — repo root)
python -c "import ast; ast.parse(open(r'experiments/exp15_context_router/run_v23_failed_units_ab.py',encoding='utf-8').read()); print('syntax OK')"
```

```bash
# 2. 3 arm + FU 도구 wiring 정적 확인
python -c "s=open(r'experiments/exp15_context_router/run_v23_failed_units_ab.py',encoding='utf-8').read(); assert 'control' in s and 'fu_offered' in s and 'fu_mandatory' in s; assert 'FAILED_UNITS_TOOL_SCHEMAS' in s; assert 'exp21a_crashloop' in s; print('arms+tool+task OK')"
```

```bash
# 3. (사용자/에이전트 실행 — 터널 필요) 실제 A/B.
#   python -u experiments/exp15_context_router/run_v23_failed_units_ab.py
#   → diagnostics/v23_failed_units_result.json (3 arm × n=15)
```

## Risks

1. **used_fu 계측 부정확** — native caller 내부 실행이라 tool_rounds 만으로 fu 특정 어려움. → fu 함수 wrap 카운터(진단 스크립트 per_attempt_diag 방식) 사용.
2. **fu_mandatory hint 가 constraints 로 안 먹힘** — lever_test 처럼 constraints append 경로 확인. → run_abc_chain 이 constraints 를 프롬프트에 반영하는지 Task 03 작성 시 확인(기존 lever_test.py 참조).
3. **에이전트가 실수로 실행** — 긴 실험. → Verification 3 사용자/에이전트 실행 명시.
4. **결과 유실** — `diagnostics/` durable + 증분 write (§20 교훈).

## Scope boundary

**수정 금지**: `context_tools.py`/`tools/__init__.py`(Task 01), `run_v21_facet_ab.py`(read-only), `native_ollama_caller.py`, `orchestrator.py`, `system_prompt.py`. 본 task 는 신규 드라이버 1개만.
