---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: exp06-h4-recheck-expanded-taskset-pre-exp11
parallel_group: D
depends_on: [01, 02, 03]
prerequisites: Stage 2A 마감 (healthcheck/abort + 결과 JSON meta v1.0)
---

# Task 04 — 실험 실행 (사용자 직접) — 15 × 3 × 5 = 225 trial

## Changed files

- `experiments/exp_h4_recheck/results/exp_h4_recheck_<TS>.json` — **신규 출력** (사용자 실행)

신규 1, 수정 0.

## Change description

### 배경

본 task 는 **사용자 직접 실행** (메모리 정책 `feedback_agent_no_experiment_run.md`). Architect/Developer 는 명령 명시 + 사전 체크 + 사후 결과 보고서 placeholder 작성까지.

### Step 1 — 사전 체크 (사용자 실행 전 의무)

```powershell
# 1a) Stage 2A 마감 검증 — healthcheck/abort + meta v1.0 helper 모두 import 가능
.\.venv\Scripts\python.exe -c "
from experiments.run_helpers import (
    classify_trial_error, is_fatal_error, check_error_rate,
    build_result_meta, get_taskset_version, normalize_sampling_params,
)
print('ok: Stage 2A helper 마감')
"

# 1b) Task 01 마감 — 15 task 확인
.\.venv\Scripts\python.exe -m experiments.validate_taskset
# 기대: 25 PASS / 0 FAIL (taskset 15 + longctx 10)

# 1c) Task 02 마감 — exp_h4_recheck/run.py 의 import + help
.\.venv\Scripts\python.exe -m experiments.exp_h4_recheck.run --help
# 기대: usage 출력

# 1d) Task 03 마감 — analyze.py import
.\.venv\Scripts\python.exe -c "from experiments.exp_h4_recheck.analyze import analyze, classify_error_mode; print('ok')"

# 1e) lmstudio API 가용성
curl -s http://192.168.1.179:1234/v1/models | head -5
# 또는 실험 자체가 connection check 자체 — Stage 2A 의 healthcheck/abort 가 단발 fail 시 즉시 abort
```

위 5 명령 모두 통과 후 Step 2 진행.

### Step 2 — 짧은 dry-run (1 task × 1 trial × 1 condition)

전체 실행 전 작은 입력으로 정합성 확인:

```powershell
.\.venv\Scripts\python.exe -m experiments.exp_h4_recheck.run `
  --taskset experiments/tasks/taskset.json `
  --trials 1 `
  --conditions solo_1call `
  --max-cycles 8 `
  --out-name dryrun_solo_1call.json
```

기대:
- stdout 에 condition aggregate 출력 (solo_1call n=15? 아니, --trials 1 라 task 15 × trial 1 = 15)
- 새 파일 `experiments/exp_h4_recheck/results/dryrun_solo_1call.json` 생성
- top-level meta: schema_version="1.0" + model + sampling_params + scorer_version + taskset_version
- error 비율 < 30% (정상 run)

dry-run 통과 후 본 실행.

### Step 3 — 본 실행 (전체 225 trial)

**시간 예상** (Risk 3):
- Solo-1call: 15 task × 5 trial = 75 trial. 단발 호출 ~30s/trial → ~37 min
- Solo-budget: 15 task × 5 trial = 75 trial. 8 cycle × 30s = ~4 min/trial → ~5 시간
- ABC: 15 task × 5 trial = 75 trial. 8 cycle × 3 model call × 30s = ~12 min/trial → ~15 시간

**총 예상**: ~20 시간. 분할 권장 (사용자 결정).

#### 분할 옵션 A — condition 별 분할 (권장)

```powershell
# 1) Solo-1call (~37 min)
.\.venv\Scripts\python.exe -m experiments.exp_h4_recheck.run `
  --conditions solo_1call --trials 5 --max-cycles 8 `
  --out-name h4_recheck_solo_1call.json

# 2) Solo-budget (~5 hr)
.\.venv\Scripts\python.exe -m experiments.exp_h4_recheck.run `
  --conditions solo_budget --trials 5 --max-cycles 8 `
  --out-name h4_recheck_solo_budget.json

# 3) ABC (~15 hr)
.\.venv\Scripts\python.exe -m experiments.exp_h4_recheck.run `
  --conditions abc --trials 5 --max-cycles 8 `
  --out-name h4_recheck_abc.json
```

→ 3 파일을 Task 05 의 분석 시 merge 또는 각각 분석.

#### 분할 옵션 B — 단일 실행 (밤 동안)

```powershell
.\.venv\Scripts\python.exe -m experiments.exp_h4_recheck.run `
  --conditions solo_1call solo_budget abc `
  --trials 5 --max-cycles 8 `
  --out-name h4_recheck_full.json
```

→ 단일 결과 파일. 밤 동안 ~20 시간 실행 — 안정성 우려 (Risk 3 — Stage 2A healthcheck/abort 가 fatal 차단)

**Architect 추천**: **옵션 A** (분할). connection 안정성 + 부분 결과 보존 보장.

### Step 4 — 결과 검증 (실행 직후)

```powershell
# 4a) 결과 파일 존재 + schema_version
.\.venv\Scripts\python.exe -c "
import json, glob
files = sorted(glob.glob('experiments/exp_h4_recheck/results/*.json'))
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    print(f'{f}: schema={d.get(\"schema_version\")}, trials={len(d[\"trials\"])}')
"

# 4b) 옵션 A 사용 시 — 3 condition 의 trial 수 합산 = 225
# (옵션 B 사용 시 단일 파일에 225 trial)

# 4c) error 비율 검사 (Stage 2A 의 check_error_rate 가 저장 직전 검증한 결과 — 추가 확인)
.\.venv\Scripts\python.exe -c "
import json, glob
from experiments.run_helpers import check_error_rate
files = sorted(glob.glob('experiments/exp_h4_recheck/results/*.json'))
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    ok, rate = check_error_rate(d['trials'], threshold=0.30)
    print(f'{f}: error rate={rate:.1%}, ok={ok}')
"
```

### Step 5 — 부분 abort 처리 (사용자 호출)

Step 3 실행 중 fatal connection error → Stage 2A 의 abort 발동 → 부분 결과 저장 거부 (`SystemExit(1)`).

이 경우:
- stdout 에 `[ABORT] cond=... task=... trial=... fatal=connection_error` 메시지
- 결과 파일 미생성 (또는 0-byte)
- **사용자 호출 의무** — 모델 서버 healthcheck 후 재실행 결정

부분 결과 보존 옵션 (`*_partial.json`) 은 본 plan 영역 외 (Stage 2A 의 task-01 Risk 절 참조). 후속 plan 후보.

## Dependencies

- Stage 2A 마감 (필수 prerequisites — healthcheck/abort + meta v1.0)
- Task 01 마감 — 15 task taskset
- Task 02 마감 — exp_h4_recheck/run.py
- Task 03 마감 — analyze.py (Task 05 입력용)
- 모델 서버 (`http://192.168.1.179:1234`) 가용성

## Verification

본 task 의 검증은 결과 JSON 의 schema 일관성 + error 비율 < 30% + condition aggregate 출력. Step 4 의 명령 그대로.

추가:

```powershell
# 1) trial 수 = 225 (옵션 A 합산 또는 옵션 B 단일)
.\.venv\Scripts\python.exe -c "
import json, glob
files = sorted(glob.glob('experiments/exp_h4_recheck/results/h4_recheck_*.json'))
total = 0
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    total += len(d['trials'])
print(f'total trials: {total}')
assert total == 225, f'expected 225, got {total}'
"

# 2) condition 별 trial 수 = 75 (15 task × 5 trial)
.\.venv\Scripts\python.exe -c "
import json, glob
from collections import Counter
files = sorted(glob.glob('experiments/exp_h4_recheck/results/h4_recheck_*.json'))
c = Counter()
for f in files:
    d = json.load(open(f, encoding='utf-8'))
    for t in d['trials']:
        c[t['condition']] += 1
for cond, n in sorted(c.items()):
    print(f'  {cond:15} n={n}')
    assert n == 75, f'{cond}: expected 75, got {n}'
"
```

## Risks

- **Risk 1 — 모델 서버 connection refused**: Stage 2A 의 healthcheck/abort 발동. 부분 결과 저장 거부. 사용자 healthcheck 후 재실행
- **Risk 2 — 단일 condition 의 부분 abort**: 옵션 A 의 분할 실행 중 한 condition 만 abort 시 다른 condition 결과는 보존. 사용자 결정 — abort 된 condition 만 재실행 또는 전체 재실행
- **Risk 3 — 실행 시간 ~20 시간**: 사용자 시간 자원. 분할 (옵션 A) 권장. 단일 실행 시 밤 동안 진행
- **Risk 4 — 5 trial 의 통계적 검정력**: 직전 Exp09 5-trial dilute 사고 학습. 단 본 plan 은 task 수 확대 (9→15) 가 답. trial 수는 5 유지 — 직전 사고 패턴 회피
- **Risk 5 — assertion turnover 측정의 Tattoo history 미저장**: Task 02 의 run.py 가 `tattoo_history` 필드를 trial 결과에 포함시켜야 함. Task 02 의 Risk 4 와 연관. 누락 시 turnover 분석 불가 — Task 03 의 helper 가 빈 history 처리 (turnover 0)

## Scope boundary

본 task 에서 **수정 금지** 파일:
- 본 plan 의 다른 subtask 영역 (taskset / run.py / analyze.py) — read-only
- `experiments/run_helpers.py` (Stage 2A 영역) — read-only
- `experiments/measure.py` / `experiments/orchestrator.py` / `experiments/schema.py` — read-only
- 결과 JSON (본 task 의 신규 출력 외 모두 read-only)
- 모든 분석 helper / 다른 plan / README / 노트북 — Task 05 영역

## 사용자 호출 시점

- 분할 옵션 결정 (A 권장 / B 가능)
- fatal abort 발생 시 (Risk 1)
- 시간 자원 결정 (옵션 A 의 condition 별 분할 일정)
- 결과 파일의 trial 수 미달 (Verification 1 의 assertion 실패)

## Architect 메모

Task 04 는 실행 자체보다 **사전 체크 (Step 1)** 와 **결과 검증 (Step 4)** 가 핵심. Stage 2A 의 healthcheck/abort 가 직전 사고 (Exp09 5-trial dilute) 와 같은 패턴을 차단하는지 본 task 가 첫 실전 검증 무대.
