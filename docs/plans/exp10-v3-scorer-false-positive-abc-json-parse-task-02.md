---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: exp10-v3-scorer-false-positive-abc-json-parse
parallel_group: A
depends_on: [01]
---

# Task 02 — taskset.json 의 logic-04 negative_patterns 보강

## Changed files

- `experiments/tasks/taskset.json` — **수정**. `id == "logic-04"` 의 task 객체에 `negative_patterns` 필드 추가. 다른 task 객체 변경 0.

신규 파일 0.

## Change description

### 배경

Architect 측 사전 점검 결과 logic-04 60 trial 의 false positive 12건 (mismatch 9 + ambig 3) 모두 다음 4 패턴 중 하나에 매칭:

1. `r"no\s+(unique|definitive|clear)\s+(culprit|answer|solution)"` — "no single suspect can be identified" / "no definitive answer" 류
2. `r"cannot\s+be\s+(identified|determined|solved)"` — "cannot be identified"
3. `r"contradicts?|contradiction|contradictions"` — "leads to a contradiction" 류
4. `r"puzzle\s+is\s+(flawed|inconsistent|ill-?posed)"` — "the puzzle is logically inconsistent" 류

본 task 는 이 4 패턴을 logic-04 task 정의에 추가한다.

### Step 1 — taskset.json 의 logic-04 객체 수정

`experiments/tasks/taskset.json` 의 `tasks` 배열에서 `"id": "logic-04"` 인 객체를 찾아, 기존 필드 (`prompt`, `scoring_keywords`, `expected_answer`, `constraints`, `prefab_assertions`, `fault_injections`, `category`, `difficulty`, `objective`) 와 동일 레벨에 다음 필드를 **추가**:

```json
"negative_patterns": [
  "no\\s+(unique|definitive|clear)\\s+(culprit|answer|solution)",
  "cannot\\s+be\\s+(identified|determined|solved)",
  "contradicts?|contradiction|contradictions",
  "puzzle\\s+is\\s+(flawed|inconsistent|ill-?posed)"
],
```

JSON 이라 정규식의 `\s` 는 `\\s` 로 escape. 문자열 자체는 Python 의 `re` 가 받았을 때 의도한 패턴.

### Step 2 — 정합성 검증

추가 후 JSON 파싱 가능 + 4 패턴이 의도대로 컴파일되는지 확인:

```bash
.venv/bin/python -c "
import json, re
with open('experiments/tasks/taskset.json') as f:
    d = json.load(f)
logic04 = next(t for t in d['tasks'] if t['id'] == 'logic-04')
patterns = logic04.get('negative_patterns', [])
print('count:', len(patterns))
for p in patterns:
    re.compile(p)
    print('  ok:', p)
"
```

기대 출력:
```
count: 4
  ok: no\s+(unique|definitive|clear)\s+(culprit|answer|solution)
  ok: cannot\s+be\s+(identified|determined|solved)
  ok: contradicts?|contradiction|contradictions
  ok: puzzle\s+is\s+(flawed|inconsistent|ill-?posed)
```

### Step 3 — 다른 task 변경 없음 확인

`experiments/tasks/taskset.json` 의 `tasks` 배열 길이, logic-04 외 task 의 필드, `scoring_keywords` 모든 task 변경 없음을 git diff 로 확인.

## Dependencies

- Task 01 — `score_answer_v3` 가 이 필드를 읽음. 함수 구현이 먼저 있어야 통합 검증 가능.
- 패키지: 표준 `json`, `re`.

## Verification

```bash
# 1) JSON parse + 4 패턴 정규식 컴파일
.venv/bin/python -c "
import json, re
with open('experiments/tasks/taskset.json') as f:
    d = json.load(f)
logic04 = next(t for t in d['tasks'] if t['id'] == 'logic-04')
patterns = logic04['negative_patterns']
assert len(patterns) == 4, f'expected 4 patterns, got {len(patterns)}'
for p in patterns:
    re.compile(p)
print('ok')
"

# 2) Task 01 의 score_answer_v3 가 실제 logic-04 task 로 동작
.venv/bin/python -c "
import json
from experiments.measure import score_answer_v3
with open('experiments/tasks/taskset.json') as f:
    d = json.load(f)
logic04 = next(t for t in d['tasks'] if t['id'] == 'logic-04')

# false positive 케이스: 본 v2 의 retry trial 17 답안
fp = 'The problem as stated leads to a logical contradiction, implying no one can be the culprit.'
assert score_answer_v3(fp, logic04) == 0.0, 'expected negative_pattern block'

# true positive 케이스: 명시적 정답
tp = 'Casey committed the crime.'
assert score_answer_v3(tp, logic04) == 1.0

# v2 와 비교 (substring) — fp 는 v2 에서 1.0 (false positive)
from experiments.measure import score_answer_v2
assert score_answer_v2(fp, logic04) == 1.0
print('v3 blocks fp; v2 does not — ok')
"

# 3) 다른 task 변경 없음 (git diff 로 logic-04 만 변경)
git diff experiments/tasks/taskset.json | grep -E '^\+|\-' | grep -v '^[+-]{3}' | head -30
# Manual: diff 의 추가 라인이 모두 negative_patterns 블록 안에만 있는지 확인
```

세 명령 모두 정상 출력 + assertion 통과.

## Risks

- **JSON escape 실수**: 정규식의 `\s` 가 JSON 문자열에서 `\\s` 로 escape 안 되면 `re.compile` 에서 deprecation warning 또는 의도와 다른 매칭. Verification step 1 에서 검증.
- **다른 task 우발적 변경**: 큰 JSON 파일에서 indent 자동 정렬로 다른 객체가 reformat 될 수 있음. git diff 로 logic-04 영역만 변경됐는지 검증.
- **logic-04 의 진짜 정답 trial 1 건이 negative_patterns 에 잡힐 위험**: 본 plan 의 4 패턴은 사전 점검에서 mismatch/ambig 만 잡고 진짜 정답 trial (gemma_8loop t? 단 1 건) 은 통과 확인됨. Task 03 의 전수 재산정에서 재확인.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/tasks/taskset.json` 의 logic-04 외 모든 task 객체. 본 plan 에서는 logic-04 만 영향.
- `experiments/measure.py` — Task 01 영역.
- `experiments/orchestrator.py` — Task 04/05 영역.
- 신규 task 추가 / 기존 task 의 `scoring_keywords` 변경 / `expected_answer` 변경 — 본 task 범위 밖.
