---
type: plan-task
status: todo
updated_at: 2026-05-03
parent_plan: exp12-extractor-role-pre-search
parallel_group: D
depends_on: [03]
---

# Task 04 — 실험 실행 (사용자 직접) — 15 task × 2 condition × 5 trial = 150 trial

## Changed files

- `experiments/exp12_extractor_role/results/exp12_baseline_abc.json` — **신규 출력** (사용자 실행)
- `experiments/exp12_extractor_role/results/exp12_extractor_abc.json` — **신규 출력**

신규 2 (사용자 실행 결과).

## Change description

### 배경

본 task = **사용자 직접 실행** (메모리 정책 `feedback_agent_no_experiment_run.md`). Sonnet 직접 실행 금지.

Exp11 task-04 의 패턴 그대로 — 분할 실행 권장 (옵션 A: baseline_abc 먼저 → extractor_abc 이어서).

### Step 1 — 사전 체크

```powershell
$env:GEMENTO_API_BASE_URL = "http://192.168.1.179:1234"
# GEMINI_API_KEY 불필요 (본 plan 은 외부 API 호출 0)

# 1a) Stage 2A + 2B + task-01/02/03 마감 검증
.\.venv\Scripts\python.exe -c "
from experiments.run_helpers import classify_trial_error, build_result_meta
from experiments.schema import FailureLabel
from experiments.system_prompt import EXTRACTOR_PROMPT, build_extractor_prompt
from experiments.orchestrator import run_abc_chain
from experiments.exp12_extractor_role.run import (
    run_baseline_abc, run_extractor_abc, CONDITION_DISPATCH,
)
import inspect
sig = inspect.signature(run_abc_chain)
assert 'extractor_pre_stage' in sig.parameters
assert sig.parameters['extractor_pre_stage'].default is False
print('ok: 모든 prerequisite 마감')
"

# 1b) lmstudio 서버 가용성
curl -s http://192.168.1.179:1234/v1/models | head -3
```

### Step 2 — dry-run (1 task × 1 trial × 2 condition, ~10분)

```powershell
# 2a) baseline_abc dry-run
.\.venv\Scripts\python.exe -m experiments.exp12_extractor_role.run `
  --conditions baseline_abc --trials 1 --max-cycles 8 `
  --out-name dryrun_baseline.json

# 2b) extractor_abc dry-run — Extractor pre-stage 동작 확인
.\.venv\Scripts\python.exe -m experiments.exp12_extractor_role.run `
  --conditions extractor_abc --trials 1 --max-cycles 8 `
  --out-name dryrun_extractor.json
```

기대 (extractor_abc):
- stdout 에 `[Extractor] result preview: {"claims": [...], "entities": [...]}` 출력
- A 의 첫 cycle 응답이 Extractor claims 참조 (assertion 에 entity 명시 등)
- cycles ≥ 1, tattoo_history len ≥ 2, acc 정상 분포

dry-run 통과 후 폐기:

```powershell
Remove-Item experiments\exp12_extractor_role\results\dryrun_*.json -ErrorAction SilentlyContinue
Remove-Item experiments\exp12_extractor_role\results\partial_*.json -ErrorAction SilentlyContinue
```

### Step 3 — 본 실행 (분할 권장)

**시간 추정**:
- baseline_abc: ~12시간 (Exp11 / Stage 2C 정합)
- extractor_abc: ~12.6시간 (Extractor 호출 ~30s × 75 trial = +38min)
- **총 ~25시간**

```powershell
# 1) baseline_abc (~12h, 밤 동안)
.\.venv\Scripts\python.exe -m experiments.exp12_extractor_role.run `
  --conditions baseline_abc --trials 5 --max-cycles 8 `
  --out-name exp12_baseline_abc.json

# 2) extractor_abc (~12.6h)
.\.venv\Scripts\python.exe -m experiments.exp12_extractor_role.run `
  --conditions extractor_abc --trials 5 --max-cycles 8 `
  --out-name exp12_extractor_abc.json
```

또는 통합 (자동 chain):

```powershell
.\.venv\Scripts\python.exe -m experiments.exp12_extractor_role.run `
  --conditions baseline_abc extractor_abc --trials 5 --max-cycles 8 `
  --out-name exp12_full.json
```

### Step 4 — 결과 검증

```powershell
.\.venv\Scripts\python.exe -c "
import json, glob
total = 0
for f in sorted(glob.glob('experiments/exp12_extractor_role/results/exp12_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    print(f'{f}: trials={len(d[\"trials\"])}, schema={d.get(\"schema_version\")}')
    total += len(d['trials'])
print(f'total: {total}')
"
```

기대: 2 파일 (baseline 75 + extractor 75 = 150), schema_version="1.0".

## Dependencies

- Stage 2A 마감 (helper)
- Stage 2B 마감 (FailureLabel)
- task-01 (EXTRACTOR_PROMPT)
- task-02 (run_abc_chain extractor_pre_stage)
- task-03 (exp12_extractor_role/run.py)
- 모델 서버 (LM Studio) 가용성

## Verification

```powershell
# 1) trial 수 = 150
.\.venv\Scripts\python.exe -c "
import json, glob
total = 0
for f in sorted(glob.glob('experiments/exp12_extractor_role/results/exp12_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    total += len(d['trials'])
assert total == 150, f'expected 150, got {total}'
print(f'verification 1 ok: 150 trial')
"

# 2) condition 별 trial 수 = 75
.\.venv\Scripts\python.exe -c "
import json, glob
from collections import Counter
c = Counter()
for f in sorted(glob.glob('experiments/exp12_extractor_role/results/exp12_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    for t in d['trials']: c[t['condition']] += 1
for cond, n in sorted(c.items()):
    print(f'  {cond:18} n={n}')
    assert n == 75
"

# 3) tattoo_history cycle-by-cycle 검증 (Stage 2C 결함 fix 보존)
.\.venv\Scripts\python.exe -c "
import json, glob
for f in sorted(glob.glob('experiments/exp12_extractor_role/results/exp12_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    multi = sum(1 for t in d['trials'] if (t.get('tattoo_history') or []) and len(t['tattoo_history']) >= 2)
    print(f'{f}: multi-cycle history >= 2: {multi}/{len(d[\"trials\"])}')
"
```

## Risks

- **Risk 1 — Extractor 응답 schema 깨짐 빈도** — Gemma E4B JSON 한계. graceful fallback (prefix 미주입) 동작 확인. Stage 2A reject 임계 30% 안 유지
- **Risk 2 — extractor_abc 의 시간 폭증**: A 가 Extractor prefix 받아 응답 길어짐 가능. 첫 trial 모니터링 — duration 차이 +50% 초과 시 사용자 호출
- **Risk 3 — Sonnet 직접 실행 시도**: 본 task = 사용자 직접. 모델 호출 금지

## Scope boundary

본 task 에서 **수정 금지** 파일:
- 모든 코드 (`experiments/*.py`) — read-only
- 결과 JSON (본 task 의 신규 출력 외 모두 read-only)
- 본 plan 의 다른 subtask 영역

## 사용자 호출 시점

- 분할 옵션 결정
- dry-run 결과 검증
- fatal abort / Risk 발생
- 본 실행 결과 받으면 task-05 진행 신호
