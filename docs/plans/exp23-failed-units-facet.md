---
type: plan
status: draft
updated_at: 2026-07-02
slug: exp23-failed-units-facet
version: 1
author: Architect (Windows)
audience: Developer (Sonnet) 또는 Architect 직접 진행 + 사용자 검토
parent_strategy: docs/reference/researchNotebook.md
---

# Stage 11 — Exp23: list_failed_units facet 레버 (per-attempt retrieval_gap 우회)

## Description

오케스트레이터 신뢰성 트랙 종결(§20) 이후 후속 진단(`per_attempt_diag.py`, pooled n=9)이 per-attempt 실패의 실체를 규명했다: **실패 7/7 이 retrieval_gap** — 모델이 넓은 패턴(`error`)만 3~8회 반복 grep 하고 `gohttpserver` 를 못 띄운 채 종료. emission_gap(찾고도 커밋 실패, Exp16b 영역)은 **0건**. 성공 chain 은 예외 없이 tool 이 답을 retrieve(grep_hit=1). 즉 per-attempt 병목은 **query-formulation(검색어 형성)** 능력이고, 이걸 프롬프트로 고치려던 narrow-query nudge 는 **H22 에서 반증**됐다.

본 plan 의 가설(H23): **"좁혀라"라고 말하는 대신, 실패 unit 을 결정론적으로 직접 건네면(쿼리 형성 우회) per-attempt finalization/accuracy 가 오른다.** 신규 도구 `list_failed_units(handle, top_n)` = **인자 없는 preset** — 내부에서 systemd 실패 신호(`Failed with result` / `Main process exited` / `start-limit` + `(\S+\.service)`)를 untruncated 전수 집계해 top-N 실패 unit 을 반환. `aggregate_context`(H21)와 달리 모델이 pattern/group_by 를 formulate 할 필요가 없다 — retrieval_gap 을 정면 우회.

**H21 경고 반영**: Exp21 에서 task A(single-needle)는 모델이 facet 을 거의 안 썼다(3 calls, 무효). 따라서 "도구 제공"만으로는 부족할 수 있어, A/B 에 **fu_mandatory arm**(드라이버가 constraint 로 "먼저 `list_failed_units` 호출" 주입)을 필수 포함해 "사용 강제 시 효과"를 분리 측정한다.

**격리 원칙**: FACET_TOOL(H21) opt-in 패턴을 그대로 복제 — 별도 `FAILED_UNITS_TOOL_SCHEMAS/FUNCTIONS`, 글로벌 `CONTEXT_TOOL_*` 불변(byte-identical). shared code 변경은 `context_tools.py` + `tools/__init__.py` **단일 파일군에 국한**(orchestrator/system_prompt 무변경).

## Expected Outcome

1. `experiments/tools/context_tools.py` 에 `list_failed_units(handle, top_n=10)` 함수 + `FAILED_UNITS_TOOL_SCHEMAS/FUNCTIONS` (글로벌 분리 opt-in).
2. `experiments/tools/__init__.py` export 추가 (글로벌 목록 불변).
3. 회귀 게이트: `experiments/tests/test_failed_units_tool.py` — 글로벌 CONTEXT_TOOL_* 불변 + FU 분리 + fixture 집계 정확성.
4. A/B 드라이버 `run_v23_failed_units_ab.py`: control(grep_only) / fu_offered / fu_mandatory × task A × n=15. **파일까지 — 실행은 사용자/에이전트.**
5. 분석 + Stage 11 verdict (H23) 기록.

## Subtask Index

1. **Task 01 — 도구 구현 + export** (`context_tools.py`, `tools/__init__.py`). (M, parallel_group A, depends_on: [])
2. **Task 02 — 회귀 게이트** (`tests/test_failed_units_tool.py`). (S, parallel_group B, depends_on: [01])
3. **Task 03 — A/B 드라이버 (3 arm)** (`exp15_context_router/run_v23_failed_units_ab.py`). (M, parallel_group C, depends_on: [01])
4. **Task 04 — 분석 + Stage 11 verdict** (노트북 + index). (S, parallel_group D, depends_on: [02, 03])

### 의존성

```
Stage 11
  Group A: task-01 (도구 + export)
            │
            ├──────────────┐
  Group B: task-02        Group C: task-03
   (regression gate)       (3-arm A/B 드라이버 — 사용자 실행)
            │              │
            └──────┬───────┘
  Group D: task-04 (분석 + verdict, 실행 결과 후)
```

Task 01 선행. 02(테스트)·03(드라이버) 병렬. 04 는 둘 다 + 사용자 실행 결과 후.

## Constraints

- **shared code 단일 파일군**: `context_tools.py` + `tools/__init__.py` 만. **orchestrator.py / system_prompt.py 무변경.**
- **글로벌 불변식**: `CONTEXT_TOOL_SCHEMAS/FUNCTIONS`(read_context/grep_context)와 `FACET_TOOL_*`(aggregate_context) 텍스트·구성 무변경 — 기존 실험(Exp15~22) byte-identical.
- **fu_mandatory 프롬프트는 드라이버 레벨** (constraints 주입) — system_prompt 공유코드에 넣지 않는다.
- `list_failed_units` 는 untruncated(top_n 행만 반환 → 출력 항상 작음), 16KB 캡 없음 — aggregate_context 철학 계승.
- 실패 신호 패턴은 systemd 표준(`Failed with result`/`Main process exited`/`start-limit`/`.service`) — 임의 확장 금지, 본 벤치(test9ng 저널) 재현 우선.

## 결정 1 — 레버 형태 — **인자 없는 preset 도구 (opt-in)** 확정 (Architect default)
`aggregate_context` 재사용(모델이 pattern/group_by formulate)이 아니라 신규 preset — retrieval_gap 진단이 "모델이 쿼리를 못 만든다"이므로 formulate 부담 0 이 핵심.

## 결정 2 — 사용 강제 — **fu_offered + fu_mandatory 양 arm** 확정 (Architect default)
H21 저사용 경고 → "제공 시 효과"와 "강제 시 효과"를 분리. mandatory 는 드라이버 constraint 주입(공유코드 아님).

## 결정 3 — 실험 규모 — **task A(crashloop), n=15/arm, 3 arm** 확정 (Architect default)
retrieval_gap 은 task A 에서 관측됨. task B(집계)는 H21 이 이미 다룸 → 본 plan 제외. n=15 는 per-attempt(~49%) 대비 arm 차이 감지 최소선. 소표본 caveat 명시.

## 결정 4 — pre-stage 스캐폴드(auto-inject) — **본 plan 제외 (후속 후보)** 확정 (Architect default)
실패 unit 을 orchestrator 가 자동 주입하는 push 변종은 orchestrator.py 변경 → single-path 원칙상 별도 plan. 본 plan 은 tool(pull) 접근만.

## Non-goals

- orchestrator pre-stage 스캐폴드(auto-inject) — 결정 4, 별도 plan.
- system_prompt 공유코드에 mandatory-use 규칙 상시 편입 — 본 plan 은 드라이버 레벨 A/B 까지.
- task B(집계) — H21 영역.
- `aggregate_context`/글로벌 도구 수정.
- 실험 실행(사용자/에이전트 몫) — 본 plan 은 드라이버 파일까지.

## Risks

1. **글로벌 불변 파괴** — 신규 도구 추가 중 CONTEXT_TOOL_*/FACET_TOOL_* 오염. → Task 02 정적 테스트로 글로벌 목록·텍스트 무변경 assert.
2. **모델이 fu_offered 에서도 도구 미사용** (H21 재현) → fu_offered 무효. → fu_mandatory arm 이 "강제 시 효과"를 분리 측정. offered 무효/mandatory 유효면 = "사용 강제가 관건" 결론.
3. **fu_mandatory 도 미개선** — 실패 unit 을 건네도 finalize 못 하면 = retrieval 넘어선 병목(judge/synthesize). → per-attempt_diag 의 emission_gap 0 과 배치 확인, verdict 에서 재프레이밍.
4. **실패 신호 패턴이 test9ng 저널과 불일치** — gohttpserver crashloop 이 표준 systemd 신호로 안 잡히면 도구가 빈손. → Task 01 Verification 에서 실제 메가로그(또는 fixture)로 gohttpserver 반환 확인 필수.
5. **소표본(n=15) + 단일 task** — per-attempt 고분산(35~57%, §20) 감안 시 검정력 한계. → verdict 조건부/방향 명시, control 재확인 병행.

## Sonnet (Developer) 진행 가이드

1. Plan 그대로. scope 확장 금지 (orchestrator pre-stage / system_prompt 편입 / task B 금지).
2. 결정 1~4 변경 금지.
3. Task 01 → (02 ∥ 03) → 04. 각 task: read → Step → Verification → commit → 사용자 confirm.
4. **글로벌 불변식**이 최우선 — Task 02 통과 전 Task 04 진행 금지.
5. FACET_TOOL(H21) 패턴을 정확히 미러 — 별도 스키마/함수 dict, `__init__` export, 글로벌 목록 무변경.
6. **실험 실행은 사용자/에이전트(cloud/boxie)** — Sonnet 은 드라이버 파일까지. 로컬 LLM 로딩 금지.
7. 테스트는 repo root `python -m unittest discover -s experiments/tests -t .` (62 OK + 신규).
8. Verification 실패 / Scope boundary 위반 직전 / Risk 발견 / README·conceptFramework 갱신 결정 시 사용자 호출.

## 변경 이력

- 2026-07-02 v1: 초안. per_attempt_diag(pooled n=9) retrieval_gap 7/7·emission_gap 0 확인 후, 프롬프트(H22 반증) 대신 결정론적 preset 도구(list_failed_units)로 쿼리 형성 우회. FACET(H21) opt-in 패턴 복제, orchestrator 무변경. H21 저사용 경고로 fu_mandatory arm 필수.
