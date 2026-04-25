---
type: task
status: abandoned
plan: exp07-loop-saturation
task: 1
parallel_group: A
depends_on: []
updated_at: 2026-04-25---

# Task 1: 고난도 태스크 3종 추가

## Changed files

- `experiments/tasks/taskset.json` — 기존 9개 태스크 뒤에 3개 추가

## Change description

기존 03급(hard/very_hard)보다 추론 단계가 1~2단 더 긴 04급 태스크 3종을 추가한다.
목적: 현재 태스크셋의 난이도 천장을 높여 루프 포화점 측정의 유효성을 확보.

### math-04: 3변수 최적화 (difficulty: very_hard)

```json
{
  "id": "math-04",
  "category": "math",
  "difficulty": "very_hard",
  "objective": "제약 조건이 있는 최적화 문제를 단계적으로 풀어라.",
  "prompt": "A factory produces three products X, Y, Z. Each unit of X requires 2 hours of labor and 3 kg of material. Each unit of Y requires 3 hours of labor and 2 kg of material. Each unit of Z requires 4 hours of labor and 1 kg of material. Available: 240 hours of labor and 150 kg of material per week. Profit per unit: X=$50, Y=$40, Z=$30. Additionally, the factory must produce at least 10 units of each product. What production plan maximizes weekly profit? Find the exact quantities.",
  "expected_answer": "X=30, Y=30, Z=10, profit=$2800",
  "scoring_keywords": [["30"], ["2800"]],
  "constraints": ["모든 제약 조건을 명시해야 한다", "가능 영역 경계점을 검사해야 한다", "검산 필수"],
  "prefab_assertions": [],
  "fault_injections": []
}
```

### logic-04: 4인 거짓말쟁이 퍼즐 (difficulty: very_hard)

```json
{
  "id": "logic-04",
  "category": "logic",
  "difficulty": "very_hard",
  "objective": "각 인물의 진실/거짓을 판별하고 범인을 찾아라.",
  "prompt": "A crime was committed by exactly one of four suspects: Alex, Blake, Casey, Dana. Each makes two statements:\n\nAlex: 'I didn't do it.' 'Blake did it.'\nBlake: 'I didn't do it.' 'Casey did it.'\nCasey: 'I didn't do it.' 'I was at home all day.'\nDana: 'I didn't do it.' 'Alex is lying about Blake.'\n\nRules: The guilty person lies in BOTH statements. Each innocent person tells the truth in EXACTLY ONE of their two statements. Who committed the crime?",
  "expected_answer": "Casey committed the crime",
  "scoring_keywords": [["casey"]],
  "constraints": ["각 인물의 두 진술을 모두 분석해야 한다", "가정 후 모순 검증(귀류법)을 사용해야 한다", "모든 4명을 테스트해야 한다"],
  "prefab_assertions": [],
  "fault_injections": []
}
```

### synthesis-04: 6개 소스 교차 검증 + 모순 식별 (difficulty: very_hard)

```json
{
  "id": "synthesis-04",
  "category": "information_synthesis",
  "difficulty": "very_hard",
  "objective": "6개의 데이터 소스를 교차 검증하여 모순을 식별하고 가장 신뢰할 수 있는 결론을 도출하라.",
  "prompt": "A research team is investigating the population of a rare bird species in a region. Six reports:\n\nReport 1 (2024 field survey): 'Counted 340 individuals in 5 zones. Zone A: 80, Zone B: 65, Zone C: 70, Zone D: 55, Zone E: 70.'\nReport 2 (satellite imagery, 2024): 'Estimated 400±50 individuals based on nest counts.'\nReport 3 (local ranger, 2024): 'Population has declined 20% since 2020 when it was 500.'\nReport 4 (university study, 2023): 'Population was 380 in 2023 with 5% annual growth expected.'\nReport 5 (conservation NGO, 2024): 'Zone C was destroyed by wildfire in early 2024. No birds remain in Zone C.'\nReport 6 (government census, 2024): 'Total population across all zones: 350. Zone C: 60 individuals.'\n\nIdentify all contradictions between reports. Which reports are most likely reliable? What is the best estimate of the current population?",
  "expected_answer": "Reports 5 and 6 contradict on Zone C (0 vs 60). Reports 1 and 6 conflict on total (340 vs 350). Report 3 implies 400 (500×0.8) which aligns with Report 2. Report 4 predicts 399 (380×1.05) for 2024. If Zone C is destroyed (Report 5), adjusted Report 1 total = 340-70 = 270. Best estimate: 270-280 (field survey minus destroyed zone).",
  "scoring_keywords": [["270"], ["contradict", "zone c"], ["report 5", "report 6"]],
  "constraints": ["모든 6개 보고서를 분석해야 한다", "보고서 간 모순을 명시적으로 나열해야 한다", "신뢰도 판단 근거를 제시해야 한다", "최종 추정치에 계산 과정을 포함해�� 한다"],
  "prefab_assertions": [],
  "fault_injections": []
}
```

### 구현 순서

1. `taskset.json`의 `tasks` 배열 끝(synthesis-03 다음)에 위 3개 객체를 추가
2. 기존 9개 태스크는 절대 수정하지 않음
3. JSON 유효성 검증

## Dependencies

없음 (Task 2, 3과 병렬 가능)

## Verification

```bash
cd /Users/d9ng/privateProject/gemento/experiments
python -c "
import json
with open('tasks/taskset.json') as f:
    data = json.load(f)
tasks = data['tasks']
print(f'Total tasks: {len(tasks)}')
assert len(tasks) == 12, f'Expected 12 tasks, got {len(tasks)}'
new_ids = {t['id'] for t in tasks[-3:]}
assert new_ids == {'math-04', 'logic-04', 'synthesis-04'}, f'Wrong new task IDs: {new_ids}'
for t in tasks[-3:]:
    assert 'scoring_keywords' in t, f'{t[\"id\"]} missing scoring_keywords'
    assert len(t['scoring_keywords']) > 0, f'{t[\"id\"]} empty scoring_keywords'
print('All checks passed')
"
```

## Risks

- math-04 최적해 검증: LP 문제이므로 정답이 맞는지 수작업 확인 필요 (코너 포인트 계산)
- synthesis-04 채점 난이도: 자유 형식 답변에서 키워드 매칭이 까다로울 수 있음 → scoring_keywords를 보수적으로 설정

## Scope boundary

수정 금지:
- `experiments/system_prompt.py` (Task 2 영역)
- `experiments/orchestrator.py` (Task 3 영��)
- `experiments/run_experiment.py` (Task 4 영���)
- `experiments/measure.py` (Task 5 영역)
- 기존 9개 태스크 데이터
