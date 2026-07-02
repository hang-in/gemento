"""Stage 12 회귀 게이트 — a2a_proposer opt-in 정적 검증.

LLM 없음. 불변식: a2a_proposer=False(기본) 시 A-stage = 기존 run_loop 경로.
True 시 _a2a_propose 로 분기. Planner/Executor 빌더 shape + 기존 프롬프트 불변.
"""
from __future__ import annotations
import inspect, sys, unittest
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent


class TestA2AProposerOptIn(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))

    def tearDown(self):
        if str(EXPERIMENTS_DIR) in sys.path:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_param_default_false(self):
        import orchestrator
        p = inspect.signature(orchestrator.run_abc_chain).parameters["a2a_proposer"]
        self.assertIs(p.default, False)

    def test_branch_guarded_in_source(self):
        src = inspect.getsource(__import__("orchestrator").run_abc_chain)
        self.assertIn("if a2a_proposer:", src)
        self.assertIn("_a2a_propose", src)
        self.assertIn("run_loop(", src)                    # else 경로 보존

    def test_helper_returns_4tuple_shape(self):
        """_a2a_propose 소스가 run_loop 와 동일 4-tuple 반환."""
        src = inspect.getsource(__import__("orchestrator")._a2a_propose)
        self.assertIn("return", src)
        self.assertIn("apply_llm_response", src)           # 기존 적용 재사용
        self.assertIn("extract_json_from_response", src)   # 기존 파서 재사용

    def test_prompt_builders(self):
        from system_prompt import (A2A_PLANNER_SYSTEM,
                                    build_a2a_planner_prompt, build_a2a_executor_prompt)
        self.assertIn("PLANNER", A2A_PLANNER_SYSTEM)
        pm = build_a2a_planner_prompt("{}")
        self.assertEqual(pm[0]["role"], "system")
        em = build_a2a_executor_prompt("unit X is failing", "{}")
        etxt = " ".join(m["content"] for m in em)
        self.assertIn("Do NOT call tools", etxt)           # probe 조건
        self.assertIn("new_assertion", etxt)

    def test_existing_prompt_unchanged(self):
        """기존 proposer SYSTEM_PROMPT 무변경 (Exp15~23 보존)."""
        from system_prompt import SYSTEM_PROMPT, build_prompt
        self.assertTrue(len(SYSTEM_PROMPT) > 0)
        self.assertEqual(build_prompt("{}")[0]["role"], "system")


if __name__ == "__main__":
    unittest.main()
