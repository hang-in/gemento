"""RoleAgent base and shared result container."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time
from typing import Any


@dataclass
class AgentResult:
    """Result of a single role-agent call."""

    parsed: dict | None = None
    raw: str = ""
    duration_ms: int = 0
    error: str | None = None
    tool_calls: list[dict] = field(default_factory=list)


class RoleAgent(ABC):
    """Shared retry/parse behavior for role-specific prompt adapters."""

    role_name: str = "abstract"

    @abstractmethod
    def _build_messages(self, **kwargs: Any) -> list[dict]:
        raise NotImplementedError

    def _post_parse_check(self, parsed: dict) -> str | None:
        return None

    def call(
        self,
        max_retries: int = 1,
        tools: list[dict] | None = None,
        tool_functions: dict | None = None,
        **kwargs: Any,
    ) -> AgentResult:
        from orchestrator import call_model, extract_json_from_response

        result = AgentResult()
        messages = self._build_messages(**kwargs)
        start = time.time()

        for attempt in range(max_retries + 1):
            try:
                raw, tool_calls = call_model(
                    messages,
                    tools=tools,
                    tool_functions=tool_functions,
                )
                result.raw = raw
                result.tool_calls = tool_calls
                parsed = extract_json_from_response(raw)
            except Exception as exc:
                result.raw = ""
                result.error = str(exc)
                parsed = None

            if parsed:
                result.parsed = parsed
                result.error = self._post_parse_check(parsed)
                if result.error is None:
                    break

            if attempt < max_retries:
                print(f"    {self.role_name} ↻ retry")

        if result.parsed is None and result.error is None:
            result.error = "JSON parse failed"

        result.duration_ms = int((time.time() - start) * 1000)
        return result
