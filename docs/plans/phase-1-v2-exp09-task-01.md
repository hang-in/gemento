---
type: task
status: pending
updated_at: 2026-04-29
parent_plan: phase-1-v2-exp09
task_number: 1
title: "v2 역행 진단 스크립트"
depends_on: []
parallel_group: A
---

# Task 01: v2 역행 진단 스크립트

## Changed files

- `experiments/scoring_diagnostic.py` — **신규 생성**
- `experiments/scoring_diagnostic_results/` — **신규 디렉토리** (분석 결과 JSON 저장)

## Change description

### 1.1 목적

Exp04(v1=0.607, v2=0.583)와 Exp05a(v1=0.636, v2=0.583)에서 v2가 v1보다 낮은 근본 원인을 trial 단위로 진단한다. "v1 pass + v2 fail" 패턴을 식별하고, 해당 trial의 response와 keyword group을 대조해 역행 원인을 분류한다.

### 1.2 구현 단계

**단계 1: 데이터 로딩**
- Exp04 결과: `experiments/exp04_abc_pipeline/results/exp04_abc_pipeline_20260409_182751.json`
- Exp05a 결과: `experiments/exp05a_prompt_enhance/results/exp05a_prompt_enhance_20260410_145033.json`
- Taskset: `experiments/tasks/taskset.json`
- 기존 `experiments/measure.py`에서 `score_answer`, `score_answer_v2`, `score_answer_v3` import

**단계 2: trial별 재채점**
- 각 실험의 모든 trial에 대해 v1/v2/v3 점수를 재계산
- v1과 v2의 차이(Δ = v1 - v2)를 trial별로 기록
- Δ > 0인 trial (v1이 더 높은, 즉 v2 역행 trial)을 식별

**단계 3: 역행 원인 분류**
- 각 역행 trial에서:
  - `final_answer` 텍스트 (첫 200자)
  - `expected_answer` 텍스트
  - `scoring_keywords` 그룹별 매칭 결과 (어느 그룹이 실패했는지)
  - v1의 어떤 경로로 점수를 얻었는지 (full substring → 1.0 / token subset → 0.8 / partial overlap → 0.6×ratio)
- 역행 패턴 분류:
  - **Type A**: v1 substring match(1.0) but v2 keyword group partial fail
  - **Type B**: v1 token subset(0.8) but v2 group miss
  - **Type C**: v1 partial overlap(>0) but v2 zero groups matched
  - **Type D**: 기타

**단계 4: 출력**
- 터미널 테이블: 실험별 → task별 → trial별 v1/v2/v3 + Δ + 역행 유형
- 요약 테이블: 역행 유형별 빈도, 영향받는 task/keyword group 패턴
- JSON 저장: `experiments/scoring_diagnostic_results/v2_regression_<timestamp>.json`

**단계 5: 채점 정책 권고**
- 스크립트 마지막에 human-readable 요약 출력:
  - 역행이 특정 task/keyword group에 집중되는지
  - v2 keyword 정의 개선으로 해결 가능한지
  - v3로 전면 전환하면 해결되는지
  - 현행 유지가 합리적인지 (역행 규모가 미미한 경우)

### 1.3 코드 구조

```
experiments/scoring_diagnostic.py
├── _load_experiment(json_path) → list[dict]
├── _rescore_trial(response, task_entry) → dict(v1, v2, v3, v1_path)
├── _classify_regression(v1_score, v2_score, v1_path, keyword_groups, response) → str
├── _print_table(results)
├── _print_summary(results)
└── main()
```

`v1_path` 는 v1이 어떤 분기로 점수를 부여했는지 기록하는 필드:
- `"substring"` (line 30: `expected_lower in response_lower` → 1.0)
- `"token_subset"` (line 35: `expected_tokens.issubset` → 0.8)
- `"partial_overlap"` (line 40: `overlap / expected_tokens * 0.6`)
- `"zero"` (0.0)

이를 위해 measure.py의 score_answer 내부 분기를 외부에서 재현하되, **measure.py 자체는 수정하지 않는다**. scoring_diagnostic.py 내부에 `_score_answer_with_path()` 헬퍼를 구현.

## Dependencies

- Python 패키지: 없음 (표준 라이브러리 + 기존 measure.py)
- 다른 subtask: 없음 (parallel_group A)

## Verification

```bash
# 1. 스크립트 실행 (에러 없이 완료)
python -m experiments.scoring_diagnostic 2>&1 | tail -5
# 기대: 마지막 줄에 "DIAGNOSTIC COMPLETE" 또는 유사 완료 메시지

# 2. JSON 결과 파일 생성 확인
ls experiments/scoring_diagnostic_results/v2_regression_*.json | wc -l
# 기대: 1 이상

# 3. 역행 trial 식별 확인 (Exp04 또는 Exp05a에서 Δ > 0인 trial 존재)
python -c "
import json, glob
f = sorted(glob.glob('experiments/scoring_diagnostic_results/v2_regression_*.json'))[-1]
d = json.load(open(f))
regressed = [t for t in d.get('trials', []) if t.get('delta_v1_v2', 0) > 0]
print(f'Regressed trials: {len(regressed)}')
assert len(regressed) > 0, 'Expected at least 1 regressed trial'
print('OK')
"
# 기대: Regressed trials: N (N > 0), OK

# 4. 타입 체크
python -c "import ast; ast.parse(open('experiments/scoring_diagnostic.py').read()); print('Syntax OK')"
# 기대: Syntax OK
```

## Risks

- **v1 분기 재현 정확도**: `_score_answer_with_path()`가 `measure.py:score_answer`와 동일한 분기 로직을 가져야 함. `score_answer` 업데이트 시 sync 필요 — 단, 이 플랜에서 measure.py 수정은 금지이므로 위험 낮음.
- **response 인코딩**: Exp04/05a JSON의 `final_answer`에 한국어나 유니코드 문자가 포함될 수 있음. `lower()` 처리 시 로케일 이슈 없는지 확인.
- **None 처리**: 일부 trial에서 `final_answer`가 `null`일 수 있음 (수렴 실패). 빈 문자열로 처리.

## Scope boundary

수정 금지 파일:
- `experiments/measure.py` — 읽기만 허용 (import), 수정 금지
- `experiments/exp04_abc_pipeline/` — 읽기만 허용
- `experiments/exp05a_prompt_enhance/` — 읽기만 허용
- `experiments/tasks/taskset.json` — 읽기만 허용 (Task 2 영역)
- `docs/reference/researchNotebook.md` — Task 5 영역
- `README.ko.md`, `README.md` — Task 5 영역
