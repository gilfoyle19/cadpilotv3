from cadpilotv3.config.settings import AppSettings


def test_llm_profiles_use_per_profile_max_token_caps() -> None:
    settings = AppSettings(
        llm_max_tokens=16000,
        llm_structured_max_tokens=4500,
        llm_planner_max_tokens=7500,
        llm_critic_max_tokens=5500,
        llm_summary_max_tokens=3500,
    )

    profiles = settings.llm_profiles

    assert profiles["structured"]["max_tokens"] == 4500
    assert profiles["planner"]["max_tokens"] == 7500
    assert profiles["critic"]["max_tokens"] == 5500
    assert profiles["summary"]["max_tokens"] == 3500
    assert profiles["coder"]["max_tokens"] == 16000


def test_llm_code_max_tokens_can_override_global_code_budget() -> None:
    settings = AppSettings(
        llm_max_tokens=16000,
        llm_code_max_tokens=12000,
    )

    assert settings.llm_profiles["coder"]["max_tokens"] == 12000
