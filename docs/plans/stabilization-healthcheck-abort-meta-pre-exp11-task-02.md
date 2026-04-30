---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: stabilization-healthcheck-abort-meta-pre-exp11
parallel_group: A
depends_on: [01]
---

# Task 02 — 모든 multi-trial 도구에 healthcheck/abort 확장

## Changed files

- `experiments/exp00_baseline/run.py` (정찰 후 결정)
- `experiments/exp01_assertion_cap/run.py` (정찰 후 결정)
- `experiments/exp02_multiloop/run.py` (정찰 후 결정)
- `experiments/exp03_critic/run.py` (정찰 후 결정)
- `experiments/exp04_abc/run.py` (정찰 후 결정)
- `experiments/exp045_handoff/run.py` (정찰 후 결정)
- `experiments/exp05_prompt_enhance/run.py` (정찰 후 결정)
- `experiments/exp06_solo_budget/run.py` (정찰 후 결정)
- `experiments/exp07_loop_saturation/run.py` (정찰 후 결정)
- `experiments/exp08_math_tools/run.py` (정찰 후 결정)
- `experiments/exp08b_tool_refinement/run.py` (정찰 후 결정)
- `experiments/exp09_longctx/run.py` (정찰 후 결정)
- `experiments/exp10_reproducibility_cost/run.py` (정찰 후 결정)

> 위 파일 목록은 **정찰 결과 기준 잠정**. 실제 존재하는 파일만 수정. Step 1 의 정찰 결과로 final 목록 확정.

수정 multi (정찰 후 결정), 신규 0.

## Change description

### 배경

Subtask 01 에서 `experiments/run_helpers.py` 신규 + `run_append_trials.py` proof-of-concept 통합 완료. 본 task 는 동일 패턴을 모든 multi-trial 도구로 확장.

### Step 1 — 정찰 (Glob + 구조 파악)

```bash
.venv/Scripts/python -c "
import glob
files = sorted(glob.glob('experiments/exp*/run.py'))
for f in files:
    print(f)
"
```

각 파일의 trial loop 구조 분류 (수동 read):
- (A) `for arm/condition: for task: for trial:` 3중 중첩 (Exp09 패턴)
- (B) `for task: for trial:` 2중 중첩 (단순 패턴)
- (C) `for trial: for task:` (loop 순서 다름)
- (D) async / generator / 다른 패턴

각 파일을 표로 정리하여 plan 진행 보고:

```markdown
| 파일 | trial loop 구조 | error 추출 키 | 결과 dict 의 trial list 위치 |
|------|----------------|---------------|------------------------------|
| exp00_baseline/run.py | (B) | result.error | results[task_id].trials |
| exp09_longctx/run.py  | (A) | trial['error'] | results_by_arm[arm][i].trials |
| ...   | ...   | ...   | ... |
```

### Step 2 — 도구별 helper 적용 (구조 분류 따름)

각 도구의 trial loop 에 **subtask 01 의 Step 2b/2c 와 동일 패턴**:

#### 패턴 (A) 3중 중첩 — Exp09 와 동일

```python
aborted = False
for arm in arms:
    if aborted: break
    for task in tasks:
        if aborted: break
        for trial_idx in range(N):
            result = _run_trial(arm, task, trial_idx)
            ...append...
            err = classify_trial_error(result.get("error"))
            if is_fatal_error(err):
                print(f"[ABORT] arm={arm} task={task['id']} trial={trial_idx} fatal={err.value}")
                aborted = True
                break
```

#### 패턴 (B) 2중 중첩 — 더 단순

```python
aborted = False
for task in tasks:
    if aborted: break
    for trial_idx in range(N):
        result = _run_trial(task, trial_idx)
        ...append...
        err = classify_trial_error(result.get("error"))
        if is_fatal_error(err):
            print(f"[ABORT] task={task['id']} trial={trial_idx} fatal={err.value}")
            aborted = True
            break
```

#### 패턴 (D) async / generator

flag 가 효력 없으면 **exception 기반 fallback**:

```python
class _FatalAbort(Exception):
    """fatal connection error — outer 에서 catch."""

try:
    for ... in async_iter:
        ...
        err = classify_trial_error(result.get("error"))
        if is_fatal_error(err):
            raise _FatalAbort(...)
except _FatalAbort as e:
    print(f"[ABORT] {e}")
```

### Step 3 — 저장 직전 error 비율 검사

각 도구의 결과 저장 (`json.dump(...)` 또는 `save_result(...)`) 직전:

```python
all_trials = _flatten_trials(result_data)  # 도구별 helper, 또는 inline
ok, rate = check_error_rate(all_trials, threshold=0.30)
if not ok:
    print(f"[REJECT] {result_data.get('experiment','run')} error 비율 {rate:.1%} ≥ 30%. 저장 거부")
    raise SystemExit(1)
```

`_flatten_trials` 추출 로직은 도구별 dict 구조에 맞춰 inline. 공통 helper 로 빼지 않음 (구조 차이 > 추상화 가치).

### Step 4 — `run_helpers.py` 의 import path 통일

각 도구가 `from experiments.run_helpers import ...` 형태로 import. 기존 import 패턴 (`sys.path.insert(0, ...)` 등) 보존 — 본 task 는 추가만.

### Step 5 — 도구별 healthcheck 적용 보고서

진행 후 다음 형식으로 보고:

```markdown
## 적용 결과 (subtask 02)

| 파일 | 패턴 | 적용 | abort flag 위치 | 비고 |
|------|------|------|-----------------|------|
| exp00_baseline/run.py | (B) | 적용 | line N | — |
| exp09_longctx/run.py  | (A) | 적용 | line M | run_append_trials 와 동일 패턴 |
| exp03_critic/run.py   | (D) | exception fallback | line K | async generator |
| ... | ... | ... | ... | ... |
```

위 보고를 plan 진행 commit 의 message body 또는 별도 reference 문서에 명시.

## Dependencies

- subtask 01 완료 (`experiments/run_helpers.py` 존재)
- 패키지: 표준만
- 입력: subtask 01 의 helper

## Verification

```bash
# 1) 정찰 - 영향 받는 파일 목록
.venv/Scripts/python -c "
import glob
files = sorted(glob.glob('experiments/exp*/run.py'))
print('\\n'.join(files))
print(f'total: {len(files)}')
"

# 2) 모든 run.py 가 helper import + syntax
.venv/Scripts/python -c "
import glob, py_compile, sys
files = sorted(glob.glob('experiments/exp*/run.py'))
fails = []
for f in files:
    try:
        py_compile.compile(f, doraise=True)
    except Exception as e:
        fails.append(f'{f}: {e}')
if fails:
    for f in fails: print(f)
    sys.exit(1)
print(f'ok: {len(files)} files compile')
"

# 3) 모든 run.py 가 healthcheck import 포함 확인
.venv/Scripts/python -c "
import glob, re
files = sorted(glob.glob('experiments/exp*/run.py'))
missing = []
for f in files:
    text = open(f, encoding='utf-8').read()
    if 'classify_trial_error' not in text:
        missing.append(f)
if missing:
    print('MISSING:')
    for f in missing: print(f'  {f}')
else:
    print(f'ok: {len(files)} files have healthcheck import')
"

# 4) flag/exception 패턴 일관 - 단일 도구 sample read
# (Developer 가 적용 결과 보고서를 plan 진행 commit message 에 포함)
```

위 명령 실행 + Step 5 의 보고서 작성. 전체 도구 lint pass + healthcheck import 100%.

## Risks

- **Risk 1 — 일부 `experiments/exp**/run.py` 가 multi-trial 가 아닌 단발 도구**: 그 경우 본 task 의 healthcheck/abort 패턴 부적합. 정찰 결과로 결정 — multi-trial 만 대상.
- **Risk 2 — 일부 도구가 이미 자체 abort 로직 보유**: 중복되면 helper 호출만 추가하고 자체 로직 유지. **자체 로직 제거 금지**.
- **Risk 3 — 도구 별 dict 구조 차이로 `_flatten_trials` 가 inline 화 산발**: 파일별 4~8 라인 추가. 공통화 시도하지 말 것.
- **Risk 4 — async generator 도구가 cancellation 처리 없으면 exception 으로 trial 손실**: 그 경우 부분 결과 보존 추가 분기 필요. fallback: subtask 별도 plan.
- **Risk 5 — Developer 가 정찰 단계에서 임의로 도구 제외**: Architect 호출 필수. 임의 결정 금지.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/run_helpers.py` — subtask 01 영역 (read-only, 추가 함수 정의 금지)
- `experiments/orchestrator.py` — 본 plan 영역 외
- `experiments/measure.py` / `score_answer_v*` — Stage 2B 영역
- `experiments/schema.py` — subtask 03 영역
- `experiments/tasks/*.json` — Phase 1 후속 영역
- `experiments/exp09_longctx/run_append_trials.py` — subtask 01 에서 처리 완료, 본 task 는 read-only
- 모든 analyze 스크립트 (`experiments/exp*/analyze_*.py`) — subtask 04 영역
- 결과 JSON (모두 read-only)
- `docs/reference/*` / `docs/plans/*` (본 task 의 plan 파일 외)
- README / researchNotebook

도구별 client (`experiments/lmstudio_client.py` / `gemini_client.py` 등) 도 변경 금지 — healthcheck 는 trial loop 단계에서 적용.
