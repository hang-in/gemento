---
type: task
status: pending
updated_at: 2026-04-29
parent_plan: exp06-h4-scoring-reconciliation-h4-verdict
task_number: 3
title: "result.md + README H4 갱신"
depends_on: [1, 2]
parallel_group: B
---

# Task 03: result.md + README H4 갱신

## Changed files

- `docs/reference/results/exp-06-solo-budget.md` — 기존 파일 수정 (전체 29줄)
- `README.ko.md` — 기존 파일 수정
  - line 149: H4 가설 테이블 행
- `README.md` — 기존 파일 수정
  - line 50: H4 가설 테이블 행

## Change description

### 3.1 result.md 갱신 (`docs/reference/results/exp-06-solo-budget.md`)

기존 내용 유지 + 정합 비교 섹션 추가:

1. **기존 표 유지** (§2 "핵심 메트릭 비교") — 원본 비교를 삭제하지 않음.
   단, 표 아래에 disclosure 추가:
   > ⚠ 위 "88.9%" 수치는 현재 v1 `score_answer` 함수로 재현 불가. 아래 정합 비교 참조.

2. **정합 비교 섹션 신규 추가** (§2.1 또는 §5):

   ```
   ## 5. 정합 비교 (2026-04-29 reconciliation)

   기존 비교의 "Solo 표본 9"는 사실 오류 — Solo = 9 task × 5 trial = 45 trial (ABC와 동일).
   아래는 동일 채점법 × 동일 표본(45 vs 45) 비교.

   | 채점법 | Solo (45 trial) | ABC (45 trial) | Δ (Solo−ABC) |
   |--------|-----------------|----------------|-------------|
   | v1 (partial score) | 0.663 | 0.649 | +0.015 |
   | v2 (keyword group) | 0.967 | 0.900 | +0.067 |
   | v3 (neg+keyword) | 0.967 | 0.900 | +0.067 |

   Per-task v2 승패: ABC 1승 (logic-01), Solo 3승 (logic-02, synthesis-01, synthesis-02), 무승부 5.

   ### "88.9%" 재현 시도
   - trial-level: 어떤 v1 threshold에서도 40/45 미재현
   - task-level: `v2 mean ≥ 0.75` → ABC 8/9 = 88.9% (logic-02만 탈락)
   - 원본 비교가 task-level metric에서 유래했을 가능성

   ### H4 verdict (이 task set 한정)
   [Task 1 분석 결과 기반 — 아래는 정찰 기반 예상 verdict]
   재현 가능한 채점법에서 ABC 정확도 우위 미확인.
   Solo 조기 수렴(avg 4.5 loops) vs ABC 구조적 안정성 차이는 확인되나,
   이 9-task set에서는 정확도 Δ로 나타나지 않음.
   ```

3. **기존 §3 "분석 결과" / §4 "결론"** — 과장 표현 정정:
   - "실질적인 지능적 시너지를 생성" → 보수적 톤으로 교체
   - "역할 분리의 승리" → 조건부 표현으로 교체

### 3.2 README.ko.md H4 행 (line 149)

현재:
```
| **H4** | [Role 외부화 시너지] A-B-C 역할 분리가 단일 에이전트 반복보다 (일부 채점 조건에서) 우수할 수 있다 | ⚠ 조건부 채택 (Exp06 v1: +22.6%p ABC 우위; v2: 비대칭 표본 하에서 Solo 약간 우위 가능성 — balanced rerun 필요) | Exp06 |
```

교체:
```
| **H4** | [Role 외부화 시너지] A-B-C 역할 분리가 단일 에이전트 반복보다 우수하다 | ⚠ 미결 (Exp06 9-task × 45-trial 정합 비교: v1 +0.015 / v2 +0.067, 모두 Solo 소폭 우위. 원본 "+22.6%p" 재현 불가. 구조적 차이 확인되나 정확도 Δ는 미확인 — 확대 task set 재검증 필요) | Exp06 |
```

> **주의**: "balanced rerun 필요" caveat 제거. 대신 "확대 task set 재검증 필요"로 교체 — 표본 크기가 아닌 task 다양성이 미해결 변수.
> verdict가 "미결"(Inconclusive)인 이유: 재현 가능한 데이터에서 ABC 우위를 확인할 수 없으나, Solo 우위라고 주장하기에도 Δ가 작고 v2 scoring 해상도 한계가 있음.

### 3.3 README.md H4 행 (line 50)

현재:
```
| **H4** | [Role externalization synergy] A-B-C role separation may outperform repeated single-agent iteration under some scoring conditions | ⚠ Conditionally supported (Exp06 v1: +22.6pp ABC; v2: slightly favors Solo under asymmetric sample — needs balanced rerun) | Exp06 |
```

교체:
```
| **H4** | [Role externalization synergy] A-B-C role separation outperforms repeated single-agent iteration | ⚠ Inconclusive (Exp06 9-task × 45-trial reconciled comparison: v1 +0.015 / v2 +0.067, both slightly favor Solo. Original "+22.6pp" not reproducible. Structural difference confirmed but accuracy Δ not observed — needs expanded task set) | Exp06 |
```

한·영 동일 사실: verdict "⚠ 미결 / ⚠ Inconclusive", 수치 동일, caveat 동일.

## Dependencies

- **Task 1 완료 필수** — 분석 수치 (CI, task-level metrics)
- **Task 2 완료 필수** — 노트북 H4 verdict와 README verdict 일치해야 함

## Verification

```bash
# 1. README.ko.md H4 행에 "balanced rerun" 잔존 여부 (0건이어야)
grep -c "balanced rerun" README.ko.md
# 기대: 0

# 2. README.md H4 행에 "balanced rerun" 잔존 여부 (0건이어야)
grep -c "balanced rerun" README.md
# 기대: 0

# 3. README.ko.md H4 행에 "미결" 또는 "Inconclusive" 포함 확인
grep "H4" README.ko.md | grep -c "미결"
# 기대: 1

# 4. README.md H4 행에 "Inconclusive" 포함 확인
grep "H4" README.md | grep -c "Inconclusive"
# 기대: 1

# 5. result.md에 정합 비교 표 존재 확인
grep -c "Solo (45 trial)" docs/reference/results/exp-06-solo-budget.md
# 기대: 1 이상

# 6. result.md에 disclosure 존재 확인
grep -c "재현 불가" docs/reference/results/exp-06-solo-budget.md
# 기대: 1 이상

# 7. 한·영 README H4 verdict 동일 확인 (수동)
# Manual: grep "H4" README.ko.md && grep "H4" README.md
# 두 행의 verdict 유형 (미결/Inconclusive)과 수치가 일치하는지 확인
```

## Risks

- **README 렌더링**: H4 행이 길어지면 GitHub 마크다운 테이블 렌더링에서 줄바꿈 이슈 가능. 셀 내용이 ~150자 이내인지 확인.
- **외부 링크/인용**: README H4를 인용한 외부 문서 (블로그, 이슈 등)가 있을 수 있음. 현재 repo는 public이므로 verdict 변경이 외부에 노출됨 — 이것은 의도된 행동 (오류 정정).
- **과장 방지**: result.md의 기존 표현 ("실질적인 지능적 시너지를 생성") 정정 시 보수적 톤 유지 필수. "시너지 불존재" 주장도 과장 — "이 task set에서 미확인"으로 한정.

## Scope boundary

수정 금지 파일:
- `README.ko.md` H4 행 외 다른 영역
- `README.md` H4 행 외 다른 영역
- `docs/reference/results/exp-06-solo-budget.md` 기존 §1~§4 삭제 금지 (추가만 허용, 과장 표현 정정은 허용)
- `docs/reference/researchNotebook.md` — Task 2 영역, Task 3에서 변경 금지
- `docs/reference/researchNotebook.en.md` — Task 2 영역, Task 3에서 변경 금지
- `experiments/` 하위 모든 파일 — 변경 금지
