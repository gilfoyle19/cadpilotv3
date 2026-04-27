from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")

    provider: str = "openai"
    model: str = "gpt-4.1-mini"
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout_seconds: int = 120
    streaming: bool = True
    reasoning_model: str = "gpt-4.1"
    critic_model: str = "gpt-4.1"
    code_model: str = "gpt-4.1"


class LangSmithSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LANGSMITH_", extra="ignore")

    tracing: bool = True
    project: str = "cadpilotv3"
    endpoint: str = "https://api.smith.langchain.com"
    api_key: str | None = None


class LoggingSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LOG_", extra="ignore")

    level: str = "INFO"
    json_logs: bool = False
    include_timestamps: bool = True


class RuntimeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CAD_", extra="ignore")

    environment: str = "development"
    max_repair_attempts: int = 3
    max_critic_a_attempts: int = 2
    max_critic_b_attempts: int = 2
    artifacts_dir: str = "artifacts"
    prompt_dir: str = "src/cadpilotv3/prompts"
    enable_async: bool = True
    enable_streaming: bool = True


class ExecutionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="EXEC_", extra="ignore")

    sandbox_enabled: bool = True
    cadquery_python_bin: str = "python"
    export_step: bool = True
    export_stl: bool = True
    export_dxf: bool = False
    execution_timeout_seconds: int = 180


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "cadpilotv3"
    app_version: str = "0.1.0"

    llm: LLMSettings = Field(default_factory=LLMSettings)
    langsmith: LangSmithSettings = Field(default_factory=LangSmithSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    runtime: RuntimeSettings = Field(default_factory=RuntimeSettings)
    execution: ExecutionSettings = Field(default_factory=ExecutionSettings)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()