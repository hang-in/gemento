---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: role-adapter-phase-1-a-b-c
parallel_group: A
depends_on: []
---

# Task 01 — RoleAgent 베이스 + 3 어댑터 클래스

## Changed files

- `experiments/agents/__init__.py` — **신규**. `RoleAgent`, `ProposerAgent`, `CriticAgent`, `JudgeAgent`, `AgentResult` export.
- `experiments/agents/base.py` — **신규**. `RoleAgent` 추상 베이스 + 공통 retry/parse 로직 + `AgentResult` dataclass.
- `experiments/agents/proposer.py` — **신규**. `ProposerAgent` (A 역할).
- `experiments/agents/critic.py` — **신규**. `CriticAgent` (B 역할).
- `experiments/agents/judge.py` — **신규**. `JudgeAgent` (C 역할).

## Change description

### Step 1 — `base.py`: RoleAgent 추상 베이스

```python
"""RoleAgent — A/B/C 역할 어댑터의 추상 베이스.

각 역할은 동일한 인터페이스 `call(...)`를 노출한다:
  inputs:  필요한 컨텍스트(role-specific)
  outputs: 파싱된 dict 또는 None (parse 실패 시)
  retry:   1회 (기존 인라인 동작과 동일)
  errors:  raw text + error string으로 결과에 포함

기존 함수 `call_model`, `extract_json_from_response`는 호출만 한다 (수정 금지).
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class AgentResult:
    """역할 호출 1회의 결과. 기존 인라인 처리에서 추출하던 변수들을 담는 객체."""
    parsed: dict | None = None
    raw: str = ""
    duration_ms: int = 0
    error: str | None = None
    tool_calls: list[dict] = field(default_factory=list)


class RoleAgent(ABC):
    """A/B/C 역할 어댑터의 추상 베이스.

    Subclass는 _build_messages()와 _post_parse_check()를 구현한다.
    공통 retry/parse는 base에서 처리.
    """

    role_name: str = "abstract"

    @abstractmethod
    def _build_messages(self, **kwargs) -> list[dict]:
        """역할별 prompt builder 호출. system_prompt.py 함수를 wrap."""
        raise NotImplementedError

    def _post_parse_check(self, parsed: dict) -> str | None:
        """파싱은 됐지만 의미상 실패인 경우 error 메시지 반환. 기본은 None."""
        return None

    def call(
        self,
        max_retries: int = 1,
        tools: list[dict] | None = None,
        tool_functions: dict | None = None,
        **kwargs,
    ) -> AgentResult:
        """역할 호출 1회 + retry. 기존 인라인 패턴을 그대로 보존."""
        from orchestrator import call_model, extract_json_from_response

        result = AgentResult()
        start = time.time()
        messages = self._build_messages(**kwargs)

        for attempt in range(max_retries + 1):
            try:
                if tools is not None:
                    raw, tool_calls = call_model(messages, tools=tools, tool_functions=tool_functions)
                    result.tool_calls = tool_calls
                else:
                    raw, _ = call_model(messages)
                result.raw = raw
                parsed = extract_json_from_response(raw)
                if parsed:
                    check_err = self._post_parse_check(parsed)
                    if check_err:
                        result.error = check_err
                        result.parsed = parsed
                    else:
                        result.parsed = parsed
                        result.error = None
                    break
            except Exception as e:
                result.raw = ""
                result.error = str(e)

            if attempt < max_retries:
                print(f"    {self.role_name} ↻ retry")

        if result.parsed is None and result.error is None:
            result.error = "JSON parse failed"

        result.duration_ms = int((time.time() - start) * 1000)
        return result
```

### Step 2 — `proposer.py`: A 역할 어댑터

```python
"""ProposerAgent — A 역할. SYSTEM_PROMPT 사용."""
from __future__ import annotations
from .base import RoleAgent


class ProposerAgent(RoleAgent):
    role_name = "A"

    def _build_messages(
        self,
        tattoo_json: str,
        tool_results: str | None = None,
        phase_args: tuple[int, int] | None = None,
        chunked: dict | None = None,  # {"current_chunk": str, "chunk_id": int}
        **_,
    ) -> list[dict]:
        if chunked is not None:
            from system_prompt import build_prompt_chunked
            return build_prompt_chunked(
                tattoo_json=tattoo_json,
                current_chunk=chunked["current_chunk"],
                chunk_id=chunked["chunk_id"],
            )
        if phase_args is not None:
            from system_prompt import build_prompt_with_phase
            return build_prompt_with_phase(
                tattoo_json=tattoo_json,
                tool_results=tool_results,
                cycle=phase_args[0],
                max_cycles=phase_args[1],
            )
        from system_prompt import build_prompt
        return build_prompt(tattoo_json=tattoo_json, tool_results=tool_results)
```

**참고**: A 역할의 호출은 현재 `run_loop()`(orchestrator 별도 함수)가 담당한다. Task 02에서 `run_abc_chain` 리팩토링할 때 `ProposerAgent`를 직접 사용할지, `run_loop()`를 그대로 쓸지 결정. 단위 테스트(Task 04)는 ProposerAgent 자체의 `call()`을 검증.

### Step 3 — `critic.py`: B 역할 어댑터

```python
"""CriticAgent — B 역할. CRITIC_PROMPT 사용. 기존 line 549~624 인라인 블록 추출."""
from __future__ import annotations
from .base import RoleAgent


class CriticAgent(RoleAgent):
    role_name = "B"

    def _build_messages(
        self,
        problem: str,
        assertions: list[dict],
        handoff_a2b: dict | None = None,
        phase_args: tuple[int, int] | None = None,
        **_,
    ) -> list[dict]:
        if phase_args is not None:
            from system_prompt import build_critic_prompt_with_phase
            return build_critic_prompt_with_phase(
                problem,
                assertions,
                handoff_a2b=handoff_a2b,
                cycle=phase_args[0],
                max_cycles=phase_args[1],
            )
        from system_prompt import build_critic_prompt
        return build_critic_prompt(problem, assertions, handoff_a2b=handoff_a2b)

    def _post_parse_check(self, parsed: dict) -> str | None:
        # B는 judgments 없으면 의미적 실패 — 기존 인라인은 silent했지만 여기선 명시
        # 단 Phase 1 동작 동치 보장을 위해 이 체크는 일단 None 반환 (기존 동작 유지)
        return None
```

### Step 4 — `judge.py`: C 역할 어댑터

```python
"""JudgeAgent — C 역할. JUDGE_PROMPT 사용. 기존 line 629~ 인라인 블록 추출."""
from __future__ import annotations
from .base import RoleAgent


class JudgeAgent(RoleAgent):
    role_name = "C"

    def _build_messages(
        self,
        problem: str,
        current_phase: str,
        current_critique: dict | None,
        previous_critique: dict | None,
        assertion_count: int,
        handoff_b2c: dict | None = None,
        phase_args: tuple[int, int] | None = None,
        **_,
    ) -> list[dict]:
        if phase_args is not None:
            from system_prompt import build_judge_prompt_with_phase
            return build_judge_prompt_with_phase(
                problem=problem,
                current_phase=current_phase,
                current_critique=current_critique,
                previous_critique=previous_critique,
                assertion_count=assertion_count,
                handoff_b2c=handoff_b2c,
                cycle=phase_args[0],
                max_cycles=phase_args[1],
            )
        from system_prompt import build_judge_prompt
        return build_judge_prompt(
            problem=problem,
            current_phase=current_phase,
            current_critique=current_critique,
            previous_critique=previous_critique,
            assertion_count=assertion_count,
        )
```

### Step 5 — `__init__.py`

```python
from .base import RoleAgent, AgentResult
from .proposer import ProposerAgent
from .critic import CriticAgent
from .judge import JudgeAgent

__all__ = [
    "RoleAgent",
    "AgentResult",
    "ProposerAgent",
    "CriticAgent",
    "JudgeAgent",
]
```

### Step 6 — 설계 원칙

- **Prompt builder 재사용 (수정 금지)** — 어댑터는 `system_prompt.py`의 기존 함수를 wrap. prompt 생성 로직 중복 금지.
- **`call_model` 호출 그대로** — `tools=None`이면 기존 시그니처 호환 (`raw, _ = call_model(messages)`).
- **`AgentResult` dataclass** — 기존 인라인이 `b_raw`, `b_parsed`, `b_duration`, `b_error` 같은 변수들을 따로 두던 것을 1개 객체로 통일.
- **동작 동치** — retry 횟수(1회), retry 메시지(`B ↻ retry` / `C ↻ retry`) 모두 기존과 동일.

## Dependencies

- 선행 Task 없음.
- 외부 패키지 추가 없음.
- 기존 모듈(`orchestrator`, `system_prompt`)은 import만, 수정 안 함.

## Verification

```bash
# 1. 디렉터리 + 파일 존재
test -d experiments/agents && echo "agents dir: OK"
ls experiments/agents/{__init__.py,base.py,proposer.py,critic.py,judge.py} 2>&1 | wc -l
# 기대: 5

# 2. import 가능 + 클래스 정의
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from agents import RoleAgent, AgentResult, ProposerAgent, CriticAgent, JudgeAgent
import inspect
assert inspect.isabstract(RoleAgent) or hasattr(RoleAgent, '_build_messages')
for cls in (ProposerAgent, CriticAgent, JudgeAgent):
    assert issubclass(cls, RoleAgent)
    assert hasattr(cls, 'role_name')
    assert hasattr(cls, '_build_messages')
print('OK: all classes import + structure')
"

# 3. AgentResult dataclass 필드 확인
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from dataclasses import fields
from agents import AgentResult
names = {f.name for f in fields(AgentResult)}
required = {'parsed', 'raw', 'duration_ms', 'error', 'tool_calls'}
assert required.issubset(names), f'missing: {required - names}'
r = AgentResult()
assert r.parsed is None and r.error is None and r.tool_calls == []
print('OK AgentResult')
"

# 4. role_name 값 정확
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from agents import ProposerAgent, CriticAgent, JudgeAgent
assert ProposerAgent.role_name == 'A'
assert CriticAgent.role_name == 'B'
assert JudgeAgent.role_name == 'C'
print('OK role names')
"

# 5. 기존 모듈 회귀 없음
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import orchestrator, system_prompt, schema, run_experiment, measure
# 기존 함수가 그대로 존재하는지
assert callable(orchestrator.run_abc_chain)
assert callable(orchestrator.run_abc_chunked)
assert callable(orchestrator.call_model)
assert callable(system_prompt.build_prompt)
assert callable(system_prompt.build_critic_prompt)
assert callable(system_prompt.build_judge_prompt)
print('OK existing modules intact')
"

# 6. _build_messages가 abstract — 직접 인스턴스화하면 에러
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
from agents import RoleAgent
try:
    RoleAgent()
    print('FAIL: RoleAgent should be abstract')
    exit(1)
except TypeError as e:
    print(f'OK abstract: {e}')
"
```

## Risks

- **Circular import**: `agents/base.py`가 `from orchestrator import call_model, extract_json_from_response`를 함수 내부에서 import. 모듈 레벨 import는 회피 (`run_abc_chain`이 어댑터를 import할 때 순환).
- **`run_loop()`와의 관계**: A 역할 호출은 현재 `run_loop()` 함수가 담당. ProposerAgent를 직접 쓸지, run_loop을 그대로 쓸지는 Task 02에서 결정. 본 Task에서는 **ProposerAgent의 `call()`이 단독 호출 가능하도록만 설계**. Task 02에서 통합 시점에 결정.
- **`tools` 파라미터 호환성**: `call_model(messages, tools=...)`은 Exp08+ 추가된 시그니처. 어댑터가 `tools=None`/`tools=[...]` 양쪽을 모두 지원해야 함. AgentResult.tool_calls 필드로 결과 캡처.
- **Phase variant 처리**: `build_prompt_with_phase` 등 with_phase 변형은 기본 변형과 다른 시그니처. 어댑터의 `_build_messages`에서 `phase_args` 인자로 분기.
- **`system_prompt.py` 함수가 향후 변경되면**: 어댑터가 wrap하므로 시그니처 변화 시 어댑터도 갱신 필요. 단 Phase 1 범위에서는 system_prompt.py 수정 금지이므로 문제 없음.

## Scope boundary

**Task 01에서 절대 수정 금지**:
- `experiments/orchestrator.py` (Task 02·03 영역)
- `experiments/system_prompt.py` — import만 허용
- `experiments/schema.py` — import만 허용
- `experiments/run_experiment.py`, `experiments/measure.py`
- `experiments/tools/` 내부 모든 파일
- `experiments/tasks/` 내부 모든 파일
- 기존 `run_loop()`, `run_abc_chain`, `run_abc_chunked`, `call_model`, `extract_json_from_response`, `select_assertions`, `apply_llm_response`, `create_initial_tattoo` — 호출만, 수정 금지

**허용 범위**: `experiments/agents/` 디렉터리 내 5개 신규 파일만.
