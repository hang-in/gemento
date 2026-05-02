---
type: plan-task
status: todo
updated_at: 2026-05-03
parent_plan: exp12-extractor-role-pre-search
parallel_group: E
depends_on: [04]
---

# Task 05 — 분석 + H11 verdict + 문서 갱신

## Changed files

- `docs/reference/exp12-extractor-role-analysis-<TS>.md` — **신규**. 분석 보고서
- `docs/reference/results/exp-12-extractor-role.md` — **신규**. result.md
- `docs/reference/researchNotebook.md` — H11 entry + 축 매트릭스 + Exp12 섹션
- `docs/reference/researchNotebook.en.md` — Closed 추가만 ("Exp12 note (2026-MM-DD)")
- (조건부) `README.md` / `README.ko.md` — H11 채택 시 H 표 갱신 (사용자 결정)

신규 2, 수정 2-3.

## Change description

### 배경

Task 04 의 실험 결과 (150 trial) 를 분석하여 H11 verdict 결정. Stage 2C analyze.py 의 `count_assertion_turnover` + `classify_error_mode` 재사용. Exp11 task-05 와 같은 패턴.

### Step 1 — 결과 통합 + condition aggregate

```python
import json
from collections import defaultdict
files = ['experiments/exp12_extractor_role/results/exp12_baseline_abc.json',
         'experiments/exp12_extractor_role/results/exp12_extractor_abc.json']
all_trials = []
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    all_trials.extend(d['trials'])
# condition × task aggregate (Exp11 task-05 패턴)
```

### Step 2 — ablation 분석 (n=15 task paired)

H11 본 가설 = `extractor_abc − baseline_abc`:

```
Δ = extractor_per_task[i] - baseline_per_task[i]  (n=15)

mean Δ / median Δ / std Δ
Wilcoxon W, p
Paired t-test t, p
Cohen's d (paired)
Bootstrap 95% CI Δ
```

추가 비교:
- baseline_abc 결과의 Stage 2C abc 회귀 검증 (정합성)
- Exp11 baseline_abc (mean=0.7778) 와 본 plan baseline_abc 비교 (도구 변경 영향 0 검증)

### Step 3 — 메커니즘 측정 (assertion turnover + 첫 cycle 분석)

| condition | added (mean) | modified (mean) | first_cycle_assertions |
|-----------|-------------:|----------------:|----------------------:|
| baseline_abc | (Stage 2C 정합 ~4.80) | ~0.28 | (cycle 1 assertion 수) |
| extractor_abc | <FILL> | <FILL> | <FILL — Extractor 효과 시 더 빠른 누적> |

→ extractor 의 *첫 cycle* assertion 이 baseline 보다 많거나 같음 (Extractor 가 sub-claim 사전 제공 효과). H11 의 직접 증거.

### Step 4 — error mode (FailureLabel)

| condition | NONE | FORMAT_ERROR | WRONG_SYNTHESIS | NULL_ANSWER | OTHER |
|-----------|----:|-------------:|----------------:|------------:|------:|

extractor 가 baseline 보다 NONE 비율 ↑ 면 정답 안정성 우위 (질적 차이).

### Step 5 — 카테고리별 break-down (Stage 2C / Exp11 정합)

| category | baseline | extractor | Δ |
|----------|---------:|----------:|--:|
| math | <FILL> | <FILL> | <FILL> |
| logic | <FILL> | <FILL> | <FILL> |
| **synthesis** | <FILL> | <FILL> | **<FILL — 핵심 영역>** |
| planning | <FILL> | <FILL> | <FILL> |

특히 **synthesis 카테고리** 가 H11 의 핵심 효과 영역 (Stage 2C H4 회복 정합).

### Step 6 — H11 verdict 결정 트리

```
if extractor - baseline ≥ +0.10 + p < 0.05:
    verdict = "✅ 채택" (Extractor 가 명확한 보완)
elif extractor - baseline ≥ +0.05:
    verdict = "✅ 조건부 채택"
elif |Δ| < 0.05:
    verdict = "⚠ 미결"
elif extractor - baseline < 0:
    verdict = "❌ 기각" (Extractor 가 baseline 보다 약함 — 추론 chain 단절 또는 schema mismatch)
```

**Architect 사전 예측** (확률):
- ✅ 채택: 30% (synthesis 카테고리에서 명확한 우위)
- ⚠ 조건부: 30%
- ⚠ 미결: 25%
- ❌ 기각: 15% (Exp11 정반대 메커니즘 학습 — Extractor 가 추론 chain 단절 가능성, 단 같은 모델이라 risk 작음)

### Step 7-11 — 분석 보고서 + 문서 갱신

Exp11 task-05 패턴 그대로:
- Step 7: `docs/reference/exp12-extractor-role-analysis-<TS>.md` 신규 (15 섹션)
- Step 8: `docs/reference/results/exp-12-extractor-role.md` 신규
- Step 9: `researchNotebook.md` H11 entry + Exp12 섹션
- Step 10: `researchNotebook.en.md` Closed 추가만
- Step 11: README 갱신 (사용자 결정 의무)

## Dependencies

- task-04 마감 (사용자 직접)
- Stage 2C `experiments/exp_h4_recheck/analyze.py` — `count_assertion_turnover` + `classify_error_mode` 재사용
- 패키지: `scipy.stats`

## Verification

Exp11 task-05 의 Verification 5종 그대로:

```bash
# 1) 분석 보고서 placeholder 0
grep -E '<FILL[^>]*>' docs/reference/exp12-extractor-role-analysis-*.md | wc -l

# 2) result.md exp-12 신규 + frontmatter
.venv/Scripts/python -c "
text = open('docs/reference/results/exp-12-extractor-role.md', encoding='utf-8').read()
assert 'experiment: 실험 12' in text
print('verification 2 ok: exp-12 result.md')
"

# 3) researchNotebook H11 entry
grep -c "H11" docs/reference/researchNotebook.md

# 4) 영문 노트북 추가만 (기존 H 표 변경 0)
grep -c "Exp12" docs/reference/researchNotebook.en.md

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

- **Risk 1 — H11 기각 결과** (Extractor 가 baseline 보다 약함) — Exp11 정반대 메커니즘 재발 가능. 단 같은 모델 사용으로 risk 작음. 발생 시 disclosure + Stage 5 의 다음 축 (Search Tool) 우선 권장
- **Risk 2 — synthesis 카테고리 효과 미관측** — Stage 2C H4 회복 + Extractor 효과 = 강화 기대. 단 효과 0 면 H11 미결 + 다른 카테고리 영향 분석 의무
- **Risk 3 — Extractor 결과 미보존**으로 직접 메커니즘 측정 어려움 — assertion turnover + first cycle 패턴으로 간접
- **Risk 4 — 영문 노트북 정책 위반** — 기존 H1~H10 entry 변경 절대 금지. Verification 4 의 grep 으로 검증

## Scope boundary

본 task 에서 **수정 금지** 파일:
- 모든 코드 (`experiments/*.py`) — read-only
- 결과 JSON (모두 read-only)
- 본 plan 의 다른 subtask 영역
- 다른 reference 문서 (analysis + result.md exp-12 만 신규, researchNotebook 한·영 만 수정)
- 다른 result.md (exp-00 ~ exp-11) — 변경 금지
- conceptFramework.md / namingConventions.md / 기타 canonical reference — 변경 금지

## 사용자 호출 시점

- Step 6 의 verdict 결정 트리에서 ❌ 기각
- Step 11 의 README 갱신 — 사용자 결정 의무
- Risk 1/2 발견 시
