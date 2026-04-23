---
type: plan
status: in_progress
updated_at: 2026-04-24
version: 1
---

# Exp08 Math Tool-Use (Calculator + Linalg + LP) + Exp07 정정

## Description

Exp07에서 math-04(LP 최적화) 태스크가 8개 조건(baseline/phase × MAX_CYCLES 8/11/15/20) 모두 **50% 정답률로 완전히 정체**되었다. 루프 수·프롬프트 분화로는 돌파되지 않는 **계산 능력 한계**가 확인되었으므로, E4B에 외부 수학 도구(calculator, solve_linear_system, linprog)를 function-calling 경로로 노출하여 이 벽을 돌파하는 실험을 수행한다.

동시에 Exp07 산출물에서 발견된 두 가지 품질 이슈를 함께 정정한다:
1. `experiments/results/exp07_report.md`가 UTF-16 LE로 저장되어 macOS/Linux 도구에서 깨진 출력. 원인은 Windows PowerShell `>` 리다이렉트의 기본 인코딩. measure.py에 `--output` 옵션을 추가하여 근본 해결.
2. Gemini 핸드오프 문서의 "MAX_CYCLES=15가 포화점" 해석은 `actual_cycles ≈ 7`인 원시 데이터와 어긋남. 정정 섹션 추가.

실험 설계 근거:
- llama.cpp 서버 `/props` 응답에서 `chat_template_caps.supports_tools: true, supports_parallel_tool_calls: true` 확인 — OpenAI 호환 tool_calls 경로 사용 가능.
- math-04는 5변수 선형계획법 문제(3개 ≥10 하한 + 2개 자원 제약 + 3개 비용 함수). 단순 계산기로는 불충분, `scipy.optimize.linprog`이 필요.
- B·C는 도구 없이 유지하여 역할 분리(A=실행자, B=검증자, C=판정자)의 구조적 분리 원칙 보존.

### 가설

**H7**: 외부 수학 도구(calculator + solve_linear_system + linprog)를 A에게 제공하면 math 카테고리 태스크(math-01~04) 평균 정답률이 baseline(tool 미주입 동일 조건) 대비 **+15%p 이상** 상승한다. 특히 math-04에서 tool-use가 50% → ≥80%로 이동한다.

## Expected Outcome

1. `experiments/measure.py`에 `-o/--output PATH` 옵션이 존재하고, 해당 옵션 사용 시 보고서가 UTF-8로 파일에 기록된다.
2. `docs/reference/handoff-to-gemini-exp7-final.md`에 "Loop Saturation 해석 정정" 섹션이 추가되고, `actual_cycles ≈ 7`이 명시된다.
3. `experiments/tools/math_tools.py`가 `calculator`, `solve_linear_system`, `linprog` 3개 함수와 OpenAI tool schema dict를 제공한다. 단위 테스트 통과.
4. `experiments/orchestrator.py:call_model()`이 `tools` 키워드 인자를 받고, `finish_reason=tool_calls` 응답을 올바르게 루프 처리한다. A 경로에서만 tool 주입.
5. `experiments/run_experiment.py`에 `tool-use` 커맨드가 등록되어 있고, math-01~04 × 5 trial × 2 arm(baseline / tooluse) = 40 runs를 실행할 수 있다. 체크포인트 기능 포함.
6. `experiments/measure.py:ANALYZERS`에 `tool_use` 분석기가 등록되어 있고, markdown 보고서에 arm별 정답률·tool call 통계가 출력된다.
7. `docs/reference/handoff-to-gemini-exp8.md`와 `docs/prompts/2026-04-24/run-exp8.md` 완성 — Gemini가 Windows에서 복붙만으로 Exp08을 실행할 수 있다.
8. `experiments/tools/smoke_test.py`가 **실제 llama.cpp 서버로 end-to-end 1회 round-trip**을 성공한다: math-04 프롬프트 → A가 linprog 호출 → 결과 재주입 → final_answer 생성까지.

## Subtasks (Summary)

| # | Title | parallel_group | depends_on |
|---|-------|----------------|------------|
| 01 | Exp07 산출물 정정 (UTF-8 옵션 + 해석 보정) | A | — |
| 02 | Tool 런타임 모듈 (calculator/linalg/linprog) | B | — |
| 03 | Orchestrator tool 통합 (call_model + A 경로) | C | 02 |
| 04 | Exp08 실행 분기 (run_tool_use + tool-use 커맨드) | C | 03 |
| 05 | Measure 분석기 (analyze_tool_use) | D | 04 |
| 06 | Gemini 핸드오프 문서 | D | 04 |
| 07 | 로컬 도구 검증 (smoke test) | — | 03 |

Subtask 01과 02는 서로 독립 — 동시 착수 가능. Subtask 07은 03 완료 직후 실행하여 04로 진입하기 전 관문으로 둔다.

## Constraints

- 기존 실험(baseline / handoff-protocol / loop-saturation 등)에 회귀 없음: `call_model`의 `tools` 인자는 기본값 None.
- Tool 모듈은 **순수 함수**만 — 네트워크·파일 I/O 금지(보안·재현성).
- calculator는 `eval()` 직접 호출 금지. Python AST 화이트리스트(허용 노드: Expression, BinOp, UnaryOp, Num, Constant, Load, 허용 연산자: Add/Sub/Mult/Div/Pow/Mod/USub/UAdd)만.
- scipy.linprog은 `method='highs'` 기본.
- Subtask 07 smoke test가 실패하면 Subtask 04 착수 보류 — llama.cpp 서버의 tool_calls 동작을 먼저 조사.

## Non-goals

- B(비판자)/C(판정자)가 도구로 재검증하는 확장 → Exp08b로 분리.
- Python REPL sandbox, 웹 검색, 파일시스템 도구 → 범위 외.
- logic-04/synthesis-04 개선은 목표 아님 (이미 100%, 회귀 감시 용도로만 동일 arm에 포함).
- Exp07 원시 데이터 재채점·재분석은 범위 외 — 정정은 산출물(해석·보고서) 레벨만.
- Q8_0(llama.cpp) 정밀도 효과를 과거 Q4_K_M(Ollama) 실험과 직접 비교 → 별도 표본 필요, 이번 범위 외.

## Version

- v1 (2026-04-24): 최초 작성. 7 서브태스크, 도구 3종(calculator/linalg/linprog), math-01~04 × 5 trial × 2 arm.
