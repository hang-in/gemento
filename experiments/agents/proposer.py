"""Proposer (A) prompt adapter."""

from __future__ import annotations

from agents.base import RoleAgent


class ProposerAgent(RoleAgent):
    role_name = "A"

    def _build_messages(
        self,
        tattoo_json: str,
        phase_args: tuple[int, int] | None = None,
        chunked: dict | None = None,
    ) -> list[dict]:
        if chunked is not None:
            from system_prompt import build_prompt_chunked

            return build_prompt_chunked(
                tattoo_json=tattoo_json,
                current_chunk=chunked["current_chunk"],
                chunk_id=chunked["chunk_id"],
            )

        if phase_args is not None:
            from system_prompt import build_prompt_with_phase

            return build_prompt_with_phase(
                tattoo_json,
                cycle=phase_args[0],
                max_cycles=phase_args[1],
            )

        from system_prompt import build_prompt

        return build_prompt(tattoo_json)
