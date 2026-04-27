---
type: plan-task
status: todo
updated_at: 2026-04-27
parent_plan: exp10-gemma-8loop-a-b-c-raw-response-debug-logging
parallel_group: A
depends_on: []
---

# Task 01 — trial_gemma_8loop debug logging 추가

## Changed files

- `experiments/exp10_reproducibility_cost/run.py` — **수정**. `trial_gemma_8loop()` 함수 (line 65-98) 에 `_debug.abc_logs` 추가 + helper 함수 2개 (`_truncate_raw`, `_serialize_abc_logs`) 모듈 상단 영역에 신규.

신규 파일 0. 다른 파일 수정 0.

## Change description

### 배경

현재 `trial_gemma_8loop()` 의 result dict (line 86-98) 는 `accuracy`, `final_answer`, `actual_cycles`, `duration_ms` 등만 포함. `abc_logs: list[ABCCycleLog]` 는 `actual_cycles = len(abc_logs)` 로 길이만 추출 후 폐기.

`ABCCycleLog` (`experiments/orchestrator.py:454-468`) 는 다음 필드를 이미 capture:

```python
@dataclass
class ABCCycleLog:
    cycle: int
    phase: str
    a_log: LoopLog          # LoopLog.raw_response 가 A 의 raw
    b_judgments: dict | None
    b_raw: str              # B 의 raw
    b_duration_ms: int
    b_error: str | None
    c_decision: dict | None
    c_raw: str              # C 의 raw
    c_duration_ms: int
    c_error: str | None
    phase_transition: str | None
    tool_calls: list[dict]
```

본 task 는 이 정보를 추출 + truncate 한 dict 로 변환하여 result dict 의 `_debug.abc_logs` 로 저장.

### Step 1 — Helper 함수 2개 추가 (모듈 상단)

`experiments/exp10_reproducibility_cost/run.py` 의 import 영역 다음, 상수 영역 (`GEMINI_CALL_SLEEP_SEC = 1.0` 근처) 에 추가:

```python
# Debug logging — gemma_8loop A/B/C raw response 4KB truncate 정책
DEBUG_RAW_TRUNCATE_LIMIT = 4096


def _truncate_raw(text: str | None, limit: int = DEBUG_RAW_TRUNCATE_LIMIT) -> str:
    """Raw response 를 limit char 까지 truncate. 끝에 메타 정보 표시."""
    if not text:
        return ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"... (truncated, original_len={len(text)})"


def _serialize_abc_logs(logs) -> list[dict]:
    """list[ABCCycleLog] → list[dict] (raw 필드 truncate 적용)."""
    serialized = []
    for log in logs:
        serialized.append({
            "cycle": log.cycle,
            "phase": log.phase,
            "a_raw": _truncate_raw(log.a_log.raw_response if log.a_log else ""),
            "a_error": log.a_log.error if log.a_log else None,
            "b_raw": _truncate_raw(log.b_raw),
            "b_error": log.b_error,
            "c_raw": _truncate_raw(log.c_raw),
            "c_error": log.c_error,
            "phase_transition": log.phase_transition,
        })
    return serialized
```

### Step 2 — `trial_gemma_8loop()` 의 return dict 변경

기존 (line 86-98):

```python
return {
    "trial": trial_idx + 1,
    "condition": "gemma_8loop",
    "task_id": task["id"],
    "final_answer": str(final_answer) if final_answer else None,
    "accuracy": accuracy,
    "actual_cycles": actual_cycles,
    "duration_ms": duration_ms,
    "input_tokens": 0,
    "output_tokens": 0,
    "cost_usd": 0.0,
    "error": error,
}
```

→ 마지막 필드 다음에 `_debug` 추가:

```python
return {
    "trial": trial_idx + 1,
    "condition": "gemma_8loop",
    "task_id": task["id"],
    "final_answer": str(final_answer) if final_answer else None,
    "accuracy": accuracy,
    "actual_cycles": actual_cycles,
    "duration_ms": duration_ms,
    "input_tokens": 0,
    "output_tokens": 0,
    "cost_usd": 0.0,
    "error": error,
    "_debug": {
        "abc_logs": _serialize_abc_logs(abc_logs) if "abc_logs" in dir() and abc_logs else [],
    },
}
```

주의: `try/except` 안에서 `abc_logs` 가 정의되지 않을 수 있음 (Exception 시). 안전 처리:

```python
# try 블록 안에서 abc_logs 가 정의되었는지 명시적으로 확인
debug_abc_logs = []
try:
    if abc_logs:                  # try 블록에서 성공 시
        debug_abc_logs = _serialize_abc_logs(abc_logs)
except NameError:
    pass

return {
    ...
    "_debug": {"abc_logs": debug_abc_logs},
}
```

또는 `abc_logs = []` 초기화를 try 블록 위에:

```python
abc_logs = []  # 초기화 — except 발생 시 빈 list
try:
    tattoo, abc_logs, final_answer = run_abc_chain(...)
    actual_cycles = len(abc_logs)
    error = None
except Exception as e:
    ...
```

권고: **초기화 방식** — 더 명확. exception 발생 시 빈 list, 성공 시 abc_logs 가 정상 채워짐.

### Step 3 — `_serialize_abc_logs` 의 tool_calls 처리 결정

`ABCCycleLog.tool_calls` (list[dict]) 도 직렬화 후보. 단 본 plan 의 truncate 정책은 raw 만. tool_calls 는 작아 truncate 불필요. 본 task 는 단순화 위해 tool_calls 미포함 — 향후 별도 plan 으로 추가 가능.

만약 tool_calls 가 필요하면 `_serialize_abc_logs` 의 dict 에 `"tool_calls": log.tool_calls or []` 추가.

본 task 권고: **tool_calls 미포함** — minimal first iteration.

### Step 4 — analyze.py 호환 확인

`experiments/exp10_reproducibility_cost/analyze.py` 가 `_debug` 필드를 무시하는지 확인 (단순 read-only 검증, 본 task 에서 변경 X). `aggregate()` 함수가 trial dict 의 특정 키만 참조 (`accuracy`, `input_tokens`, `output_tokens`, `cost_usds`, `duration_mss`, `error`) — `_debug` 미참조면 OK. Verification 단계에서 dummy 결과 JSON 으로 확인.

## Dependencies

- 없음. 본 task 는 plan 의 foundation.
- 외부 패키지: 없음 (stdlib `dataclasses`, `pathlib`, `time` 만 사용 — 기존 import).

## Verification

```bash
# 1. import smoke
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.run import trial_gemma_8loop, _truncate_raw, _serialize_abc_logs
assert callable(trial_gemma_8loop)
assert callable(_truncate_raw)
assert callable(_serialize_abc_logs)
print('OK helpers + trial_gemma_8loop importable')
"

# 2. _truncate_raw 동작 — 단순 케이스
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.run import _truncate_raw, DEBUG_RAW_TRUNCATE_LIMIT
assert _truncate_raw('') == ''
assert _truncate_raw(None) == ''
assert _truncate_raw('short') == 'short'
long_text = 'A' * 5000
result = _truncate_raw(long_text)
assert result.startswith('A' * DEBUG_RAW_TRUNCATE_LIMIT)
assert 'truncated' in result
assert 'original_len=5000' in result
assert _truncate_raw('exactly') == 'exactly'  # under limit
print('OK _truncate_raw edge cases')
"

# 3. _serialize_abc_logs 동작 — dummy ABCCycleLog
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.run import _serialize_abc_logs
from orchestrator import ABCCycleLog, LoopLog

dummy_a_log = LoopLog(loop_index=1, tattoo_in={}, raw_response='A' * 100, parsed_response={'foo': 'bar'}, tattoo_out={}, duration_ms=500, error=None)
dummy_log = ABCCycleLog(
    cycle=1, phase='DECOMPOSE',
    a_log=dummy_a_log,
    b_judgments={'verdict': 'APPROVE'}, b_raw='B' * 100, b_duration_ms=300, b_error=None,
    c_decision={'next_phase': 'INVESTIGATE'}, c_raw='C' * 100, c_duration_ms=200, c_error=None,
    phase_transition='DECOMPOSE→INVESTIGATE',
)
result = _serialize_abc_logs([dummy_log])
assert len(result) == 1
assert result[0]['cycle'] == 1
assert result[0]['phase'] == 'DECOMPOSE'
assert result[0]['a_raw'] == 'A' * 100
assert result[0]['b_raw'] == 'B' * 100
assert result[0]['c_raw'] == 'C' * 100
assert result[0]['phase_transition'] == 'DECOMPOSE→INVESTIGATE'
assert result[0]['a_error'] is None
print('OK _serialize_abc_logs single log')
"

# 4. 빈 list 처리
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.run import _serialize_abc_logs
assert _serialize_abc_logs([]) == []
print('OK empty list')
"

# 5. trial_gemma_8loop result schema — _debug 필드 존재 + abc_logs key 보유
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from exp10_reproducibility_cost.run import trial_gemma_8loop
import inspect
src = inspect.getsource(trial_gemma_8loop)
assert '_debug' in src, 'trial_gemma_8loop must include _debug field'
assert 'abc_logs' in src, 'trial_gemma_8loop must include abc_logs key'
print('OK _debug.abc_logs in trial_gemma_8loop')
"

# 6. analyze.py 호환 — _debug 필드 무시
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import json
import tempfile
from pathlib import Path
from exp10_reproducibility_cost.analyze import build_report

dummy = {
    'experiment': 'reproducibility_cost',
    'model': 'gemma4-e4b',
    'trials_per_condition': 1,
    'conditions': ['gemma_8loop'],
    'task_ids': ['math-01'],
    'trials': [
        {'condition': 'gemma_8loop', 'task_id': 'math-01', 'trial': 1, 'accuracy': 1.0, 'input_tokens': 0, 'output_tokens': 0, 'cost_usd': 0.0, 'duration_ms': 1000, 'error': None, 'final_answer': 'x', '_debug': {'abc_logs': [{'cycle': 1, 'phase': 'DECOMPOSE', 'a_raw': 'A', 'a_error': None, 'b_raw': 'B', 'b_error': None, 'c_raw': 'C', 'c_error': None, 'phase_transition': None}]}},
    ],
}
with tempfile.NamedTemporaryFile(suffix='.json', mode='w', delete=False) as f:
    json.dump(dummy, f)
    p = Path(f.name)
report = build_report(p)
assert '# Exp10 Report' in report
print('OK analyze.py handles _debug field gracefully')
p.unlink()
"

# 7. 다른 파일 변경 없음
cd /Users/d9ng/privateProject/gemento && git diff HEAD --name-only experiments/ docs/ | grep -vE "^experiments/exp10_reproducibility_cost/run\.py$" | grep -v "^$" || echo "OK no extra changes"
```

## Risks

- **`abc_logs` NameError**: try 블록 안에서 정의되므로 except 발생 시 NameError 위험. **초기화 방식** (try 위에서 `abc_logs = []`) 권고로 안전 확보.
- **JSON 직렬화 — nested dict**: `LoopLog.parsed_response`, `tattoo_in/out` 이 dict 라 직렬화 가능. 단 본 task 는 raw 만 추출 — nested 미사용.
- **truncate 4KB 의 정보 손실**: 어떤 raw response 가 4KB 초과면 끝부분 손실. 분석 시 `original_len` 메타로 인지 가능. 향후 8KB / 16KB 로 늘리는 plan 가능 — 본 plan 범위 밖.
- **결과 JSON 크기 +17 MB**: gemma_8loop 180 trial × 평균 ~96 KB / trial. git push 가능하나 매우 크면 LFS 검토. 단 17 MB 는 일반 git 한계 (100 MB) 의 17% — 안전.
- **`tool_calls` 미포함**: 본 task 는 minimal first iteration. tool_calls 분석이 필요하면 별도 plan.
- **analyze.py 의 `_debug` 키 처리**: `aggregate()` 가 `_debug` 미참조면 OK. Verification 6 가 강제 — fail 시 analyze.py 도 정정 task 추가.

## Scope boundary

**Task 01 에서 절대 수정 금지**:

- `experiments/orchestrator.py` — `LoopLog`, `ABCCycleLog`, `run_abc_chain()` 등 raw capture 영역. 이미 정상.
- `experiments/exp10_reproducibility_cost/run.py` 의 `trial_gemma_1loop()`, `trial_gemini_flash()` 등 다른 trial 함수.
- `experiments/exp10_reproducibility_cost/analyze.py`, `tasks.py`, `INDEX.md`.
- `experiments/_external/` 의 모든 파일.
- `experiments/tests/test_static.py` — task-02 영역.
- 다른 expXX/ 디렉토리.
- `docs/plans/` 의 다른 plan 문서.

**허용 범위**:

- `experiments/exp10_reproducibility_cost/run.py` 상단에 helper 함수 2개 + 상수 1개 (~25 줄) 추가.
- 같은 파일의 `trial_gemma_8loop()` 함수 (line 65-98) 의 try/except 초기화 + return dict 영역 수정 (~5 줄 추가, 1 줄 정정).
