---
type: plan
status: in_progress
updated_at: 2026-04-24
version: 1
---

# Exp08b — Tool-Use Refinement (에러 메시지 + Prompt 강화)

## Description

Exp08에서 H7(외부 수학 도구가 E4B의 계산 한계를 보완한다)은 **+18.3%p**, math-04 0→80%로 채택되었다. 그러나 원시 데이터에서 2가지 부작용이 관찰되었다.

**부작용 1 — Calculator `^` 혼동**
- Tool errors 4건 중 3건이 `calculator`의 `"Disallowed operator: BitXor"`.
- 원인: 모델이 Python `^`(XOR)를 수학적 거듭제곱으로 오인(`2^10` 같은 식 생성).
- AST 화이트리스트는 정확히 차단하고 있으나 에러 메시지가 모델에게 힌트를 주지 못해 수정 재호출이 일어나지 않음.

**부작용 2 — Tool neglect**
- math-04 tooluse trial 2에서 도구가 주입되어 있음에도 모델이 한 번도 호출하지 않고 (total_tool_calls=0) 10 cycle 동안 `None`만 반환 → 실패.
- SYSTEM_PROMPT의 tool-use 가이드가 "권장" 수준이라 LP 같은 structural problem에서도 모델이 수동 시도 후 포기하는 패턴.

Exp08b는 이 2개 이슈를 **최소 침습**으로 개선하고 동일 태스크셋(math-01~04)에서 재측정한다. `tool_choice="required"`나 도구 추가 같은 범위 확대는 의도적으로 배제 — 현 개선만으로 얼마나 회수되는지 먼저 측정.

### 가설

**H8**:
- (a) Calculator `BitXor` 에러 메시지에 `**` 힌트 추가 → calculator 성공률 50% → **≥85%**.
- (b) A 프롬프트의 tool-use 지시 강화(LP는 `linprog` 의무 호출, `^` 금지, 에러 후 재시도 의무) → math-04 tool_neglect 비율 20%(1/5) → **0%**.
- (c) 전체 tooluse arm 정답률 **90% → ≥95%**.

## Expected Outcome

1. `experiments/tools/math_tools.py`의 `calculator` 에러 메시지가 BitXor 사용 시 "use `**` for power; `^` is XOR in Python" 힌트를 포함한다. 기존 다른 disallowed operator 메시지는 그대로.
2. `experiments/system_prompt.py`의 `SYSTEM_PROMPT` 내 Tool-use 섹션이 3가지 새 지시를 포함:
   - LP/최적화 → `linprog` 호출 의무.
   - 거듭제곱은 `**` (절대 `^` 사용 금지).
   - Tool 에러 수신 시 에러 메시지 읽고 재시도 의무 (한 번 실패 후 수동 풀이 금지).
3. `experiments/run_experiment.py`에 `tool-use-refined` 커맨드 등록. 결과 JSON 파일명 접두사는 `exp08b_tool_use_refined`, 체크포인트는 `partial_tool_use_refined.json`. 기존 `tool-use`는 손대지 않음.
4. `experiments/measure.py:analyze_tool_use()`가 `tool_neglect_rate` 메트릭(tool 주입 arm에서 `total_tool_calls == 0 AND (final_answer is None or "")` 비율) 반환. `generate_markdown_report()`의 tool_use 분기에 해당 메트릭 1행 출력 추가.
5. `docs/reference/handoff-to-gemini-exp8b.md` 및 `docs/prompts/2026-04-24/run-exp8b.md` 완성 — Gemini가 Windows에서 복붙해서 바로 실행할 수 있는 절차.

## Subtasks (Summary)

| # | Title | parallel_group | depends_on |
|---|-------|----------------|------------|
| 01 | Calculator 에러 메시지 개선 | A | — |
| 02 | SYSTEM_PROMPT tool-use 가이드 강화 | A | — |
| 03 | Exp08b 실행 분기 (`tool-use-refined`) | B | 01, 02 |
| 04 | Measure에 tool_neglect_rate 추가 | B | 03 |
| 05 | Gemini 핸드오프 문서 | C | 03 |

- Task 01·02는 서로 독립 (tools vs system_prompt). 병렬 가능.
- Task 03은 01·02의 개선이 반영된 상태에서 새 커맨드를 등록.
- Task 04·05는 03 완료 후 병렬 가능.

## Constraints

- 기존 `run_tool_use()`(Exp08) 로직에 회귀 없음 — Exp08b는 별도 함수·커맨드·체크포인트 파일.
- `tool_choice="auto"` 유지. `"required"`는 Exp08c 이후로 연기.
- Calculator 시그니처·반환 타입 변경 금지 — 에러 메시지 문자열만 개선.
- taskset 수정 금지 — Exp08과 동일 태스크로 직접 비교 가능해야 함.
- SYSTEM_PROMPT는 `build_prompt`/`build_prompt_with_phase` 로직 건드리지 않고 **상수만** 수정.
- `max_tool_rounds=5` 유지.

## Non-goals

- `tool_choice="required"` 전략 → Exp08c로 분리.
- 도구 추가(검색, 코드 인터프리터) → Exp09+ 범위.
- math-03 한국어 답변 매칭 이슈 → 본 실험에서는 현상 관찰만 (코드 변경 없음).
- Exp08 원시 데이터 재채점·재분석은 범위 외.
- B/C 역할에 도구 노출 → Exp08d 이후로 분리.

## Version

- v1 (2026-04-24): 최초 작성. 5 서브태스크, 최소 침습 방식, 40 runs 재측정.
