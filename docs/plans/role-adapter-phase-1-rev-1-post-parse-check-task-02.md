---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: role-adapter-phase-1-rev-1-post-parse-check
parallel_group: B
depends_on: [01]
---

# Task 02 — 회귀 게이트 — math-04 격리 스크립트 + 다단 워크플로

## Changed files

- `experiments/run_regression_gate.py` — **신규**. math-04 격리 회귀 실행 스크립트.
- `experiments/results/role_adapter_regression_post.json` — **신규** (사용자 offline 실행 후 생성).
- `docs/plans/role-adapter-phase-1-rev-1-post-parse-check-result.md`(또는 자동 생성 result 파일) — 사용자 offline 실행 절차 명시.

신규 외 다른 파일 수정 금지. 특히 `experiments/run_experiment.py`·`experiments/regression_check.py`·`experiments/results/role_adapter_regression_pre.json` 수정 금지.

## Change description

### Step 0 — 사전 조건 확인

- Task 01 완료(`_post_parse_check` 두 메소드가 `return None`만 수행)되어 있어야 함. 미완 상태에서 회귀 게이트를 돌리면 추가 LLM 재시도로 인한 편차로 회귀 PASS 가능성이 낮아진다.
- `experiments/results/role_adapter_regression_pre.json`이 commit `2d42ce4` 시점 Exp08b 결과에서 추출된 상태로 존재해야 함 (이미 존재 — 본 task에서 수정 금지).
- llama.cpp 서버가 사용자 환경에서 실행 가능해야 함 (offline 실행 단계).

### Step 1 — `experiments/run_regression_gate.py` 신규 작성

목적: math-04 한 task만 baseline_refined / tooluse_refined 5 trials = 10 runs 실행하고 결과를 `role_adapter_regression_post.json` 형식으로 저장. `run_experiment.py:run_tool_use_refined`(line 1126-1238) 의 trial 루프와 결과 dict 형식을 *간소화하여* 직접 흉내낸다.

`run_experiment.py`는 수정하지 않는다. 본 스크립트는 `run_abc_chain`을 직접 호출한다.

#### 스크립트 골격

```python
"""math-04 격리 회귀 실행 — Role Adapter 리팩토링 동치 검증용.

`run_experiment.py:run_tool_use_refined`의 trial 루프를 math-04 한 task만 실행하도록
간소화한 entry point. 출력은 `regression_check.py:compare()`가 직접 읽을 수 있는
형식이며 `experiments/results/role_adapter_regression_pre.json` 과 동일 구조이다.

usage:
    python run_regression_gate.py [--trials N] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from orchestrator import run_abc_chain
from run_experiment import (
    TOOL_USE_REFINED_REPEAT,
    TOOL_USE_REFINED_MAX_CYCLES,
    TOOL_USE_REFINED_PHASE_PROMPT,
    TOOL_USE_REFINED_CONDITIONS,
    load_tasks,
)


TARGET_TASK_ID = "math-04"
DEFAULT_OUT = Path(__file__).parent / "results" / "role_adapter_regression_post.json"


def run_one_trial(task: dict, label: str, use_tools: bool, trial_idx: int) -> dict:
    """run_tool_use_refined 의 1 trial 실행 로직을 그대로 호출."""
    tattoo, abc_logs, final_answer = run_abc_chain(
        task_id=f"{task['id']}_{label}_t{trial_idx}",
        objective=task["objective"],
        prompt=task["prompt"],
        constraints=task.get("constraints"),
        termination="모든 비판이 수렴하고 최종 답변이 확정되면 종료",
        max_cycles=TOOL_USE_REFINED_MAX_CYCLES,
        use_phase_prompt=TOOL_USE_REFINED_PHASE_PROMPT,
        use_tools=use_tools,
    )
    total_tool_calls = 0
    tool_errors = 0
    for cl in abc_logs:
        tc_list = getattr(cl, "tool_calls", []) or []
        total_tool_calls += len(tc_list)
        tool_errors += sum(1 for tc in tc_list if tc.get("error"))
    return {
        "trial": trial_idx + 1,
        "final_answer": final_answer,
        "actual_cycles": len(abc_logs),
        "num_assertions": len(tattoo.assertions),
        "total_tool_calls": total_tool_calls,
        "tool_errors": tool_errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Role Adapter 회귀 게이트 — math-04 격리 실행")
    parser.add_argument("--trials", type=int, default=TOOL_USE_REFINED_REPEAT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    all_tasks = load_tasks()
    task = next((t for t in all_tasks if t["id"] == TARGET_TASK_ID), None)
    if task is None:
        print(f"task {TARGET_TASK_ID} not found in taskset")
        return 2

    output: dict[str, dict] = {}
    for cond in TOOL_USE_REFINED_CONDITIONS:
        label = cond["label"]
        use_tools = cond["use_tools"]
        print(f"\n[regression-gate] arm={label} | task={TARGET_TASK_ID}")
        trials: list[dict] = []
        for i in range(args.trials):
            print(f"  Trial {i + 1}/{args.trials}...")
            trials.append(run_one_trial(task, label, use_tools, i))
        output[label] = {
            "task_id": TARGET_TASK_ID,
            "expected_answer": task.get("expected_answer"),
            "trials": trials,
        }
        # incremental save — 중간에 끊겨도 부분 결과 보존
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"  saved partial -> {args.out}")

    print(f"\nDone. wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

#### 핵심 설계 포인트

- **재사용 원칙** — `run_experiment.py`의 상수(`TOOL_USE_REFINED_REPEAT`, `TOOL_USE_REFINED_MAX_CYCLES`, `TOOL_USE_REFINED_PHASE_PROMPT`, `TOOL_USE_REFINED_CONDITIONS`)와 `load_tasks` 함수를 import만 한다. `run_experiment.py` 본문은 수정 금지.
- **출력 형식 호환** — `regression_check.py:compare()`가 `pre[arm]["trials"][trial]`에서 읽는 키들(`trial`, `final_answer`, `num_assertions`, `total_tool_calls`)을 정확히 동일 이름으로 출력. `accuracy_by_arm`은 `final_answer`만 본다.
- **incremental save** — 매 arm 완료 시 partial 저장. 사용자가 중간에 Ctrl+C 해도 일부 데이터 보존.
- **smoke 모드** — `--trials 1`로 빠른 sanity check 가능 (2 runs ≈ 10~30분).
- **본격 게이트** — `--trials 5` (기본값)로 10 runs ≈ 50~120분.
- **`load_tasks` 재사용** — `experiments/run_experiment.py`의 `load_tasks` 함수가 taskset 로드 진입점. 본 스크립트도 같은 진입점 사용해 task 정의 일관성 보장.

### Step 2 — 사용자 offline 실행 절차 (result 문서에 명시)

**다단 워크플로**:

```
[Agent turn N]
  - Task 01 완료 (critic.py / judge.py 수정)
  - Task 02 Step 1 완료 (run_regression_gate.py 작성)
  - Verification 1~3 (smoke import / regression_check import 등) 실행
  → 사용자에게 offline 실행 안내 보고

[사용자 offline 실행]
  cd experiments
  ../.venv/bin/python run_regression_gate.py --trials 5
  # 예상 소요시간: 50~120분 (Gemma 4 E4B Q8_0 + llama.cpp 기준)
  # 진행 상황은 stdout 으로 trial 단위로 출력됨
  # 결과: experiments/results/role_adapter_regression_post.json

[Agent turn N+1 — 사용자가 실행 완료 보고 후]
  - Verification 4 (post.json 존재) 실행
  - Verification 5 (regression_check.py 비교) 실행 → exit 0 기대
  - 단위 테스트 19개 회귀 확인
  → impl-complete 마커
```

result 문서(또는 plan별 자동 생성 result.md)에 위 절차 + 예상 소요시간 + 실패 시 fallback(예: `--trials 2` smoke로 축소 후 재시도)을 명시한다.

### Step 3 — Verification 명령 분리 — agent turn 내 vs offline 후

본 task의 Verification 명령은 두 그룹으로 분리된다:

- **Group A (agent turn 내, 즉시 실행 가능)** — 1, 2, 3, 7, 8.
- **Group B (사용자 offline 실행 후, 후속 turn에서 실행)** — 4, 5, 6.

agent turn 내에서는 Group A만 실행하고 보고. Group B는 사용자 offline 실행 완료 후 별도 turn에서 실행하고 보고.

## Dependencies

- **Task 01 완료** — `_post_parse_check` 두 메소드가 None 반환 상태여야 회귀 게이트 통과 가능성이 높다.
- 외부 의존성: `experiments/run_experiment.py`의 상수·`load_tasks`·`run_abc_chain` (수정 금지, import만).
- 외부 의존성 (offline 실행 시): llama.cpp 서버 가동.
- 외부 패키지 추가 없음.

## Verification

### Group A — agent turn 내 즉시 실행

```bash
# 1. 스크립트 파일 존재
test -f /Users/d9ng/privateProject/gemento/experiments/run_regression_gate.py && echo "script: OK"

# 2. 스크립트 import smoke — 실제 실행 없이 import만 성공하는지
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import run_regression_gate
assert callable(run_regression_gate.run_one_trial)
assert callable(run_regression_gate.main)
assert run_regression_gate.TARGET_TASK_ID == 'math-04'
print('OK script imports')
"

# 3. CLI --help 동작
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python run_regression_gate.py --help 2>&1 | grep -q "trials" && echo "OK help"

# 7. 다른 파일이 수정되지 않았는지 (Task 02 범위 검증)
cd /Users/d9ng/privateProject/gemento && git diff --name-only experiments/ | grep -vE '^experiments/(run_regression_gate\.py|results/role_adapter_regression_post\.json)$' | grep -v '^$' || echo "OK no extra modifications"
# 기대: "OK no extra modifications" — agents/critic.py, agents/judge.py 는 Task 01 영역이라 별도

# 8. regression_check.py 가 본 스크립트의 출력 구조를 받아들이는지 — pre.json 기준 dry-run
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from regression_check import compare, load_json
pre = load_json('results/role_adapter_regression_pre.json')
# pre 와 동일 구조를 post로 입력 → 자기자신 비교는 violations 0 이어야 함
ok, viol = compare(pre, pre)
assert ok, f'self-compare failed: {viol}'
print('OK regression_check.compare accepts the format')
"
```

### Group B — 사용자 offline 실행 후 후속 agent turn에서 실행

```bash
# 4. post.json 생성됨 (사용자 offline 실행 완료 후)
test -f /Users/d9ng/privateProject/gemento/experiments/results/role_adapter_regression_post.json && echo "post: OK"

# 5. post.json 형식 확인 — pre.json과 동일 키 구조
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import json
with open('results/role_adapter_regression_post.json') as f:
    post = json.load(f)
for arm in ('baseline_refined', 'tooluse_refined'):
    assert arm in post, f'missing arm: {arm}'
    assert 'trials' in post[arm]
    for t in post[arm]['trials']:
        for k in ('trial','final_answer','actual_cycles','num_assertions','total_tool_calls'):
            assert k in t, f'missing key {k} in {arm} trial'
print('OK post.json structure')
"

# 6. 회귀 비교 PASS — 본 plan 의 핵심 게이트
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python regression_check.py \
    results/role_adapter_regression_pre.json \
    results/role_adapter_regression_post.json
# 기대 exit code: 0
# 기대 stdout: "PASS role-adapter regression gate"

# (Task 01 회귀 재확인 — 게이트 실행 직후 단위 테스트 회귀 없는지)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest agents.test_role_agents 2>&1 | tail -3
# 기대: "OK" 19 tests
```

## Risks

- **회귀 게이트 FAIL 가능성**: 4개 기준(`final_answer` 일치, `num_assertions` ±1, `accuracy` 일치, `tool_calls` ±2) 중 하나라도 위반하면 FAIL. LLM 비결정성·서버 재시작·n_ctx 차이 등이 원인일 수 있음. 첫 의심: Task 01의 `_post_parse_check` 수정이 정확히 적용됐는지 (Verification 1 재확인). 둘째 의심: pre.json이 commit `2d42ce4` 시점에서 추출됐는지 (이미 그렇게 생성된 상태).
- **사용자 offline 실행 시간**: 5 trials × 2 arms = 10 runs. baseline math-04는 도구 미사용으로 max_cycles(15)까지 가는 경우 많음 → trial당 ~15-25분. tooluse는 7 cycles 수준 → trial당 ~5-10분. 합계 ~50~120분. 첫 시도 시 `--trials 2`로 smoke (4 runs, ~30분) 권장.
- **incremental save로 인한 partial post.json**: 사용자가 중간에 Ctrl+C 하면 partial 데이터만 저장됨. Verification 5(구조 검사)가 missing arm 감지 → 사용자가 재실행하면 됨 (스크립트는 재시작 시 처음부터 다시 — checkpoint resume은 본 task 범위 밖).
- **`run_experiment.py`의 상수 변경 시 영향**: `TOOL_USE_REFINED_*` 상수가 다른 plan에서 변경되면 본 스크립트도 영향. 그러나 본 plan 내 Constraints에서 `run_experiment.py` 수정 금지이므로 안전.
- **`run_abc_chain` 시그니처 변경 위험**: 본 스크립트가 직접 호출. rev.0 Task 02에서 시그니처 보존(verified) → 변경 위험 없음.
- **다단 워크플로 책임 분리**: agent는 스크립트 작성·smoke 검증까지. 사용자가 offline 실행. 후속 turn에서 agent가 비교 검증. 사용자가 실행 보고 없이 turn 진행 시 Verification 4가 fail로 잡아냄.
- **`load_tasks` 부재 가능성**: `run_experiment.py`에서 `load_tasks`를 import한다 — 함수가 존재해야 import 성공. 작업 시작 전 `grep -n '^def load_tasks' experiments/run_experiment.py` 로 존재 확인. 미존재 시 `experiments/tasks/taskset.json` 직접 로드로 대체 (이 경우 task 구조도 직접 파싱 — JSON 형식 확인 필요).

## Scope boundary

**Task 02에서 절대 수정 금지**:

- `experiments/run_experiment.py` — 본문·상수 모두. 상수와 `load_tasks`는 import만.
- `experiments/regression_check.py` — 비교 기준·extract 로직 모두 그대로.
- `experiments/results/role_adapter_regression_pre.json` — 기준선.
- `experiments/orchestrator.py` — `run_abc_chain` 등 모두 import만.
- `experiments/agents/` — Task 01 영역 (단 Task 01 완료 후이므로 critic.py / judge.py 는 Task 01의 결과물 그대로).
- `experiments/system_prompt.py`, `experiments/schema.py`, `experiments/measure.py`.
- `experiments/tools/`, `experiments/tasks/`.
- 기존 `experiments/results/exp*.json` 결과 파일.

**허용 범위**:

- `experiments/run_regression_gate.py` 신규 작성.
- `experiments/results/role_adapter_regression_post.json` 신규 (사용자 offline 실행 결과물).
- `docs/plans/role-adapter-phase-1-rev-1-post-parse-check-result.md` (자동 생성 result 문서가 있으면 그쪽에 절차 기록 — 신규 작성 가능).
