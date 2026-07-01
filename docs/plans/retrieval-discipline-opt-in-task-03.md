---
type: plan-task
status: pending
updated_at: 2026-07-01
parent_plan: retrieval-discipline-opt-in
parallel_group: C
depends_on: [01]
---

# Task 03 — 재검증 A/B 드라이버 준비 (사용자 실행)

## Changed files

- `experiments/exp15_context_router/run_v22_retrieval_discipline.py` (신규) — control vs discipline A/B 정식 드라이버. 진단 스크립트 `lever_test.py` 승격: (a) 수동 `extra_constraint` 주입 대신 **Task 01 의 `retrieval_discipline_prompt=True` 플래그**를 켜서 편입 경로를 직접 검증, (b) n≥10/arm, (c) task A(crashloop) + task B(집계 bruteforce) 둘 다, (d) 결과 JSON 을 scratchpad 아닌 `diagnostics/` 에 저장(durable).

요약: 신규 1, 수정 0. **실행은 사용자** — 본 task 는 드라이버 파일까지.

## Change description

### 배경
레버 A/B(`lever_test.py`)는 (1) n=6 소표본 (2) task A 만 (3) nudge 를 `constraints` 에 **수동 주입**(편입 경로 아님) (4) 결과가 scratchpad(소실). 편입(Task 01) 후 재검증은 **실제 opt-in 플래그 경로**로, n↑ + task B 포함, durable 저장으로 다시 돌린다.

### Step 1 — 드라이버 작성
`run_v21_facet_ab.py` 의 인프라(`BASE_URL`/`MODEL`/`NUM_CTX`/`REDIS_KEY`/`TASKS`/`_healthcheck`/`_load_megalog_to_redis`)를 재사용. arm 은 constraint 주입이 아니라 `run_abc_chain` 플래그로 분기:

- **control arm**: `run_abc_chain(..., mandatory_tool_prompt=True, retrieval_discipline_prompt=False)`
- **discipline arm**: `run_abc_chain(..., mandatory_tool_prompt=True, retrieval_discipline_prompt=True)`

(mandatory 는 양 arm 공통 — 레버 하네스와 동일 조건, discipline 만 토글.) 측정 지표는 lever_test 와 동일: `finalized_rate` / `empty_tattoo_rate`(n_assertions==0) / `correct_rate`. task 별로 정답 키워드 분리 (task A=`gohttpserver`, task B=집계 정답 IP `45.144.212.75` — `run_v21` scorer/verdict 참조).

핵심 파라미터:
```python
N = 10                      # arm 당 (결정 3, ≥10)
MAX_CYCLES = 8
TASK_IDS = ["exp21a_crashloop", "exp21b_bruteforce"]
OUT = Path(__file__).resolve().parent / "diagnostics" / "v22_retrieval_discipline_result.json"
```

결과 JSON 은 `lever_test_result.json` 스키마 확장: task × arm 매트릭스. 증분 저장(매 trial write) — 터널 불안정 대비(핸드오프 §2).

### Step 2 — 실행 안내 주석
파일 상단 docstring 에 사용자 실행 명령 명시:
```
# 사용자 실행 (터널 필요):
#   ssh 터널 (11435) 수립 + curl healthcheck 후:
#   python -u experiments/exp15_context_router/run_v22_retrieval_discipline.py
#   EXP20_LOG_PATH 로 메가로그 경로 오버라이드 가능.
```

## Dependencies

- Task 01 완료 (`retrieval_discipline_prompt` 파라미터 존재 — 없으면 discipline arm 이 control 과 동일).
- 외부: boxie e4b 터널(11435) + Redis 메가로그 키 (핸드오프 §2). **실행 시점에만** 필요 — 파일 작성엔 불필요.
- 기존 파일 (read-only): `run_v21_facet_ab.py`(인프라 재사용), `diagnostics/lever_test.py`(측정 로직 원본), `orchestrator.py:run_abc_chain`.

## Verification

```bash
# 1. syntax + import (LLM/터널 없이 — repo root)
python -c "import ast; ast.parse(open(r'experiments/exp15_context_router/run_v22_retrieval_discipline.py',encoding='utf-8').read()); print('syntax OK')"
```

```bash
# 2. arm 이 플래그로 분기하는지 정적 확인 (수동 constraint 주입 아님)
python -c "s=open(r'experiments/exp15_context_router/run_v22_retrieval_discipline.py',encoding='utf-8').read(); assert 'retrieval_discipline_prompt=True' in s and 'retrieval_discipline_prompt=False' in s; assert s.count('exp21a_crashloop') and s.count('exp21b_bruteforce'); print('arms+tasks OK')"
```

```bash
# 3. (사용자 실행 — 터널 필요) 실제 A/B. Sonnet/Architect 는 실행 금지.
#   python -u experiments/exp15_context_router/run_v22_retrieval_discipline.py
#   → diagnostics/v22_retrieval_discipline_result.json 생성 확인
```

## Risks

1. **에이전트가 실수로 실행** — 긴 실험 + 사용자 VRAM/터널. → Verification 3 은 사용자 전용 명시, Sonnet 진행 가이드 6 준수.
2. **task B scorer 오적용** — 집계 정답 키워드가 task A 와 다름. → `run_v21_facet_ab.py` 의 task B verdict(정답 IP) 그대로 참조, task 별 분리.
3. **control/discipline 조건 불일치** — mandatory 를 한 arm 만 켜면 교란. → 양 arm mandatory=True 공통, discipline 만 토글 (Step 1 명시).
4. **결과 유실** — scratchpad 저장 시 재부팅 소실. → `diagnostics/` 저장 + 증분 write.

## Scope boundary

**수정 금지**: `system_prompt.py`, `orchestrator.py`(Task 01), `run_v21_facet_ab.py`(read-only 재사용), 기존 진단 스크립트/결과. 본 task 는 신규 드라이버 1개만. **실험 실행 금지**(사용자 몫).
