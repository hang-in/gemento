---
type: task
status: pending
updated_at: 2026-04-29
parent_plan: exp06-h4-scoring-reconciliation-h4-verdict
task_number: 1
title: "Exp06 scoring reconciliation 분석 스크립트"
depends_on: []
parallel_group: A
---

# Task 01: Exp06 scoring reconciliation 분석 스크립트

## Changed files

- `experiments/exp06_solo_budget/analyze_reconciliation.py` — **신규 생성**

## Change description

Solo 45 trial + ABC 45 trial을 v1/v2/v3 동일 채점으로 비교하는 독립 분석 스크립트.

### 구현 단계

1. **데이터 로딩**
   - Solo: `experiments/exp06_solo_budget/results/exp06_solo_budget_20260415_114625.json`
   - ABC: `experiments/exp045_handoff_protocol/results/exp045_handoff_protocol_20260414_135634.json`
   - Tasks: `experiments/tasks/taskset.json`
   - Solo의 9-task subset만 사용 (`math-01/02/03`, `logic-01/02/03`, `synthesis-01/02/03`)

2. **채점 (3개 버전)**
   - 각 trial에 대해 `score_answer` (v1), `score_answer_v2`, `score_answer_v3` 산출
   - `experiments/measure.py:14` (`score_answer`), `:39` (`score_answer_v2`), `:65` (`score_answer_v3`) 임포트

3. **per-task break-down 테이블**
   - 각 task별: Solo mean (v1/v2/v3), ABC mean (v1/v2/v3), Δ, winner
   - 전체 mean (45 trial 평균)

4. **task-level metric (8/9 가설 검증)**
   - 다양한 정의로 "task correct" 판정:
     - (a) `any trial v1 ≥ 0.5` per task
     - (b) `any trial v2 ≥ 0.5` per task
     - (c) `task v2 mean ≥ 0.75` per task
   - 각 정의에서 ABC / Solo 의 task correct count 산출
   - `v2 mean ≥ 0.75` → ABC 8/9 = 88.9% 인지 검증 (정찰에서 확인됨)

5. **"88.9%" 재현 시도**
   - trial-level: v1 > {0.0, 0.1, 0.2, 0.3, 0.4, 0.5} threshold 별 correct count
   - task-level: 위 (a)(b)(c) 결과
   - 어떤 조합이 40/45 또는 8/9 를 재현하는지 보고

6. **95% CI (bootstrap)**
   - Solo 45 trial / ABC 45 trial 각각의 mean accuracy에 대해
   - 10,000회 bootstrap resampling → 2.5~97.5 percentile
   - v1, v2 각각 산출

7. **출력**
   - 터미널: 구조화된 테이블 (per-task, overall, task-level, 88.9% 재현, CI)
   - 마지막 줄: `RECONCILIATION COMPLETE`
   - JSON summary: `experiments/exp06_solo_budget/results/exp06_reconciliation_<timestamp>.json`

### 스크립트 실행 방법

```bash
.venv/Scripts/python.exe -m experiments.exp06_solo_budget.analyze_reconciliation
```

또는 Mac:

```bash
.venv/bin/python -m experiments.exp06_solo_budget.analyze_reconciliation
```

## Dependencies

- `experiments/measure.py` (score_answer, score_answer_v2, score_answer_v3)
- `experiments/tasks/taskset.json`
- 표준 라이브러리: `json`, `random`, `time`, `pathlib`
- **외부 패키지 추가 불필요** (bootstrap는 표준 random으로 구현)

## Verification

```bash
# 1. 스크립트 실행 + 정상 종료 확인
.venv/Scripts/python.exe -m experiments.exp06_solo_budget.analyze_reconciliation

# 2. 출력 마지막 줄에 RECONCILIATION COMPLETE 포함 확인
.venv/Scripts/python.exe -m experiments.exp06_solo_budget.analyze_reconciliation 2>&1 | tail -1
# 기대: RECONCILIATION COMPLETE

# 3. JSON summary 파일 생성 확인
ls experiments/exp06_solo_budget/results/exp06_reconciliation_*.json

# 4. JSON에 필수 키 존재 확인
.venv/Scripts/python.exe -c "
import json, glob
f = sorted(glob.glob('experiments/exp06_solo_budget/results/exp06_reconciliation_*.json'))[-1]
d = json.load(open(f))
required = ['per_task', 'overall', 'task_level_metrics', 'reproduce_889', 'bootstrap_ci']
missing = [k for k in required if k not in d]
print('PASS' if not missing else f'FAIL: missing {missing}')
"
```

## Risks

- **bootstrap CI 재현성**: `random.seed` 고정하지 않으면 매 실행마다 CI 미세 변동. CI 값 자체는 문서 고정치가 아니므로 문제 없음 (JSON에 기록).
- **score_answer v1 특성**: v1은 partial score (0.0~1.0 연속값). binary threshold 선택에 따라 해석 달라짐 — 복수 threshold 동시 보고로 대응.

## Scope boundary

수정 금지 파일:
- `experiments/measure.py` — read-only 임포트만
- `experiments/tasks/taskset.json` — read-only
- `experiments/exp06_solo_budget/run.py` — 변경 금지
- `experiments/exp06_solo_budget/results/exp06_solo_budget_20260415_114625.json` — read-only
- `experiments/exp045_handoff_protocol/results/exp045_handoff_protocol_20260414_135634.json` — read-only
- `experiments/config.py` — 변경 금지
