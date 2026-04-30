---
type: plan-task
status: todo
updated_at: 2026-04-30
parent_plan: stabilization-healthcheck-abort-meta-pre-exp11
parallel_group: A
depends_on: []
---

# Task 01 — `run_helpers.py` 신규 + `run_append_trials.py` 통합

## Changed files

- `experiments/run_helpers.py` — **신규**. 4 함수 + 1 enum
- `experiments/exp09_longctx/run_append_trials.py` — **수정**. trial loop 에 fatal abort + 저장 직전 error 비율 검사

신규 1, 수정 1.

## Change description

### 배경

직전 사고 (Exp09 5-trial, 2026-04-30 분석) 의 root cause 는 `run_append_trials.py` 의 trial loop 가 connection refused 후에도 빈 trial 을 그대로 append 한 점. 본 task 는 helper 모듈 신규 + 해당 도구에 proof-of-concept 적용까지.

### Step 1 — `experiments/run_helpers.py` 신규

다음 코드 그대로 작성:

```python
"""Multi-trial 실행 도구 공통 helper.

healthcheck / abort 정책 + 결과 JSON top-level meta 표준화 (subtask 03 에서 확장).
"""
from __future__ import annotations

from enum import Enum
from typing import Any


class TrialError(Enum):
    """trial error 분류. fatal 여부는 ``is_fatal_error`` 참조."""

    NONE = "none"
    CONNECTION_ERROR = "connection_error"  # WinError 10061, refused, ENOTFOUND, dns
    TIMEOUT = "timeout"                     # ReadTimeout, asyncio.TimeoutError
    PARSE_ERROR = "parse_error"             # JSON parse fail
    MODEL_ERROR = "model_error"             # 모델 응답 자체의 error (4xx, 5xx 본문)
    OTHER = "other"                         # 미분류


# 분류용 substring (소문자 비교, 보수적 시작)
_PATTERN_CONNECTION = (
    "connection refused",
    "winerror 10061",
    "대상 컴퓨터에서 연결을 거부",
    "connection reset",
    "connection aborted",
    "no route to host",
    "name or service not known",
    "name resolution",
    "getaddrinfo failed",
    "[errno 111]",  # linux ECONNREFUSED
)
_PATTERN_TIMEOUT = (
    "readtimeout",
    "timeout",
    "timed out",
)
_PATTERN_PARSE = (
    "json parse",
    "jsondecodeerror",
    "expecting value",
    "expecting property name",
)


def classify_trial_error(error_msg: str | None) -> TrialError:
    """error 문자열을 TrialError 로 분류.

    None 또는 빈 문자열이면 NONE. 패턴 매칭은 소문자 substring (보수적).
    """
    if not error_msg:
        return TrialError.NONE
    s = str(error_msg).lower()
    for pat in _PATTERN_CONNECTION:
        if pat in s:
            return TrialError.CONNECTION_ERROR
    for pat in _PATTERN_TIMEOUT:
        if pat in s:
            return TrialError.TIMEOUT
    for pat in _PATTERN_PARSE:
        if pat in s:
            return TrialError.PARSE_ERROR
    return TrialError.OTHER


def is_fatal_error(err: TrialError) -> bool:
    """fatal = 즉시 abort 가 정합한 error 분류.

    현재 정책: CONNECTION_ERROR 단독 fatal. TIMEOUT/PARSE/MODEL/OTHER 는 non-fatal
    (trial 단위 fail 으로 기록하되 run 전체 중단은 안 함).
    """
    return err == TrialError.CONNECTION_ERROR


def check_error_rate(
    trials: list[dict[str, Any]], threshold: float = 0.30
) -> tuple[bool, float]:
    """저장 직전 trial 별 error 비율 검사.

    Returns:
        (ok, rate). ok=False 면 호출자가 저장 거부 또는 사용자 알림.
        rate = error 가 None 이 아니거나 final_answer 가 None 인 trial 의 비율.
    """
    if not trials:
        return True, 0.0
    bad = sum(
        1
        for t in trials
        if t.get("error") is not None or t.get("final_answer") is None
    )
    rate = bad / len(trials)
    return rate < threshold, rate


def build_result_meta(
    *,
    experiment: str,
    model_name: str,
    model_engine: str,
    model_endpoint: str | None,
    sampling_params: dict[str, Any],
    scorer_version: str,
    taskset_version: str | None = None,
    started_at: str | None = None,
    ended_at: str | None = None,
    schema_version: str = "1.0",
) -> dict[str, Any]:
    """결과 JSON top-level meta 표준 dict 반환 (subtask 03 에서 호출).

    각 도구의 결과 저장 직전에 호출하여 dict 의 top-level 에 unpack 추천.
    """
    meta: dict[str, Any] = {
        "schema_version": schema_version,
        "experiment": experiment,
        "model": {
            "name": model_name,
            "engine": model_engine,
            "endpoint": model_endpoint,
        },
        "sampling_params": dict(sampling_params),
        "scorer_version": scorer_version,
    }
    if taskset_version is not None:
        meta["taskset_version"] = taskset_version
    if started_at is not None:
        meta["started_at"] = started_at
    if ended_at is not None:
        meta["ended_at"] = ended_at
    return meta
```

이 코드를 그대로 작성. **함수 시그니처 / 패턴 / threshold 기본값 변경 금지** (사용자 결정 의존 영역).

### Step 2 — `experiments/exp09_longctx/run_append_trials.py` 통합

#### Step 2a — import 추가

파일 상단의 기존 import 영역에 추가:

```python
from experiments.run_helpers import (
    TrialError,
    classify_trial_error,
    is_fatal_error,
    check_error_rate,
)
```

(기존 import 가 `from experiments.xxx import ...` 패턴이면 그에 맞춤. 패턴 차이 시 `sys.path` 조정 후 직접 import 도 가능 — 같은 파일의 기존 import 패턴 따름)

#### Step 2b — trial loop 보강

`run_append_trials.py` 의 trial loop (각 arm × task × append_trials 의 실행부) 에:

```python
# 기존 패턴 (개념):
result = _run_longctx_trial(arm, task_obj, trial_idx)
task_entry["trials"].append(result)
```

→ 다음으로 변경:

```python
result = _run_longctx_trial(arm, task_obj, trial_idx)
task_entry["trials"].append(result)

# 신규: fatal classify + abort
err_class = classify_trial_error(result.get("error"))
if is_fatal_error(err_class):
    print(
        f"[ABORT] arm={arm} task={task_obj['id']} trial={trial_idx} "
        f"fatal error={err_class.value}: {str(result.get('error'))[:200]}"
    )
    print("[ABORT] 부분 결과는 보존. 저장 직전 error 비율 검사 진행.")
    aborted = True
    break  # 또는 적절한 outer break — 기존 loop 구조에 맞춰 조정
```

여러 중첩 loop (arm × task × trial) 면 fatal 발생 시 가장 바깥 loop 까지 break 가 정합. 기존 구조를 살펴보고 다음 패턴 중 하나 선택:

- 단일 flag (`aborted = True`) + 모든 loop 의 break 조건에 `if aborted: break` 추가
- exception 기반 (`raise _FatalAbort()` + 가장 바깥에서 catch)

**결정**: flag 기반 (exception 은 stack trace 노이즈). flag 변수명 정확히 `aborted` 사용.

#### Step 2c — 저장 직전 error 비율 검사

기존 결과 저장 (`json.dump(...)`) 직전에:

```python
# 모든 arm × task 의 flat trial list 추출 (구조에 맞춰 조정)
all_trials = [
    t
    for arm_data in result_data["results_by_arm"].values()
    for task_entry in arm_data
    for t in task_entry.get("trials", [])
]
ok, rate = check_error_rate(all_trials, threshold=0.30)
if not ok:
    print(f"[REJECT] error 비율 {rate:.1%} ≥ 30%. 저장 거부 + warning")
    print("[REJECT] 부분 결과는 메모리에 유지 — 사용자가 별도 처리 권고")
    raise SystemExit(1)
```

**결정**: 저장 거부 시 `SystemExit(1)`. 부분 결과 별도 파일 (`*_partial.json`) 저장은 **본 task 영역 외** (후속 plan 의 옵션 a/c 와 함께 검토).

기존 trial 추출 구조가 다르면 (`results_by_arm` 이 아닌 다른 키), Step 2c 의 `all_trials` 추출만 그에 맞춰 조정. **Step 2a/2b 변경 없음**.

### Step 3 — 명시적 healthcheck 함수 (선택, 기본 도입 안 함)

옵션 (a) 매 N trial healthcheck 는 **사용자 결정 의존 — 본 plan 의 default 는 도입 안 함**. 사용자가 (a) 도 함께 도입 결정 시 별도 sub-task 추가.

## Dependencies

- 패키지: 기존 표준 라이브러리만 (`enum`, `typing`)
- 다른 subtask: 없음 (parallel_group A, 첫 노드)
- 입력: 없음
- 출력: 본 task 의 helper 가 subtask 02 / 03 의 입력

## Verification

```bash
# 1) helper import + signature 검증
.venv/Scripts/python -c "
from experiments.run_helpers import (
    TrialError, classify_trial_error, is_fatal_error,
    check_error_rate, build_result_meta,
)
assert TrialError.CONNECTION_ERROR.value == 'connection_error'
assert classify_trial_error('[WinError 10061] connection refused') == TrialError.CONNECTION_ERROR
assert classify_trial_error('ReadTimeout 120s') == TrialError.TIMEOUT
assert classify_trial_error('JSONDecodeError') == TrialError.PARSE_ERROR
assert classify_trial_error('') == TrialError.NONE
assert classify_trial_error(None) == TrialError.NONE
assert is_fatal_error(TrialError.CONNECTION_ERROR) is True
assert is_fatal_error(TrialError.TIMEOUT) is False
assert check_error_rate([{'error': None, 'final_answer': 'a'}] * 10) == (True, 0.0)
assert check_error_rate([{'error': 'x', 'final_answer': None}] * 10)[0] is False
print('verification 1 ok: helper signature + 분류 동작')
"

# 2) run_append_trials.py 의 import 가 깨지지 않음
.venv/Scripts/python -c "
import importlib
m = importlib.import_module('experiments.exp09_longctx.run_append_trials')
print('verification 2 ok: import path')
"

# 3) run_append_trials.py 의 syntax 검증
.venv/Scripts/python -m py_compile experiments/exp09_longctx/run_append_trials.py
echo "verification 3 ok: syntax"
```

3 명령 모두 정상.

**dry-run (실제 abort 동작 검증)** 은 subtask 05 에서 진행 — 본 task 는 정적 검증까지.

## Risks

- **Risk 1 — `run_append_trials.py` 의 trial loop 구조가 `(arm × task × trial)` 외 패턴일 가능성**: 파일 정찰 후 break 위치 결정. 다중 중첩이면 flag 기반 이중 break 필요.
- **Risk 2 — `results_by_arm` 키 이름 차이**: 실제 dict 키가 다르면 (`arms` / `results` / `runs` 등) Step 2c 의 추출만 조정. helper 시그니처 무관.
- **Risk 3 — 패턴 매칭의 false positive**: 한국어 windows error 메시지 "대상 컴퓨터에서 연결을 거부" 등은 포함했으나 다른 OS / locale 의 connection refused 표현 누락 가능. 첫 도입은 보수적 시작 + 후속 plan 에서 패턴 보강.
- **Risk 4 — flag-based break 의 outer loop 도달 비용**: 기존 inner trial loop 가 generator 기반이면 flag 가 효력 없음. 그 경우 exception 기반으로 fallback.

각 Risk 가 발생하면 **Developer 는 임의 우회 금지** — Architect 호출 후 Step 보강. 단순 패턴 추가 (Risk 3) 는 Developer 가 직접 패턴 1~2개 추가하는 정도까지 허용.

## Scope boundary

본 task 에서 **수정 금지** 파일:
- `experiments/orchestrator.py` — try/except swallow 자체는 본 plan 영역 외
- `experiments/measure.py` / `score_answer_v0/v2/v3` — Stage 2B 영역
- `experiments/schema.py` — 신규 meta type 은 subtask 03 영역
- `experiments/exp09_longctx/run.py` — 본 task 는 `run_append_trials.py` 만. `run.py` 는 subtask 02
- 다른 모든 `experiments/exp**/run.py` — subtask 02 영역
- `experiments/exp09_longctx/analyze_stats.py` — subtask 04 영역
- `experiments/tasks/*.json` — Phase 1 후속에서 정정 완료
- 결과 JSON (모두 read-only)
- `docs/reference/*` / `docs/plans/*` (본 task 의 plan 파일 외)
- README / researchNotebook
