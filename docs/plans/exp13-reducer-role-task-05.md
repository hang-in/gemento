---
type: plan-task
status: done
updated_at: 2026-05-05
parent_plan: exp13-reducer-role
parallel_group: E
depends_on: [04]
---

# Task 05 — 분석 + H12 verdict + 문서 갱신

## Changed files

- `docs/reference/exp13-reducer-role-analysis-<TS>.md` — **신규**. 분석 보고서
- `docs/reference/results/exp-13-reducer-role.md` — **신규**. result.md
- `docs/reference/researchNotebook.md` — H12 entry + 축 매트릭스 + Exp13 섹션
- `docs/reference/researchNotebook.en.md` — Closed 추가만 ("Exp13 note")
- (조건부) `README.md` / `README.ko.md` — H12 채택 시 H 표 갱신 (사용자 결정)

신규 2, 수정 2-3.

## Change description

Exp12 task-05 패턴 그대로. 본 plan 의 핵심 metric 차이:
- **final_answer 길이 변동** 측정 (Reducer 의 직접 효과)
- **task essential keyword 출현 비율** (예: logic-02 의 "105", "inconsistent")
- assertion turnover 는 본 plan 영역 외 (Reducer = post-stage, cycle 안 변경 0)

### Step 1 — 결과 통합 + condition aggregate

Exp12 task-05 의 Step 1 패턴 그대로. 입력 파일:
- `experiments/exp13_reducer_role/results/exp13_baseline_abc.json`
- `experiments/exp13_reducer_role/results/exp13_reducer_abc.json`

### Step 2 — ablation 분석 (n=15 task paired)

H12 본 가설 = `reducer_abc − baseline_abc`. Exp12 의 +0.05 양수 정합성 검토.

| 검정 | 측정 |
|------|------|
| mean Δ / median Δ / std | — |
| Wilcoxon W, p | — |
| Paired t, p | — |
| Cohen's d (paired) | — |
| Bootstrap 95% CI Δ | — |

추가 비교 (3 회차 baseline 안정성):
- Stage 2C abc: 0.7589
- Exp11 baseline: 0.7778
- Exp12 baseline: 0.7500
- 본 plan baseline: <FILL>

### Step 3 — 메커니즘 측정 (final_answer 길이 + keyword 출현)

| condition | avg final_answer len (chars) | task essential keyword 출현 비율 |
|-----------|----------------------------:|--------------------------------:|
| baseline_abc | <FILL> | <FILL> |
| reducer_abc | <FILL> | <FILL> |

**task essential keyword** — 각 task 의 scoring_keywords 의 첫 group 의 모든 token 이 final_answer 에 등장하는 trial 비율 (substring contains 기준).

→ Reducer 가 keyword 를 더 명확히 출력시키면 비율 ↑. 단 Reducer 가 답 자체 바꾸면 (Risk 1) 비율 변동 큼.

### Step 4 — error mode (FailureLabel)

Exp12 패턴. NONE 비율 / WRONG_SYNTHESIS / FORMAT_ERROR 등.

### Step 5 — 카테고리별 break-down

| category | baseline | reducer | Δ |
|----------|---------:|--------:|--:|
| math | <FILL> | <FILL> | <FILL> |
| logic | <FILL> | <FILL> | <FILL — Stage 2C/Exp11 catastrophic 영역, Exp12 회복 정합성> |
| **synthesis** | <FILL> | <FILL> | <FILL — Exp12 회복 +0.050 정합성> |
| planning | <FILL> | <FILL> | <FILL> |

Exp12 와의 비교:
- logic-02 회복 (Exp12 +0.30) — Reducer 도 비슷한 효과? 또는 다른 메커니즘
- synthesis-05 회복 (Exp12 +0.45) — Reducer 효과 측정
- synthesis-02 역효과 (Exp12 −0.20) — Reducer 도 같은 패턴 가능

### Step 6 — H12 verdict 결정 트리

Exp12 패턴 (Δ ≥ +0.05 + p<0.05 / Δ ≥ +0.05 + p≥0.05 / |Δ|<0.05 / Δ<0).

**Architect 사전 예측** (확률):
- ✅ 채택: 25% (Reducer 가 keyword 명료화로 정확도 +0.10 이상)
- ⚠ 조건부 (양수): 35% (Exp12 패턴 — +0.05 임계, 검정력 한계)
- ⚠ 미결: 25% (격차 작음)
- ❌ 기각: 15% (Reducer 가 답을 바꿈 — Risk 1 발현)

### Step 7-11 — 분석 보고서 + 문서 갱신

Exp12 task-05 패턴 그대로:
- Step 7: `docs/reference/exp13-reducer-role-analysis-<TS>.md` 신규
- Step 8: `docs/reference/results/exp-13-reducer-role.md` 신규
- Step 9: `researchNotebook.md` H12 entry + Exp13 섹션
- Step 10: `researchNotebook.en.md` Closed 추가만
- Step 11: README 갱신 (사용자 결정)

추가로 Exp12 ↔ Exp13 결정적 대비 표 (analysis 보고서 §):

| 비교 | Exp12 Extractor (H11) | Exp13 Reducer (H12) |
|------|---------------------:|--------------------:|
| 위치 | pre-stage | post-stage |
| 효과 | 입력 정리 | 출력 정리 |
| Δ | +0.0500 | <FILL> |
| catastrophic 영역 효과 | logic-02 +0.30 / synthesis-05 +0.45 | <FILL> |

## Dependencies

- task-04 마감 (사용자 직접)
- Exp12 의 비교 baseline (Stage 2C analyze.py 의 helper 재사용)
- 패키지: `scipy.stats`

## Verification

```bash
# 1) 분석 보고서 placeholder 0
grep -E '<FILL[^>]*>' docs/reference/exp13-reducer-role-analysis-*.md | wc -l

# 2) result.md exp-13 신규
.venv/Scripts/python -c "
text = open('docs/reference/results/exp-13-reducer-role.md', encoding='utf-8').read()
assert 'experiment: 실험 13' in text
print('verification 2 ok')
"

# 3) researchNotebook H12 entry
grep -c "H12" docs/reference/researchNotebook.md

# 4) 영문 노트북 추가만 (기존 H1~H11 entry 변경 0)
grep -c "Exp13" docs/reference/researchNotebook.en.md

# 5) banned tone 부재
.venv/Scripts/python -c "
import re
banned = (r'\bOperating System\b', r'\bnovel framework\b', r'\bAGI\b')
for path in ('README.md', 'README.ko.md'):
    text = open(path, encoding='utf-8').read()
    for pat in banned:
        if re.search(pat, text):
            raise SystemExit(f'{path}: banned {pat}')
print('verification 5 ok: banned tone 부재')
"
```

## Risks

- **Risk 1 — Reducer 가 답을 바꾸어 false positive / false negative** — keyword 매칭 정확도가 정답 자체의 의미와 분리. 단 task 는 Reducer 가 답 변경 시 의미 변화 측정 (manual review 권고)
- **Risk 2 — Exp12 와 비교 시 baseline 변동** — 3 회차 baseline (Stage 2C / Exp11 / Exp12) 가 모두 다른 mean (0.7589 / 0.7778 / 0.7500). 본 plan baseline 도 변동 가능 — Exp12 와 직접 비교 시 noise
- **Risk 3 — synthesis-02 역효과 재발** — Exp12 의 −0.20 패턴. Reducer 도 saturation 영역 흔들림 가능
- **Risk 4 — H12 기각 (Reducer 가 baseline 보다 약함)** — Exp11 의 정반대 메커니즘 변종 가능. disclosure + Stage 5 의 다음 의제 (Search Tool / Extractor+Reducer 조합) 우선순위 변경

## Scope boundary

본 task 에서 **수정 금지** 파일:
- 모든 코드 (`experiments/*.py`) — read-only
- 결과 JSON (모두 read-only)
- 본 plan 의 다른 subtask 영역
- 다른 reference 문서 (analysis + result.md exp-13 만 신규)
- 다른 result.md (exp-00 ~ exp-12) — 변경 금지
- conceptFramework.md / namingConventions.md / 기타 canonical reference

## 사용자 호출 시점

- Step 6 의 verdict 결정 트리에서 ❌ 기각
- Step 11 의 README 갱신 — 사용자 결정 의무
- Risk 1/4 발견 시
