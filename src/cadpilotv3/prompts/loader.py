from pathlib import Path

from cadpilotv3.config import get_settings


def get_prompt_root() -> Path:
    settings = get_settings()
    return Path(settings.cad_prompt_dir)


def read_prompt(relative_path: str) -> str:
    prompt_path = get_prompt_root() / relative_path
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8").strip()


def read_system_prompt(name: str) -> str:
    return read_prompt(f"system/{name}.md")


def read_example_prompt(name: str) -> str:
    return read_prompt(f"examples/{name}.md")


def compose_prompt(system_name: str, example_name: str | None = None) -> str:
    system_prompt = read_system_prompt(system_name)

    if example_name is None:
        return system_prompt

    example_prompt = read_example_prompt(example_name)
    return f"{system_prompt}\n\n---\n\n{example_prompt}"