from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from cadpilotv3.config.settings import AppSettings


class PromptNotFoundError(FileNotFoundError):
    """Raised when a prompt file cannot be found."""


def get_prompt_root(settings: AppSettings) -> Path:
    return Path(settings.cad_prompt_dir).resolve()


def get_prompt_path(settings: AppSettings, prompt_name: str) -> Path:
    return _get_prompt_path_cached(str(get_prompt_root(settings)), prompt_name)


@lru_cache(maxsize=256)
def _get_prompt_path_cached(prompt_root: str, prompt_name: str) -> Path:
    root = Path(prompt_root)
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
    stat = prompt_path.stat()
    return _read_prompt_text_cached(
        str(prompt_path),
        stat.st_mtime_ns,
        stat.st_size,
    )


@lru_cache(maxsize=256)
def _read_prompt_text_cached(
    prompt_path: str,
    mtime_ns: int,
    size_bytes: int,
) -> str:
    return Path(prompt_path).read_text(encoding="utf-8")


def clear_prompt_cache() -> None:
    _get_prompt_path_cached.cache_clear()
    _read_prompt_text_cached.cache_clear()


def render_prompt(template: str, **kwargs: object) -> str:
    return template.format(**kwargs)
