---
type: plan-task
status: abandoned
updated_at: 2026-04-25
parent_plan: role-adapter-phase-1-a-b-c
parallel_group: B
depends_on: [01]
---

# Task 04 — 어댑터 단위 테스트

## Changed files

- `experiments/agents/test_role_agents.py` — **신규 파일**. 3개 어댑터의 단위 테스트.

## Change description

### Step 1 — 테스트 파일 위치 결정

기존 `experiments/tools/test_*.py` 패턴(Exp08, Exp09에서 채택)과 일관성 있게:
- `experiments/agents/test_role_agents.py` (현재 Task 위치)
- 일괄 실행: `cd experiments && python -m unittest agents.test_role_agents tools.test_*`

### Step 2 — `unittest.mock.patch`로 `call_model` mocking

**핵심 원칙**: 실제 LLM 서버 호출 없이 어댑터의 retry/parse/error 로직만 검증.

```python
"""ProposerAgent / CriticAgent / JudgeAgent 단위 테스트.

기존 인라인 패턴(orchestrator.py L549~624 B블록, L629~ C블록)의 동작을
어댑터가 정확히 재현하는지 검증. 실제 call_model은 mocking.
"""
import unittest
from unittest.mock import patch
from agents import ProposerAgent, CriticAgent, JudgeAgent, AgentResult


class _Base:
    """공통 mocking 헬퍼."""
    def _ok(self, payload_json: str):
        return (payload_json, [])  # call_model 반환 형식: (raw, tool_calls)
    
    def _empty(self):
        return ("", [])


class TestCriticAgent(unittest.TestCase, _Base):
    def setUp(self):
        self.agent = CriticAgent()
        self.kwargs = dict(
            problem="test problem",
            assertions=[{"id": "a01", "content": "x", "confidence": 0.8, "status": "active", "source_loop": 0}],
            handoff_a2b=None,
            phase_args=None,
        )
    
    def test_normal_call_returns_parsed(self):
        with patch("orchestrator.call_model", return_value=self._ok('{"judgments": []}')):
            r = self.agent.call(**self.kwargs)
        self.assertIsNotNone(r.parsed)
        self.assertEqual(r.parsed, {"judgments": []})
        self.assertIsNone(r.error)
        self.assertGreater(r.duration_ms, -1)  # >= 0
    
    def test_retry_on_parse_fail_then_success(self):
        side_effects = [self._ok("not json"), self._ok('{"judgments": [{"status": "valid"}]}')]
        with patch("orchestrator.call_model", side_effect=side_effects):
            r = self.agent.call(max_retries=1, **self.kwargs)
        self.assertIsNotNone(r.parsed)
        self.assertEqual(len(r.parsed["judgments"]), 1)
        self.assertIsNone(r.error)
    
    def test_parse_fail_after_all_retries(self):
        with patch("orchestrator.call_model", return_value=self._ok("garbage")):
            r = self.agent.call(max_retries=1, **self.kwargs)
        self.assertIsNone(r.parsed)
        self.assertEqual(r.error, "JSON parse failed")
    
    def test_empty_response(self):
        with patch("orchestrator.call_model", return_value=self._empty()):
            r = self.agent.call(max_retries=1, **self.kwargs)
        self.assertIsNone(r.parsed)
        self.assertIsNotNone(r.error)  # parse failed or similar
    
    def test_call_model_raises_propagated(self):
        with patch("orchestrator.call_model", side_effect=RuntimeError("network down")):
            r = self.agent.call(max_retries=0, **self.kwargs)
        self.assertIsNone(r.parsed)
        self.assertIn("network down", r.error)
    
    def test_phase_args_uses_with_phase_builder(self):
        """phase_args 전달 시 build_critic_prompt_with_phase 호출되는지."""
        kwargs = dict(self.kwargs, phase_args=(3, 8))
        with patch("system_prompt.build_critic_prompt_with_phase") as mock_build, \
             patch("orchestrator.call_model", return_value=self._ok('{"judgments": []}')):
            mock_build.return_value = [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}]
            self.agent.call(**kwargs)
        mock_build.assert_called_once()
        call_args = mock_build.call_args.kwargs
        self.assertEqual(call_args["cycle"], 3)
        self.assertEqual(call_args["max_cycles"], 8)


class TestJudgeAgent(unittest.TestCase, _Base):
    def setUp(self):
        self.agent = JudgeAgent()
        self.kwargs = dict(
            problem="test",
            current_phase="DECOMPOSE",
            current_critique={"judgments": []},
            previous_critique=None,
            assertion_count=2,
            handoff_b2c=None,
            phase_args=None,
        )
    
    def test_normal_call(self):
        payload = '{"converged": true, "next_phase": "INVESTIGATE", "next_directive": "..."}'
        with patch("orchestrator.call_model", return_value=self._ok(payload)):
            r = self.agent.call(**self.kwargs)
        self.assertTrue(r.parsed["converged"])
        self.assertEqual(r.parsed["next_phase"], "INVESTIGATE")
    
    def test_retry_then_success(self):
        side_effects = [self._ok("garbage"), self._ok('{"converged": false}')]
        with patch("orchestrator.call_model", side_effect=side_effects):
            r = self.agent.call(max_retries=1, **self.kwargs)
        self.assertIsNotNone(r.parsed)
    
    def test_parse_fail_after_retries(self):
        with patch("orchestrator.call_model", return_value=self._ok("not json at all")):
            r = self.agent.call(max_retries=1, **self.kwargs)
        self.assertEqual(r.error, "JSON parse failed")
    
    def test_empty_response(self):
        with patch("orchestrator.call_model", return_value=self._empty()):
            r = self.agent.call(max_retries=1, **self.kwargs)
        self.assertIsNone(r.parsed)
    
    def test_exception_propagated(self):
        with patch("orchestrator.call_model", side_effect=ValueError("boom")):
            r = self.agent.call(max_retries=0, **self.kwargs)
        self.assertIn("boom", r.error)


class TestProposerAgent(unittest.TestCase, _Base):
    def setUp(self):
        self.agent = ProposerAgent()
    
    def test_default_build_prompt(self):
        with patch("system_prompt.build_prompt") as mock_b, \
             patch("orchestrator.call_model", return_value=self._ok('{"new_assertions": []}')):
            mock_b.return_value = [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}]
            r = self.agent.call(tattoo_json='{"task_id":"t"}')
        mock_b.assert_called_once()
        self.assertIsNotNone(r.parsed)
    
    def test_phase_args_uses_with_phase(self):
        with patch("system_prompt.build_prompt_with_phase") as mock_b, \
             patch("orchestrator.call_model", return_value=self._ok('{"new_assertions": []}')):
            mock_b.return_value = [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}]
            r = self.agent.call(tattoo_json='{}', phase_args=(2, 5))
        mock_b.assert_called_once()
        kw = mock_b.call_args.kwargs
        self.assertEqual(kw["cycle"], 2)
        self.assertEqual(kw["max_cycles"], 5)
    
    def test_chunked_uses_chunked_builder(self):
        """chunked dict 전달 시 build_prompt_chunked 호출."""
        with patch("system_prompt.build_prompt_chunked") as mock_b, \
             patch("orchestrator.call_model", return_value=self._ok('{"new_assertions": []}')):
            mock_b.return_value = [{"role": "system", "content": "x"}, {"role": "user", "content": "y"}]
            r = self.agent.call(tattoo_json='{}', chunked={"current_chunk": "...", "chunk_id": 7})
        mock_b.assert_called_once_with(
            tattoo_json='{}', current_chunk="...", chunk_id=7,
        )
    
    def test_tools_passed_through(self):
        """tools 인자가 call_model에 전달되는지."""
        tools = [{"type": "function", "function": {"name": "calc"}}]
        with patch("orchestrator.call_model", return_value=('{"x":1}', [{"name": "calc", "result": 42}])) as mock_call:
            r = self.agent.call(tattoo_json='{}', tools=tools, tool_functions={"calc": lambda: 42})
        mock_call.assert_called_once()
        # tools 인자가 전달됐는지
        kw = mock_call.call_args
        self.assertIn("tools", kw.kwargs)
        self.assertEqual(r.tool_calls, [{"name": "calc", "result": 42}])
    
    def test_parse_fail(self):
        with patch("orchestrator.call_model", return_value=self._ok("rubbish")):
            r = self.agent.call(tattoo_json='{}', max_retries=1)
        self.assertEqual(r.error, "JSON parse failed")


if __name__ == "__main__":
    unittest.main()
```

### Step 3 — 케이스 커버리지 요약

| 어댑터 | 테스트 케이스 |
|--------|--------------|
| ProposerAgent | default builder, with_phase builder, chunked builder, tools 전달, parse fail |
| CriticAgent | 정상, retry then success, parse fail after retries, empty response, exception 전파, phase_args 분기 |
| JudgeAgent | 정상, retry, parse fail, empty, exception 전파 |

총 케이스: 5 + 6 + 5 = **16개**.

### Step 4 — Mock 대상 — `orchestrator.call_model` vs `system_prompt.build_*`

- `orchestrator.call_model`: 실제 LLM 서버 호출 회피. 모든 테스트에서 mock.
- `system_prompt.build_*`: prompt builder를 호출했는지만 검증할 때 mock. 일반 정상 케이스에선 mock 안 함 (실제 builder가 호출되어 messages 생성).

### Step 5 — 동작 동치 검증의 한계

- 단위 테스트는 어댑터 자체의 logic만 검증.
- 어댑터를 사용하는 `run_abc_chain` / `run_abc_chunked`의 결과 동치는 **Task 05 회귀 게이트**가 검증.
- 두 검증 레이어가 함께 Phase 1 통과를 보장.

## Dependencies

- **Task 01 완료**: `agents/{base, proposer, critic, judge}.py` 존재해야 import 가능.
- 외부 패키지 추가 없음 (`unittest.mock`은 표준 라이브러리).

## Verification

```bash
# 1. 파일 존재
test -f experiments/agents/test_role_agents.py && echo "test file: OK"

# 2. 단위 테스트 전체 통과
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest agents.test_role_agents -v 2>&1 | tail -10
# 기대: "OK", 16개 테스트 pass

# 3. 다른 단위 테스트(tools)와 일괄 실행 호환
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -m unittest \
    agents.test_role_agents \
    tools.test_chunker tools.test_bm25_tool tools.test_math_tools 2>&1 | tail -5
# 기대: "OK", 합계 38개 테스트 pass (16 + 7 + 6 + 9)

# 4. patch 대상 경로가 정확 — orchestrator.call_model 가 import path로 유효
cd /Users/d9ng/privateProject/gemento/experiments && _ZO_DOCTOR=0 ../.venv/bin/python -c "
import orchestrator
assert hasattr(orchestrator, 'call_model')
print('OK orchestrator.call_model is mockable target')
"

# 5. 테스트 코드에서 실제 LLM 호출 없음 확인 — 환경변수로 서버 끄고 실행
# (mocking 잘 됐다면 서버 없어도 통과)
cd /Users/d9ng/privateProject/gemento/experiments && API_BASE_URL=http://localhost:1 _ZO_DOCTOR=0 ../.venv/bin/python -m unittest agents.test_role_agents -v 2>&1 | tail -3
# 기대: "OK" — call_model이 mocking되어 실제 네트워크 호출 0
```

## Risks

- **Mock 경로**: `unittest.mock.patch("orchestrator.call_model", ...)`이 정확하려면 어댑터 내부에서 `from orchestrator import call_model`로 함수 내 import해야 함. 모듈 레벨 import면 patch 대상이 `agents.base.call_model` 같은 다른 경로가 됨. Task 01에서 함수 내부 import로 설계 → 이 구조와 일치.
- **`system_prompt.build_*` mock**: 일부 테스트는 builder 호출 검증. mock하지 않으면 실제 prompt 생성되며 외부 네트워크 호출은 없으므로 부작용 없음.
- **`AgentResult.duration_ms`**: 실제 wall clock 측정. 테스트에서는 항상 ≥ 0 이므로 정확한 값 검증 안 함.
- **회귀 게이트가 진짜 동치를 증명**: 단위 테스트는 어댑터 *자체*의 동작만. `run_abc_chain` 통합 동치는 Task 05가 책임.
- **테스트 간 격리**: 각 테스트는 `with patch(...)` 블록 내에서만 mock. 테스트 후 자동 unwind.

## Scope boundary

**Task 04에서 절대 수정 금지**:
- `experiments/agents/{__init__, base, proposer, critic, judge}.py` (Task 01 영역) — import·인스턴스화만
- `experiments/orchestrator.py` (Task 02·03 영역)
- `experiments/system_prompt.py`, `experiments/schema.py`
- `experiments/run_experiment.py`, `experiments/measure.py`, `experiments/tools/`, `experiments/tasks/`
- 기존 `experiments/tools/test_*.py` 단위 테스트 — 추가 변경 금지

**허용 범위**: `experiments/agents/test_role_agents.py` 신규 파일 1개.
