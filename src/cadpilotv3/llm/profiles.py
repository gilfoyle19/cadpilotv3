from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class LLMProfile(StrEnum):
    STRUCTURED = "structured"
    PLANNER = "planner"
    CODER = "coder"
    CRITIC = "critic"
    SUMMARY = "summary"


class AgentName(StrEnum):
    INTENT_SPEC = "intent_spec_agent"
    DESIGN_SYNTHESIS = "design_synthesis_agent"
    GEOMETRY_PLANNER = "geometry_planner_agent"
    CRITIC_A = "critic_checkpoint_a"
    PARAMETER = "parameter_agent"
    CODEGEN = "code_generation_agent"
    EXECUTION_VALIDATION = "execution_validation"
    REPAIR = "repair_agent"
    CRITIC_B = "critic_checkpoint_b"
    EXPORT_SUMMARY = "export_summary_agent"


AGENT_TO_PROFILE: dict[AgentName, LLMProfile] = {
    AgentName.INTENT_SPEC: LLMProfile.STRUCTURED,
    AgentName.DESIGN_SYNTHESIS: LLMProfile.PLANNER,
    AgentName.GEOMETRY_PLANNER: LLMProfile.PLANNER,
    AgentName.CRITIC_A: LLMProfile.CRITIC,
    AgentName.PARAMETER: LLMProfile.STRUCTURED,
    AgentName.CODEGEN: LLMProfile.CODER,
    AgentName.EXECUTION_VALIDATION: LLMProfile.CODER,
    AgentName.REPAIR: LLMProfile.CODER,
    AgentName.CRITIC_B: LLMProfile.CRITIC,
    AgentName.EXPORT_SUMMARY: LLMProfile.SUMMARY,
}


@dataclass(frozen=True)
class LLMRuntimeConfig:
    provider: str
    model: str
    temperature: float
    max_tokens: int
    timeout: int
    streaming: bool
