from types import SimpleNamespace

from cadpilotv3.shared.prompt_utils import (
    clear_prompt_cache,
    get_prompt_path,
    load_prompt_text,
)


def test_load_prompt_text_caches_file_reads(tmp_path, monkeypatch) -> None:
    clear_prompt_cache()
    prompt_path = tmp_path / "system" / "agent.md"
    prompt_path.parent.mkdir()
    prompt_path.write_text("cached prompt", encoding="utf-8")
    settings = SimpleNamespace(cad_prompt_dir=str(tmp_path))

    read_count = 0
    original_read_text = type(prompt_path).read_text

    def counting_read_text(self, *args, **kwargs):
        nonlocal read_count
        read_count += 1
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(type(prompt_path), "read_text", counting_read_text)

    assert load_prompt_text(settings, "agent.md") == "cached prompt"
    assert load_prompt_text(settings, "agent.md") == "cached prompt"
    assert read_count == 1

    clear_prompt_cache()


def test_load_prompt_text_cache_refreshes_when_file_changes(tmp_path) -> None:
    clear_prompt_cache()
    prompt_path = tmp_path / "agent.md"
    prompt_path.write_text("first prompt", encoding="utf-8")
    settings = SimpleNamespace(cad_prompt_dir=str(tmp_path))

    assert load_prompt_text(settings, "agent.md") == "first prompt"

    prompt_path.write_text("second prompt with different size", encoding="utf-8")

    assert load_prompt_text(settings, "agent.md") == "second prompt with different size"

    clear_prompt_cache()


def test_get_prompt_path_caches_resolution_for_same_root_and_prompt(tmp_path, monkeypatch) -> None:
    clear_prompt_cache()
    prompt_path = tmp_path / "examples" / "agent_examples.md"
    prompt_path.parent.mkdir()
    prompt_path.write_text("example prompt", encoding="utf-8")
    settings = SimpleNamespace(cad_prompt_dir=str(tmp_path))

    exists_count = 0
    original_exists = type(prompt_path).exists

    def counting_exists(self):
        nonlocal exists_count
        exists_count += 1
        return original_exists(self)

    monkeypatch.setattr(type(prompt_path), "exists", counting_exists)

    assert get_prompt_path(settings, "agent_examples.md") == prompt_path
    assert get_prompt_path(settings, "agent_examples.md") == prompt_path
    assert exists_count == 3

    clear_prompt_cache()


def test_clear_prompt_cache_forces_reload(tmp_path, monkeypatch) -> None:
    clear_prompt_cache()
    prompt_path = tmp_path / "agent.md"
    prompt_path.write_text("cached prompt", encoding="utf-8")
    settings = SimpleNamespace(cad_prompt_dir=str(tmp_path))

    read_count = 0
    original_read_text = type(prompt_path).read_text

    def counting_read_text(self, *args, **kwargs):
        nonlocal read_count
        read_count += 1
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(type(prompt_path), "read_text", counting_read_text)

    assert load_prompt_text(settings, "agent.md") == "cached prompt"
    clear_prompt_cache()
    assert load_prompt_text(settings, "agent.md") == "cached prompt"
    assert read_count == 2

    clear_prompt_cache()
