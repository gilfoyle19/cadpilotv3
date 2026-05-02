from __future__ import annotations

from pathlib import Path

from cadpilotv3.config.settings import AppSettings


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt file cannot be found."""


def get_prompt_dir(settings: AppSettings) -> Path:
    return Path(settings.cad_prompt_dir).resolve()


def get_prompt_path(settings: AppSettings, prompt_name: str) -> Path:
    prompt_path = get_prompt_dir(settings) / prompt_name
    if not prompt_path.exists():
        raise PromptNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path


def load_prompt_text(settings: AppSettings, prompt_name: str) -> str:
    prompt_path = get_prompt_path(settings, prompt_name)
    return prompt_path.read_text(encoding="utf-8")


def render_prompt(template: str, **kwargs: object) -> str:
    return template.format(**kwargs)