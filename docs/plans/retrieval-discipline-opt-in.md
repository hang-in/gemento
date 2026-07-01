---
type: plan
status: draft
updated_at: 2026-07-01
slug: retrieval-discipline-opt-in
version: 1
author: Architect (Windows)
audience: Developer (Sonnet) 또는 Architect 직접 진행 + 사용자 검토
parent_strategy: docs/reference/handoff-to-next-agent.md
---

# Stage 10 — 오케스트레이터 신뢰성: retrieval-discipline nudge opt-in 편입

## Description

Stage 9 이후 착수한 **오케스트레이터 신뢰성**(확률적 finalization) 트랙의 근본 원인 진단이 끝났다. Phase 0/마이크로 진단(메모리 [[phase0-finalization-rootcause]], `diagnostics/`)에서 밝혀진 결론: `final_answer=None` 의 진짜 원인은 judge 가 아니라 **상류 A(제안자)가 ~50% chain 에서 assertion 0개 emit(empty tattoo)** 이고, 그 A-stage 실패의 메커니즘은 **under-query + 조기 포기** — 넓은 패턴(`error`, gohttpserver 로그엔 없음)으로 grep→노이즈→"pinpoint 불가"라며 구체 패턴(`Failed with result`/`.service`)으로 **좁히지 않고** assertion 없이 종료. 이는 Exp14(H13 insufficient retrieval iterations) + under-query 약점의 finalization 렌즈 재출현이다. judge/tool-channel/schema 문제가 아니다.

가장 싼 레버(anti-give-up + narrow-query nudge, 프롬프트 only)를 **레버 A/B (task A crashloop, n=6/arm, 2026-07-01)** 로 falsify 한 결과가 결정적이다:

```
             finalized   empty_tattoo   correct
  control      17%          83%          17%
  nudge        67%          33%          50%
  Δ           +50pp        -50pp        +33pp
```

포기(empty-tattoo)를 정확히 절반으로 줄여 finalized +50pp / correct +33pp — **겨냥한 메커니즘대로** 작동. 원본 결과 `experiments/exp15_context_router/diagnostics/lever_test_result.json`. (소표본 n=6, nudge 도 2/6 여전히 포기 + 1건 assertion 과잉생성 오답 → 완전 해결 아닌 ~절반 개선.)

본 plan 은 이 검증된 nudge 문구를 진단 스크립트에서 **공유 코드(`system_prompt.py`)의 canonical 상수 + `run_abc_chain` 의 opt-in 파라미터**로 정식 승격한다.

**핵심 결정 (안 A — 별도 독립 플래그)**: 기존 `MANDATORY_TOOL_RULES` 에 **병합하지 않는다.** nudge 는 under-query 실패(집계/대형 로그) 특화이고, `MANDATORY_TOOL_RULES` 는 단일-needle 전사누락 특화(Exp16b 27→83% 검증)다. 병합 시 (a) Exp16b 검증 경로를 byte-identical 로 깨고 (b) 단일-needle task 에 nudge 노이즈를 주입할 위험이 있다. 따라서 **별도 상수 + 별도 `retrieval_discipline_prompt: bool = False` 파라미터**로 독립 토글한다. Stage 8 opt-in 패턴을 그대로 복제 — 기본 False → 거동 byte-identical.

## Expected Outcome

1. `experiments/system_prompt.py` 에 canonical `RETRIEVAL_DISCIPLINE_RULES` 문자열 상수 (lever_test.py `NUDGE` 검증 문구를 `MANDATORY_TOOL_RULES` 스타일로 정형화, 의미 무변경).
2. `experiments/orchestrator.py:run_abc_chain` 에 `retrieval_discipline_prompt: bool = False` 파라미터 + True 일 때만 prompt 에 주입하는 로직 (mandatory 주입 직후 동일 패턴, 독립 가드).
3. 회귀 게이트: `experiments/tests/test_retrieval_discipline_optin.py` — 기본 False 시 byte-identical, True 시 정확히 1회 append, 두 플래그(mandatory + discipline) 조합의 순서·멱등 검증. 기존 `test_mandatory_optin` 도 함께 통과(56 OK 회귀 없음).
4. 재검증 A/B 드라이버 (lever_test → 정식 드라이버 승격, n≥10/arm, task A + task B). **파일만 준비 — 실행은 사용자.**
5. 문서: "언제 켜나" 가이드 (conceptFramework / 연구노트) + Stage 10 verdict 기록 (재검증 결과 후).

## Subtask Index

1. **Task 01 — 코드: 상수 + 파라미터 + 주입 로직** (`system_prompt.py`, `orchestrator.py`). (M, parallel_group A, depends_on: [])
2. **Task 02 — 회귀 게이트 + opt-in 동작 검증** (`experiments/tests/test_retrieval_discipline_optin.py`). (S, parallel_group B, depends_on: [01])
3. **Task 03 — 재검증 A/B 드라이버 준비** (`experiments/exp15_context_router/`, lever_test 승격, n↑ + task B). 사용자 실행. (S, parallel_group C, depends_on: [01])
4. **Task 04 — 문서 + Stage 10 verdict** (conceptFramework / 연구노트 / index). 재검증 결과 반영. (S, parallel_group D, depends_on: [02, 03])

### 의존성

```
Stage 10
  Group A: task-01 (code: 상수 + 파라미터 + 주입)
            │
            ├──────────────┐
  Group B: task-02        Group C: task-03
   (regression gate)       (재검증 A/B 드라이버 — 사용자 실행)
            │              │
            └──────┬───────┘
  Group D: task-04 (docs + Stage 10 verdict, 재검증 결과 후)
```

Task 01 이 선행. Task 02(테스트)와 Task 03(재검증 드라이버)은 01 이후 **병렬 가능**. Task 04 는 둘 다 완료 + 재검증 결과 후.

## Constraints

- **공유 코드 단일 경로 수정**: `run_abc_chain` 의 prompt 주입 영역만 (mandatory 주입 직후). 다른 경로 (A/B/C 호출, model_caller, search_tool, extractor/reducer, context_router) 변경 금지.
- **기본 False 불변식**: `retrieval_discipline_prompt=False` (기본) 시 prompt / 거동이 변경 전과 **완전히 byte-identical** 해야 한다. 기존 exp 드라이버 / Stage 6~9 영향 0.
- **MANDATORY_TOOL_RULES 무변경**: 기존 상수 텍스트·시그니처 손대지 않는다 (Exp16b 검증 보존, Risk 2).
- **nudge 문구는 lever_test.py `NUDGE` 검증 버전 그대로** (정형화는 표기 스타일만 — 핵심 문구 `Failed with result`/`Main process exited`/`.service`/`new_assertion`/"never finish empty-handed" 보존, 의미 수정 금지).
- **자동 게이트 금지**: opt-in 파라미터까지만. "언제 켤지" 자동 휴리스틱은 범위 밖 (별도 plan).

## 결정 1 — 편입 방식 — **안 A (별도 독립 opt-in 파라미터)** 확정 (Architect default)
`MANDATORY_TOOL_RULES` 병합(안 B) 미채택 — Exp16b byte-identical 파괴 + 단일-needle 노이즈 위험. Stage 8 opt-in 패턴 복제, 독립 플래그.

## 결정 2 — 상수 위치/이름 — **`system_prompt.py` / `RETRIEVAL_DISCIPLINE_RULES`** 확정 (Architect default)
`MANDATORY_TOOL_RULES` 바로 아래. 선행 `"\n\n"` 포함 (caller prompt 끝 append 용, 동일 관례).

## 결정 3 — 재검증 규모 — **n≥10/arm, task A(crashloop) + task B(집계) 둘 다** 확정 (Architect default)
레버 A/B 는 n=6 task A 만 — 소표본. 편입 후 재검증은 n 상향 + task B 포함으로 일반화 확인. **실행은 사용자** (에이전트는 드라이버 파일만).

## 결정 4 — 두 플래그 조합 시 주입 순서 — **mandatory 먼저, discipline 나중** 확정 (Architect default)
둘 다 True 인 caller 를 위해 결정적 순서 고정. 회귀 테스트로 순서·멱등 assert (Task 02).

## Non-goals

- 자동 (신호 기반) 게이트 / 임계 — 별도 plan.
- `MANDATORY_TOOL_RULES` 개선·수정.
- a2a (planner→executor 분리) — 가장 비싼 레버, 싼 레버로 충분한지 본다 (핸드오프 §4.4).
- facet 강제 (Exp21 `aggregate_context` 사용 강제) — 별도 후속 레버.
- nudge 문구 자체의 추가 실험/개선 — 검증 버전 보존.
- 재검증 실험 **실행** (사용자 몫) — 본 plan 은 드라이버 파일까지.

## Risks

1. **기본 False 비불변** — 주입 로직이 False 경로에 영향 주면 전체 실험 회귀. → Task 02 정적 동치 테스트로 차단.
2. **MANDATORY 상수 오염** — 편입 중 실수로 기존 상수 텍스트 변경 시 Exp16b 재현 불가. → Task 01 에서 `MANDATORY_TOOL_RULES` diff 0 확인, Task 02 에서 기존 `test_mandatory_optin` 재통과.
3. **두 플래그 순서 비결정** — mandatory + discipline 동시 True 시 순서가 caller 별로 달라지면 재현성 붕괴. → 결정 4 고정 + Task 02 순서 assert.
4. **nudge 문구 drift** — 정형화하며 검증 문구가 미세 변형되면 레버 효과 재현 불가. → Task 01 에서 lever_test `NUDGE` 핵심 문구 문자 단위 보존 확인.
5. **재검증이 편입 효과를 재현 못 함** — n↑/task B 에서 nudge 효과가 소멸하면 편입 근거 약화. → Task 04 는 재검증 결과 후 verdict, 음수면 조건부/롤백 명시. plan 은 편입까지, verdict 는 데이터 따라감.

## Sonnet (Developer) 진행 가이드

본 plan 은 Stage 8 과 규모·구조가 동일 — Architect 직접 진행도 가능. Sonnet 위임 시:

1. Plan 그대로. scope 확장 금지 (자동 게이트 / MANDATORY 수정 / a2a 금지).
2. 결정 1~4 변경 금지.
3. Task 01 → (02 ∥ 03) → 04. 각 task: read → Step → Verification → commit → 사용자 confirm.
4. **기본 False 불변식**이 최우선 — Task 02 통과 전 Task 04 진행 금지.
5. `MANDATORY_TOOL_RULES` 는 read-only. lever_test.py `NUDGE` 핵심 문구 보존 확인 (Risk 2/4).
6. **재검증 실행은 사용자** — Sonnet/Architect 는 Task 03 드라이버 파일까지. 로컬 LLM 로딩 금지. cloud 터널(boxie e4b) 필요 시 healthcheck 만.
7. 테스트는 repo root 에서 `python -m unittest discover -s experiments/tests -t .` (56 OK 기대 + 신규 테스트).
8. Verification 실패 / Scope boundary 위반 직전 / Risk 발견 / README·conceptFramework 갱신 결정 시 사용자 호출.

## 변경 이력

- 2026-07-01 v1: 초안. 오케스트레이터 신뢰성 근본원인(under-query 조기포기) 진단 + 레버 A/B(finalized +50pp) 결과 후, narrow-query nudge 를 Stage 8 opt-in 패턴으로 별도 독립 플래그(안 A) 편입 확정. MANDATORY 병합(안 B)은 Exp16b 파괴 위험으로 미채택.
