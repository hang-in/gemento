---
type: plan-task
status: done
updated_at: 2026-05-05
parent_plan: exp13-reducer-role
parallel_group: D
depends_on: [03]
---

# Task 04 — 실험 실행 (사용자 직접) — 15 task × 2 condition × 5 trial = 150 trial

## Changed files

- `experiments/exp13_reducer_role/results/exp13_baseline_abc.json` — **신규 출력**
- `experiments/exp13_reducer_role/results/exp13_reducer_abc.json` — **신규 출력**

신규 2 (사용자 실행 결과).

## Change description

### 배경

Exp12 task-04 의 패턴 그대로. **사용자 직접 실행** (메모리 정책). 외부 API 비용 0 (local Gemma).

### Step 1 — 사전 체크

```powershell
$env:GEMENTO_API_BASE_URL = "http://192.168.1.179:1234"

# 1a) Stage 2A + 2B + task-01/02/03 마감 검증
.\.venv\Scripts\python.exe -c "
from experiments.run_helpers import classify_trial_error, build_result_meta
from experiments.schema import FailureLabel
from experiments.system_prompt import REDUCER_PROMPT, build_reducer_prompt
from experiments.orchestrator import run_abc_chain
from experiments.exp13_reducer_role.run import (
    run_baseline_abc, run_reducer_abc, CONDITION_DISPATCH,
)
import inspect
sig = inspect.signature(run_abc_chain)
assert 'reducer_post_stage' in sig.parameters
assert 'extractor_pre_stage' in sig.parameters  # Exp12 보존
assert 'c_caller' in sig.parameters  # Exp11 보존
print('ok: 모든 prerequisite 마감')
"

# 1b) lmstudio 가용성
curl -s http://192.168.1.179:1234/v1/models | head -3
```

### Step 2 — dry-run (1 task × 1 trial × 2 condition)

```powershell
# baseline_abc dry-run
.\.venv\Scripts\python.exe -m experiments.exp13_reducer_role.run `
  --conditions baseline_abc --trials 1 --max-cycles 8 `
  --out-name dryrun_baseline.json

# reducer_abc dry-run
.\.venv\Scripts\python.exe -m experiments.exp13_reducer_role.run `
  --conditions reducer_abc --trials 1 --max-cycles 8 `
  --out-name dryrun_reducer.json
```

기대 (reducer_abc):
- stdout 에 `[Reducer] candidate (orig N chars) → reduced (M chars)` 출력
- `[Reducer] preview: ...` 미리보기
- final_answer 가 baseline 보다 더 정리된 형태 (특히 keyword 명시)

dry-run 통과 후 폐기:
```powershell
Remove-Item experiments\exp13_reducer_role\results\dryrun_*.json -ErrorAction SilentlyContinue
Remove-Item experiments\exp13_reducer_role\results\partial_*.json -ErrorAction SilentlyContinue
```

### Step 3 — 본 실행 (분할 권장)

**시간 추정**:
- baseline_abc: ~12시간 (Exp11/Exp12 정합)
- reducer_abc: ~12.5시간 (Reducer 호출 ~30s × 75 trial 추가)
- **총 ~25시간**

```powershell
# 1) baseline_abc (~12h)
.\.venv\Scripts\python.exe -m experiments.exp13_reducer_role.run `
  --conditions baseline_abc --trials 5 --max-cycles 8 `
  --out-name exp13_baseline_abc.json

# 2) reducer_abc (~12.5h)
.\.venv\Scripts\python.exe -m experiments.exp13_reducer_role.run `
  --conditions reducer_abc --trials 5 --max-cycles 8 `
  --out-name exp13_reducer_abc.json
```

또는 통합:

```powershell
.\.venv\Scripts\python.exe -m experiments.exp13_reducer_role.run `
  --conditions baseline_abc reducer_abc --trials 5 --max-cycles 8 `
  --out-name exp13_full.json
```

### Step 4 — 결과 검증

```powershell
.\.venv\Scripts\python.exe -c "
import json, glob
total = 0
for f in sorted(glob.glob('experiments/exp13_reducer_role/results/exp13_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    print(f'{f}: trials={len(d[\"trials\"])}, schema={d.get(\"schema_version\")}')
    total += len(d['trials'])
assert total == 150
"
```

## Dependencies

- Stage 2A 마감
- Stage 2B 마감
- task-01 (REDUCER_PROMPT)
- task-02 (run_abc_chain reducer_post_stage)
- task-03 (run.py)
- 모델 서버 가용성

## Verification

```powershell
# 1) trial 수 = 150
.\.venv\Scripts\python.exe -c "
import json, glob
total = sum(len(json.load(open(f, encoding='utf-8'))['trials'])
            for f in sorted(glob.glob('experiments/exp13_reducer_role/results/exp13_*.json')))
assert total == 150, f'expected 150, got {total}'
print('verification 1 ok: 150 trial')
"

# 2) condition 별 trial = 75
.\.venv\Scripts\python.exe -c "
import json, glob
from collections import Counter
c = Counter()
for f in sorted(glob.glob('experiments/exp13_reducer_role/results/exp13_*.json')):
    for t in json.load(open(f, encoding='utf-8'))['trials']:
        c[t['condition']] += 1
for cond, n in sorted(c.items()):
    print(f'  {cond:18} n={n}')
    assert n == 75
"

# 3) tattoo_history multi-cycle (Stage 2C 결함 fix 보존)
.\.venv\Scripts\python.exe -c "
import json, glob
for f in sorted(glob.glob('experiments/exp13_reducer_role/results/exp13_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    multi = sum(1 for t in d['trials'] if (t.get('tattoo_history') or []) and len(t['tattoo_history']) >= 2)
    print(f'{f}: multi-cycle history >= 2: {multi}/{len(d[\"trials\"])}')
"

# 4) reducer_abc 의 final_answer 길이 — Reducer 효과 간접 측정
.\.venv\Scripts\python.exe -c "
import json
for cond, p in (('baseline_abc', 'experiments/exp13_reducer_role/results/exp13_baseline_abc.json'),
                ('reducer_abc',  'experiments/exp13_reducer_role/results/exp13_reducer_abc.json')):
    d = json.load(open(p, encoding='utf-8'))
    lens = [len(t.get('final_answer') or '') for t in d['trials']]
    print(f'  {cond:18} avg final_answer len: {sum(lens)/len(lens):.0f} chars')
"
```

## Risks

- **Risk 1 — Reducer 가 답을 *바꿈*** — prompt 의 "do NOT change conclusion" 제약에도 발생 가능. dry-run 시 logic-02 case 의 답 보존 여부 확인 (원: "105 inconsistent" → reduced: 변형 시 fail)
- **Risk 2 — Reducer 응답 한계** — Gemma 의 plain text 응답이 quoted JSON 아니면 안정적 예상. 단 빈 응답 시 graceful fallback (원본 final_answer 보존)
- **Risk 3 — 비용/시간** — local 한정, 비용 0. 시간 +0.5h (Reducer 호출만)
- **Risk 4 — Sonnet 직접 실행 시도** — 본 task = 사용자 직접

## Scope boundary

본 task 에서 **수정 금지** 파일:
- 모든 코드 — read-only
- 결과 JSON (본 task 의 신규 출력 외 모두 read-only)
- 본 plan 의 다른 subtask 영역

## 사용자 호출 시점

- 분할 옵션 결정
- dry-run 결과 검증 (Reducer 가 답을 보존하는지 확인 — Risk 1)
- fatal abort / Risk 발생
- 본 실행 결과 받으면 task-05 진행 신호
