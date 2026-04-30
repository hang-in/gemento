---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: exp06-h4-recheck-expanded-taskset-pre-exp11
parallel_group: C
depends_on: []
---

# Task 03 — assertion turnover + error mode classifier (분석 helper)

## Changed files

- `experiments/exp_h4_recheck/analyze.py` — **신규**. 결정 4 의 (ii) assertion turnover + (iii) error mode classifier
- `docs/reference/h4-metric-definitions.md` — **신규**. 측정 metric 정의 reference

신규 2 파일.

## Change description

### 배경

결정 4 (사용자 — iv 셋 다) 에 따라 분석 metric 3 축:
1. **정확도** — 기존 measure.py:score_answer_v3 (Task 02 에서 호출)
2. **assertion turnover** — Tattoo 의 cycle 별 assertion 변화량 (신규)
3. **error mode** — format_error / wrong_synthesis / evidence_miss / null_answer / connection_error 분류 (신규, Exp09 H9c 패턴)

본 task 는 (ii) + (iii) 의 분석 helper 작성. measure.py 변경 0.

### Step 1 — `experiments/exp_h4_recheck/analyze.py` 신규

```python
"""H4 재검증 분석 — assertion turnover + error mode + 정확도 종합.

Task 04 의 결과 JSON 을 입력으로 받아 condition × task 별 3 축 metric 산출.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


# ============================================================
# (ii) assertion turnover
# ============================================================

def count_assertion_turnover(tattoo_history: list[dict] | None) -> dict:
    """Tattoo history 에서 cycle 별 assertion 추가/수정/삭제 카운트.

    Args:
        tattoo_history: cycle 별 Tattoo dict 의 list. 각 dict 의 'assertions' 필드 비교.

    Returns:
        {added: int, modified: int, deleted: int, total_cycles: int, final_count: int}
    """
    if not tattoo_history or len(tattoo_history) < 2:
        return {"added": 0, "modified": 0, "deleted": 0, "total_cycles": len(tattoo_history or []), "final_count": 0}

    added = 0
    modified = 0
    deleted = 0
    prev_assertions = []
    for cycle_idx, t in enumerate(tattoo_history):
        curr_assertions = t.get("assertions") or []
        if cycle_idx == 0:
            added += len(curr_assertions)
        else:
            prev_ids = {a.get("id") or i: a for i, a in enumerate(prev_assertions)}
            curr_ids = {a.get("id") or i: a for i, a in enumerate(curr_assertions)}
            added += len(set(curr_ids) - set(prev_ids))
            deleted += len(set(prev_ids) - set(curr_ids))
            for k in set(curr_ids) & set(prev_ids):
                if json.dumps(curr_ids[k], sort_keys=True) != json.dumps(prev_ids[k], sort_keys=True):
                    modified += 1
        prev_assertions = curr_assertions

    return {
        "added": added,
        "modified": modified,
        "deleted": deleted,
        "total_cycles": len(tattoo_history),
        "final_count": len(tattoo_history[-1].get("assertions") or []),
    }


# ============================================================
# (iii) error mode classifier
# ============================================================

# Stage 2B (`scorer-failure-label-reference`) 통합:
# `experiments/schema.py:FailureLabel` 이 표준 enum.
# 본 모듈의 ErrorMode 는 그 alias — 두 이름 모두 사용 가능.
from experiments.schema import FailureLabel as ErrorMode


def classify_error_mode(trial: dict, task: dict | None = None) -> ErrorMode:
    """trial 결과 + task 정보로 error mode 분류.

    Args:
        trial: {final_answer, error, accuracy_v3, ...}
        task: 정답 검증용 (optional)

    Returns:
        ErrorMode enum 값
    """
    if trial.get("error"):
        # Stage 2A 의 classify_trial_error 와 동기
        from experiments.run_helpers import classify_trial_error, TrialError
        te = classify_trial_error(trial["error"])
        return {
            TrialError.CONNECTION_ERROR: ErrorMode.CONNECTION_ERROR,
            TrialError.TIMEOUT: ErrorMode.TIMEOUT,
            TrialError.PARSE_ERROR: ErrorMode.PARSE_ERROR,
            TrialError.MODEL_ERROR: ErrorMode.OTHER,
            TrialError.OTHER: ErrorMode.OTHER,
        }.get(te, ErrorMode.OTHER)

    final = trial.get("final_answer")
    if final is None or (isinstance(final, str) and not final.strip()):
        return ErrorMode.NULL_ANSWER

    acc = trial.get("accuracy_v3", 0)
    if acc >= 0.5:
        return ErrorMode.NONE  # 정답 (또는 부분 정답)

    # 형식은 있는데 틀림
    if isinstance(final, str) and len(final) > 10:
        # heuristic — JSON / dict 형태인데 keyword 누락이면 wrong_synthesis
        return ErrorMode.WRONG_SYNTHESIS

    return ErrorMode.FORMAT_ERROR


# ============================================================
# main
# ============================================================

def analyze(result_path: Path, taskset_path: Path | None = None) -> dict:
    with open(result_path, encoding='utf-8') as f:
        d = json.load(f)

    tasks = {}
    if taskset_path:
        with open(taskset_path, encoding='utf-8') as f:
            ts = json.load(f)
        tasks = {t["id"]: t for t in ts["tasks"]}

    # condition × task 별 aggregate
    by_cond_task: dict = defaultdict(lambda: {
        "n": 0,
        "acc_v3_sum": 0.0,
        "turnover_added_sum": 0,
        "turnover_modified_sum": 0,
        "turnover_deleted_sum": 0,
        "turnover_final_count_sum": 0,
        "error_modes": defaultdict(int),
    })

    for trial in d["trials"]:
        key = (trial["condition"], trial["task_id"])
        agg = by_cond_task[key]
        agg["n"] += 1
        agg["acc_v3_sum"] += trial.get("accuracy_v3", 0)
        turn = count_assertion_turnover(trial.get("tattoo_history"))
        agg["turnover_added_sum"] += turn["added"]
        agg["turnover_modified_sum"] += turn["modified"]
        agg["turnover_deleted_sum"] += turn["deleted"]
        agg["turnover_final_count_sum"] += turn["final_count"]
        em = classify_error_mode(trial, tasks.get(trial["task_id"]))
        agg["error_modes"][em.value] += 1

    # 정리
    summary = {}
    for (cond, task_id), agg in by_cond_task.items():
        n = agg["n"]
        summary[(cond, task_id)] = {
            "n": n,
            "acc_v3_mean": agg["acc_v3_sum"] / n if n else 0,
            "turnover": {
                "added_mean": agg["turnover_added_sum"] / n if n else 0,
                "modified_mean": agg["turnover_modified_sum"] / n if n else 0,
                "deleted_mean": agg["turnover_deleted_sum"] / n if n else 0,
                "final_count_mean": agg["turnover_final_count_sum"] / n if n else 0,
            },
            "error_modes": dict(agg["error_modes"]),
        }

    # condition aggregate
    by_cond: dict = defaultdict(lambda: {"n": 0, "acc": 0.0, "turn_added": 0, "turn_modified": 0})
    for (cond, _), s in summary.items():
        by_cond[cond]["n"] += s["n"]
        by_cond[cond]["acc"] += s["acc_v3_mean"] * s["n"]
        by_cond[cond]["turn_added"] += s["turnover"]["added_mean"] * s["n"]
        by_cond[cond]["turn_modified"] += s["turnover"]["modified_mean"] * s["n"]

    return {"by_cond_task": summary, "by_cond": dict(by_cond)}


def main() -> int:
    parser = argparse.ArgumentParser(description="H4 재검증 분석")
    parser.add_argument("--result", required=True, help="exp_h4_recheck_*.json 경로")
    parser.add_argument("--taskset", default="experiments/tasks/taskset.json")
    args = parser.parse_args()

    out = analyze(Path(args.result), Path(args.taskset))

    print("=== condition aggregate ===")
    for cond, stat in out["by_cond"].items():
        n = stat["n"]
        print(f"  {cond:15} n={n:4} acc={stat['acc']/n:.4f} turn_added={stat['turn_added']/n:.2f} turn_modified={stat['turn_modified']/n:.2f}")

    print()
    print("=== ablation ===")
    if "solo_1call" in out["by_cond"] and "solo_budget" in out["by_cond"] and "abc" in out["by_cond"]:
        s1 = out["by_cond"]["solo_1call"]
        sb = out["by_cond"]["solo_budget"]
        ab = out["by_cond"]["abc"]
        s1_acc = s1["acc"] / s1["n"]
        sb_acc = sb["acc"] / sb["n"]
        ab_acc = ab["acc"] / ab["n"]
        print(f"  다단계 효과 (solo_budget − solo_1call) = {sb_acc - s1_acc:+.4f}")
        print(f"  역할 분리 효과 (abc − solo_budget)    = {ab_acc - sb_acc:+.4f}")
        print(f"  합산 효과 (abc − solo_1call)         = {ab_acc - s1_acc:+.4f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### Step 2 — `docs/reference/h4-metric-definitions.md` 신규

```markdown
---
type: reference
status: done
updated_at: 2026-04-30
canonical: true
---

# H4 재검증 — Metric 정의

## 1. 측정 3 축 (사용자 결정 4 — iv 셋 다)

### 1.1 정확도 (existing)

`measure.py:score_answer_v3`. 변경 0.

### 1.2 assertion turnover (신규)

각 trial 의 Tattoo history (cycle 별 assertion list) 에서:
- **added**: 신규 추가된 assertion 수 (cycle N+1 에 있는데 N 에 없음)
- **modified**: 같은 id 인데 내용 바뀐 assertion 수
- **deleted**: cycle N 에 있는데 N+1 에 없음
- **final_count**: 마지막 cycle 의 assertion 수

`experiments/exp_h4_recheck/analyze.py:count_assertion_turnover` 로 산출.

**의미**:
- Solo-1call: 0 (single cycle, 변화 측정 불가)
- Solo-budget: 같은 모델 자기 반복 — turnover 가 적을수록 조기 수렴 (Exp06 의 avg 4.5 loops 패턴)
- ABC: A→B→C 비판 루프 — turnover 가 클수록 역할 분리가 active 하게 다양성 추가

→ ABC 의 turnover_modified 가 Solo-budget 보다 유의미하게 크면, "B 의 비판이 A 의 assertion 을 수정시킨다" 의 직접 증거.

### 1.3 error mode (신규)

| 분류 | 정의 |
|------|------|
| NONE | 정답 (acc_v3 ≥ 0.5) |
| FORMAT_ERROR | JSON parse / schema 위반 |
| WRONG_SYNTHESIS | 형식 OK 인데 내용 틀림 (acc < 0.5, len > 10) |
| EVIDENCE_MISS | evidence_ref 누락 또는 잘못된 출처 (현 heuristic 미구현, 향후 보강) |
| NULL_ANSWER | final_answer 가 None / 빈 문자열 |
| CONNECTION_ERROR | Stage 2A `TrialError.CONNECTION_ERROR` 와 동기 |
| PARSE_ERROR | Stage 2A `TrialError.PARSE_ERROR` |
| TIMEOUT | Stage 2A `TrialError.TIMEOUT` |
| OTHER | 미분류 |

`experiments/exp_h4_recheck/analyze.py:classify_error_mode` 로 산출. Exp09 H9c 와 호환.

## 2. ablation 정의

| 측정 | 의미 |
|------|------|
| solo_budget − solo_1call | 다단계 효과 (H1 재확인) |
| abc − solo_budget | 역할 분리 단독 효과 (H4 본 가설) |
| abc − solo_1call | 합산 효과 |

H4 채택 조건 (Architect 권장):
- abc − solo_budget ≥ +0.05 (정확도)
- 또는 ABC 의 turnover_modified ≥ Solo-budget × 1.5 (질적 차이)
- 통계적 유의성 검정 — Wilcoxon signed-rank (15 task, paired)

## 3. 향후 확장

- evidence_ref 정합성 검사 — Critic Tool 도입 시 보강
- assertion 의 confidence 변화 — Tattoo 의 confidence 필드 활용 (현 미사용)
```

## Dependencies

- 패키지: 표준만 (`json`, `argparse`, `enum`, `collections`)
- Stage 2A 의 `TrialError` import 의존 — Stage 2A task-01 마감 후 본 task 진행 가능
- 다른 subtask: 없음 (parallel_group C, 첫 노드)
- 입력: 없음 (Task 04 결과를 받지만 본 task 는 helper 만)

## Verification

```bash
# 1) syntax + import
.venv/Scripts/python -m py_compile experiments/exp_h4_recheck/analyze.py
echo "verification 1 ok: syntax"

# 2) help
.venv/Scripts/python -m experiments.exp_h4_recheck.analyze --help
# 기대: --result / --taskset

# 3) classify_error_mode 단위 테스트
.venv/Scripts/python -c "
from experiments.exp_h4_recheck.analyze import classify_error_mode, ErrorMode
assert classify_error_mode({'final_answer': 'ok', 'accuracy_v3': 1.0}) == ErrorMode.NONE
assert classify_error_mode({'final_answer': None}) == ErrorMode.NULL_ANSWER
assert classify_error_mode({'final_answer': '', 'accuracy_v3': 0}) == ErrorMode.NULL_ANSWER
assert classify_error_mode({'final_answer': 'wrong long answer here', 'accuracy_v3': 0}) == ErrorMode.WRONG_SYNTHESIS
assert classify_error_mode({'error': '[WinError 10061]'}) == ErrorMode.CONNECTION_ERROR
print('verification 3 ok: error mode classifier')
"

# 4) count_assertion_turnover 단위 테스트
.venv/Scripts/python -c "
from experiments.exp_h4_recheck.analyze import count_assertion_turnover
hist = [
    {'assertions': [{'id': 'a1', 'claim': 'foo'}]},
    {'assertions': [{'id': 'a1', 'claim': 'foo'}, {'id': 'a2', 'claim': 'bar'}]},
    {'assertions': [{'id': 'a1', 'claim': 'foo modified'}, {'id': 'a2', 'claim': 'bar'}]},
]
t = count_assertion_turnover(hist)
assert t['added'] == 2, f'added={t[\"added\"]}'
assert t['modified'] == 1, f'modified={t[\"modified\"]}'
assert t['deleted'] == 0
assert t['final_count'] == 2
print('verification 4 ok: assertion turnover')
"

# 5) reference 문서 존재
.venv/Scripts/python -c "
text = open('docs/reference/h4-metric-definitions.md', encoding='utf-8').read()
assert 'canonical: true' in text
assert 'turnover' in text and 'error mode' in text.lower()
print('verification 5 ok: reference 문서')
"
```

5 명령 모두 정상.

## Risks

- **Risk 1 — Tattoo history 의 assertion id schema 차이**: 기존 ABC chain 이 assertion 에 id 를 일관되게 부여하는지 정찰 필수. 부재 시 list index 사용 (count_assertion_turnover 의 fallback 이미 구현)
- **Risk 2 — Solo-budget 의 Tattoo history**: Solo 가 Tattoo 를 사용하는지 확인. 사용 안 하면 turnover 측정 불가 — Solo 는 turnover=0 으로 default 처리
- **Risk 3 — error mode 의 EVIDENCE_MISS**: 본 task 는 heuristic 미구현. 향후 Critic Tool 도입 시 보강. 본 plan 영역 외
- **Risk 4 — ablation 의 통계적 유의성**: 15 task × 5 trial × 3 condition = 225 trial. condition 별 75 trial — Wilcoxon signed-rank 가능. 단 paired comparison (task 별) 로 n=15. Exp09 H9b 와 같은 검정력 한계 가능 — Task 05 에서 명시
- **Risk 5 — Solo-1call 의 turnover 가 0** — turnover 비교에서 Solo-budget vs ABC 한정 의미. solo_1call 은 정확도 비교에만 사용

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/measure.py` — read-only
- `experiments/orchestrator.py` / `experiments/schema.py` — read-only
- `experiments/run_helpers.py` — Stage 2A 영역 (read-only import)
- 모든 `experiments/exp**/run.py` — Task 02 영역
- `experiments/tasks/*` — Task 01 영역
- 결과 JSON (모두 read-only)
- README / 노트북 — Task 05 영역
- 다른 reference 문서 (`h4-metric-definitions.md` 만 신규)

## 사용자 호출 시점

- Risk 4 (통계적 검정력) 의 결과가 Task 05 에서 미달이면 N 확대 결정 — 사용자 호출
- Risk 1/2 (Tattoo schema 차이) 발견 시
