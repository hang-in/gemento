---
type: task
status: abandoned
updated_at: 2026-04-25
plan: scoring-v2
task_number: 2
parallel_group: B
depends_on: [1]
---

# Task 2: score_answer_v2 구현 및 교체

## Changed files

- `experiments/measure.py` — `score_answer_v2` 함수 추가 (line 24 이후), 분석 함수 4개 수정

## Change description

### 1. score_answer_v2 함수 추가

`measure.py` `score_answer` 함수 (line 24) 바로 아래에 추가:

```python
def score_answer_v2(response: str, task_entry: dict) -> float:
    """
    keyword-group 기반 채점.
    scoring_keywords: [[token, ...], ...]
    각 그룹의 모든 토큰이 response에 포함되면 해당 그룹 매칭.
    점수 = 매칭된 그룹 수 / 전체 그룹 수
    scoring_keywords 없으면 score_answer(v1) fallback.
    """
    keywords = task_entry.get("scoring_keywords")
    if not keywords:
        return score_answer(response, task_entry.get("expected_answer", ""))
    
    response_lower = response.lower()
    matched = sum(
        1 for group in keywords
        if all(token.lower() in response_lower for token in group)
    )
    return matched / len(keywords)
```

### 2. 분석 함수 4개 수정

`score_answer(str, str)` 호출을 `score_answer_v2(str, task_entry)` 로 교체.

대상 함수 및 수정 위치:

| 함수 | 현재 호출 | 변경 후 |
|------|-----------|---------|
| `analyze_baseline` (line 50) | `score_answer(t["response"], tr.get("expected_answer", ""))` | `score_answer_v2(t["response"], tr)` |
| `analyze_multiloop` (line 65) | `score_answer(str(trial.get("final_answer", "")), tr.get("expected_answer", ""))` | `score_answer_v2(str(trial.get("final_answer", "")), tr)` |
| `analyze_abc_pipeline` (line 82) | `score_answer(str(trial.get("final_answer", "")), tr.get("expected_answer", ""))` | `score_answer_v2(str(trial.get("final_answer", "")), tr)` |
| `analyze_solo_budget` (line 141) | `score_answer(str(trial.get("final_answer", "")), tr.get("expected_answer", ""))` | `score_answer_v2(str(trial.get("final_answer", "")), tr)` |

**주의**: `analyze_handoff_protocol` (line 98)은 정확도 채점이 아닌 handoff loss/backprop 측정이므로 수정 불필요.

### 3. taskset.json 로드 추가

분석 함수들이 `score_answer_v2`를 호출하려면 `task_entry` (scoring_keywords 포함)가 필요하다.
현재 `data["results"]` 의 각 `tr`은 `expected_answer` 만 포함하고 `scoring_keywords`는 없다.

해결 방법: `measure.py` `main()` 함수에서 taskset.json을 로드하여 task_id → task_entry 매핑을 구성하고, 각 분석 함수에 파라미터로 전달한다.

```python
# main() 내부, load_result() 호출 이후에 추가
TASKSET_PATH = Path(__file__).parent / "tasks" / "taskset.json"
task_map: dict = {}
if TASKSET_PATH.exists():
    with open(TASKSET_PATH) as f:
        ts = json.load(f)
    task_map = {t["id"]: t for t in ts.get("tasks", [])}
```

분석 함수 시그니처 변경:
- `analyze_baseline(data)` → `analyze_baseline(data, task_map=None)`
- `analyze_multiloop(data)` → `analyze_multiloop(data, task_map=None)`
- `analyze_abc_pipeline(data)` → `analyze_abc_pipeline(data, task_map=None)`
- `analyze_solo_budget(data)` → `analyze_solo_budget(data, task_map=None)`

내부에서 `task_map.get(tr["task_id"], tr)` 로 task_entry를 가져온다 (없으면 tr 자체를 fallback으로 사용).

## Dependencies

- Task 1 완료 필수 (`scoring_keywords` 필드가 taskset.json에 존재해야 함)

## Verification

```bash
cd /Users/d9ng/privateProject/gemento

# 1. score_answer_v2 함수 존재 확인
python3 -c "from experiments.measure import score_answer_v2; print('score_answer_v2 imported OK')" 2>/dev/null || \
python3 -c "
import sys; sys.path.insert(0, 'experiments')
from measure import score_answer_v2
# 기본 동작 테스트
task = {'scoring_keywords': [['13', 'apples'], ['7', 'oranges']]}
score = score_answer_v2('The customer bought 13 apples and 7 oranges.', task)
assert score == 1.0, f'Expected 1.0, got {score}'
score2 = score_answer_v2('13 apples only', task)
assert score2 == 0.5, f'Expected 0.5, got {score2}'
print('score_answer_v2: OK (1.0 full match, 0.5 partial match)')
"

# 2. 기존 분석 함수 정상 동작 확인 (exp06 재채점)
python3 experiments/measure.py experiments/results/exp06_solo_budget_20260415_114625.json
```

예상 출력: exp06 solo_budget 분석이 출력되며, 기존과 다른 (더 높은) 점수 확인.

## Risks

- 분석 함수 시그니처 변경으로 인해 `main()`에서 호출 방식도 수정 필요 — `ANALYZERS` 딕셔너리와 호출 코드 일관성 유지
- `task_map`이 없는 환경(taskset.json 경로 불일치)에서는 v1 fallback으로 동작 — 명시적 경고 출력 권장

## Scope boundary

수정 금지 파일:
- `experiments/tasks/taskset.json` — Task 1 영역 (읽기만 허용)
- `experiments/results/` 하위 모든 JSON — 읽기 전용
