---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: phase-1-taskset-3-fail-exp09-5-trial-exp10-v3
parallel_group: A
depends_on: [01]
---

# Task 03 — Exp10 v3 재산정 (Taskset 정정 반영)

## Changed files

- `experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_<TS>.json` — **신규 출력**. Task 01 의 taskset 정정 후 `rescore_v3.py` 재실행 결과.

신규 파일 1, 다른 파일 수정 0.

## Change description

### 배경

Task 01 의 taskset 정정 중 **math-03 + synthesis-04 가 Exp10 task subset 포함** (Exp10 의 9 task: math-01~04, synthesis-01/03/04, logic-03/04). 정정 후 Exp10 v3 결과가 변동.

직전 v3 final (`exp10_v3_rescored_20260429_053939.json`):
- gemma_8loop: 0.7815
- gemini_flash_1call: 0.5907
- gemma_1loop: 0.4130

본 task 는 Task 01 적용 후 새 timestamp 의 v3 rescored JSON 생성. 변동 수치를 Task 04 의 입력으로 사용.

### Step 1 — Task 01 완료 확인

```bash
.venv/bin/python -m experiments.validate_taskset 2>&1 | grep "PASS" | head -1
# 기대: PASS 22 / FAIL 0 (Task 01 완료 신호)
```

`validate_taskset` 의 22/22 PASS 가 확인되어야 본 task 진행.

### Step 2 — `rescore_v3.py` 재실행 (사용자 직접)

메모리 정책 (에이전트 직접 실험 실행 금지) 준수. 사용자 명령:

```bash
.venv/bin/python -m experiments.exp10_reproducibility_cost.rescore_v3
```

기대 출력 (직전 v3 053939 와 비교):
- 새 timestamp 의 `exp10_v3_rescored_<TS>.json` 생성
- condition × task aggregate 출력 — 이전과 비교한 Δ
- per-task Δ != 0 표 — math-03 / synthesis-04 의 변동이 표시 (logic-04 외에)

### Step 3 — 변동 수치 식별

새 v3 rescored 결과의 condition aggregate 와 직전 053939 비교:

```bash
.venv/bin/python -c "
import json, glob
files = sorted(glob.glob('experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_*.json'))
prev = json.load(open(files[-2]))  # 053939 (이전 canonical)
curr = json.load(open(files[-1]))  # 새 timestamp (이번 결과)
from collections import defaultdict
def agg(d):
    a = defaultdict(lambda: {'n':0,'v3':0.0})
    for t in d['trials']:
        a[t['condition']]['n'] += 1
        a[t['condition']]['v3'] += t.get('accuracy_v3', 0)
    return {c: x['v3']/x['n'] for c, x in a.items()}
p, c = agg(prev), agg(curr)
for cond in ('gemma_8loop','gemini_flash_1call','gemma_1loop'):
    print(f'{cond:24} prev={p[cond]:.4f}  curr={c[cond]:.4f}  Δ={c[cond]-p[cond]:+.4f}')
"
```

이 출력이 Task 04 의 result.md / 노트북 갱신 입력.

### Step 4 — task-level Δ break-down

```bash
.venv/bin/python -c "
import json, glob
from collections import defaultdict
files = sorted(glob.glob('experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_*.json'))
prev = json.load(open(files[-2]))
curr = json.load(open(files[-1]))
def agg_task(d):
    a = defaultdict(lambda: {'n':0,'v3':0.0})
    for t in d['trials']:
        k = (t['condition'], t['task_id'])
        a[k]['n'] += 1
        a[k]['v3'] += t.get('accuracy_v3', 0)
    return {k: x['v3']/x['n'] for k, x in a.items()}
p, c = agg_task(prev), agg_task(curr)
for k in sorted(p.keys()):
    if abs(p[k] - c[k]) > 0.001:
        print(f'{k[0]:24} {k[1]:13} prev={p[k]:.3f}  curr={c[k]:.3f}  Δ={c[k]-p[k]:+.3f}')
"
```

기대: math-03 / synthesis-04 의 변동만 출력 (다른 task v2==v3 보존). logic-04 도 변동 없음 (직전 plan 의 negative_patterns / conclusion_required 그대로).

## Dependencies

- Task 01 — taskset 정정 완료 후 본 task 진행
- 기존 산출물: `experiments/exp10_reproducibility_cost/rescore_v3.py` (변경 0)
- v2 final JSON: `exp10_v2_final_20260429_033922.json` (read-only 입력)
- 패키지: 없음 (재실행만)

## Verification

```bash
# 1) Task 01 완료 검증 (validate_taskset PASS 22/22)
.venv/bin/python -m experiments.validate_taskset 2>&1 | grep -E "PASS|FAIL" | tail -3
# 기대: 22 PASS, 0 FAIL

# 2) rescore_v3 재실행 (사용자 직접)
.venv/bin/python -m experiments.exp10_reproducibility_cost.rescore_v3 2>&1 | tail -15
# 기대: 새 출력 파일 + condition aggregate

# 3) 새 v3 결과 schema 검증
.venv/bin/python -c "
import json, glob
latest = sorted(glob.glob('experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_*.json'))[-1]
d = json.load(open(latest))
assert len(d['trials']) == 540, f'trials: {len(d[\"trials\"])}'
for t in d['trials']:
    assert 'accuracy_v2' in t and 'accuracy_v3' in t
print(f'ok: {latest}, trials={len(d[\"trials\"])}')
"

# 4) condition Δ 출력 (Task 04 입력)
# (Step 3 의 명령 그대로 — 양쪽 v3 비교)

# 5) task-level Δ break-down (math-03 / synthesis-04 만 변동 확인)
# (Step 4 의 명령 그대로)
```

5 명령 모두 정상 + math-03 / synthesis-04 만 task-level 변동, 다른 task v2==v3 보존.

## Risks

- **Task 01 의 math-03 prompt 변경 영향**: 옵션 A (96→88) 적용 시 v3 trial 의 답변과 새 정답 (round=6, square=4, rectangular=5) 의 매칭이 어떻게 될지 — 현 v3 v2 에서 0/20 인지 / 일부 정답 매칭인지 결과가 변동. 옵션 B (rect 제약 변경) 시 답변 무효화 가능.
- **synthesis-04 keyword 변경 영향**: `[['reports'], ['5'], ['6']]` (Task 01 권장 옵션 A) 적용 시 v3 trial 의 acc 가 더 관대 → 일부 trial 정답 처리 가능.
- **rescore_v3.py 의 기존 동작**: 직전 plan 에서 검증됨 (회귀 0). taskset 변경만 반영.
- **Δ 가 의도와 다를 위험**: math-03 acc 가 큰 변동이면 README Headline 갱신 필요 (Task 04). 사소하면 disclosure 만.
- **사용자 직접 실행 의존**: rescore_v3.py 자체는 LLM 호출 0 (정적 채점) 이라 실행 시간 작음. 단 메모리 정책상 사용자 직접 실행이 정합.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/exp10_reproducibility_cost/rescore_v3.py` — 코드 변경 0, 재실행만
- `experiments/exp10_reproducibility_cost/results/exp10_v2_final_20260429_033922.json` — read-only 입력
- 직전 v3 결과 (053939, 052748, 045819) — read-only, archive
- `experiments/measure.py` / score_answer_v3 — 직전 plan 의 검증된 영역
- `experiments/tasks/taskset.json` / `longctx_taskset.json` — Task 01 영역
- `experiments/exp09_longctx/` — Task 02 영역
- README / 노트북 / result.md — Task 04 영역
- `experiments/exp10_reproducibility_cost/run.py` / `merge_v2_final.py` / `diagnose_json_fails.py` 등 다른 스크립트 — 변경 0
