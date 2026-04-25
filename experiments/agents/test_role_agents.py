"""Unit tests for role-agent adapters."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from agents import CriticAgent, JudgeAgent, ProposerAgent


class _BaseHelpers:
    def _ok(self, payload_json: str) -> tuple[str, list[dict]]:
        return (payload_json, [])

    def _empty(self) -> tuple[str, list[dict]]:
        return ("", [])


class TestProposerAgent(unittest.TestCase, _BaseHelpers):
    def setUp(self) -> None:
        self.agent = ProposerAgent()
        self.kwargs = {"tattoo_json": '{"task_id":"t1"}'}

    def test_normal_call_returns_parsed(self) -> None:
        payload = '{"reasoning":"ok","new_assertions":[],"final_answer":null}'
        with patch("orchestrator.call_model", return_value=self._ok(payload)):
            result = self.agent.call(**self.kwargs)
        self.assertIsNone(result.error)
        self.assertEqual(result.parsed["reasoning"], "ok")

    def test_retry_on_parse_fail_then_success(self) -> None:
        side_effects = [
            self._ok("not json"),
            self._ok('{"reasoning":"ok","new_assertions":[],"final_answer":null}'),
        ]
        with patch("orchestrator.call_model", side_effect=side_effects):
            result = self.agent.call(max_retries=1, **self.kwargs)
        self.assertIsNone(result.error)
        self.assertEqual(result.parsed["reasoning"], "ok")

    def test_parse_fail_after_all_retries(self) -> None:
        with patch("orchestrator.call_model", return_value=self._ok("garbage")):
            result = self.agent.call(max_retries=1, **self.kwargs)
        self.assertIsNone(result.parsed)
        self.assertEqual(result.error, "JSON parse failed")

    def test_empty_response(self) -> None:
        with patch("orchestrator.call_model", return_value=self._empty()):
            result = self.agent.call(max_retries=1, **self.kwargs)
        self.assertIsNone(result.parsed)
        self.assertEqual(result.error, "JSON parse failed")

    def test_call_model_raises_propagated(self) -> None:
        with patch("orchestrator.call_model", side_effect=RuntimeError("network down")):
            result = self.agent.call(max_retries=0, **self.kwargs)
        self.assertIsNone(result.parsed)
        self.assertIn("network down", result.error)

    def test_phase_args_uses_phase_builder(self) -> None:
        with patch("system_prompt.build_prompt_with_phase") as mock_build:
            mock_build.return_value = [{"role": "user", "content": "x"}]
            with patch("orchestrator.call_model", return_value=self._ok('{"reasoning":"ok"}')):
                self.agent.call(tattoo_json="{}", phase_args=(3, 8))
        mock_build.assert_called_once_with("{}", cycle=3, max_cycles=8)

    def test_chunked_uses_chunked_builder(self) -> None:
        with patch("system_prompt.build_prompt_chunked") as mock_build:
            mock_build.return_value = [{"role": "user", "content": "x"}]
            with patch("orchestrator.call_model", return_value=self._ok('{"reasoning":"ok"}')):
                self.agent.call(
                    tattoo_json="{}",
                    chunked={"current_chunk": "chunk body", "chunk_id": 4},
                )
        mock_build.assert_called_once_with(
            tattoo_json="{}",
            current_chunk="chunk body",
            chunk_id=4,
        )


class TestCriticAgent(unittest.TestCase, _BaseHelpers):
    def setUp(self) -> None:
        self.agent = CriticAgent()
        self.kwargs = {
            "problem": "test problem",
            "assertions": [
                {
                    "id": "a01",
                    "content": "x",
                    "confidence": 0.8,
                    "status": "active",
                    "source_loop": 0,
                }
            ],
            "handoff_a2b": None,
            "phase_args": None,
        }

    def test_normal_call_returns_parsed(self) -> None:
        with patch("orchestrator.call_model", return_value=self._ok('{"judgments": []}')):
            result = self.agent.call(**self.kwargs)
        self.assertEqual(result.parsed, {"judgments": []})
        self.assertIsNone(result.error)

    def test_retry_on_parse_fail_then_success(self) -> None:
        side_effects = [self._ok("not json"), self._ok('{"judgments": [{"status": "valid"}]}')]
        with patch("orchestrator.call_model", side_effect=side_effects):
            result = self.agent.call(max_retries=1, **self.kwargs)
        self.assertEqual(len(result.parsed["judgments"]), 1)
        self.assertIsNone(result.error)

    def test_parse_fail_after_all_retries(self) -> None:
        with patch("orchestrator.call_model", return_value=self._ok("garbage")):
            result = self.agent.call(max_retries=1, **self.kwargs)
        self.assertIsNone(result.parsed)
        self.assertEqual(result.error, "JSON parse failed")

    def test_empty_response(self) -> None:
        with patch("orchestrator.call_model", return_value=self._empty()):
            result = self.agent.call(max_retries=1, **self.kwargs)
        self.assertIsNone(result.parsed)
        self.assertEqual(result.error, "JSON parse failed")

    def test_call_model_raises_propagated(self) -> None:
        with patch("orchestrator.call_model", side_effect=RuntimeError("network down")):
            result = self.agent.call(max_retries=0, **self.kwargs)
        self.assertIsNone(result.parsed)
        self.assertIn("network down", result.error)

    def test_phase_args_uses_with_phase_builder(self) -> None:
        with patch("system_prompt.build_critic_prompt_with_phase") as mock_build:
            mock_build.return_value = [{"role": "user", "content": "x"}]
            with patch("orchestrator.call_model", return_value=self._ok('{"judgments": []}')):
                self.agent.call(**{**self.kwargs, "phase_args": (3, 8)})
        mock_build.assert_called_once()
        self.assertEqual(mock_build.call_args.kwargs["cycle"], 3)
        self.assertEqual(mock_build.call_args.kwargs["max_cycles"], 8)


class TestJudgeAgent(unittest.TestCase, _BaseHelpers):
    def setUp(self) -> None:
        self.agent = JudgeAgent()
        self.kwargs = {
            "problem": "test",
            "current_phase": "DECOMPOSE",
            "current_critique": {"judgments": []},
            "previous_critique": None,
            "assertion_count": 2,
            "handoff_b2c": None,
            "phase_args": None,
        }

    def test_normal_call(self) -> None:
        payload = '{"converged": true, "next_phase": "INVESTIGATE", "next_directive": "..."}'
        with patch("orchestrator.call_model", return_value=self._ok(payload)):
            result = self.agent.call(**self.kwargs)
        self.assertTrue(result.parsed["converged"])
        self.assertIsNone(result.error)

    def test_retry_on_parse_fail_then_success(self) -> None:
        payload = '{"converged": false, "next_phase": null, "next_directive": "retry"}'
        with patch("orchestrator.call_model", side_effect=[self._ok("bad"), self._ok(payload)]):
            result = self.agent.call(max_retries=1, **self.kwargs)
        self.assertFalse(result.parsed["converged"])
        self.assertIsNone(result.error)

    def test_parse_fail_after_all_retries(self) -> None:
        with patch("orchestrator.call_model", return_value=self._ok("garbage")):
            result = self.agent.call(max_retries=1, **self.kwargs)
        self.assertIsNone(result.parsed)
        self.assertEqual(result.error, "JSON parse failed")

    def test_empty_response(self) -> None:
        with patch("orchestrator.call_model", return_value=self._empty()):
            result = self.agent.call(max_retries=1, **self.kwargs)
        self.assertIsNone(result.parsed)
        self.assertEqual(result.error, "JSON parse failed")

    def test_call_model_raises_propagated(self) -> None:
        with patch("orchestrator.call_model", side_effect=RuntimeError("judge down")):
            result = self.agent.call(max_retries=0, **self.kwargs)
        self.assertIsNone(result.parsed)
        self.assertIn("judge down", result.error)

    def test_phase_args_uses_with_phase_builder(self) -> None:
        payload = '{"converged": false, "next_phase": null, "next_directive": "x"}'
        with patch("system_prompt.build_judge_prompt_with_phase") as mock_build:
            mock_build.return_value = [{"role": "user", "content": "x"}]
            with patch("orchestrator.call_model", return_value=self._ok(payload)):
                self.agent.call(**{**self.kwargs, "phase_args": (2, 5)})
        mock_build.assert_called_once()
        self.assertEqual(mock_build.call_args.kwargs["cycle"], 2)
        self.assertEqual(mock_build.call_args.kwargs["max_cycles"], 5)


if __name__ == "__main__":
    unittest.main()
