---
type: task
status: in_progress
updated_at: 2026-04-15
plan: scoring-v2
task_number: 3
parallel_group: B
depends_on: [2]
---

# Task 3: rescore 명령 추가 및 전체 재채점

## Changed files

- `experiments/measure.py` — `--rescore` 옵션 및 `rescore_all()` 함수 추가

## Change description

### 1. rescore_all() 함수 추가

`main()` 함수 위에 추가:

```python
def rescore_all(results_dir: Path, task_map: dict):
    """
    results/ 디렉토리의 모든 JSON을 v1/v2로 재채점하여 비교표 출력.
    결과 JSON은 수정하지 않는다 (읽기 전용).
    """
```

처리 대상 실험 타입 및 집계 방식:

| 실험 타입 | final_answer 위치 | 집계 단위 |
|-----------|-------------------|-----------|
| baseline | `tr["trials"][i]["response"]` | task × trial |
| multiloop | `tr["trials"][i]["final_answer"]` | task × trial |
| abc_pipeline | `tr["trials"][i]["final_answer"]` | task × trial |
| handoff_protocol | `tr["trials"][i]["final_answer"]` | task × trial |
| solo_budget | `tr["trials"][i]["final_answer"]` | task × trial |

출력 형식 (stdout):

```
═══════════════════════════════════════════════════
  Rescore 결과 비교 (v1 substring vs v2 keyword)
═══════════════════════════════════════════════════
파일명                              v1 avg   v2 avg   diff
exp00_baseline_...json             0.500    0.500    +0.0%
exp04_abc_pipeline_...json         0.750    0.833    +8.3%
exp045_handoff_...20260414...json  0.889    0.889    +0.0%
exp06_solo_budget_...json          0.311    0.663    +35.2%
...
```

- 가장 최신 파일만 처리 (각 실험 타입별 `sorted()[-1]`)
- `handoff_protocol` 타입은 accuracy 채점이 없으므로 skip (N/A 표시)
- v2가 scoring_keywords 없는 태스크를 만나면 v1 값과 동일 처리

### 2. main() argparse 수정

```python
parser.add_argument("result_file", nargs="?", help="단일 파일 분석")
parser.add_argument("--rescore", action="store_true", help="전체 결과 재채점 비교")
```

`result_file`을 optional로 변경하고 `--rescore` 플래그 추가:

```python
if args.rescore:
    rescore_all(Path(__file__).parent / "results", task_map)
elif args.result_file:
    # 기존 단일 파일 분석 로직
    ...
else:
    parser.print_help()
```

## Dependencies

- Task 2 완료 필수 (`score_answer_v2`, `task_map` 로드 로직이 있어야 함)

## Verification

```bash
cd /Users/d9ng/privateProject/gemento

# 1. --rescore 옵션 존재 및 실행 확인
python3 experiments/measure.py --rescore

# 2. 출력에 v1/v2 비교 컬럼이 있는지 확인
python3 experiments/measure.py --rescore | grep -E "v1|v2|diff"

# 3. exp06 solo_budget v2 점수가 v1보다 높은지 확인
python3 experiments/measure.py --rescore | grep "exp06"
# 예상: v2 avg > v1 avg (0.311 → 0.5 이상)

# 4. 기존 단일 파일 분석이 여전히 동작하는지 확인 (regression)
python3 experiments/measure.py experiments/results/exp06_solo_budget_20260415_114625.json
```

## Risks

- `nargs="?"` 변경으로 기존 호출 방식 (`python measure.py result_file.json`) 이 여전히 동작해야 함 — Verification #4로 확인
- 결과 디렉토리에 파싱 불가한 JSON이 있을 경우 skip하되 경고 출력

## Scope boundary

수정 금지 파일:
- `experiments/tasks/taskset.json` — Task 1 영역
- `experiments/results/` 하위 모든 JSON — 읽기 전용
