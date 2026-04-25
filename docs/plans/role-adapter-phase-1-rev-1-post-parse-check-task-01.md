---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: role-adapter-phase-1-rev-1-post-parse-check
parallel_group: A
depends_on: []
---

# Task 01 — `_post_parse_check` 동작 동치 복원

## Changed files

- `experiments/agents/critic.py:39-42` — `CriticAgent._post_parse_check` 본문 교체.
- `experiments/agents/judge.py:48-51` — `JudgeAgent._post_parse_check` 본문 교체.

신규 파일 없음. 두 파일 외 다른 파일 수정 금지.

## Change description

### 배경 — 현재 구현이 명세와 어긋나는 부분

**`experiments/agents/critic.py:39-42` 현재 구현**:

```python
def _post_parse_check(self, parsed: dict[str, Any]) -> str | None:
    if "judgments" not in parsed:
        return "missing judgments"
    return None
```

**`experiments/agents/judge.py:48-51` 현재 구현**:

```python
def _post_parse_check(self, parsed: dict[str, Any]) -> str | None:
    if "converged" not in parsed:
        return "missing converged"
    return None
```

rev.0 task-01 명세는 Phase 1 동작 동치 보장을 위해:

- `CriticAgent._post_parse_check`: *"단 Phase 1 동작 동치 보장을 위해 이 체크는 일단 None 반환 (기존 동작 유지)"*
- `JudgeAgent._post_parse_check`: 명세에 정의 없음 → base 클래스(`agents/base.py:31-32`)의 `return None`이 기준.

`base.py:62-66`의 retry 루프는 `_post_parse_check`가 None일 때만 break한다. 따라서 현재 구현은 B 응답에 `judgments`가 없거나 C 응답에 `converged`가 없을 때 1회 추가 LLM 호출(retry)을 발동시켜 원본 인라인 코드(`run_abc_chain`의 기존 B/C 블록 — 인라인은 `parsed`만 truthy면 break)와 동작이 다르다.

### Step 1 — `experiments/agents/critic.py:39-42` 수정

기존 4줄을 다음 3줄로 교체:

```python
    def _post_parse_check(self, parsed: dict[str, Any]) -> str | None:
        # Phase 1: semantic checks belong to the caller (run_abc_chain) — base behavior preserved.
        return None
```

`from typing import Any` import는 그대로 유지(다른 곳에서 사용되거나 추후 확장 시 필요할 수 있으므로 이 task에서는 손대지 않는다).

### Step 2 — `experiments/agents/judge.py:48-51` 수정

기존 4줄을 다음 3줄로 교체:

```python
    def _post_parse_check(self, parsed: dict[str, Any]) -> str | None:
        # Phase 1: semantic checks belong to the caller (run_abc_chain) — base behavior preserved.
        return None
```

`from typing import Any` import는 그대로 유지.

### Step 3 — 영향 분석 (코드 수정은 아니지만 검증 시 확인)

- `run_abc_chain`(`experiments/orchestrator.py:574`)은 `if b_parsed and "judgments" in b_parsed`로 caller 측에서 이미 `judgments` 누락을 처리한다 → 어댑터 측 추가 retry는 불필요.
- `run_abc_chain`(`experiments/orchestrator.py:625`)은 `if c_parsed:` truthy 체크 후 `c_parsed.get("converged", False)`로 caller 측에서 이미 `converged` 누락을 처리한다 → 어댑터 측 추가 retry는 불필요.
- `run_abc_chunked`(`experiments/orchestrator.py:884-916`)도 동일 패턴 — caller가 `judgments`/`converged` 키 존재를 직접 확인.

따라서 `_post_parse_check`를 None으로 되돌려도 caller의 처리 로직은 변하지 않고, 단지 LLM 호출 횟수(retry)만 원본 인라인과 동치로 복원된다.

### Step 4 — 단위 테스트 영향 확인

`experiments/agents/test_role_agents.py`의 19개 케이스 중 `_post_parse_check`의 에러 반환에 의존하는 케이스가 있는지 확인:

- `TestCriticAgent.test_normal_call_returns_parsed`: `'{"judgments": []}'` mocking → `judgments` 키 존재 → 현재도 None 반환 → 영향 없음.
- `TestCriticAgent.test_retry_on_parse_fail_then_success`: 첫 응답이 invalid JSON → parse 실패로 retry → `_post_parse_check` 진입 안 함 → 영향 없음.
- `TestJudgeAgent.test_normal_call`: `'{"converged": true, ...}'` mocking → `converged` 키 존재 → 영향 없음.
- 다른 케이스들도 모두 valid JSON에 키 존재 또는 parse 실패 시나리오 → 영향 없음.

따라서 본 task의 수정은 단위 테스트 19개 모두 그대로 통과해야 한다. 테스트 코드는 수정하지 않는다.

## Dependencies

- 선행 Task 없음 (`depends_on: []`).
- 외부 패키지 추가 없음.
- `experiments/agents/base.py`, `experiments/agents/__init__.py`, `experiments/agents/proposer.py`, `experiments/agents/test_role_agents.py`는 import만 가능, 수정 금지.

## Verification

```bash
# 1. CriticAgent._post_parse_check 본문이 None만 반환
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import inspect
from agents import CriticAgent
src = inspect.getsource(CriticAgent._post_parse_check)
assert 'missing judgments' not in src, f'still has missing judgments: {src}'
assert 'return None' in src, f'no return None: {src}'
# 함수 호출 결과 확인 — 키 없는 dict에도 None 반환
assert CriticAgent()._post_parse_check({}) is None
assert CriticAgent()._post_parse_check({'irrelevant': 'x'}) is None
print('OK CriticAgent._post_parse_check returns None')
"

# 2. JudgeAgent._post_parse_check 본문이 None만 반환
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import inspect
from agents import JudgeAgent
src = inspect.getsource(JudgeAgent._post_parse_check)
assert 'missing converged' not in src, f'still has missing converged: {src}'
assert 'return None' in src, f'no return None: {src}'
assert JudgeAgent()._post_parse_check({}) is None
assert JudgeAgent()._post_parse_check({'irrelevant': 'x'}) is None
print('OK JudgeAgent._post_parse_check returns None')
"

# 3. 단위 테스트 19개 모두 통과 (회귀 없음)
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest agents.test_role_agents -v 2>&1 | tail -5
# 기대: "OK" 이고 "Ran 19 tests" 가 나와야 함

# 4. base.py·proposer.py·__init__.py·test_role_agents.py 수정 없음 (git diff)
cd /Users/d9ng/privateProject/gemento && git diff --name-only experiments/agents/ | sort
# 기대: critic.py 와 judge.py 만 출력. base.py·proposer.py·__init__.py·test_role_agents.py 가 나오면 안 됨.

# 5. orchestrator import 회귀 없음
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from orchestrator import run_abc_chain, run_abc_chunked
from agents import ProposerAgent, CriticAgent, JudgeAgent, AgentResult, RoleAgent
print('OK imports clean')
"

# 6. CriticAgent._post_parse_check 가 retry를 유발하지 않는지 mock으로 확인
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from unittest.mock import patch
from agents import CriticAgent
# judgments 가 없는 응답이라도 retry 안 하고 break — call_model 호출 1회
with patch('orchestrator.call_model', return_value=('{\"unexpected\": \"value\"}', [])) as m:
    r = CriticAgent().call(
        problem='p', assertions=[{'id':'a','content':'x','confidence':0.5,'status':'active','source_loop':0}],
        max_retries=1,
    )
assert m.call_count == 1, f'expected 1 call, got {m.call_count}'
assert r.parsed == {'unexpected': 'value'}
assert r.error is None
print('OK CriticAgent no extra retry on missing judgments')
"

# 7. JudgeAgent._post_parse_check 도 동일 확인
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from unittest.mock import patch
from agents import JudgeAgent
with patch('orchestrator.call_model', return_value=('{\"unexpected\": \"value\"}', [])) as m:
    r = JudgeAgent().call(
        problem='p', current_phase='DECOMPOSE',
        current_critique={'judgments': []}, previous_critique=None, assertion_count=1,
        max_retries=1,
    )
assert m.call_count == 1, f'expected 1 call, got {m.call_count}'
assert r.parsed == {'unexpected': 'value'}
assert r.error is None
print('OK JudgeAgent no extra retry on missing converged')
"
```

## Risks

- **base.py break 로직과의 상호작용**: `agents/base.py:62-66`은 `parsed` truthy + `_post_parse_check` 결과 None 일 때만 break한다. 본 task가 `_post_parse_check`를 None 반환으로 되돌리면 모든 valid parse 시 즉시 break — 이는 원본 인라인 동작과 동치이다 (인라인 코드는 `if parsed: break`). base.py 수정은 본 task 범위 밖.
- **`from typing import Any` 잔존**: 두 파일에서 `_post_parse_check` 시그니처에 `dict[str, Any]`를 사용 중. import 그대로 유지. 미사용 경고가 떠도 본 task에서는 손대지 않는다 (rev.0 successful subtasks 수정 금지 원칙).
- **단위 테스트 회귀**: Step 4에서 분석한 대로 기존 19 케이스는 모두 valid JSON·키 존재 시나리오라 영향 없음. 만약 회귀가 발생하면 본 task가 잘못 수정한 것 — Verification 3번이 catch.
- **회귀 게이트 영향**: 본 task는 회귀 게이트 통과 가능성을 *높이는* 방향(추가 LLM 호출 제거 → tool_calls·num_assertions 편차 축소). 단 LLM 비결정성으로 인한 잔여 편차는 Task 02의 비교 tolerance(±1, ±2)로 흡수.
- **caller가 의존하는 에러 메시지**: `b_error == "missing judgments"` 등 caller가 특정 문자열에 의존하는지 확인 필요. `experiments/orchestrator.py`의 B/C 블록은 `b_error or "no output"` 패턴(truthy 체크)만 사용 → 메시지 문자열 변경(없어짐)은 안전.

## Scope boundary

**Task 01에서 절대 수정 금지**:

- `experiments/agents/base.py` — break 로직, AgentResult, RoleAgent 추상화.
- `experiments/agents/proposer.py` — A 어댑터.
- `experiments/agents/__init__.py` — export.
- `experiments/agents/test_role_agents.py` — 단위 테스트.
- `experiments/orchestrator.py` — `run_abc_chain`·`run_abc_chunked`·`run_loop`·`call_model`·`extract_json_from_response` 등 본문.
- `experiments/system_prompt.py`, `experiments/schema.py`, `experiments/measure.py`, `experiments/run_experiment.py`, `experiments/regression_check.py`.
- `experiments/tools/`, `experiments/tasks/`, `experiments/results/`.
- `critic.py`·`judge.py`의 `_build_messages` 메소드, `role_name` 클래스 변수, import 구문.

**허용 범위**: `experiments/agents/critic.py`의 `_post_parse_check` 본문 (line 39-42 영역) 및 `experiments/agents/judge.py`의 `_post_parse_check` 본문 (line 48-51 영역) — 각 메소드의 함수 본문 라인만 교체.
