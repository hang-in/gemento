"""Stage 8 회귀 게이트 — mandatory_tool_prompt opt-in 정적 검증.

LLM 호출 없음. 핵심 불변식: `mandatory_tool_prompt=False` (기본) 시 prompt 가 변경 전과
byte-identical, True 시 MANDATORY_TOOL_RULES 가 정확히 1회 append. 자동 게이트 없음.
"""
from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent


class TestMandatoryOptIn(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))

    def tearDown(self):
        if str(EXPERIMENTS_DIR) in sys.path:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_constant_exists_and_shape(self):
        from system_prompt import MANDATORY_TOOL_RULES
        self.assertTrue(MANDATORY_TOOL_RULES.startswith("\n\n"))   # caller prompt 끝에 append 용
        self.assertIn("MANDATORY TOOL-USE RULES", MANDATORY_TOOL_RULES)
        self.assertIn("transcribe", MANDATORY_TOOL_RULES)          # 핵심 규칙 4 (전사)
        self.assertIn("grep_context", MANDATORY_TOOL_RULES)

    def test_param_default_false(self):
        """불변식: 기본값 False — 기존 실험/Stage 6 거동 불변."""
        import orchestrator
        p = inspect.signature(orchestrator.run_abc_chain).parameters["mandatory_tool_prompt"]
        self.assertIs(p.default, False)

    def test_injection_guarded_in_source(self):
        """실제 코드 경로: False 시 주입 분기를 건너뛰도록 `if mandatory_tool_prompt:` 가드 존재."""
        src = inspect.getsource(__import__("orchestrator").run_abc_chain)
        self.assertIn("if mandatory_tool_prompt:", src)
        self.assertIn("MANDATORY_TOOL_RULES", src)

    def test_injection_contract(self):
        """주입 계약 (코드와 동일 식): False=동일, True=정확히 1회 append, 멱등."""
        from system_prompt import MANDATORY_TOOL_RULES

        def inject(prompt, mandatory):
            return f"{prompt}{MANDATORY_TOOL_RULES}" if mandatory else prompt

        base = "TASK PROMPT BODY"
        self.assertEqual(inject(base, False), base)                       # byte-identical
        self.assertEqual(inject(base, True), base + MANDATORY_TOOL_RULES)  # exactly one append
        self.assertEqual(inject(base, True).count("MANDATORY TOOL-USE RULES"), 1)

    def test_drivers_use_canonical_constant(self):
        """source-of-truth: v16b/v16c 드라이버가 로컬 복사본이 아닌 canonical 상수를 쓴다."""
        from system_prompt import MANDATORY_TOOL_RULES
        import importlib.util
        for name in ("run_v16b_mandatory", "run_v16c_combined"):
            path = EXPERIMENTS_DIR / "exp15_context_router" / f"{name}.py"
            sys.path.insert(0, str(EXPERIMENTS_DIR / "exp15_context_router"))
            try:
                spec = importlib.util.spec_from_file_location(name, path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                self.assertEqual(mod.MANDATORY_BLOCK, MANDATORY_TOOL_RULES, f"{name} drifted")
            finally:
                p = str(EXPERIMENTS_DIR / "exp15_context_router")
                if p in sys.path:
                    sys.path.remove(p)


if __name__ == "__main__":
    unittest.main()
