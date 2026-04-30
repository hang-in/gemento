---
type: task
status: pending
updated_at: 2026-04-29
parent_plan: phase-1-v2-exp09
task_number: 4
title: "Exp09 통계 검정 스크립트"
depends_on: [3]
parallel_group: B
---

# Task 04: Exp09 통계 검정 스크립트

## Changed files

- `experiments/exp09_longctx/analyze_stats.py` — **신규 생성**
- `experiments/exp09_longctx/results/exp09_stats_<timestamp>.json` — 분석 결과 (자동 생성)

## Change description

### 4.1 목적

5-trial 데이터(Task 03 산출물)를 기반으로 H9b(+3.3%p)의 통계적 유의성을 검정하고, Small Paradox를 하위 분석한다.

### 4.2 입력

- 5-trial 결과 JSON: `experiments/exp09_longctx/results/exp09_longctx_5trial_*.json` (Task 03 산출물)
- Taskset: `experiments/tasks/longctx_taskset.json`
- 채점 함수: `experiments/measure.py` → `score_answer_v2`

### 4.3 분석 항목

**항목 1: Per-task 정확도 계산**
- 각 (arm, task)에 대해 5 trial의 v2 점수 평균 계산
- 10 tasks × 3 arms = 30 task-level 평균

**항목 2: H9b 주 검정 — abc_tattoo vs rag_baseline**
- Paired data: 10개 task에 대해 (abc_mean, rag_mean) 쌍
- **검정 1**: Paired t-test (`scipy.stats.ttest_rel`)
  - H₀: μ(abc) - μ(rag) = 0
  - H₁: μ(abc) - μ(rag) ≠ 0
- **검정 2**: Wilcoxon signed-rank test (`scipy.stats.wilcoxon`)
  - 비모수 대안 (표본 10개로 정규성 가정 위험)
- 보고: t-statistic, p-value, effect size (Cohen's d), 판정 (α=0.05)

**항목 3: Bootstrap 95% CI**
- Trial-level 점수 (50 per arm)에 대한 mean의 bootstrap CI
- N=10,000, seed=42 (Exp06 reconciliation과 동일 방법론)
- abc - rag 차이의 CI: 0을 포함하면 비유의

**항목 4: Size class 분해**
- small / medium / large 별로 abc vs rag 비교
- 각 size class 내 paired test (태스크 수가 적으므로 — small 2개, medium 4개, large 4개 — Wilcoxon 또는 기술 통계만)

**항목 5: Hop type 분해**
- needle / 2-hop / 3-hop 별 abc vs rag
- 3-hop: 기존 +33%p가 5-trial에서도 유지되는지

**항목 6: Small Paradox 하위 분석**
- small task만 추출 (2 tasks × 5 trials = 10 data points/arm)
- abc vs rag 비교: 기존 3-trial에서 abc 0.67 vs rag 1.00이었음
- 5-trial로 noise vs 실제 패턴 판별
- 개별 task별 trial 결과 전수 출력

**항목 7: abc_tattoo vs solo_dump (참고)**
- H9a는 이미 확정(+68.3%p)이므로 참고용 통계만
- Large task에서 solo의 format_error 비율 확인

### 4.4 출력 형식

```
═══════════════════════════════════════════════
  Exp09 Statistical Analysis (5-trial)
═══════════════════════════════════════════════

  H9b: abc_tattoo vs rag_baseline
  ─────────────────────────────────────────────
  Overall mean:  abc=0.XXX  rag=0.XXX  Δ=+X.X%p
  Paired t-test: t=X.XX, p=0.XXX, Cohen's d=X.XX
  Wilcoxon:      W=XX, p=0.XXX
  Bootstrap 95% CI for Δ: [X.XXX, X.XXX]
  → Verdict: [Significant / Not significant] at α=0.05

  Size class breakdown:
  ─────────────────────────────────────────────
  small  (n=2):  abc=0.XXX  rag=0.XXX  Δ=X.X%p  [Small Paradox: ...]
  medium (n=4):  abc=0.XXX  rag=0.XXX  Δ=X.X%p
  large  (n=4):  abc=0.XXX  rag=0.XXX  Δ=X.X%p

  ...
```

JSON 저장: `experiments/exp09_longctx/results/exp09_stats_<timestamp>.json`

### 4.5 코드 구조

```
experiments/exp09_longctx/analyze_stats.py
├── _load_5trial_result() → dict
├── _compute_task_means(results_by_arm, task_ids) → dict[arm][task] = mean
├── _paired_ttest(abc_means, rag_means) → dict(t, p, cohens_d)
├── _wilcoxon_test(abc_means, rag_means) → dict(W, p)
├── _bootstrap_ci(scores_a, scores_b, n=10000, seed=42) → dict
├── _analyze_by_group(results, group_key) → dict  # size_class 또는 hop_type
├── _small_paradox_detail(results) → dict
├── _print_report(analysis)
└── main()
```

### 4.6 H9b verdict 결정 로직

스크립트가 자동으로 verdict를 제안:
- p < 0.05 (both tests) + CI excludes 0 + Δ > 0 → **"채택 (Supported)"**
- p < 0.05 (one test) → **"조건부 채택 유지 (Conditionally supported)"**
- p ≥ 0.05 (both tests) → **"미결 (Inconclusive)"** 또는 **"기각 후보"**

최종 verdict는 Task 05에서 사람이 확인 후 문서에 반영.

## Dependencies

- Python 패키지: `scipy` (stats.ttest_rel, stats.wilcoxon), `numpy` (선택)
- 다른 subtask: **Task 3 완료 필수** (5-trial 결과 JSON 필요)
- 채점: `experiments/measure.py` → `score_answer_v2` import

## Verification

```bash
# 1. 5-trial 결과 파일이 있는 상태에서 스크립트 실행
python -m experiments.exp09_longctx.analyze_stats 2>&1 | tail -10
# 기대: "ANALYSIS COMPLETE" 포함, p-value 출력

# 2. 결과 JSON 생성 확인
ls experiments/exp09_longctx/results/exp09_stats_*.json | wc -l
# 기대: 1 이상

# 3. 결과 JSON에 필수 키 존재 확인
python -c "
import json, glob
files = sorted(glob.glob('experiments/exp09_longctx/results/exp09_stats_*.json'))
d = json.load(open(files[-1]))
required = ['h9b_paired_ttest', 'h9b_wilcoxon', 'bootstrap_ci', 'size_class_breakdown', 'small_paradox']
missing = [k for k in required if k not in d]
assert not missing, f'Missing keys: {missing}'
print(f'All required keys present. H9b p-value (ttest): {d[\"h9b_paired_ttest\"][\"p_value\"]:.4f}')
print('OK')
"
# 기대: All required keys present. H9b p-value (ttest): X.XXXX, OK

# 4. 문법 체크
python -c "import ast; ast.parse(open('experiments/exp09_longctx/analyze_stats.py').read()); print('Syntax OK')"
# 기대: Syntax OK
```

## Risks

- **표본 크기 제한**: 10 tasks로 paired test의 검정력이 낮음. 큰 effect size가 아니면 p > 0.05 가능성 높음 — 이것은 실패가 아니라 정당한 "미결" 결론.
- **size class 분해 시 n 부족**: small=2 tasks, medium=4, large=4. 하위 그룹 paired test는 검정력 극히 낮음 → 기술 통계(mean, range)만 보고, p-value는 참고용으로만 표기.
- **scoring 일관성**: Task 01에서 v2 역행 원인이 밝혀진 후 채점 정책이 변경되면, Exp09 점수도 재계산 필요. 단 Exp09는 longctx 태스크셋이므로 base taskset의 v2 역행과 무관할 가능성 높음.
- **scipy 미설치**: ttest_rel, wilcoxon import 실패 시 graceful skip + 경고.

## Scope boundary

수정 금지 파일:
- `experiments/exp09_longctx/run.py` — Task 3 영역
- `experiments/exp09_longctx/run_append_trials.py` — Task 3 영역
- `experiments/exp09_longctx/results/exp09_longctx_20260425_144412.json` — 원본 보존
- `experiments/measure.py` — 읽기(import)만 허용
- `docs/` 하위 모든 파일 — Task 5 영역
