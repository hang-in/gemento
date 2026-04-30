---
type: plan
status: done
updated_at: 2026-04-30
slug: phase-1-taskset-3-fail-exp09-5-trial-exp10-v3
version: 1
---

# Phase 1 후속 정리 — Taskset 3 FAIL 수정 + Exp09 5-trial 분석 + Exp10 v3 재산정

## Description

직전 commit `3ed255a windows` 의 Phase 1 산출물 (v2 regression / taskset validate / Exp09 5-trial stats) 의 미해결 항목 + Exp10 v3 결과 영향까지 한 사이클로 정리:

1. **Taskset 3 FAIL** — Phase 1 validate_taskset 결과 22 task 중 3건 FAIL.
   - `math-03`: prompt 의 연립방정식이 **해 없음** (4r+6s+8rect=96 + r+s+rect=15 + rect=r-1 → 0r=8 모순). expected/constraints 만 정정으론 불가, **prompt 본문 변경 필요** — 사용자 결정 의존
   - `synthesis-04`: keyword `'report 5'` / `'report 6'` 가 expected `'Reports 5 and 6'` 에 substring 매칭 실패 (복수형 + 중간 '5 and')
   - `longctx-medium-2hop-02`: keyword group 2 `'500 hp'` 가 expected `'500 horsepower'` 에 토큰 부재
2. **Exp09 5-trial 점수 하락 원인 분석** — 3-trial → 5-trial 시 양 arm 동시 0.353/0.340 하락. 원인 후보 (a) 환경 차이 / (b) 모델 비결정성 / (c) 시스템 결함 결정.
3. **Exp10 v3 재산정** — Subtask 1 의 taskset 정정 중 `math-03` + `synthesis-04` 가 Exp10 task subset 포함. 정정 후 v3 rescored 재실행 + 보고서/노트북/README 일관성 회복.

**범위 외**: Mixed Intelligence (Phase 2/A) 는 본 plan 결과 보고 후 별도 plan.

## Expected Outcome

1. `experiments/tasks/taskset.json` — math-03 / synthesis-04 정정
2. `experiments/tasks/longctx_taskset.json` — longctx-medium-2hop-02 정정
3. `experiments/validate_taskset.py` 재실행 시 **22/22 PASS**
4. `experiments/exp09_longctx/analyze_5trial_drop.py` (또는 `analyze_stats.py` 옵션) — trial 1-3 vs 4-5 비교
5. `docs/reference/exp09-5trial-drop-analysis-2026-04-30.md` — 5-trial 하락 원인 분석 보고서
6. `experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_<TS>.json` — taskset 정정 적용한 v3 재산정 (canonical 갱신)
7. `docs/reference/results/exp-10-reproducibility-cost.md` — §2/§3 mean_acc / per-task 표 갱신, Δ disclosure
8. `docs/reference/researchNotebook.md` Exp09 + Exp10 섹션 갱신
9. `docs/reference/results/exp-09-longctx.md` 갱신
10. `README.md` / `README.ko.md` — Exp10 수치 변동 시 Headline / H1 evidence 갱신 (한·영 동기화)
11. 영문 `researchNotebook.en.md` — Exp09 / Exp10 v3 재산정 note 추가만 (Closed 추가만 정책)

## Subtask Index

1. [task-01](./phase-1-taskset-3-fail-exp09-5-trial-exp10-v3-task-01.md) — Taskset 3 FAIL 수정 (S, 정적, parallel_group A, depends_on: [])
2. [task-02](./phase-1-taskset-3-fail-exp09-5-trial-exp10-v3-task-02.md) — Exp09 5-trial 점수 하락 원인 분석 (M, parallel_group B, depends_on: [])
3. [task-03](./phase-1-taskset-3-fail-exp09-5-trial-exp10-v3-task-03.md) — Exp10 v3 재산정 (S, parallel_group A, depends_on: [01])
4. [task-04](./phase-1-taskset-3-fail-exp09-5-trial-exp10-v3-task-04.md) — 문서 갱신 통합 (M, parallel_group C, depends_on: [02, 03])

### 의존성 (Stage 기반)

```
Stage 1 (병렬):
  Group A:                  Group B:
    task-01 (Taskset 수정)    task-02 (Exp09 5-trial 분석, 사용자)
       │                          │
       ▼                          │
    task-03 (Exp10 v3 재산정,     │
            사용자)                │
       │                          │
       └────────────┬─────────────┘
                    ▼
            Stage 2 (단독):
              task-04 (문서 갱신, 한·영)
```

Group A 직렬 (Taskset → Exp10 v3), Group B 독립 (Exp09 5-trial). Task 04 가 합류.

## Constraints

- 사용자 정책 메모리 준수:
  - 메인 단일 흐름 (브랜치 분기 금지)
  - Architect/Developer/Reviewer/사용자 분리 — 본격 분석/실행 (Subtask 2/3) 사용자 직접
- score_answer_v3 / `experiments/measure.py` 변경 0
- `experiments/exp09_longctx/run.py` / `run_append_trials.py` 변경 0
- `experiments/exp10_reproducibility_cost/rescore_v3.py` 변경 0 (재실행만)
- v2 final / v3 rescored (이전 053939) / 5-trial / Exp06 reconciliation / 다른 결과 JSON 모두 read-only
- 영문 노트북 Closed 추가만 정책 — 기존 영문 수치 변경 0
- math-03 prompt 본문 변경은 **사용자 결정 의존** (task-01 의 두 옵션 중 사용자 선택)
- Exp10 v3 새 결과의 README 반영은 변동 크기 기반 결정 — 사소하면 disclosure 만, 의미 있으면 Headline / H1 evidence 갱신

## Non-goals

- Mixed Intelligence (Judge C 강한 모델 교체) — Plan #1 결과 보고 후 별도 큰 plan
- Exp09 6-trial+ 추가 실행
- Exp09 Small Paradox 심층 원인 — 본 plan 은 5-trial 점수 하락에 한정
- score_answer_v4 도입
- 다른 task 의 keyword 보강 (synthesis-01 의 'only' 누락 등 v2 regression finding) — 별도 plan
- 새 H 가설 추가 (H10+)
- math-03 prompt 본문 재작성 — 사용자 결정 후 task-01 진행 (Architect 가 자체 결정 금지)
- Exp10 v3 의 ABC 4 fail 윈도우 retry — 우선순위 낮음 권고 유지
- Exp10 use_tools 정책 통일 (Exp11 후보, 별도 plan)
- Logic 카테고리 multi-stage / 도구화 (Exp12 후보, 별도 plan)

## 변경 이력

- 2026-04-30 v1: 초안. Phase 1 후속 정리 + Exp10 v3 재산정 추가 (Subtask 3 신규 rev.1).
- 2026-04-30 done: 4 subtask 모두 완료. Mac (Task 01/02) + Windows (Task 03/04) 분담. v3 재산정 결과 (`exp10_v3_rescored_20260430_152306.json`) — condition mean Δ=+0.0019 / synthesis-04 task Δ=+0.017. README 본문 변경 0 (|Δ| < 0.01). Verification 5종 통과.
