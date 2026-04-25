"""Critic (B) prompt adapter."""

from __future__ import annotations

from typing import Any

from agents.base import RoleAgent


class CriticAgent(RoleAgent):
    role_name = "B"

    def _build_messages(
        self,
        problem: str,
        assertions: list[dict],
        handoff_a2b: dict | None = None,
        phase_args: tuple[int, int] | None = None,
    ) -> list[dict]:
        if phase_args is not None:
            from system_prompt import build_critic_prompt_with_phase

            return build_critic_prompt_with_phase(
                problem=problem,
                assertions=assertions,
                handoff_a2b=handoff_a2b,
                cycle=phase_args[0],
                max_cycles=phase_args[1],
            )

        from system_prompt import build_critic_prompt

        return build_critic_prompt(
            problem=problem,
            assertions=assertions,
            handoff_a2b=handoff_a2b,
        )

    def _post_parse_check(self, parsed: dict[str, Any]) -> str | None:
        # Phase 1: semantic checks belong to the caller (run_abc_chain) — base behavior preserved.
        return None
