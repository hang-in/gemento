"""aggregate_context 정확성 + 글로벌 도구 표면 회귀 게이트 + caller opt-in 서명 검증.

unittest.TestCase 스타일 (pytest 미설치, python -m unittest 실행).
Redis 미가동 시 집계 정확성 테스트만 skipTest — 회귀·서명 테스트는 항상 실행.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

EXPERIMENTS_DIR = Path(__file__).resolve().parent.parent


class TestAggregateContextAccuracy(unittest.TestCase):
    """Redis fixture 기반 aggregate_context 집계 정확성.

    Redis(localhost:6379) 미가동 시 클래스 전체 skipTest.
    """

    def setUp(self):
        """import + Redis ping — 미가동 시 스킵."""
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from tools.context_tools import get_redis_client, aggregate_context  # noqa: F401
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

        # module is now cached; direct reference for test use
        import tools.context_tools as _ct
        try:
            self._r = _ct.get_redis_client()
            self._r.ping()
            self._aggregate = _ct.aggregate_context
        except Exception:
            self.skipTest("redis unavailable (localhost:6379 unreachable)")

    def test_top_ip_aggregation(self):
        """1.1.1.1×3 > 2.2.2.2×2 > 3.3.3.3×1 → top[0]==1.1.1.1,count==3,total==6,unique==3"""
        key = "ctx:test_facet_tool:ip_test"
        content = "\n".join([
            "Failed password for root from 1.1.1.1 port 22 ssh2",
            "Failed password for root from 2.2.2.2 port 22 ssh2",
            "Failed password for root from 1.1.1.1 port 22 ssh2",
            "Failed password for root from 3.3.3.3 port 22 ssh2",
            "Failed password for root from 2.2.2.2 port 22 ssh2",
            "Failed password for root from 1.1.1.1 port 22 ssh2",
        ])
        self._r.set(key, content)
        try:
            result = self._aggregate(
                key, "Failed password",
                group_by=r"from (\d+\.\d+\.\d+\.\d+)",
            )
            self.assertNotIn("error", result, f"unexpected error: {result}")
            self.assertEqual(result["total_matches"], 6)
            self.assertEqual(result["unique_groups"], 3)
            self.assertEqual(result["top"][0], {"value": "1.1.1.1", "count": 3})
        finally:
            self._r.delete(key)

    def test_systemd_unit_aggregation(self):
        """foo.service×4 > bar.service×1 → top[0]==foo.service,count==4"""
        key = "ctx:test_facet_tool:unit_test"
        content = "\n".join([
            "foo.service: Failed with result 'exit-code'",
            "foo.service: Failed with result 'exit-code'",
            "bar.service: Failed with result 'exit-code'",
            "foo.service: Failed with result 'exit-code'",
            "foo.service: Failed with result 'exit-code'",
        ])
        self._r.set(key, content)
        try:
            result = self._aggregate(
                key, "Failed with result",
                group_by=r"(\S+\.service)",
            )
            self.assertNotIn("error", result, f"unexpected error: {result}")
            self.assertEqual(result["top"][0]["value"], "foo.service")
            self.assertEqual(result["top"][0]["count"], 4)
        finally:
            self._r.delete(key)

    def test_no_group_by_returns_total_and_sample(self):
        """group_by 생략 → total_matches + sample(≤5) + truncated==False"""
        key = "ctx:test_facet_tool:nogroup_test"
        content = "\n".join(
            [f"error: something went wrong line {i}" for i in range(8)]
        )
        self._r.set(key, content)
        try:
            result = self._aggregate(key, "error: something")
            self.assertNotIn("error", result, f"unexpected error: {result}")
            self.assertIn("total_matches", result)
            self.assertEqual(result["total_matches"], 8)
            self.assertIn("sample", result)
            self.assertLessEqual(len(result["sample"]), 5)
            self.assertFalse(result["truncated"])
        finally:
            self._r.delete(key)

    def test_missing_handle_returns_error_dict(self):
        """존재하지 않는 handle → {'error': ...} dict (예외 아님)"""
        result = self._aggregate("ctx:nonexistent:__test_facet__", "anything")
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)

    def test_invalid_group_by_regex_returns_error_dict(self):
        """잘못된 group_by regex '(' → {'error': ...} dict (예외 아님)"""
        key = "ctx:test_facet_tool:badregex_test"
        self._r.set(key, "hello world\nhello again")
        try:
            result = self._aggregate(key, "hello", group_by="(")
            self.assertIsInstance(result, dict)
            self.assertIn("error", result)
        finally:
            self._r.delete(key)


class TestGlobalToolSurfaceUnchanged(unittest.TestCase):
    """글로벌 CONTEXT_TOOL_* 가 facet 추가 후에도 byte-identical 회귀 게이트."""

    def test_global_tool_surface_unchanged(self):
        """CONTEXT_TOOL_SCHEMAS/FUNCTIONS 에 read_context, grep_context 만 포함."""
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from tools import CONTEXT_TOOL_SCHEMAS, CONTEXT_TOOL_FUNCTIONS
            names = [s["function"]["name"] for s in CONTEXT_TOOL_SCHEMAS]
            self.assertEqual(names, ["read_context", "grep_context"])
            self.assertEqual(list(CONTEXT_TOOL_FUNCTIONS.keys()),
                             ["read_context", "grep_context"])
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))

    def test_facet_is_separate(self):
        """FACET_TOOL_* 에 aggregate_context 만 포함 — 글로벌에서 분리."""
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from tools import FACET_TOOL_SCHEMAS, FACET_TOOL_FUNCTIONS
            names = [s["function"]["name"] for s in FACET_TOOL_SCHEMAS]
            self.assertEqual(names, ["aggregate_context"])
            self.assertEqual(list(FACET_TOOL_FUNCTIONS.keys()), ["aggregate_context"])
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))


class TestCallerOptinSignature(unittest.TestCase):
    """make_ollama_native_caller 의 extra_tool_* 파라미터 default None 서명 검증."""

    def test_caller_optin_signature_default_none(self):
        """extra_tool_schemas, extra_tool_fns 의 default 가 모두 None."""
        import inspect
        sys.path.insert(0, str(EXPERIMENTS_DIR))
        try:
            from exp15_context_router.native_ollama_caller import make_ollama_native_caller
            sig = inspect.signature(make_ollama_native_caller)
            self.assertIs(sig.parameters["extra_tool_schemas"].default, None)
            self.assertIs(sig.parameters["extra_tool_fns"].default, None)
        finally:
            sys.path.remove(str(EXPERIMENTS_DIR))


if __name__ == "__main__":
    unittest.main()
