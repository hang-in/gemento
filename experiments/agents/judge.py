"""Judge (C) prompt adapter."""

from __future__ import annotations

from typing import Any

from agents.base import RoleAgent


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
            handoff_b2c=handoff_b2c,
        )

    def _post_parse_check(self, parsed: dict[str, Any]) -> str | None:
        # Phase 1: semantic checks belong to the caller (run_abc_chain) — base behavior preserved.
        return None
