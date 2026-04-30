---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: phase-1-taskset-3-fail-exp09-5-trial-exp10-v3
parallel_group: A
depends_on: []
---

# Task 01 — Taskset 3 FAIL 수정

## Changed files

- `experiments/tasks/taskset.json` — **수정**. `math-03` 의 prompt / expected / constraints 정정 (사용자 결정 의존). `synthesis-04` 의 scoring_keywords 정정.
- `experiments/tasks/longctx_taskset.json` — **수정**. `longctx-medium-2hop-02` 의 keyword 또는 expected_answer 정정.

신규 파일 0.

## Change description

### 배경 — 3 FAIL 원인 (Phase 1 validate_taskset 결과)

#### 1. math-03 — **prompt 자체가 해 없음**

현재 prompt:
> A school has 3 types of tables: round (seats 4), square (seats 6), and rectangular (seats 8). The total number of tables is 15. The total number of seats is 96. The number of rectangular tables equals the number of round tables minus 1.

연립방정식:
- (1) r + s + rect = 15
- (2) 4r + 6s + 8·rect = 96
- (3) rect = r − 1

(3) → (1): 2r + s − 1 = 15 → s = 16 − 2r
(3), s 대입 (2): 4r + 6(16−2r) + 8(r−1) = 96 → 4r + 96 − 12r + 8r − 8 = 96 → 0r = 8 → **모순**

→ **prompt 본문 변경 없이는 정합 불가**. expected `round=6, square=4, rectangular=5` 도 검산 시 4·6+6·4+8·5=88 ≠ 96.

**사용자 결정 의존 — 두 옵션**:

| 옵션 | 변경 | 영향 |
|------|------|------|
| **A** | prompt 의 "96" → "88" (총 좌석 수 정정) | 정답 (6,4,5) 보존, prompt 본문 1자 변경. Exp10 v3 의 math-03 trial 답변과 호환 가능성 ↑ |
| **B** | prompt 의 "rectangular tables equals round minus 1" 제거 + 정합한 다른 constraint | 정답 변경 필요. Exp10 v3 의 math-03 답변 무효화 가능 |

**권장: A** — 최소 변경, Exp10 결과 보존성 ↑. 단 prompt 본문 변경이라 plan Constraint "math-03 prompt 본문 변경 금지" 위반. 사용자 명시 승인 필요.

#### 2. synthesis-04 — keyword substring 매칭 실패

현재:
- expected: `"Reports 5 and 6 contradict on Zone C..."`
- scoring_keywords: `[['270'], ['contradict', 'zone c'], ['report 5', 'report 6']]`

문제: keyword group 3 의 `'report 5'` 가 expected (lowercase: `"reports 5 and 6"`) 에 substring 부재 (`'report 5'` 가 통째로 나오지 않음 — `'reports 5 and 6'` 라 'reports' 다음 ' 5' 라 'report 5' 8글자 패턴 없음). 마찬가지 `'report 6'`.

수정: keyword group 3 정정 — 두 옵션:

| 옵션 | 변경 |
|------|------|
| **A** | `[['270'], ['contradict', 'zone c'], ['reports', '5', '6']]` (3 토큰 모두 매칭 = group 매칭) |
| **B** | `[['270'], ['contradict', 'zone c'], ['5 and 6']]` (단일 substring) |

권장: **A** — '5 and 6' 보다 일반적, 모델 답변에서 'reports', '5', '6' 모두 등장하는 경우가 자연스러움.

#### 3. longctx-medium-2hop-02 — keyword 토큰 부재

현재 (`experiments/tasks/longctx_taskset.json` line 80):
- expected: `"500 horsepower"`
- scoring_keywords: `[['500 horsepower'], ['500 hp']]`

문제: keyword group 2 `'500 hp'` 의 토큰이 expected 에 부재. validate_taskset.py 가 expected 에 토큰 존재 검사하면 fail. 단 실제 채점 시 모델 답변에 '500 hp' 등장하면 group 2 매칭 가능.

수정: 두 옵션

| 옵션 | 변경 |
|------|------|
| **A** | scoring_keywords → `[['500'], ['horsepower']]` 단일 group 분리 (모델이 '500 hp' / '500 horsepower' 어느 쪽 답변해도 ['500'] 매칭) |
| **B** | expected_answer → `"500 horsepower (500 hp)"` (두 표현 포함, validate 통과) |

권장: **B** — expected 가 답변 예시 역할도 하므로 두 표현 명시가 자연스러움. validate 통과 + 채점 정확.

### Step 1 — math-03 (사용자 결정 후)

`experiments/tasks/taskset.json` 의 math-03 객체:

옵션 A 적용:
```json
"prompt": "A school has 3 types of tables: round (seats 4), square (seats 6), and rectangular (seats 8). The total number of tables is 15. The total number of seats is 88. The number of rectangular tables equals the number of round tables minus 1. How many of each type of table are there?",
```

(96 → 88 만 변경. 다른 필드 보존.)

### Step 2 — synthesis-04

`experiments/tasks/taskset.json` 의 synthesis-04 객체의 `scoring_keywords` 정정:

```json
"scoring_keywords": [["270"], ["contradict", "zone c"], ["reports", "5", "6"]]
```

### Step 3 — longctx-medium-2hop-02

`experiments/tasks/longctx_taskset.json` 의 longctx-medium-2hop-02 의 `expected_answer` 정정:

```json
"expected_answer": "500 horsepower (500 hp)",
```

scoring_keywords 보존: `[['500 horsepower'], ['500 hp']]` (validate 통과).

### Step 4 — validate_taskset.py 재실행 + 22/22 PASS 검증

```bash
.venv/bin/python -m experiments.validate_taskset
```

→ summary 에 PASS 22 / FAIL 0 출력.

## Dependencies

- 패키지: 표준 `json`, `re`. 신규 의존성 0.
- 다른 subtask: 없음 (parallel_group A 의 시작점, Task 03 가 본 task 후).
- **사용자 결정 필요** (math-03 의 옵션 A vs B). 본 task 진행 전 사용자 명시 승인.

## Verification

```bash
# 1) JSON parse + 3 task 확인
.venv/bin/python -c "
import json
with open('experiments/tasks/taskset.json') as f:
    d = json.load(f)
m3 = next(t for t in d['tasks'] if t['id']=='math-03')
s4 = next(t for t in d['tasks'] if t['id']=='synthesis-04')
print('math-03 prompt has 88:', '88' in m3['prompt'])
print('synthesis-04 keywords:', s4['scoring_keywords'])
with open('experiments/tasks/longctx_taskset.json') as f:
    ld = json.load(f)
lt = next(t for t in ld['tasks'] if t['id']=='longctx-medium-2hop-02')
print('longctx expected:', lt['expected_answer'])
"

# 2) validate_taskset 재실행 → 22/22 PASS
.venv/bin/python -m experiments.validate_taskset 2>&1 | tail -10
# 기대: PASS 22 / FAIL 0

# 3) 다른 task 변경 없음 (git diff 의 변경 라인이 모두 3 task 영역 내)
git diff experiments/tasks/taskset.json experiments/tasks/longctx_taskset.json | grep -E '^[\+\-][^+\-]' | head -30
```

3 명령 모두 정상 + validate 22/22 PASS.

## Risks

- **math-03 prompt 본문 변경**: 본 plan Constraint 와 충돌. 사용자 명시 결정 (옵션 A 또는 B) 후 진행. 결정 없이 자체 변경 금지.
- **Exp10 v3 의 math-03 trial 답변 호환성**: 옵션 A (96→88) 적용 시 Exp10 v3 trial 들 (이전 96 prompt 로 실행) 의 답변이 새 정답과 어떻게 매칭될지 — Task 03 의 v3 재산정에서 검증. 옵션 B (rect 제약 변경) 시 Exp10 trial 답변 대다수 무효화 가능.
- **synthesis-04 keyword 변경의 Exp10 v3 영향**: Task 03 의 v3 재산정에서 동일 영향 확인.
- **longctx-medium-2hop-02 영향**: Exp09 만 사용. Task 02 의 5-trial 분석에서 호환성 확인.
- **다른 task 우발 변경**: 큰 JSON 파일에서 indent / 자동 정렬로 다른 객체가 reformat 위험. Verification 3 의 git diff 검사로 보장.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/measure.py` / `experiments/orchestrator.py` / `experiments/schema.py` — 채점 / orchestrator 영역
- `experiments/exp10_reproducibility_cost/rescore_v3.py` — Task 03 영역 (재실행만)
- `experiments/exp09_longctx/run.py` / `run_append_trials.py` / `analyze_stats.py` — Task 02 영역
- 모든 결과 JSON (v2 final / v3 rescored / 5-trial / Exp06 reconciliation / longctx 결과) — read-only
- README / 노트북 / result.md — Task 04 영역
- `experiments/tasks/taskset.json` 의 logic-04 의 negative_patterns / conclusion_required 변경 금지 (직전 plan 의 검증된 영역)
- 다른 task 객체 (logic-01~04, math-01/02/04, synthesis-01/02/03, 기타 longctx) — 본 task 는 3 FAIL task 만
