from __future__ import annotations

from pathlib import Path

from cadpilotv3.config.settings import AppSettings


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt file cannot be found."""


def get_prompt_root(settings: AppSettings) -> Path:
    return Path(settings.cad_prompt_dir).resolve()


def get_prompt_path(settings: AppSettings, prompt_name: str) -> Path:
    root = get_prompt_root(settings)

    candidates = [
        root / prompt_name,
        root / "system" / prompt_name,
        root / "examples" / prompt_name,
    ]

    for prompt_path in candidates:
        if prompt_path.exists():
            return prompt_path

    searched = "\n".join(str(path) for path in candidates)
    raise PromptNotFoundError(
        f"Prompt file not found: {prompt_name}\nSearched:\n{searched}"
    )


def load_prompt_text(settings: AppSettings, prompt_name: str) -> str:
    prompt_path = get_prompt_path(settings, prompt_name)
    return prompt_path.read_text(encoding="utf-8")


def render_prompt(template: str, **kwargs: object) -> str:
    return template.format(**kwargs)