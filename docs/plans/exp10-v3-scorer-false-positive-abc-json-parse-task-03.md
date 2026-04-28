---
type: plan-task
status: todo
updated_at: 2026-04-29
parent_plan: exp10-v3-scorer-false-positive-abc-json-parse
parallel_group: A
depends_on: [01, 02]
---

# Task 03 — 540 trial 전수 v3 재산정

## Changed files

- `experiments/exp10_reproducibility_cost/rescore_v3.py` — **신규**. v2 final JSON 입력 → v3 채점 재산정 → 출력 + stdout 비교 표.

신규 파일 1, 다른 파일 수정 0.

## Change description

### 배경

Task 01·02 완료 후 `score_answer_v3` 가 logic-04 의 false positive 를 차단하도록 구성됨. 본 task 는 v2 final 540 trial 을 v3 로 재산정하여:

1. logic-04 외 task 에도 false positive 잠재 여부 확인 (v2/v3 격차 큰 항목 식별)
2. condition × task aggregate 의 v2 vs v3 비교 표 생성
3. 후속 result.md / 노트북 갱신 (Task 06) 의 입력 데이터 산출

### 신규 파일: `experiments/exp10_reproducibility_cost/rescore_v3.py`

구조:

```python
"""Exp10 v2 final 의 540 trial 을 v3 채점으로 재산정.

각 trial dict 에 `accuracy_v2` (원본 보존) + `accuracy_v3` (신규) 두 필드 보유.
출력 JSON 은 입력과 동일 schema + 위 두 필드 추가.
stdout 에 condition × task aggregate 비교 표 출력.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from measure import score_answer_v2, score_answer_v3
from exp10_reproducibility_cost.run import RESULTS_DIR, save_result


DEFAULT_INPUT = RESULTS_DIR / "exp10_v2_final_20260429_033922.json"
TASKSET_PATH = Path(__file__).resolve().parent.parent / "tasks" / "taskset.json"


def _load_task_map() -> dict[str, dict]:
    with open(TASKSET_PATH, encoding="utf-8") as f:
        d = json.load(f)
    return {t["id"]: t for t in d["tasks"]}


def rescore(input_path: Path) -> dict:
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)
    task_map = _load_task_map()

    new_trials = []
    for t in data["trials"]:
        task = task_map.get(t["task_id"])
        if task is None:
            raise RuntimeError(f"unknown task_id: {t['task_id']}")
        final = str(t.get("final_answer") or "")
        v2 = score_answer_v2(final, task)
        v3 = score_answer_v3(final, task)
        new_t = dict(t)
        new_t["accuracy_v2"] = v2
        new_t["accuracy_v3"] = v3
        new_trials.append(new_t)

    out = dict(data)
    out["trials"] = new_trials
    out["_v3_rescore"] = {
        "source": input_path.name,
        "scorer": "score_answer_v3",
        "scorer_changes": "logic-04 negative_patterns added in taskset.json",
    }
    return out


def aggregate_and_print(data: dict) -> None:
    cond_agg = defaultdict(lambda: {"n": 0, "v2": 0.0, "v3": 0.0})
    task_agg = defaultdict(lambda: {"n": 0, "v2": 0.0, "v3": 0.0})
    for t in data["trials"]:
        c = t["condition"]
        tid = t["task_id"]
        cond_agg[c]["n"] += 1
        cond_agg[c]["v2"] += t["accuracy_v2"]
        cond_agg[c]["v3"] += t["accuracy_v3"]
        task_agg[(c, tid)]["n"] += 1
        task_agg[(c, tid)]["v2"] += t["accuracy_v2"]
        task_agg[(c, tid)]["v3"] += t["accuracy_v3"]

    print("=== condition aggregate (v2 vs v3) ===")
    print(f'{"condition":24} {"n":>4} {"v2":>8} {"v3":>8} {"Δ":>8}')
    for c in ("gemma_8loop", "gemma_1loop", "gemini_flash_1call"):
        a = cond_agg[c]
        v2m = a["v2"] / a["n"]
        v3m = a["v3"] / a["n"]
        print(f'{c:24} {a["n"]:>4} {v2m:>8.4f} {v3m:>8.4f} {v3m-v2m:>+8.4f}')

    print()
    print("=== per-task v2 vs v3 (Δ != 0 만 표시) ===")
    print(f'{"condition":24} {"task":13} {"v2":>7} {"v3":>7} {"Δ":>8}')
    for (c, tid), a in sorted(task_agg.items()):
        v2m = a["v2"] / a["n"]
        v3m = a["v3"] / a["n"]
        if abs(v3m - v2m) > 1e-9:
            print(f'{c:24} {tid:13} {v2m:>7.3f} {v3m:>7.3f} {v3m-v2m:>+8.3f}')


def main() -> int:
    parser = argparse.ArgumentParser(description="Exp10 v2 final 의 v3 재산정")
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--out-name", default="exp10_v3_rescored")
    args = parser.parse_args()
    data = rescore(Path(args.input))
    out_path = save_result(args.out_name, data)
    aggregate_and_print(data)
    print(f'\noutput: {out_path}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### 실행 절차

```bash
.venv/bin/python -m experiments.exp10_reproducibility_cost.rescore_v3
```

기대 결과:
- `experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_<TS>.json` 생성
- stdout 에 condition aggregate 표 (gemma_8loop v2 0.820 → v3 0.781 등) + per-task Δ 표 (logic-04 만 변동 예상)

## Dependencies

- Task 01 — `score_answer_v3` 함수 호출
- Task 02 — `taskset.json` 의 logic-04 negative_patterns 가 채워져 있어야 v3 가 의도대로 동작
- 패키지: 표준 `json`, `argparse`, `collections`. 신규 의존성 0.

## Verification

```bash
# 1) 정적 import 통과
.venv/bin/python -m experiments.exp10_reproducibility_cost.rescore_v3 --help

# 2) 실행 + 출력 파일 생성 확인
.venv/bin/python -m experiments.exp10_reproducibility_cost.rescore_v3 2>&1 | tee /tmp/rescore_v3.log

# 3) 출력 JSON schema 검증
.venv/bin/python -c "
import json, glob, os
files = sorted(glob.glob('experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_*.json'))
assert files, 'no v3 rescored output'
latest = files[-1]
d = json.load(open(latest))
assert len(d['trials']) == 540, f'trial count: {len(d[\"trials\"])}'
for t in d['trials']:
    assert 'accuracy_v2' in t and 'accuracy_v3' in t, f'missing v2/v3 keys in {t.get(\"trial\")}'
assert d.get('_v3_rescore'), 'missing _v3_rescore meta'
print('ok:', latest, 'trials=', len(d['trials']))
"

# 4) logic-04 의 v2 vs v3 변동이 기대대로
.venv/bin/python -c "
import json, glob
latest = sorted(glob.glob('experiments/exp10_reproducibility_cost/results/exp10_v3_rescored_*.json'))[-1]
d = json.load(open(latest))
for cond in ('gemma_8loop', 'gemini_flash_1call', 'gemma_1loop'):
    trials = [t for t in d['trials'] if t['condition'] == cond and t['task_id'] == 'logic-04']
    v2 = sum(t['accuracy_v2'] for t in trials) / len(trials)
    v3 = sum(t['accuracy_v3'] for t in trials) / len(trials)
    print(f'{cond}: v2={v2:.3f}  v3={v3:.3f}')
# 기대: gemma_8loop v2 0.400 -> v3 ~0.05, flash v2 0.250 -> v3 0.0
"
```

세 명령 모두 정상 + assertion 통과 + logic-04 의 v3 acc 가 사전 추정값 (gemma_8loop ~0.05, flash 0.0, gemma_1loop 0.0) 에 일치.

## Risks

- **logic-04 외 task 의 v2 → v3 변동**: 본 plan 에서 logic-04 만 negative_patterns 추가했으므로 다른 task 의 v3 == v2 여야 함. 만약 격차 발생하면 score_answer_v3 의 logic 버그 신호 — Task 01 회귀.
- **score_answer_v3 의 fallback 호환**: scoring_keywords 없는 task 는 v1 fallback. 본 v2 final 의 모든 task 에 scoring_keywords 보유 (taskset.json 점검 완료) 이라 영향 없음.
- **trial dict 의 final_answer 누락**: error 또는 null trial 의 final_answer 가 None. `str(None or "")` = `""` 처리로 score_answer_v3 가 0.0 반환 — 정상 처리.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/measure.py` — Task 01 영역.
- `experiments/tasks/taskset.json` — Task 02 영역.
- `experiments/orchestrator.py` — Task 04/05 영역.
- v2 final JSON (`exp10_v2_final_20260429_033922.json`) — read-only.
- `docs/reference/results/exp-10-reproducibility-cost.md`, `researchNotebook*` — Task 06 영역.
