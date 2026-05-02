---
type: plan
status: done
completed_at: 2026-04-29  # auto-set 2026-05-03 stale cleanup
updated_at: 2026-04-29
slug: exp10-v3-scorer-false-positive-abc-json-parse
version: 1
---

# Exp10 v3 — Scorer 강화 (false positive 제거) + ABC JSON parse 안정성

## Description

Exp10 v2 final 분석에서 두 가지 결정적 한계가 드러났다:

1. **채점기 false positive (logic-04 13/60)** — `experiments/measure.py:score_answer_v2` (line 45) 의 `all(token.lower() in response_lower for ...)` substring 채점이 모델의 "no solution / contradiction" 결론 답을 정답으로 잡음. logic-04 에서 v2 acc 0.400 (gemma_8loop) / 0.250 (flash) → strict heuristic 적용 시 0.050 / 0.000. 다른 task 도 동일 위험 잠재, 전수 재산정 필요.
2. **ABC chain JSON parse 4 fail** — gemma_8loop 의 4 trial (`(math-03, t13)`, `(synthesis-01, t14)`, `(logic-04, t2)`, `(logic-04, t6)`) 이 `experiments/orchestrator.py:extract_json_from_response` (line 167) 에서 fail. 진단 결과 응답이 markdown fence 시작 (` ```json\n{...`) 인데 max_tokens=4096 한계로 닫는 fence (` ``` `) 까지 못 간 가능성. 사후 분석 + parser 보강.

본 patch 가 v3 의 baseline. 향후 모든 결과 (math/logic 도구 통일, 재실행 등) 의 채점 기준이 됨.

## Expected Outcome

1. `experiments/measure.py` 에 `score_answer_v3(response, task_entry)` 추가 — v2 keyword-group 매칭에 negative_patterns + conclusion_required 옵션 결합.
2. `experiments/tasks/taskset.json` 의 `logic-04` 정의에 `negative_patterns: list[str]` 정규식 4개 추가. 다른 task 는 본 plan 에서 변경 금지.
3. `experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_<TS>.json` 신규 — v2 final 540 trial 을 v3 채점으로 재산정한 결과. 각 trial dict 에 `accuracy_v2`, `accuracy_v3` 두 필드 보유.
4. `docs/reference/exp10-v3-abc-json-fail-diagnosis.md` 신규 — 4 fail trial 의 raw 끝 50 char + total length + 분류 (truncate / fence 미닫힘 / 그 외) 표.
5. `experiments/orchestrator.py:extract_json_from_response` (line 167) 보강 — markdown fence 미닫힘 처리 + partial JSON 복구 fallback. unit test 추가.
6. `docs/reference/results/exp-10-reproducibility-cost.md` 의 §2/§3/§6 표 v2/v3 양쪽 column 으로 갱신, §4.5 의 ABC 4 fail 진단 결과 반영.
7. 한국어 `docs/reference/researchNotebook.md` Exp10 섹션의 결과 표에 v3 mean column 추가, 채점 시스템 변천 표에 "v2 → v3 (2026-04-29)" 행 추가.
8. 영문 `docs/reference/researchNotebook.en.md` Exp10 섹션 끝에 "v3 rescore note" 만 추가 — 기존 v2 final 수치 유지 (Closed 추가만 정책).

## Subtask Index

1. [task-01](./exp10-v3-scorer-false-positive-abc-json-parse-task-01.md) — v3 채점기 설계 + 구현 (parallel_group A, depends_on: [])
2. [task-02](./exp10-v3-scorer-false-positive-abc-json-parse-task-02.md) — taskset.json 의 logic-04 negative_patterns 보강 (parallel_group A, depends_on: [01])
3. [task-03](./exp10-v3-scorer-false-positive-abc-json-parse-task-03.md) — 540 trial 전수 v3 재산정 (parallel_group A, depends_on: [01, 02])
4. [task-04](./exp10-v3-scorer-false-positive-abc-json-parse-task-04.md) — ABC JSON parse 4 fail 진단 (parallel_group B, depends_on: [])
5. [task-05](./exp10-v3-scorer-false-positive-abc-json-parse-task-05.md) — orchestrator JSON 추출 강화 (parallel_group B, depends_on: [04])
6. [task-06](./exp10-v3-scorer-false-positive-abc-json-parse-task-06.md) — result.md / 노트북 갱신 (depends_on: [03, 05])

### 의존성 (Stage 기반)

```
Stage 1 (병렬):
  Group A:                             Group B:
    task-01 (score_answer_v3)            task-04 (4 fail 진단)
       │                                    │
       ▼                                    ▼
    task-02 (taskset 보강)              task-05 (orchestrator 보강)
       │                                    │
       ▼                                    │
    task-03 (전수 재산정)                    │
       │                                    │
       └────────────┬───────────────────────┘
                    ▼
            Stage 2 (단독):
              task-06 (문서 갱신)
```

Group A 와 Group B 는 독립이라 병렬 가능. task-06 은 양 group 결과를 모두 입력으로 받음.

## Constraints

- **v2 final JSON 수정 금지**: `experiments/exp10_reproducibility_cost/results/exp10_v2_final_20260429_033922.json` 은 read-only. v3 결과는 별도 파일.
- **`accuracy_v2` 보존**: trial dict 의 기존 `accuracy` 키는 그대로 두고, 신규로 `accuracy_v2`/`accuracy_v3` 두 필드 동시 보유. 단순 덮어쓰기 금지.
- **logic-04 외 task 의 taskset 변경 금지**: Subtask 2 는 logic-04 만 영향. 다른 task 의 negative_patterns 추가는 Subtask 3 의 전수 재산정 보고 후 별도 patch.
- **v2 final 의 4 fail trial 해소는 본 plan 의 success 기준이 아님**: Subtask 5 의 orchestrator patch 는 미래 run 에 적용. v2 final 의 raw 원본은 4KB truncate 본만 남아 있어 retry 가 결정적이지 않음 (가능하면 별도 후속).
- **영문 노트북 정책 준수**: `researchNotebook.en.md` 는 추가만 허용·수정 금지. 본 plan 의 영문 갱신은 Exp10 섹션 끝에 v3 rescore note 추가만.
- **LLM-judge 미도입**: 정규식 + negative pattern 으로 충분히 처리 가능 — 추가 비용/외부 의존 회피.
- **score_answer_v3 의 다른 실험 적용 금지**: 본 plan 은 Exp10 v2 final 전수 재산정만. Exp00~09 적용은 별도 plan.

## Non-goals

- math 카테고리 use_tools 정책 통일 (별도 plan)
- logic 카테고리 도구화 / multi-stage prompt (별도 실험)
- v3 540 trial 재실행 (본 plan 은 채점 + parse 안정성만)
- LLM-judge 채점기 도입 (정규식으로 처리)
- score_answer_v3 의 다른 실험 (Exp00~09) 적용
- v2 final 의 4 fail trial retry (raw 원본 손실 가능, 별도 결정)
- taskset.json 의 logic-04 외 task 의 negative_patterns 추가 (Subtask 3 보고 후 별도 patch)
- gemini_flash logic-04 retry trial 의 v3 재채점 결과로 통합 JSON 갱신 (별도 결정)

## 변경 이력

- 2026-04-29 v1: 초안. Exp10 v2 final 의 두 한계 (false positive + JSON parse 4 fail) 동시 해소.
