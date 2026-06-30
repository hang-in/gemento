---
type: plan
status: draft
updated_at: 2026-06-30
slug: exp21-facet-aggregate-tool
version: 1
author: Architect (Windows)
audience: Developer (Sonnet) + 사용자 검토. 실행은 boxie 원격이므로 에이전트 직접 허용.
---

# Stage 9 — Exp21: Facet Aggregate Tool A/B (grep-only vs grep+facet)

## Description

Exp20 진단(2026-06-30, [[exp20-finalization-diagnosis]])에서 megalog(test9ng 30일, 117MB / 1.1M줄 / ~29.3M tok) task A(gohttpserver 크래시루프)가 score 0.0 인 원인이 **스케일/router 실패가 아니라** high-volume(needle 용어가 91% 줄에 등장) + grep_context 16KB 출력 캡 때문에 **모델/judge 가 절단된 firehose 로부터 결론 confidence 를 못 얻어 ABC finalization(`final_answer` set)에 실패**함이 밝혀졌다. router 자체는 정상(grep 1.5~3초, overflow 없음, `gohttpserver.service` 를 assertion 으로 정확히 식별).

가설 **H21**: grep_context 의 16KB 라인 덤프 대신 **결정론적 전수 집계**(매치 총수 + 그룹별 top-N 카운트)를 반환하는 facet 도구를 제공하면, 모델이 절단 없는 깨끗한 집계를 보고 confidence 를 회복하여 finalization(non-null `final_answer`)이 복구된다.

검증: 동일 megalog 2-task 에서 **grep-only(현행) vs grep+facet** A/B. 두 arm 의 유일한 차이는 facet 도구 가용성. 1차 지표 = **non-null ans rate(finalization)**, 2차 = keyword score(Exp19 교훈상 keyword artifact 가능).

⚠ 핸드오프 §4 경고 준수: **"more structure ≠ monotonically better"** — facet 도구는 A/B 가 finalization/score 유의 개선을 보일 때만 채택. 미개선/악화 시 기각하고 그 자체를 결과로 기록(병목이 도구가 아니라 harness 수렴임을 시사).

## Expected Outcome

1. `experiments/tools/context_tools.py` 에 `aggregate_context(handle, pattern, group_by=None, top_n=10)` + 분리된 `FACET_TOOL_SCHEMAS` / `FACET_TOOL_FUNCTIONS` (글로벌 `CONTEXT_TOOL_*` 불변).
2. `experiments/exp15_context_router/native_ollama_caller.py` 에 opt-in 파라미터 `extra_tool_schemas` / `extra_tool_fns`(default None → 거동 byte-identical).
3. `experiments/tests/test_facet_tool.py` — facet 집계 정확성(fixture 의 known top-IP/count) + 회귀 게이트(글로벌 도구 표면 불변, caller default 동치).
4. `experiments/exp15_context_router/run_v21_facet_ab.py` — A/B 드라이버, 결과 JSON `results/exp21_facet_ab_gemma4_e4b.json` (arm별 non-null rate + mean_score).
5. 분석 문서 + researchNotebook H21 verdict.

## Subtask Index

1. **Task 01 — facet 도구 + caller opt-in 플러밍** (`small-medium`, parallel_group A, depends_on: [])
2. **Task 02 — facet 단위 테스트 + 회귀 게이트** (`small`, parallel_group B, depends_on: [01])
3. **Task 03 — A/B 드라이버 `run_v21_facet_ab.py`** (`medium`, parallel_group B, depends_on: [01])
4. **Task 04 — 분석 + H21 verdict** (`small-medium`, parallel_group C, depends_on: [03])

### 의존성

```
Stage 9 (Exp21)

  Group A            Group B (01 후 병렬)          Group C
  ┌────────┐         ┌──────────────────┐          ┌──────────────┐
  │ 01     │────────▶│ 02 tests         │          │              │
  │ facet+ │         │ (회귀 게이트)     │          │ 04 분석+      │
  │ caller │────────▶│ 03 A/B driver    │─────────▶│   H21 verdict │
  └────────┘         └──────────────────┘          └──────────────┘
                       (03 실행 후 결과 JSON → 04)
```

## Constraints

- **`orchestrator.py` 변경 금지.** facet 은 context_tools(도구 정의) + native_ollama_caller(opt-in 주입)에서만. orchestrator 는 `context_router=True` 시 `CONTEXT_TOOL_SCHEMAS` 만 노출하는 현행 경로 그대로.
- **글로벌 `CONTEXT_TOOL_SCHEMAS` / `CONTEXT_TOOL_FUNCTIONS` 불변.** facet 은 `FACET_TOOL_*` 별도 구조 → 타 실험(Exp15~20) 도구 표면 byte-identical.
- native_ollama_caller 의 신규 파라미터는 **default None → 기존 호출부 거동 동치**.
- megalog 재pull 필요(scratchpad 세션별): `ssh test9ng.ddns.net "journalctl --since '30 days ago' --no-pager" > <scratch>/test9ng_journal_30d.raw`. Redis 키 `ctx:test9ng_journal_30d:stdout`(reuse).
- 단일 facet 도구만(`aggregate_context`). `list_failed_units`/`error_type_histogram` 등 다종 추가는 본 A/B 입증 후 후속 plan.

## 결정 — 사용자 위임(Architect default), [[feedback-experiment-philosophy]] 따라 양극 명료 유지

| # | 항목 | 확정값 | 근거 |
|---|------|--------|------|
| 1 | facet 도구 형태 | 단일 `aggregate_context(handle, pattern, group_by=None, top_n=10)` — group_by(capture group regex) 있으면 그룹별 top-N 카운트, 없으면 매치 총수 + 소수 sample 반환. **모두 절단 없는 집계**(16KB 라인덤프 대체) | 단일 도구로 두 task(unit 집계/IP 집계) 동시 커버. 도구 표면 최소화(핸드오프 경고) |
| 2 | opt-in 메커니즘 | 별도 `FACET_TOOL_SCHEMAS`/`FACET_TOOL_FUNCTIONS` + caller `extra_tool_schemas`/`extra_tool_fns`(default None). 글로벌 도구 불변 | 회귀 게이트 trivially 통과, facet 순수 opt-in |
| 3 | A/B 파라미터 | n=5, **max_cycles=8**, retry K=2(`mandatory_tool_prompt=True`), num_ctx 32768, boxie gemma4:e4b, 동일 megalog 2-task. 양 arm 유일 차이 = facet 가용성 | 진단상 max_cycles=5 는 SYNTHESIZE 도달 불가 → 양 arm 0v0 무정보. 8 로 양 arm 에 finalization 기회 부여 |
| 4 | 실행 주체 | boxie 원격이므로 **에이전트 직접 실행 허용** | [[reference-remote-gemma-ssh-tunnel]] line17. 로컬 LLM 로딩만 사용자 |
| 5 | 1차 지표 | **non-null ans rate(finalization)**, score 는 2차 | Exp19 0.7=keyword artifact(실 5/5) 교훈. H21 은 finalization 가설 |
| 6 | 채택 기준 | facet arm 이 grep-only 대비 non-null rate(또는 score) **유의 개선** 시에만 H21 채택. 미개선/악화 → 기각 + "병목=harness 수렴" finding | more structure ≠ monotonically better |

## Non-goals

- `orchestrator.py` ABC 수렴 로직 수정(judge 가 SYNTHESIZE 에서도 final_answer 안 내는 구조 자체) — 별도 사안, 본 A/B 가 facet 으로 우회 가능한지부터 측정.
- facet 도구 다종화(list_failed_units 등) — 입증 후 후속.
- LLM-as-judge 보조 채점 — 보류 항목.
- grep-only full Exp20 베이스라인 별도 완주 — A/B 의 grep-only arm 이 그 베이스라인 역할(사용자 결정).

## Risks

1. **양 arm 모두 finalization 실패(0 vs 0) → A/B 무정보.** 대응: max_cycles=8 로 grep-only 가 ≥SYNTHESIZE 도달 확인(진단 재현), facet arm 이 수렴 회복하는지가 신호. 그래도 0v0 이면 "병목=harness 수렴"이라는 별도 finding(Non-goal 의 orchestrator 사안으로 회부).
2. **소형 모델이 facet 도구를 안/못 씀(under-query at tool-arg level).** 대응: tool description 에 사용 예시 + group_by 예시 regex 명시, `mandatory_tool_prompt=True` 로 도구 사용 유도. 그래도 안 쓰면 그 자체 finding(도구 제공≠사용).
3. **group_by capture-group regex 를 모델이 못 만듦 → 집계 실패.** 대응: group_by 생략 시 count+sample fallback, description 에 예시 제공.
4. **글로벌 `CONTEXT_TOOL_*` 오염 → 타 실험 회귀.** 대응: FACET 완전 분리(글로벌 불변) + task-02 회귀 테스트.
5. **`aggregate_context` 가 117MB 를 매 호출 splitlines → 느림.** 대응: grep_context 와 동일 비용(~2-3초), 허용 범위. 너무 느리면 7d 윈도우.
6. **scorer keyword artifact 지속(Exp19 교훈).** 대응: non-null ans rate 1차 지표, score 2차.

## Sonnet (Developer) 진행 가이드

1. Plan 그대로 — scope 확장 금지. 결정 표 값 변경 금지(이견은 사용자 호출).
2. Group A(task-01) → Group B(task-02, task-03 병렬) → Group C(task-04) 순.
3. 각 task: read → Step 순차 → Verification bash 그대로 실행 → commit → 사용자 confirm.
4. **회귀 게이트 필수**: task-01 후 글로벌 `CONTEXT_TOOL_SCHEMAS`/`FUNCTIONS` 가 byte-identical(facet 은 FACET_* 별도)인지, native caller default 경로가 동치인지 task-02 로 검증. 깨지면 즉시 사용자 호출.
5. task-03 드라이버는 `run_v19_n100_journald.py`/`run_v20_megalog.py` 패턴 복제(로컬 파일→Redis→boxie). A/B 두 arm 은 caller 의 facet 주입 여부로만 분기.
6. **실행(task-03 run)**: boxie 원격이므로 직접 실행 가능. healthcheck(터널 11435 + gemma4:e4b) 선행. stdout block-buffer 주의 → `python -u` 또는 결과 JSON 으로 진척 추적.
7. **Scope boundary 위반 직전(orchestrator.py 수정 필요해 보임)·Verification 실패·Risk 1(0v0) 발견 시 즉시 사용자 호출.**
8. task-04 분석: 실험 실행/결과 존재 후에만. placeholder 금지(실측치). researchNotebook 영문은 Closed-append-only(`gemento-verdict-record` 스킬).

## 변경 이력

- 2026-06-30 v1 초안 — Exp20 finalization 진단 직후 작성(Windows, Architect). 사용자 결정: facet A/B 직행. 설계: 단일 aggregate_context + 분리 FACET_* opt-in + caller 주입.
