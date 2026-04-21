---
type: result
status: done
updated_at: 2026-04-15
---

# Implementation Result: 채점 시스템 통일 (Scoring V2)

> Developer: unknown
> Branch: N/A
> Date: 2026-04-15 13:17 (exp045-v2 후속 갱신: 2026-04-15)
> Plan Revision: 0

---

## Summary

```
Verification results for Task 3:
✅ `python3 experiments/measure.py --rescore` — 출력 정상, v1/v2/diff 컬럼 표시
✅ `python3 experiments/measure.py --rescore | grep -E "v1|v2|diff"` — 헤더 행 확인
✅ `python3 experiments/measure.py --rescore | grep "exp06"` — exp06: v1=0.663, v2=0.967, +30.3% (v2 > v1 확인)
✅ `python3 experiments/measure.py .../exp06_solo_budget...json` — 단일 파일 분석 정상 동작 (regression 없음)
```

---

## 구현 완료 요약

**Task 1** — `experiments/tasks/taskset.json`: 9개 태스크 전체에 `scoring_keywords` 추가

**Task 2** — `experiments/measure.py`:
- `score_answer_v2()` 함수 추가 (keyword-group 기반, v1 fallback 포함)
- `analyze_baseline`, `analyze_multiloop`, `analyze_abc_pipeline`, `analyze_solo_budget` → `task_map` 파라미터 추가 및 v2 채점 적용
- `main()`에서 `taskset.json` 로드 후 `task_map` 구성 및 각 분석 함수에 전달

**Task 3** — `experiments/measure.py`:
- `rescore_all()` 함수 추가 (실험 타입별 최신 파일 v1/v2 비교표 출력)
- `--rescore` 플래그 추가, `result_file`을 optional로 변경

**주요 결과**: exp06 solo_budget 기준 v1(0.663) → v2(0.967), **+30.3% 향상**

## Subtask Results

### 1. ```
Verification results for Task 3:
✅ `python3 experiments/measure.py --rescore` — 출력 정상, v1/v2/diff 컬럼 표시
✅ `python3 experiments/measure.py --rescore | grep -E "v1|v2|diff"` — 헤더 행 확인
✅ `python3 experiments/measure.py --rescore | grep "exp06"` — exp06: v1=0.663, v2=0.967, +30.3% (v2 > v1 확인)
✅ `python3 experiments/measure.py .../exp06_solo_budget...json` — 단일 파일 분석 정상 동작 (regression 없음)
```

---

## 구현 완료 요약

**Task 1** — `expe

---

## 후속 업데이트 (exp045-v2 Plan, 2026-04-15)

`rescore_all()`의 `SKIP_TYPES`에서 `handoff_protocol`을 제거하여 exp045(ABC/5b) 결과도 v1/v2로 재채점.

### 전체 Rescore 표 (최신)

```
═══════════════════════════════════════════════════
  Rescore 결과 비교 (v1 substring vs v2 keyword)
═══════════════════════════════════════════════════
  파일명                                  v1 avg  v2 avg     diff
  -------------------------------------------------
  exp04_abc_pipeline_20260409_182751.json   0.607   0.583   -2.3%
  exp01_assertion_cap_partial_20260408_170400.json   0.000   0.000 +   0.0%
  exp00_baseline_20260408_102018.json   0.705   0.722 +   1.7%
  exp035_cross_validation_20260409_150703.json   0.000   0.000 +   0.0%
  exp03_error_propagation_20260409_135411.json   0.000   0.000 +   0.0%
  exp045_handoff_protocol_20260414_135634.json   0.649   0.900 +  25.1%
  exp02_multiloop_20260409_072735.json   0.369   0.438 +   6.9%
  exp05a_prompt_enhance_20260410_145033.json   0.636   0.583   -5.2%
  exp06_solo_budget_20260415_114625.json   0.663   0.967 +  30.3%
```

### Solo vs ABC 동일 기준 비교 (v2)

| 실험 | v2 평균 | 태스크 수 | 트라이얼 수 |
|------|---------|-----------|-------------|
| exp06 Solo (solo_budget) | 0.967 | 9 | 9 (1 trial × 9) |
| exp045 ABC (handoff_protocol, 5b) | 0.900 | 9 | 45 (5 trial × 9) |
| **Δ (Solo − ABC)** | **+0.067** | — | — |

### 한 줄 결론

v2 동일 기준에서 Solo(0.967)가 ABC(0.900)보다 0.067 높다. 단, Solo는 1 trial × 9, ABC는 5 trial × 9로 표본 규모가 다르며, 해석은 3순위 플랜(실험 6 결론 재작성)에서 다룬다.
