---
type: plan-task
status: pending
updated_at: 2026-07-01
parent_plan: retrieval-discipline-opt-in
parallel_group: A
depends_on: []
---

# Task 01 — 코드: 상수 + 파라미터 + 주입 로직

## Changed files

- `experiments/system_prompt.py` (수정) — `MANDATORY_TOOL_RULES` 바로 아래에 canonical `RETRIEVAL_DISCIPLINE_RULES` 상수 추가.
- `experiments/orchestrator.py` (수정) — `run_abc_chain` 에 `retrieval_discipline_prompt: bool = False` 파라미터 + mandatory 주입 직후 독립 가드 주입 블록.

요약: 신규 0, 수정 2.

## Change description

### 배경
레버 A/B 에서 검증된 nudge 문구(`experiments/exp15_context_router/diagnostics/lever_test.py:25` `NUDGE`)를 공유 코드로 승격. 기존 `MANDATORY_TOOL_RULES`(`system_prompt.py:486`) opt-in 패턴을 **그대로 복제**하되 **별도 독립 플래그**로 (결정 1). MANDATORY 는 손대지 않는다.

### Step 1 — `system_prompt.py` 상수 추가
`MANDATORY_TOOL_RULES` 정의(현재 `:486~492`) **바로 아래**에 신규 상수를 추가한다. 스타일은 MANDATORY 와 동일 — 선행 `"\n\n"`, `## <HEADER>:` 넘버링. 문구는 lever_test `NUDGE` 의미 보존:

```python
# ── Retrieval-discipline rules (Stage 10 opt-in, 레버 A/B 검증) ──
# 진단(phase0/micro): A 가 넓은 패턴('error')으로 grep→노이즈→"pinpoint 불가"라며
# 좁히지 않고 assertion 없이 종료(empty tattoo)→judge 굶음→final_answer=None.
# 레버 A/B(task A, n=6): finalized 17%→67%(+50pp), empty_tattoo 83%→33%. under-query
# 조기포기 실패 특화 — MANDATORY_TOOL_RULES(단일-needle 전사누락)와 독립.
# run_abc_chain(retrieval_discipline_prompt=True) 가 주입. 선행 "\n\n" 포함.
RETRIEVAL_DISCIPLINE_RULES = (
    "\n\n## RETRIEVAL DISCIPLINE (must follow while the failing item is still unknown):\n"
    "1. A broad search term (e.g. \"error\") returns mostly noise. Do NOT conclude that you "
    "\"cannot pinpoint the cause\" after a broad query returns unrelated volume.\n"
    "2. NARROW the search instead: try exact failure phrases such as \"Failed with result\", "
    "\"Main process exited\", or unit-name patterns like \".service\". Iterate with more specific "
    "patterns until you identify the failing unit.\n"
    "3. You MUST record at least one candidate service unit as a new_assertion before ending a "
    "cycle; never finish a cycle empty-handed while the failing unit is still unknown.\n"
)
```

핵심 문구 보존 확인(Risk 4): `Failed with result`, `Main process exited`, `.service`, `new_assertion`, `never finish` (empty-handed). lever_test `NUDGE` 대비 의미 동일, 표기만 넘버링.

### Step 2 — `orchestrator.py` 파라미터 추가
`run_abc_chain` 시그니처에서 `mandatory_tool_prompt: bool = False,` (현재 `:689`) **바로 아래**에 추가:

```python
    mandatory_tool_prompt: bool = False,
    retrieval_discipline_prompt: bool = False,
```

### Step 3 — `orchestrator.py` 주입 블록 추가
현재 mandatory 주입 블록(`:718~724`) **바로 아래**에 독립 가드 블록 추가 (mandatory 먼저, discipline 나중 — 결정 4):

```python
    if mandatory_tool_prompt:
        from system_prompt import MANDATORY_TOOL_RULES
        prompt = f"{prompt}{MANDATORY_TOOL_RULES}"

    # ── Retrieval-discipline rules (opt-in, Stage 10) ──
    # under-query 조기포기(empty tattoo→None) 실패 모드를 잡는다. 레버 A/B finalized +50pp.
    # 기본 False 시 이 블록을 건너뛰어 prompt 가 변경 전과 byte-identical (불변식).
    if retrieval_discipline_prompt:
        from system_prompt import RETRIEVAL_DISCIPLINE_RULES
        prompt = f"{prompt}{RETRIEVAL_DISCIPLINE_RULES}"
```

## Dependencies

- 외부 패키지: 없음.
- 기존 파일 (read-only): `experiments/exp15_context_router/diagnostics/lever_test.py` (NUDGE 원문 대조용), `experiments/system_prompt.py:486` `MANDATORY_TOOL_RULES` (패턴 참조, **수정 금지**).

## Verification

```bash
# 1. syntax + import (repo root)
python -c "import ast; ast.parse(open(r'experiments/system_prompt.py',encoding='utf-8').read()); ast.parse(open(r'experiments/orchestrator.py',encoding='utf-8').read()); print('syntax OK')"
```

```bash
# 2. 상수 shape + 핵심 문구 보존
python -c "import sys; sys.path.insert(0,'experiments'); from system_prompt import RETRIEVAL_DISCIPLINE_RULES as R; assert R.startswith('\n\n'); [ (lambda s: (s in R) or (_ for _ in ()).throw(AssertionError(s)))(x) for x in ['Failed with result','Main process exited','.service','new_assertion','empty-handed'] ]; print('constant OK', len(R))"
```

```bash
# 3. 파라미터 기본값 False + MANDATORY 무변경
python -c "import sys,inspect; sys.path.insert(0,'experiments'); import orchestrator; p=inspect.signature(orchestrator.run_abc_chain).parameters['retrieval_discipline_prompt']; assert p.default is False; from system_prompt import MANDATORY_TOOL_RULES as M; assert M.count('MANDATORY TOOL-USE RULES')==1; print('param+mandatory-intact OK')"
```

```bash
# 4. 기본 False → prompt byte-identical (주입 스킵)
python -c "src=open(r'experiments/orchestrator.py',encoding='utf-8').read(); assert 'if retrieval_discipline_prompt:' in src; assert 'RETRIEVAL_DISCIPLINE_RULES' in src; print('guard OK')"
```

## Risks

1. **MANDATORY 상수 오염** — 편입하며 위쪽 상수를 실수로 변경. → Verification 3 에서 MANDATORY 텍스트 무변경 확인 + git diff 로 `MANDATORY_TOOL_RULES` 라인 unchanged 확인.
2. **선행 `\n\n` 누락** — append 시 이전 텍스트와 붙어버림. → Verification 2 의 `startswith('\n\n')`.
3. **주입 순서 뒤바뀜** — discipline 을 mandatory 앞에 두면 결정 4 위반. → Step 3 순서 고정, Task 02 순서 assert.

## Scope boundary

**수정 금지**: `MANDATORY_TOOL_RULES` 상수 텍스트/시그니처, `run_abc_chain` 의 다른 경로(error_blocks / extractor / reducer / A·B·C 호출 / model_caller / search_tool / context_router), 실험 드라이버(`run_v*.py`), 결과 JSON. 본 task 는 상수 1개 + 파라미터 1개 + 가드 1개만.
