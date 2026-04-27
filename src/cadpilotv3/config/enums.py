from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class RoutingTarget(str, Enum):
    PARAMETER_AGENT = "parameter_agent"
    GEOMETRY_PLANNER_AGENT = "geometry_planner_agent"
    CODE_GENERATION_AGENT = "code_generation_agent"
    CRITIC_CHECKPOINT_B = "critic_checkpoint_b"
    EXPORT_SUMMARY_AGENT = "export_summary_agent"


class CriticRouting(str, Enum):
    PROCEED = "proceed"
    REPLAN = "replan"
    EXPORT = "export"
    PATCH = "patch"
    CONDITIONAL_PASS = "conditional_pass"


class RepairAction(str, Enum):
    PATCH = "patch"
    REPLAN = "replan"