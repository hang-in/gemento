---
type: plan-task
status: todo
updated_at: 2026-05-02
parent_plan: exp11-mixed-intelligence-haiku-judge
parallel_group: E
depends_on: [04]
---

# Task 05 — 분석 + H10 verdict + 문서 갱신

## Changed files

- `docs/reference/exp11-mixed-intelligence-analysis-<TS>.md` — **신규**. 분석 보고서
- `docs/reference/results/exp-11-mixed-intelligence.md` — **신규**. result.md
- `docs/reference/researchNotebook.md` (한국어) — **수정**. H10 가설 신규 entry + Exp11 섹션 추가
- `docs/reference/researchNotebook.en.md` — **수정 (Closed 추가만)**. "Exp11 Mixed Intelligence note (2026-MM-DD)" 신규 단락
- (조건부) `README.md` / `README.ko.md` — H10 채택 시 H 표 + Headline 갱신 (사용자 결정)

신규 2, 수정 2-3.

## Change description

### 배경

Task 04 의 실험 결과 (150 trial) 를 분석하여 H10 verdict 결정. Exp10 의 cost-aware 3축 (정확도/비용/지연) + Stage 2C 의 ablation (정확도/turnover/error) 종합.

### Step 1 — 결과 통합 + condition aggregate

```python
# experiments/exp11_mixed_intelligence/analyze.py 또는 inline script
import json
from collections import defaultdict

files = ['experiments/exp11_mixed_intelligence/results/exp11_baseline_abc.json',
         'experiments/exp11_mixed_intelligence/results/exp11_mixed_flash_judge.json']
all_trials = []
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    all_trials.extend(d['trials'])

# condition × task aggregate
agg = defaultdict(lambda: {"n":0,"acc":0.0,"cost":0.0,"dur":0,"turnover_added":0,"turnover_modified":0})
for t in all_trials:
    cond = t['condition']; tid = t['task_id']
    agg[(cond, tid)]["n"] += 1
    agg[(cond, tid)]["acc"] += t.get('accuracy_v3', 0)
    agg[(cond, tid)]["cost"] += (t.get('flash_cost') or {}).get('total_cost_usd', 0)
    agg[(cond, tid)]["dur"] += t.get('duration_ms', 0)
    # turnover (Stage 2C analyze.py 의 count_assertion_turnover 재사용)
    from experiments.exp_h4_recheck.analyze import count_assertion_turnover, classify_error_mode
    turn = count_assertion_turnover(t.get('tattoo_history'))
    agg[(cond, tid)]["turnover_added"] += turn['added']
    agg[(cond, tid)]["turnover_modified"] += turn['modified']
```

### Step 2 — ablation 분석 (n=15 task paired)

H10 본 가설 = `mixed_flash_judge − baseline_abc`:

```
abc_per[i]   = baseline_abc 의 task i mean acc
mixed_per[i] = mixed_flash_judge 의 task i mean acc

Δ = mixed_per[i] - abc_per[i]  (n=15)

mean Δ
median Δ
std Δ
Wilcoxon W, p
paired t-test t, p
Cohen's d (paired)
Bootstrap 95% CI Δ
```

추가 비교 (Stage 2C abc 와의 비교 — 옵션):
- Stage 2C abc (75 trial, mean=0.7589) vs 본 plan baseline_abc — 같은 도구, 다른 시점. 회귀 검증

### Step 3 — cost-aware 3축 (Exp10 패턴)

| condition | mean_acc | total_cost | trial 당 cost | avg_dur | err+null |
|-----------|---------:|-----------:|--------------:|--------:|---------:|
| baseline_abc | 0.X | $0.0000 | $0.000 | Y min | Z |
| mixed_flash_judge | 0.X | $X.XX | $X.XX | Y min | Z |

cost-aware 비교:
- Δ acc per $: mixed 의 추가 비용 ($X.XX) 대비 acc 증가 (Δ)
- 정확도 vs 비용 trade-off 명료화

### Step 4 — assertion turnover (Stage 2C 결함 fix 후 첫 측정)

| condition | added (mean) | modified (mean) | final_count (mean) |
|-----------|-------------:|----------------:|-------------------:|
| baseline_abc | X.XX | X.XX | X.XX |
| mixed_flash_judge | X.XX | X.XX | X.XX |

Stage 2C 의 결함 (ABC turnover=0) 회복 — cycle-by-cycle 저장 확인. mixed 의 turnover_modified 가 baseline 보다 크면 "Flash Judge 가 A 의 assertion 을 수정시킴" — H10 의 직접 증거.

### Step 5 — error mode (FailureLabel)

Stage 2B FailureLabel 분류:

| condition | NONE | FORMAT | WRONG_SYN | NULL | OTHER | CONN | TIMEOUT |
|-----------|----:|-------:|----------:|----:|------:|-----:|--------:|
| baseline_abc | ... | ... | ... | ... | ... | ... | ... |
| mixed_flash_judge | ... | ... | ... | ... | ... | ... | ... |

mixed 의 NONE 비율이 baseline 보다 크면 정답 안정성 우위 (질적 차이).

### Step 6 — H10 verdict 결정 트리

```
if mixed - baseline_abc ≥ +0.10 AND p < 0.05:
    verdict = "✅ 채택" (강한 Judge 의 명확한 보완 효과)
elif mixed - baseline_abc ≥ +0.05 AND p < 0.05:
    verdict = "✅ 조건부 채택" (격차 + 통계적 유의성)
elif mixed - baseline_abc ≥ +0.05 AND p ≥ 0.05:
    verdict = "⚠ 조건부 채택" (격차 있으나 검정력 부족)
elif |mixed - baseline_abc| < 0.05:
    verdict = "⚠ 미결" (격차 작음, sample 한계)
elif mixed - baseline_abc < 0:
    verdict = "❌ 기각" (Mixed 가 baseline 보다 약함 — Flash 의 reasoning 흡수 또는 schema mismatch 가능)
```

추가 검증:
- Δ ≥ +0.20 + per-task Δ 가 모든 task 에 양수면 **cherry-pick 의심** disclosure (Risk 5)
- synthesis 카테고리 효과 (Stage 2C 회복 핵심) — mixed 도 synthesis 우위인가?

### Step 7 — 분석 보고서 작성

`docs/reference/exp11-mixed-intelligence-analysis-<TS>.md` (날짜 stamp) 신규:

구조 (Stage 2C 의 h4-recheck-analysis 패턴):
1. 결과 요약
2. condition aggregate
3. ablation (mixed - baseline)
4. 카테고리별 break-down
5. per-task break-down
6. 통계 검정
7. cost-aware 3축
8. assertion turnover (cycle-by-cycle, Stage 2C 결함 fix 후 첫 측정)
9. error mode 분포
10. H10 verdict
11. Stage 2C 와 비교 (baseline_abc 회귀)
12. 함의 (Mac 핸드오프 §5 Stage 5 SQLite 재검토 / Search Tool Exp12 후보)
13. 한계
14. 향후 보강

### Step 8 — `docs/reference/results/exp-11-mixed-intelligence.md` 신규

기존 result.md 패턴 (exp-10-reproducibility-cost.md 등). frontmatter:

```yaml
---
type: result
status: done
updated_at: 2026-MM-DD
experiment: 실험 11 — Mixed Intelligence (Flash Judge)
---
```

핵심 §1~§7 (Exp10 패턴):
- 개요
- 핵심 메트릭 (cost-aware 3축)
- per-task 정답률
- 분석 (H10 verdict 근거 + ablation)
- 패치 disclosure (없으면 생략)
- error mode + cost
- 결론 + 다음 단계

### Step 9 — `researchNotebook.md` 갱신

H 가설 표에 H10 신규 entry:

```markdown
| **H10** | **[Role 외부화 강화 — Mixed Intelligence]** 강한 Judge C (Gemini 2.5 Flash) 가 약한 Proposer/Critic (A/B = Gemma E4B) 의 한계를 보완한다 | <NEW VERDICT> (Δ <FILL>, 통계 <FILL>, cost <FILL>) | Exp11 |
```

Exp11 섹션 신규 — 6하원칙 + 결과 + 다음 단계.

### Step 10 — `researchNotebook.en.md` 갱신 (Closed 추가만)

기존 H 가설 표 / 영문 수치 변경 0. 신규 단락:

```markdown
### Exp11 — Mixed Intelligence (Flash Judge) note (2026-MM-DD)

A follow-up experiment (`exp11-mixed-intelligence-haiku-judge` slug; Flash Judge after v2 plan revision) tested H10 — whether
a stronger Judge C (Gemini 2.5 Flash) compensates for weaker Proposer/Critic (Gemma 4 E4B).
...
[ablation, statistics, verdict, cost-aware]

H10 verdict: <FILL>.

Detail: `docs/reference/exp11-mixed-intelligence-analysis-<TS>.md`.
```

### Step 11 — README 조건부 갱신 (사용자 결정)

| H10 verdict | README 영향 |
|-------------|-----------|
| ✅ 채택 (+0.10 이상) | H 표 추가 + Headline 갱신 ("Mixed Intelligence: +X%p with Flash Judge") + Roadmap |
| ✅/⚠ 조건부 채택 (+0.05~) | H 표 추가 |
| ⚠ 미결 | H 표 추가 (verdict 명시) |
| ❌ 기각 | H 표 추가 + 사용자 검토 (외부 노출 톤) |

**사용자 결정 의무**. Sonnet 임의 갱신 금지.

## Dependencies

- task-04 마감 (사용자 직접 실행)
- Stage 2C `experiments/exp_h4_recheck/analyze.py` (turnover + error mode helper)
- 패키지: `scipy.stats` (Wilcoxon / t-test)

## Verification

```bash
# 1) 분석 보고서 placeholder 0
grep -E '<FILL[^>]*>' docs/reference/exp11-mixed-intelligence-analysis-*.md | wc -l
# 기대: 0

# 2) result.md exp-11 신규 + frontmatter
.venv/Scripts/python -c "
text = open('docs/reference/results/exp-11-mixed-intelligence.md', encoding='utf-8').read()
assert 'experiment: 실험 11' in text
assert 'mean_acc' in text or '정확도' in text
print('verification 2 ok: exp-11 result.md')
"

# 3) researchNotebook H10 entry
.venv/Scripts/python -c "
text = open('docs/reference/researchNotebook.md', encoding='utf-8').read()
assert 'H10' in text
assert 'Mixed Intelligence' in text or '혼합 지능' in text
print('verification 3 ok: researchNotebook H10 entry')
"

# 4) 영문 노트북 추가만 (기존 H 표 변경 0)
grep -c 'Exp11' docs/reference/researchNotebook.en.md
# 기대: 1+ (신규 단락만 추가, 기존 표 변경 0)

# 5) 한·영 README 외부 노출 톤 (banned 명칭)
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

- **Risk 1 — H10 기각 결과 (mixed < baseline)**: Flash 가 Tattoo schema 와 mismatch / reasoning 흡수 안 됨 / 다른 원인. disclosure 명시. Stage 5 (SQLite / Search) 동기 흔들림 — 사용자 호출
- **Risk 2 — Mixed 의 turnover 측정 결함 재발**: task-03 의 cycle-by-cycle 저장 fix 가 정상 작동했는지 dry-run 시 검증. 미작동 시 사용자 호출
- **Risk 3 — Flash 비용 임계 초과**: task-04 의 Step 4 모니터링 (~\$1+ 시 비정상). 본 task 시점에 발견되면 disclosure
- **Risk 4 — 영문 노트북 정책 위반**: 기존 H 표 (H1~H9c) 변경 절대 금지. Verification 4 의 grep + Architect 시각 검토

## Scope boundary

본 task 에서 **수정 금지** 파일:
- 모든 코드 (`experiments/*.py`) — read-only
- 결과 JSON (모두 read-only)
- 본 plan 의 다른 subtask 영역
- 다른 reference 문서 (analysis + result.md exp-11 만 신규, researchNotebook 한·영 만 수정)
- 다른 result.md (exp-00 ~ exp-10) — 변경 금지
- conceptFramework.md / namingConventions.md / 기타 canonical reference — 변경 금지

## 사용자 호출 시점

- Step 6 의 verdict 결정 트리에서 ❌ 기각 또는 cherry-pick 의심
- Step 11 의 README 갱신 — 사용자 결정 의무
- Risk 1/2/3 발견 시
