---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: exp06-h4-recheck-expanded-taskset-pre-exp11
parallel_group: A
depends_on: []
---

# Task 01 — 신규 3 task 정의 + validate_taskset 통합

## Changed files

- `experiments/tasks/taskset.json` — **수정 (append only)**. 12 → 15 task. 새 3 task 추가 — planning 2 + synthesis 1 (결정 6 default)
- `experiments/validate_taskset.py` — **수정**. `_validate_planning_xx` (또는 일반 _validate) 분기 추가. synthesis 1 추가 task 는 기존 `_validate_synthesis_xx` 패턴 재사용
- (선택) `experiments/tasks/taskset_v0.json` — **신규**. 기존 12 task 백업 (reproducibility 보존). 또는 git history 로 충분 — Architect 추천: git history 의존, 별도 백업 안 함

수정 2 파일.

## Change description

### 배경

H4 재검증을 위해 task set 12 → 15 확대. 신규 3 task 의 카테고리:
- **planning 2** — 다단계 분해/조정 task. Role 분리 효과가 가장 명료할 도메인
- **synthesis 1** — 기존 카테고리 추가 (결정 6 default). H4 본질 (역할 분리) 효과 명료

### Step 1 — planning task 2 후보 정의

신규 task 의 schema (기존 task 와 일치):

```json
{
  "id": "planning-01",
  "category": "planning",
  "difficulty": "hard",
  "objective": "주어진 다단계 작업을 분해하고 의존성을 식별하라.",
  "prompt": "...",
  "expected_answer": "...",
  "scoring_keywords": [["..."], ["..."]],
  "constraints": ["...", "..."]
}
```

planning-01 (Architect 검증 완료, unique 정답):

```json
{
  "id": "planning-01",
  "category": "planning",
  "difficulty": "medium",
  "objective": "의존성 있는 다단계 task 의 sequential 일정 계산.",
  "prompt": "Three tasks (A, B, C) must be completed in strict sequential order: A first, then B, then C (each task depends on the previous one finishing). Task durations: A = 2 hours, B = 3 hours, C = 1 hour. A single worker handles all tasks with no preemption. The worker starts at 9:00 AM. Compute: (1) the start and end time of each task, and (2) the total elapsed time from start to finish.",
  "expected_answer": "A: 9:00 AM - 11:00 AM (2 hours). B: 11:00 AM - 2:00 PM (3 hours). C: 2:00 PM - 3:00 PM (1 hour). Total elapsed time: 6 hours.",
  "scoring_keywords": [["9:00", "11:00"], ["2:00"], ["3:00"], ["6", "hours"]],
  "constraints": [
    "Sequential order must be respected: A → B → C",
    "Single worker, no preemption",
    "Compute exact start/end times + total elapsed"
  ]
}
```

**검증** (Architect): A(9-11) → B(11-14) → C(14-15). 총 6h. unique 정답.

planning-02 (Architect 검증 완료, 정답 12h — 직전 plan 의 11h 는 오답이었음):

```json
{
  "id": "planning-02",
  "category": "planning",
  "difficulty": "very_hard",
  "objective": "프로젝트 작업 그래프에서 critical path 식별 + 자원 충돌 해소.",
  "prompt": "A project has 6 tasks: A(2h), B(3h), C(1h), D(4h), E(2h), F(3h). Dependencies: B requires A, C requires A, D requires B and C, E requires D, F requires D. Available workers: 2 (each can do one task at a time, no preemption). Compute the minimum total project time. List the schedule (which worker does which task at which time) and identify the critical path.",
  "expected_answer": "Total time: 12 hours. Critical path: A → B → D → F (2+3+4+3 = 12h). Schedule: W1 does A(0-2), B(2-5), D(5-9), E(9-11). W2 idle (0-2), C(2-3), idle (3-5), idle (5-9), F(9-12). E (9-11) finishes earlier than F (9-12), so total = 12h driven by F.",
  "scoring_keywords": [["12", "hours"], ["A", "B", "D", "F"], ["critical path"]],
  "constraints": [
    "Dependencies must be respected",
    "Each worker does one task at a time",
    "Total time must be minimized"
  ]
}
```

**검증** (Architect): D 완료 = t=9 (A 2h + B 3h + D 4h, B/C 병렬 가능). D 후 E(2h)+F(3h) 병렬 시작. E 끝=11, F 끝=12. 따라서 총 12h. critical path = A→B→D→F. 직전 plan 의 expected "11h" 는 오답이었음 (E=2h 만 고려, F=3h 누락).

### Step 2 — synthesis 1 추가 task 후보

기존 synthesis-01~04 패턴 따름. H4 본질 (역할 분리, 다관점 종합) 측정에 적합한 도메인:

```json
{
  "id": "synthesis-05",
  "category": "information_synthesis",
  "difficulty": "hard",
  "objective": "여러 출처의 모순된 정보를 종합하여 가장 일관된 결론 도출.",
  "prompt": "...",
  "expected_answer": "...",
  "scoring_keywords": [...]
}
```

synthesis-05 후보 (다출처 모순 종합):
```json
{
  "id": "synthesis-05",
  "category": "information_synthesis",
  "difficulty": "hard",
  "objective": "3 출처의 사건 시간 정보가 부분 모순 — 가장 가능성 높은 sequence 식별.",
  "prompt": "Source 1 says event A happened at 9am, event B at 10am. Source 2 says B happened before A, both before noon. Source 3 says A happened at 9am sharp, but C happened between A and B. List the most likely sequence of A, B, C with timing, and explain which source is most reliable.",
  "expected_answer": "Most likely: A at 9am, C between 9-10am, B at 10am. Source 1 + Source 3 corroborate A at 9am; Source 2 contradicts. Source 1 most reliable (matches Source 3).",
  "scoring_keywords": [["A", "9am"], ["C", "between"], ["B", "10am"], ["Source 1", "reliable"]],
  "constraints": [
    "Identify time of A, B, C",
    "Order A → C → B",
    "Discuss source reliability"
  ]
}
```

### Step 3 — `experiments/tasks/taskset.json` append

**중요**: append 만. 기존 12 task 변경 0. JSON 의 `tasks` array 끝에 위 3 task append.

```python
# 작업 패턴 (Developer 직접 수정 또는 짧은 script):
import json
with open('experiments/tasks/taskset.json', encoding='utf-8') as f:
    d = json.load(f)
new_tasks = [planning_01, planning_02, synthesis_05]  # 위 정의
d['tasks'].extend(new_tasks)
with open('experiments/tasks/taskset.json', 'w', encoding='utf-8') as f:
    json.dump(d, f, ensure_ascii=False, indent=2)
```

또는 직접 JSON 편집. 둘 다 가능. 단 indent + key 순서 보존.

### Step 4 — `experiments/validate_taskset.py` 분기 추가

기존 `_validate_math_xx` / `_validate_synthesis_xx` 패턴 따름. planning category 는 신규.

```python
# 추가
def _validate_planning_01(task: dict) -> tuple[str, str]:
    """planning-01 의 sequential schedule 정답 검증.

    A=9-11, B=11-14, C=14-15. 총 6h. 시각 + 총 시간 keyword 검증.
    """
    ans = task.get("expected_answer", "").lower()
    required = ["9:00", "11:00", "2:00", "3:00", "6"]
    for kw in required:
        if kw not in ans:
            return "FAIL", f"required keyword '{kw}' missing"
    return "PASS", "all keywords in expected_answer"


def _validate_planning_02(task: dict) -> tuple[str, str]:
    """planning-02 의 critical path 식별 검증.

    정답: 12 hours, critical path A→B→D→F.
    """
    ans = task.get("expected_answer", "").lower()
    if "12" not in ans:
        return "FAIL", "expected total time 12 hours missing"
    if "critical path" not in ans:
        return "FAIL", "critical path identification missing"
    return "PASS", "12 hours + critical path in expected_answer"
```

synthesis-05 는 기존 `_validate_synthesis_03` 같은 패턴 — keyword 존재 검증.

분기 등록 (`_VALIDATORS` dict 또는 dispatch):
```python
_VALIDATORS["planning-01"] = _validate_planning_01
_VALIDATORS["planning-02"] = _validate_planning_02
# synthesis-05 는 generic _validate_synthesis 적용
```

### Step 5 — validate_taskset 통합 검증

```bash
.venv/Scripts/python -m experiments.validate_taskset
# 기대: 25 PASS / 0 FAIL / 0 WARN / 0 SKIP (12 + 3 + 10 longctx = 25)
```

## Dependencies

- 패키지: 표준만 (`json`)
- 다른 subtask: 없음 (parallel_group A, 첫 노드)
- 입력: 없음
- 출력: 본 task 의 새 task set 이 task-04 의 실험 입력

## Verification

```bash
# 1) taskset.json 의 task 수
.venv/Scripts/python -c "
import json
d = json.load(open('experiments/tasks/taskset.json', encoding='utf-8'))
ids = [t['id'] for t in d['tasks']]
assert len(d['tasks']) == 15, f'tasks: {len(d[\"tasks\"])}'
assert 'planning-01' in ids
assert 'planning-02' in ids
assert 'synthesis-05' in ids
print(f'verification 1 ok: 15 tasks, 신규 3 추가')
"

# 2) validate_taskset 22 → 25 PASS (longctx 10 별개 - 25 - 10 = 15? 또는 12 → 15 만 검증)
.venv/Scripts/python -m experiments.validate_taskset 2>&1 | tail -3
# 기대: 22 PASS → 25 PASS (taskset.json + longctx_taskset.json 합산), 0 FAIL

# 3) 신규 task 의 schema 일관성
.venv/Scripts/python -c "
import json
d = json.load(open('experiments/tasks/taskset.json', encoding='utf-8'))
new = [t for t in d['tasks'] if t['id'] in ('planning-01','planning-02','synthesis-05')]
required_keys = {'id','category','difficulty','objective','prompt','expected_answer','scoring_keywords','constraints'}
for t in new:
    missing = required_keys - set(t.keys())
    assert not missing, f'{t[\"id\"]} missing: {missing}'
    assert isinstance(t['scoring_keywords'], list)
    assert all(isinstance(g, list) for g in t['scoring_keywords'])
print('verification 3 ok: 신규 task schema 일관성')
"
```

3 명령 모두 정상.

## Risks

- ~~**Risk 1 — 신규 3 task 의 정답 검증 결함**~~ — **차단 완료** (2026-04-30 Architect 시뮬레이션):
  - planning-01: 직전 multi-solution 안 (5명 4작업) 폐기. sequential schedule (A→B→C, 9:00 시작, 총 6h) 으로 재정의 — unique 정답
  - planning-02: 직전 plan 의 expected "11h" 오답. 실제 critical path A→B→D→F = 12h — Architect 정정 (E=2h 만 고려한 오류, F=3h 가 더 길어서 critical)
  - synthesis-05: A=9am, C 9-10am, B=10am, Source 1+3 corroborate, Source 2 contradicts — 직전 plan expected 와 일치. OK
- **Risk 2 — planning category 가 기존 4 카테고리와 호환 안 됨**: 결과 분석 helper / aggregation 코드가 카테고리 enum 으로 분기되어 있을 가능성. 정찰 필수 — `experiments/measure.py` 의 카테고리 처리 read.
- **Risk 3 — Developer 가 임의로 task 정의 추가**: 본 task 의 3 task 후보는 Architect 예시. Developer 가 사용자 검토 없이 정정/대체 금지. 사용자 호출 후 진행
- **Risk 4 — JSON 의 indent / key 순서 변경**: `json.dump` 의 default option 이 ascii 기본 / sort_keys 적용 — 기존 task 의 한국어 / 순서 보존 위해 `ensure_ascii=False` + key 순서 보존 필수

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/orchestrator.py` / `experiments/measure.py` / `experiments/schema.py` — 본 plan 영역 외
- `experiments/run_helpers.py` — Stage 2A 영역
- 기존 12 task 의 정답 / keyword / constraints — 변경 금지 (append only)
- `experiments/tasks/longctx_taskset.json` — 본 plan 영역 외
- 모든 `experiments/exp**/run.py` — Task 02 영역
- 모든 분석 / measure helper — Task 03 영역
- 결과 JSON (모두 read-only)
- README / researchNotebook — Task 05 영역
- `docs/reference/results/exp-06-solo-budget.md` — Task 05 영역

## 사용자 호출 시점

- 신규 3 task 의 정답 검증 — Architect 예시는 후보일 뿐, 사용자 시각 검토 의무
- 결정 6 (synthesis 외 다른 카테고리 선호) 또는 결정 8 (영어 외 한국어 선호) 변경 시
- planning-01/02 의 정답 형식이 채점 keyword 와 호환 안 될 때
