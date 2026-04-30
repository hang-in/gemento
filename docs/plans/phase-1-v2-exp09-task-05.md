---
type: task
status: pending
updated_at: 2026-04-29
parent_plan: phase-1-v2-exp09
task_number: 5
title: "문서 갱신 + 열린 질문 폐쇄"
depends_on: [1, 2, 4]
parallel_group: C
---

# Task 05: 문서 갱신 + 열린 질문 폐쇄

## Changed files

- `docs/reference/researchNotebook.md` — 기존 파일 수정
  - line 52: H9b 가설 테이블 행 (verdict 갱신)
  - line 788: 열린 질문 #1 "v2 역행 조사" → 폐쇄
  - line 796: 열린 질문 #9 "taskset expected_answer 전수 검증" → 폐쇄
  - line 802: 열린 질문 #15 "Exp09 통계 신뢰도 보강" → 폐쇄
  - Exp09 결과 섹션(lines 605~660 부근): 통계 검정 결과 추가
  - v1↔v2 전환 섹션(lines 704~723 부근): v2 역행 진단 결과 추가
- `docs/reference/researchNotebook.en.md` — 기존 파일 수정 (한국어판과 동일 위치)
  - line 56: H9b hypothesis table row
  - Exp09 results section: statistical test results
  - Open questions: close corresponding items
- `README.ko.md` — 기존 파일 수정
  - line 155: H9b 가설 테이블 행 (verdict 변경 시에만)
- `README.md` — 기존 파일 수정
  - line 56: H9b hypothesis table row (verdict 변경 시에만)
- `docs/reference/results/exp-09-longctx.md` — 기존 파일 수정 (통계 검정 결과 섹션 추가)

## Change description

### 5.1 열린 질문 폐쇄 (researchNotebook.md line 787~)

**#1 v2 역행 조사 (line 788)**
현재:
```
1. **v2 역행 조사** — Exp04, Exp05a에서 v2가 v1보다 낮은 이유 분석 필요
```
교체:
```
1. ~~**v2 역행 조사**~~ — **Phase 1 진단 완료** (2026-04-XX). 근본 원인: [Task 1 결과 요약 삽입]. 닫힘.
```
> 정확한 날짜와 요약은 Task 1 결과에 따라 구현 시 결정.

**#9 taskset expected_answer 전수 검증 (line 796)**
현재:
```
9. **taskset expected_answer 전수 검증** — math-04 결함 사례를 볼 때 다른 태스크의 정답도 수학적으로 검증되어야 함. Exp09 longctx 태스크셋도 이 검증 필요.
```
교체:
```
9. ~~**taskset expected_answer 전수 검증**~~ — **Phase 1 자동 검증 완료** (2026-04-XX). `validate_taskset.py`로 12개 기본 + 10개 longctx 태스크 전수 검증. [결과 요약: N PASS / 0 FAIL]. 닫힘.
```

**#15 Exp09 통계 신뢰도 보강 (line 802)**
현재:
```
15. **Exp09 통계 신뢰도 보강** — 현재 3 trial × 10 task = 30 데이터포인트/arm. 5 trial로 확대 + paired t-test 또는 Wilcoxon으로 H9b의 +3.3%p가 유의한지 검정.
```
교체:
```
15. ~~**Exp09 통계 신뢰도 보강**~~ — **Phase 1 통계 검정 완료** (2026-04-XX). 5 trial × 10 task = 50 데이터포인트/arm. Paired t-test p=[X.XXX], Wilcoxon p=[X.XXX]. [결론 삽입]. 닫힘.
```

### 5.2 H9b 가설 테이블 행 갱신

**갱신 조건**: Task 04의 통계 검정 결과에 따라 verdict가 변경되는 경우에만 수정.

**researchNotebook.md line 52** — 현재:
```
| H9b | [차별성] ABC+Tattoo가 RAG baseline 대비 고유 기여를 가진다 | ⚠️ 조건부 채택 (...) | Exp09 |
```
→ Task 04 verdict에 따라:
- p < 0.05: `✅ 채택 (5-trial paired t-test p=X.XXX; overall +X.X%p; 3-hop +XX%p)` 
- p ≥ 0.05: `⚠️ 미결 (5-trial 통계 검정 비유의 p=X.XXX; effect size 작음; 3-hop 하위 그룹에서만 유의미 가능성)`

**README.ko.md line 155 / README.md line 56** — 동일 로직으로 갱신. 한·영 일관성 필수.

### 5.3 Exp09 결과 섹션 보강 (researchNotebook.md lines 605~660)

기존 "H9b 차별성" 설명 뒤에 통계 검정 결과 추가:

```markdown
#### 통계 검정 결과 (Phase 1, 2026-04-XX)

5 trial × 10 task (50 data points/arm) 기반:

| 검정 | 통계량 | p-value | 판정 |
|------|--------|---------|------|
| Paired t-test | t=X.XX | X.XXX | [유의/비유의] |
| Wilcoxon signed-rank | W=XX | X.XXX | [유의/비유의] |

Bootstrap 95% CI for Δ(abc−rag): [X.XXX, X.XXX]

Small Paradox (5-trial):
- small tasks: abc=X.XX vs rag=X.XX (3-trial 대비 [변화 방향])
- [noise vs 실제 패턴 판별 결론]
```

### 5.4 v2 역행 진단 결과 기록 (researchNotebook.md lines 704~723)

기존 "v1↔v2 전환" 섹션 뒤에 진단 결과 추가:

```markdown
#### v2 역행 근본 원인 (Phase 1, 2026-04-XX)

진단 스크립트(`experiments/scoring_diagnostic.py`) 분석 결과:
- 역행 trial 수: N건 (Exp04: X건, Exp05a: Y건)
- 주요 패턴: [Type A/B/C/D 분포]
- 원인: [요약]
- 정책 결정: [v2 유지/v3 전환/keyword 수정 권고]
```

### 5.5 Exp09 결과 보고서 갱신

`docs/reference/results/exp-09-longctx.md`에 통계 검정 결과 섹션 추가:
- 5-trial 비교 표 (기존 3-trial 표 보존 + 5-trial 표 추가)
- H9b verdict 갱신
- Small Paradox 결론

### 5.6 영문 노트북 동기화

`docs/reference/researchNotebook.en.md`의 대응 위치에 동일 내용 영문 번역 반영. 수치와 verdict는 한/영 완전 일치.

## Dependencies

- **Task 1 완료 필수** — v2 역행 진단 결과 (요약 + 패턴 분류)
- **Task 2 완료 필수** — taskset 검증 결과 (PASS/FAIL 카운트)
- **Task 4 완료 필수** — Exp09 통계 검정 결과 (p-value, CI, verdict)

## Verification

```bash
# 1. 열린 질문 #1 폐쇄 확인
grep "v2 역행 조사" docs/reference/researchNotebook.md | grep -c "닫힘"
# 기대: 1

# 2. 열린 질문 #9 폐쇄 확인
grep "expected_answer 전수 검증" docs/reference/researchNotebook.md | grep -c "닫힘"
# 기대: 1

# 3. 열린 질문 #15 폐쇄 확인
grep "Exp09 통계 신뢰도 보강" docs/reference/researchNotebook.md | grep -c "닫힘"
# 기대: 1

# 4. H9b verdict 한·영 일치 확인 (수동)
# Manual: grep "H9b" README.ko.md && grep "H9b" README.md
# 두 행의 verdict 유형과 수치가 일치하는지 확인

# 5. researchNotebook에 통계 검정 결과 존재 확인
grep -c "Paired t-test" docs/reference/researchNotebook.md
# 기대: 1 이상

# 6. 영문 노트북에도 통계 결과 존재 확인
grep -c "Paired t-test" docs/reference/researchNotebook.en.md
# 기대: 1 이상

# 7. Exp09 결과 보고서에 5-trial 데이터 존재 확인
grep -c "5.trial\|5-trial" docs/reference/results/exp-09-longctx.md
# 기대: 1 이상
```

## Risks

- **verdict 충돌**: Task 04의 통계 결과가 기존 "조건부 채택"과 크게 달라질 수 있음 (예: 완전 비유의). README 갱신 시 기존 인용자에 영향.
- **줄번호 이동**: Task 1, 2, 4 실행 중 researchNotebook에 다른 변경이 없어야 함. 줄번호 기반 편집이므로 병렬 수정 시 충돌 가능 — 이 task가 마지막(parallel_group C)이므로 위험 낮음.
- **한·영 동기 누락**: 한국어판 수정 후 영문판 동기를 잊을 수 있음. verification에서 양쪽 모두 확인.
- **과장/과소 표현**: verdict 작성 시 통계 결과를 정직하게 반영. "비유의 = 효과 없음"이 아니라 "검정력 부족으로 판단 불가"일 수 있음. 정확한 표현 사용.

## Scope boundary

수정 금지 파일:
- `experiments/` 하위 모든 코드/결과 파일 — Task 1~4 영역
- `docs/plans/` — 플랜 문서 자체 수정 금지
- `README.ko.md`, `README.md`의 H9b 행 외 다른 영역
- `docs/reference/researchNotebook.md`의 Exp06 관련 섹션 (이전 플랜에서 확정)
