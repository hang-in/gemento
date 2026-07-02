---
type: plan
status: draft
updated_at: 2026-07-03
slug: exp24-a2a-planner-executor
version: 1
author: Architect (Windows)
audience: Developer (Sonnet) 또는 Architect 직접 진행 + 사용자 검토
parent_strategy: docs/reference/researchNotebook.md
---

# Stage 12 — Exp24: a2a Planner→Executor proposer 분할 (per-attempt overload 우회)

## Description

per-attempt 트랙(§20/§21)이 규명한 것: per-attempt finalization ≈49% 실패의 핵심은 A(제안자)가 답을 알아도 assertion 0개 emit(Exp23 fu_mandatory `used_fu=True asrt=0`). 프롬프트(H22)·retrieval 도구(H23) 둘 다 무개선이었다. 그러나 **싼 falsification(`scoped_emit_probe`, n=20)**이 방향을 열었다: 답을 **clean scoped 입력**으로 handed 하면 A-stage emit 이 **100%**(Wilson [0.84, 1.0]) — broad chain ~49% 와 정반대. 즉 실패는 structural(JSON/스키마 불안정)이 아니라 **broad-context overload**(A 가 decompose + megalog 검색 + propose 를 한 번에). 모델은 좁으면 안정적으로 emit 한다.

본 plan 의 가설(H24): **단일 A 를 Planner→Executor 두 스코프 호출로 분할하면 overload 를 피해 per-attempt finalization 이 오른다.**
- **Planner**: objective + 도구(grep/list_failed_units 등)로 핵심 finding 을 **clean 텍스트**로 산출 (assertion emit 아님, 검색·판단만).
- **Executor**: 그 finding 만 clean scoped 입력으로 받아 `new_assertion` emit (megalog/decompose 없음 = probe 조건 재현).

핵심은 **emit 을 별도 clean 호출로 분리**하는 것 — Exp23 fu_mandatory 가 *같은 호출* 에서 tool 결과 받고 emit 하다 실패한 지점을 정면 우회. B/C 는 무변경(Executor 가 emit 한 assertion 을 그대로 비판·판정).

**정직한 경고**: gemento 이력상 구조 추가는 종종 무효(Reducer H12 음수, Search H13 음수). a2a 도 그럴 수 있고 A-stage 호출을 2배로 늘린다(비용). 단 probe 가 前提를 실증한 유일한 방향이므로 falsify 가치가 있다.

## Expected Outcome

1. `experiments/system_prompt.py` 에 Planner/Executor 프롬프트 빌더 (신규, 기존 프롬프트 무변경).
2. `experiments/orchestrator.py:run_abc_chain` 에 `a2a_proposer: bool = False` opt-in — True 시 A-stage(단일 `run_loop`)를 Planner→Executor 헬퍼로 대체, 동일 `(tattoo, a_log, answer)` shape 반환해 B/C 무변경. 기본 False byte-identical.
3. 회귀 게이트: `experiments/tests/test_a2a_proposer_optin.py` — 기본 False 시 A-stage 경로 불변 + 파라미터/가드 정적 검증.
4. A/B 드라이버 `run_v24_a2a_ab.py`: control(monolithic A) vs a2a(Planner→Executor) × task A × n=15. **파일까지 — 실행은 사용자/에이전트.**
5. 분석 + Stage 12 verdict (H24).

## Subtask Index

1. **Task 01 — Planner/Executor 프롬프트 + a2a proposer 경로** (`system_prompt.py`, `orchestrator.py`). (L, parallel_group A, depends_on: [])
2. **Task 02 — 회귀 게이트** (`tests/test_a2a_proposer_optin.py`). (S, parallel_group B, depends_on: [01])
3. **Task 03 — A/B 드라이버** (`exp15_context_router/run_v24_a2a_ab.py`). (M, parallel_group C, depends_on: [01])
4. **Task 04 — 분석 + Stage 12 verdict** (노트북 + index). (S, parallel_group D, depends_on: [02, 03])

### 의존성

```
Stage 12
  Group A: task-01 (프롬프트 + a2a proposer 경로)
            │
            ├──────────────┐
  Group B: task-02        Group C: task-03
   (regression gate)       (A/B 드라이버 — 사용자 실행)
            │              │
            └──────┬───────┘
  Group D: task-04 (분석 + verdict, 실행 결과 후)
```

Task 01 선행(가장 큰 task). 02·03 병렬. 04 는 둘 다 + 사용자 실행 후.

## Constraints

- **shared code 단일 경로 추가**: `run_abc_chain` 의 A-stage(`run_loop` 호출부, `:823`)에 `if a2a_proposer:` 분기만. B/C/error_blocks/mandatory/discipline/context_router 등 다른 경로 무변경.
- **기본 False 불변식**: `a2a_proposer=False`(기본) 시 A-stage 가 기존 `run_loop` 경로와 완전 동일 — 기존 실험(Exp15~23)/Stage 6~11 byte-identical.
- **Executor 는 probe 조건 재현**: finding 을 clean scoped 입력(objective)으로, 도구 없이, decompose 없이 emit. (probe 100% 의 조건을 벗어나면 가설 검증이 흐려짐.)
- **기존 프롬프트 무변경**: `SYSTEM_PROMPT`/`build_prompt`/critic/judge 손대지 않음. Planner/Executor 는 신규 빌더.
- Executor 출력 schema = 기존 proposer(new_assertions) — `extract_json_from_response` + `apply_llm_response` 재사용(신규 파서 금지).

## 결정 1 — a2a 구현 형태 — **같은 E4B 2 스코프 호출 (Planner 텍스트 → Executor emit)** 확정 (Architect default)
별도 모델/프로세스 아님(A/B/C 가 이미 같은 E4B 다른 역할인 패턴 계승). Executor 는 `run_loop` 를 scoped tattoo(objective=finding)로 재사용 가능 — probe 가 정확히 이 경로로 100% 입증.

## 결정 2 — Planner 출력 — **clean 텍스트 finding (assertion 아님)** 확정 (Architect default)
Planner 는 검색·판단만, emit 은 Executor 전담. `_route_call`(extractor 류) 로 텍스트 생성.

## 결정 3 — 실험 규모 — **task A(crashloop), n=15, 2 arm(control/a2a)** 확정 (Architect default)
per-attempt 병목이 관측된 task A. n=15 는 §20 분산(35~57%) 대비 arm 차이 감지 최소선(caveat 명시). GPU 부하로 arm 순차 preempt 시 단독 러너 대비(§21 교훈).

## 결정 4 — B/C 변경 — **없음** 확정 (Architect default)
본 plan 은 proposer(A) 분할만. Critic/Judge 분할·강화는 범위 밖(별도 plan).

## Non-goals

- 별도 모델/외부 프로세스 a2a (같은 E4B 역할 분할만).
- B/C(critic/judge) 변경.
- Planner 의 정교한 multi-step 계획(본 MVP 는 "finding 1개 추출"까지).
- pre-stage push(Exp23 결정 4) 와의 결합.
- 실험 실행(사용자/에이전트 몫).

## Risks

1. **기본 False 비불변** — a2a 분기가 False 경로에 영향 → 전체 회귀. → Task 02 정적 동치 + `if a2a_proposer:` 가드.
2. **구조 추가 무효(gemento 이력)** — H12/H13 처럼 a2a 도 neutral~음수 가능. → verdict 데이터 따라감, 음수면 "per-attempt = retry 수용" 최종 확정 근거로 정직 기록.
3. **Planner finding 추출 실패 → 실패 이동** — Planner 가 gohttpserver 못 찾으면 Executor 도 빈손(retrieval_gap 재현). → Planner 에 list_failed_units 도구 허용(H23 도구는 우회엔 성공). Planner 실패율도 계측.
4. **Executor 가 clean 입력에도 emit 실패** — probe 는 100% 였으나 실제 finding(노이즈 포함) 입력 시 저하 가능. → Executor 입력을 probe 처럼 최대한 clean 하게 planner 가 정제.
5. **비용 2배** — A-stage 호출 2회. → verdict 에 per-attempt 개선 대비 비용(호출수/latency) 명시. 개선이 retry 보다 저렴할 때만 가치.
6. **B/C 계약 파손** — a2a 경로가 `(tattoo, a_log, answer)` shape 를 안 맞추면 B/C 크래시. → Task 01 에서 run_loop 반환 shape 정확 복제 + Executor 결과를 apply_llm_response 로 tattoo 반영.

## Sonnet (Developer) 진행 가이드

1. Plan 그대로. scope 확장 금지(B/C 변경·별도 모델·multi-step planner 금지).
2. 결정 1~4 변경 금지.
3. Task 01 → (02 ∥ 03) → 04. 각 task: read → Step → Verification → commit → 사용자 confirm.
4. **기본 False 불변식** 최우선 — Task 02 통과 전 Task 04 금지.
5. Executor 는 `scoped_emit_probe.py` 의 경로(scoped tattoo + run_loop, no tools)를 참고해 probe 조건 재현.
6. Executor 출력은 기존 `extract_json_from_response`+`apply_llm_response` 재사용 — 신규 파서 금지.
7. **실험 실행은 사용자/에이전트(cloud/boxie)** — Sonnet 은 드라이버 파일까지. 로컬 LLM 로딩 금지.
8. 테스트 repo root `python -m unittest discover -s experiments/tests -t .`. Verification 실패/Scope 위반/Risk 발견/README 결정 시 사용자 호출.

## 변경 이력

- 2026-07-03 v1: 초안. scoped_emit_probe(scoped emit 100% vs broad 49%)가 a2a 전제(좁으면 안정 emit) 실증 → Planner→Executor 분할로 broad-context overload 우회 falsify. gemento 구조-추가-무효 이력 감안해 MVP(proposer 분할만) + opt-in + 회귀게이트.
