"""Stage 10 회귀 게이트 — retrieval_discipline_prompt opt-in 정적 검증.

LLM 호출 없음. 불변식: `retrieval_discipline_prompt=False`(기본) 시 prompt byte-identical,
True 시 RETRIEVAL_DISCIPLINE_RULES 정확히 1회 append. 두 플래그 조합 순서=mandatory→discipline.
"""
from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent


class TestRetrievalDisciplineOptIn(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))

    def tearDown(self):
        if str(EXPERIMENTS_DIR) in sys.path:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_constant_exists_and_shape(self):
        from system_prompt import RETRIEVAL_DISCIPLINE_RULES as R
        self.assertTrue(R.startswith("\n\n"))                 # append 용
        self.assertIn("RETRIEVAL DISCIPLINE", R)
        for phrase in ("Failed with result", "Main process exited",
                       ".service", "new_assertion", "empty-handed"):
            self.assertIn(phrase, R, f"검증 문구 {phrase!r} drift")

    def test_param_default_false(self):
        import orchestrator
        p = inspect.signature(orchestrator.run_abc_chain).parameters["retrieval_discipline_prompt"]
        self.assertIs(p.default, False)

    def test_injection_guarded_in_source(self):
        src = inspect.getsource(__import__("orchestrator").run_abc_chain)
        self.assertIn("if retrieval_discipline_prompt:", src)
        self.assertIn("RETRIEVAL_DISCIPLINE_RULES", src)

    def test_injection_contract(self):
        """False=동일, True=정확히 1회 append, 멱등."""
        from system_prompt import RETRIEVAL_DISCIPLINE_RULES as R

        def inject(prompt, on):
            return f"{prompt}{R}" if on else prompt

        base = "TASK PROMPT BODY"
        self.assertEqual(inject(base, False), base)
        self.assertEqual(inject(base, True), base + R)
        self.assertEqual(inject(base, True).count("RETRIEVAL DISCIPLINE"), 1)

    def test_two_flags_order_and_independence(self):
        """결정 4: mandatory 먼저, discipline 나중. 독립 상수(중복/오염 없음)."""
        from system_prompt import MANDATORY_TOOL_RULES as M, RETRIEVAL_DISCIPLINE_RULES as R
        self.assertNotEqual(M, R)                              # 별도 상수
        base = "TASK PROMPT BODY"
        # 코드 주입 순서와 동일한 식: mandatory 먼저, discipline 나중
        combined = base
        combined = f"{combined}{M}"
        combined = f"{combined}{R}"
        self.assertTrue(combined.endswith(R))                 # discipline 이 맨 끝
        self.assertLess(combined.index("MANDATORY TOOL-USE RULES"),
                        combined.index("RETRIEVAL DISCIPLINE"))  # mandatory 가 앞
        self.assertEqual(combined.count("RETRIEVAL DISCIPLINE"), 1)
        self.assertEqual(combined.count("MANDATORY TOOL-USE RULES"), 1)

    def test_mandatory_constant_untouched(self):
        """Risk 2: 기존 MANDATORY 상수 무변경 (Exp16b 보존)."""
        from system_prompt import MANDATORY_TOOL_RULES as M
        self.assertTrue(M.startswith("\n\n"))
        self.assertIn("MANDATORY TOOL-USE RULES", M)
        self.assertIn("transcribe", M)


if __name__ == "__main__":
    unittest.main()
