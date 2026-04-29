---
type: plan
status: in_progress
updated_at: 2026-04-29
slug: exp10-readme-v2-abc-4-fail-v3-disclosure
version: 1
---

# Exp10 후속 정리 — README 갱신 + v2 ABC 4 fail 사후 분석 + v3 적용 범위 disclosure

## Description

Exp10 v3 patch 가 commit/push 됐고 결과는 `gemma_8loop 0.781 / gemini_flash 0.591 / gemma_1loop 0.413` (v3) 로 확정. 본 plan 은 그 후속 정리:

1. **v2 ABC 4 fail 사후 분석**: 직전 `exp10-v3-scorer-false-positive-abc-json-parse` plan 의 Task 04 진단은 4 trial (`(gemma_8loop, math-03 t13)`, `(synthesis-01 t14)`, `(logic-04 t2/t6)`) 의 **마지막 cycle 의 fail phase raw** 만 봤음 (kind=fence_unclosed 3 + empty 1, 1/4 사후 복구). 본 plan 은 모든 cycle × 모든 phase (a/b/c) 의 raw 를 v3 patch 적용된 `extract_json_from_response` 에 통과시켜 살릴 수 있는 raw 가 더 있는지 점검 + retry 가치 판정.
2. **v3 적용 범위 disclosure**: Architect 사전 정찰 결과 logic-04 가 Exp00~09 의 다른 result JSON 에 미포함 → Exp00~09 에 v3 채점 적용해도 변동 0. 이를 정직하게 disclosure (result.md §7 #5 + 한국어 노트북 채점 시스템 변천 표).
3. **README 갱신**: 한·영 README 가 Exp09 까지 반영. Exp10 v3 결과 추가 + Roadmap 정정. Reddit 청중 대상 외부 노출이라 정확성 우선.

## Expected Outcome

1. `experiments/exp10_reproducibility_cost/diagnose_json_fails.py` 에 `--full-cycles` 옵션 추가 (또는 신규 `diagnose_json_fails_full.py`). 4 trial 의 모든 cycle × phase 의 raw 점검 결과 stdout + 살릴 수 있는 final_answer 후보 표.
2. `docs/reference/exp10-v3-abc-json-fail-diagnosis.md` 끝에 "v2 final 4 fail 사후 분석 (full cycles)" 절 추가. 각 trial 의 살릴 수 있는 raw 위치 (cycle, phase) + final_answer 후보 + retry 권고 여부.
3. `docs/reference/results/exp-10-reproducibility-cost.md` §7 #5 항목 갱신 — "logic-04 가 Exp00~09 의 task subset 에 미포함" 사실 + v3 적용 영향 0 disclosure (한 줄).
4. `docs/reference/researchNotebook.md` 의 "v2 → v3 전환 (2026-04-29)" 표 부근에 v3 적용 범위 한 줄 추가 (Exp10 한정).
5. `README.md` (영문 메인) + `README.ko.md` 갱신 — Exp10 H 행 추가, "What I measured" 단락 보강, "Short-term" Roadmap 정정. 한·영 동일 사실 가리킴.
6. 영문 `researchNotebook.en.md` 변경 0 (Closed 추가만 정책 준수, Exp10 v3 rescore note 는 직전 plan 에서 이미 추가).

## Subtask Index

1. [task-01](./exp10-readme-v2-abc-4-fail-v3-disclosure-task-01.md) — v2 ABC 4 fail 사후 분석 (parallel_group A, depends_on: [])
2. [task-02](./exp10-readme-v2-abc-4-fail-v3-disclosure-task-02.md) — v3 적용 범위 disclosure (parallel_group A, depends_on: [])
3. [task-03](./exp10-readme-v2-abc-4-fail-v3-disclosure-task-03.md) — README 갱신 한·영 (parallel_group B, depends_on: [01, 02])

### 의존성 (Stage 기반)

```
Stage 1 (병렬):
  Group A:
    task-01 (사후 분석)         task-02 (disclosure)
       │                            │
       └────────────┬───────────────┘
                    ▼
            Stage 2 (단독):
              task-03 (README 한·영)
```

Group A 두 task 는 독립 입력. task-03 은 task-01 의 retry 권고 결과를 Roadmap 에 반영 + task-02 의 disclosure 결과를 본문에 (필요 시) 언급할 수 있도록 합류.

## Constraints

- README 외부 노출 톤 유지 (Reddit/r/LocalLLaMA 청중) — "Operating System" / "novel framework" / "AGI" 등 과적재 명칭 금지
- 본 적 없는 외부 논문 인용 금지 (이전 plan `readme-memento-acknowledgement` 정책 준수)
- 한·영 README 가 같은 사실 가리켜야 함
- v2 final JSON / v3 rescored JSON 수정 금지 — read-only
- `score_answer_v3` 함수 + `taskset.json` 의 logic-04 정의 변경 금지 (이미 r2 까지 반영, 추가 변경 별도 plan)
- 영문 researchNotebook 변경 0 — Closed 추가만 정책. Exp10 v3 rescore note 는 직전 plan 에서 추가 완료
- `diagnose_json_fails.py` 변경은 옵션 추가만 (기존 동작 회귀 없음)
- Subtask 1 의 success 기준 = "복구 가능 여부 판정 + retry 권고 결정". 실제 윈도우 측 retry 실행은 본 plan 범위 밖

## Non-goals

- math 카테고리 use_tools 정책 통일 + v3 재실행 (별도 plan, Exp11 후보)
- logic 카테고리 도구화 / multi-stage prompt (별도 plan, Exp12 후보)
- Exp00~09 의 result JSON 에 v3 채점 적용 (logic-04 미포함이라 변동 0, disclosure 만)
- 다른 task 의 `negative_patterns` 정의 + 전수 재산정 (별도 plan)
- v2 ABC 4 fail 의 윈도우 측 retry 실행 (Subtask 1 결과에 따라 별도 결정)
- 새 H 가설 (H10+) 도입 결정 — Subtask 3 진행 시 README 표기 결정 (H1 추가 evidence vs 새 H 코드)
- README 의 디자인/시각 요소 변경 (스크린샷, 다이어그램)

## 변경 이력

- 2026-04-29 v1: 초안. Exp10 v3 patch 후 외부 노출 (README) + 내부 정합 (4 fail 사후 분석 + v3 범위 disclosure) 동시 정리.
