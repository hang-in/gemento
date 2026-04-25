"""Role-agent exports."""

from agents.base import AgentResult, RoleAgent
from agents.critic import CriticAgent
from agents.judge import JudgeAgent
from agents.proposer import ProposerAgent

__all__ = [
    "AgentResult",
    "RoleAgent",
    "ProposerAgent",
    "CriticAgent",
    "JudgeAgent",
]
