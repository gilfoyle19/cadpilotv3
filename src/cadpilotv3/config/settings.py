from functools import lru_cache

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "cadpilotv3"
    app_version: str = "0.1.0"

    langsmith_tracing: bool = True
    langsmith_project: str = "cadpilotv3"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str | None = None

    llm_provider: str = "openai"
    llm_model: str = "gpt-4.1-mini"
    llm_reasoning_model: str = "gpt-4.1"
    llm_critic_model: str = "gpt-4.1"
    llm_code_model: str = "gpt-4.1"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 4000
    llm_timeout_seconds: int = 120
    llm_streaming: bool = True

    log_level: str = "INFO"
    log_json_logs: bool = False
    log_include_timestamps: bool = True

    cad_environment: str = "development"
    cad_max_repair_attempts: int = 3
    cad_max_critic_a_attempts: int = 2
    cad_max_critic_b_attempts: int = 2
    cad_artifacts_dir: str = "artifacts"
    cad_prompt_dir: str = "src/cadpilotv3/prompts"
    cad_enable_async: bool = True
    cad_enable_streaming: bool = True

    exec_sandbox_enabled: bool = True
    exec_cadquery_python_bin: str = "python"
    exec_export_step: bool = True
    exec_export_stl: bool = True
    exec_export_dxf: bool = False
    exec_execution_timeout_seconds: int = 180

    @computed_field
    @property
    def langsmith(self) -> dict:
        return {
            "tracing": self.langsmith_tracing,
            "project": self.langsmith_project,
            "endpoint": self.langsmith_endpoint,
            "api_key": self.langsmith_api_key,
        }


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()