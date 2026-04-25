---
type: task
status: abandoned
updated_at: 2026-04-25
plan: scoring-v2
task_number: 1
parallel_group: A
depends_on: []
---

# Task 1: taskset.json에 scoring_keywords 추가

## Changed files

- `experiments/tasks/taskset.json` — 기존 파일 수정 (9개 태스크 전체)

## Change description

각 태스크 오브젝트에 `scoring_keywords` 필드를 추가한다.
형식: `[[token1, token2], [token3]]` — 각 내부 배열은 AND 그룹 (모든 토큰이 응답에 포함되어야 함), 외부 배열은 OR 그룹 (하나라도 매칭되면 해당 그룹 통과).

채점 기준 (확정):

| task_id | scoring_keywords | 설계 근거 |
|---------|-----------------|-----------|
| math-01 | `[["13", "apples"], ["7", "oranges"]]` | 두 값이 각각 컨텍스트와 함께 등장해야 함 |
| logic-01 | `[["spanish"]]` | 단일 키워드, 대소문자 무관 |
| synthesis-01 | `[["provider a"], ["only"]]` | "Only Provider A" 패턴 — 두 토큰 모두 포함 시 정답 |
| math-02 | `[["192"]]` | 숫자값 단일 검증 |
| logic-02 | `[["105"], ["inconsistent"]], [["0"]]` | 105 초과 + inconsistent 언급, 또는 0 답변 |
| synthesis-02 | `[["65"], ["130"]]` | 거리 65km 및 비용 $130 |
| math-03 | `[["6"], ["4"], ["5"]]` | round=6, square=4, rectangular=5 — 세 값 모두 |
| logic-03 | `[["monday", "e"], ["tuesday", "a"], ["wednesday", "d"], ["thursday", "c"], ["friday", "b"]]` | 요일-이벤트 쌍 5개 모두 |
| synthesis-03 | `[["david"]], [["alice"], ["180"]], [["bob"], ["7"]]` | David 적격, Alice/Bob 탈락 이유 포함 |

**주의**: logic-03과 synthesis-03은 그룹 수가 많아 부분 점수 반환이 중요. `score_answer_v2`가 매칭된 그룹 비율을 점수로 반환한다 (Task 2에서 구현).

### 실제 추가할 JSON 필드 예시

```json
{
  "id": "math-01",
  ...
  "scoring_keywords": [
    ["13", "apples"],
    ["7", "oranges"]
  ]
}
```

## Dependencies

없음 (첫 번째 태스크)

## Verification

```bash
# scoring_keywords 필드가 9개 태스크 모두에 존재하는지 확인
cd /Users/d9ng/privateProject/gemento
python3 -c "
import json
with open('experiments/tasks/taskset.json') as f:
    data = json.load(f)
tasks = data['tasks']
missing = [t['id'] for t in tasks if 'scoring_keywords' not in t]
print('Missing scoring_keywords:', missing if missing else 'NONE — all tasks have it')
assert not missing, 'Some tasks are missing scoring_keywords'
print('OK: all', len(tasks), 'tasks have scoring_keywords')
"
```

## Risks

- logic-03 / synthesis-03의 keyword 설계가 너무 엄격하면 false negative 유지 가능 — 내용 확인 후 토큰 선택
- math-03의 `["6", "4", "5"]`는 다른 숫자 컨텍스트에서 우연히 매칭될 수 있음 — 실제 결과 데이터로 검증 필요

## Scope boundary

수정 금지 파일:
- `experiments/measure.py` — Task 2/3 영역
- `experiments/results/` 하위 모든 JSON — 읽기 전용
