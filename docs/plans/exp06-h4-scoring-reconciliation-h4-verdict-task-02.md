---
type: task
status: pending
updated_at: 2026-04-29
parent_plan: exp06-h4-scoring-reconciliation-h4-verdict
task_number: 2
title: "researchNotebook 정정 + disclosure"
depends_on: [1]
parallel_group: B
---

# Task 02: researchNotebook 정정 + disclosure

## Changed files

- `docs/reference/researchNotebook.md` — 기존 파일 수정
  - line 46: H4 가설 테이블 행
  - lines 361–393: Exp06 섹션 전체 교체
  - line 716: v1→v2 재채점 표의 Exp06 행 (변경 없이 유지 — 기존 v1/v2 수치는 사실이므로)
- `docs/reference/researchNotebook.en.md` — 기존 파일 수정
  - line 50: H4 가설 테이블 행
  - lines 365–397: Exp06 섹션 전체 교체

## Change description

### 2.1 researchNotebook.md — Exp06 섹션 (lines 361–393)

교체할 내용:

1. **메타 테이블 "어떻게" 행 정정**:
   - `9개 태스크 × 1 트라이얼 = 9 시행` → `9개 태스크 × 5 trial = 45 시행 (ABC와 동일)`
   - 이것이 "표본 9" 오류의 원천

2. **결과 테이블 교체** — 기존 v2-only 2행 표 → v1/v2/v3 정합 비교 표:

   ```
   | 채점법 | Solo (45 trial) | ABC (45 trial) | Δ (Solo−ABC) |
   |--------|-----------------|----------------|-------------|
   | v1 (partial score) | 0.663 | 0.649 | +0.015 |
   | v2 (keyword group) | 0.967 | 0.900 | +0.067 |
   | v3 (neg+keyword) | 0.967 | 0.900 | +0.067 |
   ```

3. **주의사항 섹션 교체**:
   - "Solo 표본(9)이 ABC(45)보다 5배 적어 분산 높음" → **삭제** (사실 오류)
   - "v1 기준으로는 ABC(88.9%) > Solo(66.3%), Δ = +22.6%p" → 정정: "원본 비교 ABC 88.9% vs Solo 66.3% (+22.6%p)는 현재 v1 `score_answer` 함수로 재현 불가. 어떤 threshold에서도 40/45 미재현. task-level `v2 mean ≥ 0.75`에서 8/9 = 88.9% 재현 — 원본이 task-level metric에서 유래했을 가능성."
   - "v2 keyword 매칭이 Solo의 부분 정답을 과대평가할 가능성" → 유지 (사실)

4. **핵심 발견 교체**:
   - 재현 가능한 3개 채점법(v1/v2/v3) 모두에서 Solo ≥ ABC
   - Solo 조기 수렴(평균 4.5 loops) → v2에서 keyword 존재만으로 점수 획득
   - ABC는 logic-01에서 완전 정답 (5/5), Solo는 4/5 → 복잡 추론에서 ABC 안정성
   - **H4 verdict**: 이 9-task set에서는 ABC 구조적 우위를 확인할 수 없음. v2 scoring 해상도의 한계 가능성.

5. **H4 가설 테이블 행 (line 46) 갱신**:
   - `**채택** (+22.6%p)` → Task 1의 분석 결과 기반 verdict (Task 3과 동일 verdict 사용)

### 2.2 researchNotebook.en.md — Exp06 섹션 (lines 365–397)

한국어 노트북과 동일한 정정 사항을 영문으로 반영:

1. 메타 테이블 "How" 행: `9 tasks × 1 trial = 9 runs` → `9 tasks × 5 trials = 45 runs (same as ABC)`
2. 결과 테이블: v1/v2/v3 정합 비교 표 (영문)
3. Caveats: "88.9%" 재현 불가 disclosure (영문)
4. Key Findings + Conclusion: 데이터 기반 갱신
5. H4 가설 테이블 행 (line 50): verdict 갱신

**제약**: 영문 노트북의 Exp06 이외 섹션은 변경 금지. 기존 수치 변경 0.

### 2.3 H4 verdict 결정 기준

Task 1의 분석 스크립트 출력을 기반으로 verdict를 결정한다:

- **재현 가능한 3개 채점법 모두** Solo ≥ ABC → "88.9% 원본 비교 재현 불가 + 정합 비교에서 ABC 우위 미확인"
- 그러나 **조기 수렴 패턴**은 실재 (Solo avg 4.5 loops vs ABC 21.6 calls) — 구조적 차이는 있으나 이 task set에서 정확도 차이로 나타나지 않음
- **결론**: "Inconclusive on this task set" 또는 "Conditionally supported — structural difference confirmed, accuracy difference not reproduced"
- Task 3에서 README에 반영할 최종 문구 결정

## Dependencies

- **Task 1 완료 필수** — 분석 스크립트의 출력 수치 (bootstrap CI, task-level metrics)를 노트북에 인용
- 분석 JSON: `experiments/exp06_solo_budget/results/exp06_reconciliation_*.json`

## Verification

```bash
# 1. researchNotebook.md 에서 "표본 9" / "× 1 트라이얼" 잔존 여부 확인 (0건이어야)
grep -c "표본.*9\|× 1 트라이얼\|1 트라이얼" docs/reference/researchNotebook.md
# 기대: 0

# 2. researchNotebook.md Exp06 섹션에 정합 비교 표 존재 확인
grep -c "Solo (45 trial)" docs/reference/researchNotebook.md
# 기대: 1 이상

# 3. researchNotebook.en.md 에서 "Sample.*9" 잔존 여부 (Exp06 섹션)
grep -c "1 trial = 9 runs\|Sample | 9" docs/reference/researchNotebook.en.md
# 기대: 0

# 4. researchNotebook.en.md Exp06 섹션에 정합 비교 표 존재 확인
grep -c "Solo (45 trial)" docs/reference/researchNotebook.en.md
# 기대: 1 이상

# 5. 한·영 H4 verdict 일치 확인
grep "H4" docs/reference/researchNotebook.md | head -1
grep "H4" docs/reference/researchNotebook.en.md | head -1
# 기대: 동일 verdict (언어만 다름)
```

## Risks

- **기존 수치와의 모순**: researchNotebook의 다른 섹션에서 "Solo 표본 9"나 "H4 채택 (+22.6%p)"를 인용한 곳이 있을 수 있음. Exp06 섹션 외에서 grep으로 확인 후, 참조하는 곳도 함께 갱신 필요.
- **영문 노트북 Closed 정책**: 영문 노트북에 Exp06이 이미 Closed 항목으로 존재 (lines 365–397). 기존 내용을 정정하는 것이므로 "Closed 추가만" 정책과 충돌 가능 — **정정은 오류 수정이므로 예외 적용** (오류를 방치하는 것이 정책 위반보다 나쁨).

## Scope boundary

수정 금지 파일:
- `docs/reference/researchNotebook.md` Exp06 섹션 외 영역 (단, H4 가설 테이블 행은 허용)
- `docs/reference/researchNotebook.en.md` Exp06 섹션 외 영역 (단, H4 가설 테이블 행은 허용)
- `docs/reference/experimentDesign.md` — 변경 금지
- `docs/reference/experimentSummary.md` — 변경 금지
- `docs/reference/conceptFramework.md` — 변경 금지
- `experiments/` 하위 모든 파일 — 변경 금지 (Task 1 영역)
