---
type: plan-task
status: pending
updated_at: 2026-06-30
parent_plan: mandatory-tool-opt-in
parallel_group: A
depends_on: []
---

# Task 01 — 코드: MANDATORY_TOOL_RULES 상수 + mandatory_tool_prompt 파라미터 + 주입 로직

## Changed files

- `experiments/system_prompt.py` (수정) — `MANDATORY_TOOL_RULES` 문자열 상수 추가 (source-of-truth).
- `experiments/orchestrator.py` (수정) — `run_abc_chain` 에 `mandatory_tool_prompt: bool = False` 파라미터 + True 시 prompt 주입.
- (선택, behavior 불변) `experiments/exp15_context_router/run_v16b_mandatory.py`, `run_v16c_combined.py` — 로컬 `MANDATORY_BLOCK` 을 `from system_prompt import MANDATORY_TOOL_RULES` 로 교체. **run_v17_hardtasks.py 의 블록은 변형(multi-finding 용)이라 교체하지 않음** (Risk 2).

> 신규 0, 수정 2 (+ 선택 2).

## Change description

### 배경
mandatory 블록이 드라이버 3곳에 복붙됨. v16b/v16c 의 블록은 **동일**하고 (1-needle 전사-fix, 검증된 +57pp), v17 의 블록은 **변형**(multi-finding aggregation 용 — "issue MULTIPLE greps", "Report ALL required items"). canonical 상수는 **v16b/v16c 버전**으로 한다 (검증된 효과의 source).

### Step 1 — system_prompt.py 에 상수 추가
`run_v16b_mandatory.py` 의 `MANDATORY_BLOCK` 문자열을 **문자 단위 그대로** 옮겨 `MANDATORY_TOOL_RULES` 상수로 정의. (선행 `\n\n` 포함 여부는 주입 로직에서 일관 처리.)

```python
# system_prompt.py
MANDATORY_TOOL_RULES = (
    "\n\n## MANDATORY TOOL-USE RULES (must follow):\n"
    "1. You MUST call `grep_context` on the given handle BEFORE answering. Do NOT answer from memory or assumption.\n"
    "2. Start by grepping for error markers, e.g. pattern \"error\" or \"E0432\". The raw log is NOT in your prompt — you can only see it via the tools.\n"
    "3. Do NOT conclude \"the log does not contain ...\" after a single query. If a grep returns no useful match, try another pattern (\"unresolved\", \"import\", a filename) before giving up.\n"
    "4. Once you find the matching line, transcribe the EXACT file path, line number, and module identifier verbatim from that line into your final_answer. Do not paraphrase or omit any of the three.\n"
)
```

### Step 2 — run_abc_chain 파라미터 추가
`run_abc_chain` 시그니처 (현재 `context_router` / `context_handles` / `error_blocks` 파라미터 인근) 에 추가:

```python
    mandatory_tool_prompt: bool = False,
```

### Step 3 — 주입 로직 (error_blocks 주입 직후, 멱등)
`run_abc_chain` 의 error_blocks pre-extraction 블록 직후 (extractor_pre_stage 앞) 에 추가:

```python
    if mandatory_tool_prompt:
        from system_prompt import MANDATORY_TOOL_RULES
        prompt = f"{prompt}{MANDATORY_TOOL_RULES}"
```

- `False` (기본) 시 이 블록을 건너뛰어 prompt 가 **변경 전과 동일** (불변식).
- error_blocks 주입과 순서 충돌 없음 (둘 다 prompt append, 독립). 단일 지점.

### Step 4 — (선택) 드라이버 중복 제거
`run_v16b_mandatory.py` / `run_v16c_combined.py` 의 로컬 `MANDATORY_BLOCK` 정의 삭제 후 `from system_prompt import MANDATORY_TOOL_RULES as MANDATORY_BLOCK` 로 교체. **문자 단위 일치 확인 후에만** (Risk 2). v17 은 변형이라 그대로 둔다.

## Dependencies
- 기존 파일 (read-only): `run_v16b_mandatory.py` (블록 source).
- 외부 패키지: 없음.

## Verification

```bash
# 1. syntax
D:/privateProject/gemento/.venv/Scripts/python.exe -c "import ast; ast.parse(open('experiments/system_prompt.py',encoding='utf-8').read()); ast.parse(open('experiments/orchestrator.py',encoding='utf-8').read()); print('syntax OK')"
```

```bash
# 2. import + 상수 존재
cd experiments && D:/privateProject/gemento/.venv/Scripts/python.exe -c "from system_prompt import MANDATORY_TOOL_RULES; print('len', len(MANDATORY_TOOL_RULES)); assert 'transcribe' in MANDATORY_TOOL_RULES; print('OK')"
```

```bash
# 3. 파라미터 존재 + 기본 False
cd experiments && D:/privateProject/gemento/.venv/Scripts/python.exe -c "import inspect, orchestrator; sig=inspect.signature(orchestrator.run_abc_chain); p=sig.parameters['mandatory_tool_prompt']; print('default', p.default); assert p.default is False; print('OK')"
```

```bash
# 4. (선택) 드라이버 상수 문자 일치 (Step 4 수행 시)
cd experiments && D:/privateProject/gemento/.venv/Scripts/python.exe -c "from system_prompt import MANDATORY_TOOL_RULES; import pathlib; print('matches v16b block:', 'MANDATORY TOOL-USE RULES' in MANDATORY_TOOL_RULES)"
```

## Risks
1. **기본 False 불변식 깨짐** — 주입 if 문이 False 경로 prompt 를 건드리면 안 됨. Step 3 의 `if mandatory_tool_prompt:` 가드 필수.
2. **상수 문자 drift** — Step 1 에서 v16b 블록을 그대로 복사 (escape `\"` 포함). 미세 차이 시 Exp16b/c 재현 불가.
3. **주입 중복** — caller 가 이미 prompt 에 mandatory 를 넣고 파라미터도 True 면 이중 주입. 문서에 "둘 중 하나만" 명시 (Task 03).

## Scope boundary
**수정 금지**: `run_abc_chain` 의 A/B/C 호출 로직, model_caller 경로, search_tool/extractor/reducer 경로, `native_ollama_caller.py`, `run_v17_hardtasks.py` 의 블록, 결과 JSON. retry-on-None 편입 금지 (본 plan 범위 밖).
