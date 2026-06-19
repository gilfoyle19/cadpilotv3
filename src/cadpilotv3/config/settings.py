from functools import lru_cache
from typing import Literal

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
    llm_model: str = "gpt-4.1"
    llm_reasoning_model: str = "gpt-4.1"
    llm_critic_model: str = "gpt-4.1"
    llm_code_model: str = "gpt-5.5"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 16000
    llm_structured_max_tokens: int = 5000
    llm_planner_max_tokens: int = 12000
    llm_critic_max_tokens: int = 6000
    llm_summary_max_tokens: int = 4000
    llm_code_max_tokens: int | None = None
    llm_timeout_seconds: int = 120
    llm_streaming: bool = Truey
    llm_trace_outputs: bool = True

    intent_web_research_enabled: bool = True
    intent_web_research_model: str | None = None
    intent_web_research_context_size: Literal["low", "medium", "high"] = "low"
    intent_web_research_max_output_tokens: int = 1200
    intent_web_research_timeout_seconds: int = 45

    openai_api_key: str | None = None
    openai_base_url: str | None = None

    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_http_referer: str | None = None
    openrouter_x_title: str | None = None

    anthropic_api_key: str | None = None

    log_level: str = "INFO"
    log_json_logs: bool = False
    log_include_timestamps: bool = True

    cad_environment: str = "development"
    cad_max_repair_attempts: int = 2
    cad_max_critic_a_attempts: int = 2
    cad_max_critic_b_attempts: int = 2
    cad_artifacts_dir: str = "artifacts"
    cad_prompt_dir: str = "src/cadpilotv3/prompts"
    cad_enable_async: bool = True
    cad_enable_streaming: bool = True
    cad_enable_design_synthesis: bool = False
    cad_enable_conditional_critic_b: bool = False
    cad_enable_llm_export_summary: bool = True
    cad_enable_direct_repair_codegen: bool = False

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

    @computed_field
    @property
    def llm_profiles(self) -> dict:
        return {
            "structured": {
                "provider": self.llm_provider,
                "model": self.llm_model,
                "temperature": 0.0,
                "max_tokens": self.llm_structured_max_tokens,
                "timeout_seconds": self.llm_timeout_seconds,
                "streaming": self.llm_streaming,
            },
            "planner": {
                "provider": self.llm_provider,
                "model": self.llm_reasoning_model,
                "temperature": self.llm_temperature,
                "max_tokens": self.llm_planner_max_tokens,
                "timeout_seconds": self.llm_timeout_seconds,
                "streaming": self.llm_streaming,
            },
            "coder": {
                "provider": self.llm_provider,
                "model": self.llm_code_model,
                "temperature": 0.0,
                "max_tokens": self.llm_code_max_tokens or self.llm_max_tokens,
                "timeout_seconds": self.llm_timeout_seconds,
                "streaming": self.llm_streaming,
            },
            "critic": {
                "provider": self.llm_provider,
                "model": self.llm_critic_model,
                "temperature": 0.0,
                "max_tokens": self.llm_critic_max_tokens,
                "timeout_seconds": self.llm_timeout_seconds,
                "streaming": self.llm_streaming,
            },
            "summary": {
                "provider": self.llm_provider,
                "model": self.llm_model,
                "temperature": 0.0,
                "max_tokens": self.llm_summary_max_tokens,
                "timeout_seconds": self.llm_timeout_seconds,
                "streaming": self.llm_streaming,
            },
        }


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()
