from cadpilotv3.config.settings import AppSettings

PIPELINE_MODE_ENV_VARS = (
    "CAD_ENABLE_DESIGN_SYNTHESIS",
    "CAD_ENABLE_CONDITIONAL_CRITIC_B",
    "CAD_ENABLE_LLM_EXPORT_SUMMARY",
    "CAD_ENABLE_DIRECT_REPAIR_CODEGEN",
)


def test_pipeline_mode_flags_default_to_current_behavior(monkeypatch) -> None:
    for env_var in PIPELINE_MODE_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)

    settings = AppSettings(_env_file=None)

    assert settings.cad_enable_design_synthesis is False
    assert settings.cad_enable_conditional_critic_b is False
    assert settings.cad_enable_llm_export_summary is True
    assert settings.cad_enable_direct_repair_codegen is False


def test_pipeline_mode_flags_can_be_overridden_from_env(monkeypatch) -> None:
    monkeypatch.setenv("CAD_ENABLE_DESIGN_SYNTHESIS", "true")
    monkeypatch.setenv("CAD_ENABLE_CONDITIONAL_CRITIC_B", "true")
    monkeypatch.setenv("CAD_ENABLE_LLM_EXPORT_SUMMARY", "false")
    monkeypatch.setenv("CAD_ENABLE_DIRECT_REPAIR_CODEGEN", "true")

    settings = AppSettings(_env_file=None)

    assert settings.cad_enable_design_synthesis is True
    assert settings.cad_enable_conditional_critic_b is True
    assert settings.cad_enable_llm_export_summary is False
    assert settings.cad_enable_direct_repair_codegen is True
