"""Stage 11 회귀 게이트 — list_failed_units opt-in 정적 검증.

글로벌 CONTEXT_TOOL_*(read/grep) 불변 + FAILED_UNITS_* 분리 + fixture 집계 정확성.
LLM/네트워크 없음 (Redis mock).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent


class TestFailedUnitsTool(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(EXPERIMENTS_DIR))

    def tearDown(self):
        if str(EXPERIMENTS_DIR) in sys.path:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_globals_unchanged(self):
        """글로벌 CONTEXT_TOOL_* / FACET_TOOL_* 불변 (Exp15~22 byte-identical)."""
        from tools import (CONTEXT_TOOL_SCHEMAS, CONTEXT_TOOL_FUNCTIONS,
                           FACET_TOOL_FUNCTIONS)
        names = [s["function"]["name"] for s in CONTEXT_TOOL_SCHEMAS]
        self.assertEqual(names, ["read_context", "grep_context"])
        self.assertEqual(list(CONTEXT_TOOL_FUNCTIONS.keys()), ["read_context", "grep_context"])
        self.assertEqual(list(FACET_TOOL_FUNCTIONS.keys()), ["aggregate_context"])

    def test_failed_units_separate(self):
        """FAILED_UNITS_TOOL_* 에 list_failed_units 만 — 글로벌에서 분리."""
        from tools import FAILED_UNITS_TOOL_SCHEMAS, FAILED_UNITS_TOOL_FUNCTIONS
        names = [s["function"]["name"] for s in FAILED_UNITS_TOOL_SCHEMAS]
        self.assertEqual(names, ["list_failed_units"])
        self.assertEqual(list(FAILED_UNITS_TOOL_FUNCTIONS.keys()), ["list_failed_units"])
        # required 는 handle 만 (top_n optional) — 쿼리 formulate 불필요가 핵심
        self.assertEqual(FAILED_UNITS_TOOL_SCHEMAS[0]["function"]["parameters"]["required"],
                         ["handle"])

    def test_aggregation_correct(self):
        """fixture: 실패 신호 unit 별 카운트 top-N (untruncated)."""
        import tools.context_tools as ct
        fake = [
            "gohttpserver.service: Main process exited, code=exited",
            "gohttpserver.service: Failed with result 'exit-code'",
            "gohttpserver.service: start-limit hit",
            "sshd.service: Started",                      # 실패 신호 아님 → 제외
            "nginx.service: Failed to start",
        ]

        class R:
            def get(self, k):
                return "\n".join(fake)

        with mock.patch.object(ct, "get_redis_client", lambda: R()):
            out = ct.list_failed_units("h")
        self.assertFalse(out.get("truncated"))
        self.assertEqual(out["top"][0]["unit"], "gohttpserver.service")
        self.assertEqual(out["top"][0]["failure_signals"], 3)
        units = [u["unit"] for u in out["top"]]
        self.assertIn("nginx.service", units)
        self.assertNotIn("sshd.service", units)           # Started 는 실패 아님

    def test_handle_missing(self):
        import tools.context_tools as ct

        class R:
            def get(self, k):
                return None

        with mock.patch.object(ct, "get_redis_client", lambda: R()):
            out = ct.list_failed_units("nope")
        self.assertIn("error", out)


if __name__ == "__main__":
    unittest.main()
