INTENT_SPEC_AGENT = "intent_spec_agent"
GEOMETRY_PLANNER_AGENT = "geometry_planner_agent"
CRITIC_CHECKPOINT_A = "critic_checkpoint_a"
PARAMETER_AGENT = "parameter_agent"
CODE_GENERATION_AGENT = "code_generation_agent"
EXECUTION_VALIDATION_AGENT = "execution_validation"
REPAIR_AGENT = "repair_agent"
CRITIC_CHECKPOINT_B = "critic_checkpoint_b"
EXPORT_SUMMARY_AGENT = "export_summary_agent"

PATCH_ERROR_CLASSES = {
    "syntax_error",
    "api_misuse",
    "parameter_overflow",
    "fillet_radius_overflow",
    "export_format_error",
}

REPLAN_ERROR_CLASSES = {
    "non_manifold_geometry",
    "assembly_misalignment",
    "topology_error",
    "zero_volume_solid",
}