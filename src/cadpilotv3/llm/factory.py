from __future__ import annotations

import logging
from functools import lru_cache

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm.profiles import (
    AGENT_TO_PROFILE,
    AgentName,
    LLMProfile,
    LLMRuntimeConfig,
)

logger = logging.getLogger(__name__)


class LLMFactoryError(RuntimeError):
    """Raised when LLM creation fails due to invalid or unsupported configuration."""


class LLMFactory:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def get_for_agent(self, agent_name: AgentName) -> BaseChatModel:
        profile = AGENT_TO_PROFILE[agent_name]
        return self.get_for_profile(profile)

    def get_for_profile(self, profile: LLMProfile) -> BaseChatModel:
        runtime = self._resolve_runtime(profile)

        logger.info(
            "Creating LLM client",
            extra={
                "profile": profile.value,
                "provider": runtime.provider,
                "model": runtime.model,
                "temperature": runtime.temperature,
                "max_tokens": runtime.max_tokens,
                "timeout": runtime.timeout,
                "streaming": runtime.streaming,
            },
        )

        return self._build_model(runtime)

    def _resolve_runtime(self, profile: LLMProfile) -> LLMRuntimeConfig:
        try:
            profile_config = self.settings.llm_profiles[profile.value]
        except KeyError as exc:
            raise LLMFactoryError(f"Missing llm profile config for '{profile.value}'") from exc

        return LLMRuntimeConfig(
            provider=profile_config["provider"],
            model=profile_config["model"],
            temperature=profile_config["temperature"],
            max_tokens=profile_config["max_tokens"],
            timeout=profile_config["timeout_seconds"],
            streaming=profile_config["streaming"],
        )

    def _build_model(self, runtime: LLMRuntimeConfig) -> BaseChatModel:
        provider = runtime.provider.lower()

        if provider == "openai":
            return self._build_openai(runtime)

        if provider == "openrouter":
            return self._build_openrouter(runtime)

        if provider == "anthropic":
            return self._build_anthropic(runtime)

        raise LLMFactoryError(
            f"Unsupported LLM provider '{runtime.provider}'. "
            "Supported providers: openai, openrouter, anthropic."
        )

    def _build_openai(self, runtime: LLMRuntimeConfig) -> BaseChatModel:
        kwargs = {
            "model": runtime.model,
            "temperature": runtime.temperature,
            "max_tokens": runtime.max_tokens,
            "timeout": runtime.timeout,
            "streaming": runtime.streaming,
        }

        if self.settings.openai_api_key:
            kwargs["api_key"] = self.settings.openai_api_key

        if self.settings.openai_base_url:
            kwargs["base_url"] = self.settings.openai_base_url

        return ChatOpenAI(**kwargs)

    def _build_openrouter(self, runtime: LLMRuntimeConfig) -> BaseChatModel:
        if not self.settings.openrouter_api_key:
            raise LLMFactoryError(
                "openrouter_api_key is required when llm_provider='openrouter'"
            )

        kwargs = {
            "model": runtime.model,
            "temperature": runtime.temperature,
            "max_tokens": runtime.max_tokens,
            "timeout": runtime.timeout,
            "streaming": runtime.streaming,
            "api_key": self.settings.openrouter_api_key,
            "base_url": self.settings.openrouter_base_url,
        }

        headers = {}
        if self.settings.openrouter_http_referer:
            headers["HTTP-Referer"] = self.settings.openrouter_http_referer
        if self.settings.openrouter_x_title:
            headers["X-Title"] = self.settings.openrouter_x_title

        if headers:
            kwargs["default_headers"] = headers

        return ChatOpenAI(**kwargs)

    def _build_anthropic(self, runtime: LLMRuntimeConfig) -> BaseChatModel:
        if not self.settings.anthropic_api_key:
            raise LLMFactoryError(
                "anthropic_api_key is required when llm_provider='anthropic'"
            )

        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError as exc:
            raise LLMFactoryError(
                "langchain-anthropic is not installed. "
                "Install it to use Anthropic models."
            ) from exc

        return ChatAnthropic(
            model=runtime.model,
            temperature=runtime.temperature,
            max_tokens=runtime.max_tokens,
            timeout=runtime.timeout,
            streaming=runtime.streaming,
            api_key=self.settings.anthropic_api_key,
        )


@lru_cache(maxsize=1)
def get_llm_factory(settings: AppSettings) -> LLMFactory:
    return LLMFactory(settings)