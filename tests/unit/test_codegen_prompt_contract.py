from pathlib import Path

PROMPT_ROOT = Path("src/cadpilotv3/prompts")


def test_codegen_prompts_standardize_single_part_entrypoint() -> None:
    system_prompt = (
        PROMPT_ROOT / "system" / "code_generation_infill.md"
    ).read_text(encoding="utf-8")
    infill_examples = (
        PROMPT_ROOT / "examples" / "codegen_infill_examples.md"
    ).read_text(encoding="utf-8")
    skeleton_examples = (
        PROMPT_ROOT / "examples" / "codegen_skeleton_examples.md"
    ).read_text(encoding="utf-8")

    assert "define build_part() -> cq.Workplane" in system_prompt
    assert "define build_assembly() -> cq.Assembly" in system_prompt
    assert "model = make_" not in infill_examples
    assert "model = make_" not in skeleton_examples
    assert "def build_part() -> cq.Workplane:" in infill_examples
    assert "def build_assembly() -> cq.Assembly:" in infill_examples
