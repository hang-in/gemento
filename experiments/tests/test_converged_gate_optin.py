"""Stage 13 회귀 게이트 — converged_requires_answer opt-in 정적 검증 (Exp25c).

LLM 없음. 불변식: converged_requires_answer=False(기본) 시 C-stage 수렴 판정 = 기존 경로
(_gated_to_synth=False → 수용 조건 `... or False` 로 동작 불변). True 시 답 없는 CONVERGED
월반을 SYNTHESIZE 로 유도. 기존 CONVERGED 직행 수용 로직 보존.
"""
from __future__ import annotations
import inspect, sys, unittest
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent


class TestConvergedGateOptIn(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))

    def tearDown(self):
        if str(EXPERIMENTS_DIR) in sys.path:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_param_default_false(self):
        import orchestrator
        p = inspect.signature(orchestrator.run_abc_chain).parameters["converged_requires_answer"]
        self.assertIs(p.default, False)

    def test_gate_guarded_in_source(self):
        src = inspect.getsource(__import__("orchestrator").run_abc_chain)
        # 게이트는 flag 로 가드된다.
        self.assertIn("converged_requires_answer and", src)
        self.assertIn("_gated_to_synth", src)
        # 게이트 조건: 답 없이 CONVERGED, 조기 phase 에서만.
        self.assertIn("final_answer is None", src)
        self.assertIn('phase_str in ("DECOMPOSE", "INVESTIGATE")', src)

    def test_existing_acceptance_logic_preserved(self):
        """기존 CONVERGED 직행/expected 수용 로직 무변경 (off-path 동작 불변)."""
        src = inspect.getsource(__import__("orchestrator").run_abc_chain)
        self.assertIn('next_phase_str == expected or next_phase_str == "CONVERGED"', src)
        # 게이트는 기존 조건에 `or _gated_to_synth` 만 덧붙인다.
        self.assertIn('or next_phase_str == "CONVERGED" or _gated_to_synth', src)

    def test_gate_redirects_to_synthesize(self):
        """게이트 발동 시 SYNTHESIZE 로 유도(A emit phase)."""
        src = inspect.getsource(__import__("orchestrator").run_abc_chain)
        self.assertIn('next_phase_str = "SYNTHESIZE"', src)
        self.assertIn("_gated_to_synth = True", src)


if __name__ == "__main__":
    unittest.main()
