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


def test_codegen_and_repair_prompts_forbid_implicit_hole_helpers() -> None:
    codegen_prompt = (
        PROMPT_ROOT / "system" / "code_generation_infill.md"
    ).read_text(encoding="utf-8")
    repair_prompt = (
        PROMPT_ROOT / "system" / "repair_agent.md"
    ).read_text(encoding="utf-8")

    for prompt in (codegen_prompt, repair_prompt):
        assert "Workplane.hole()" in prompt
        assert "Workplane.cboreHole()" in prompt
        assert "Workplane.cskHole()" in prompt
        assert "explicit cutter solids" in prompt
        assert ".cut()" in prompt


def test_prompts_include_canonical_explicit_cutter_patterns() -> None:
    codegen_prompt = (
        PROMPT_ROOT / "system" / "code_generation_infill.md"
    ).read_text(encoding="utf-8")
    repair_prompt = (
        PROMPT_ROOT / "system" / "repair_agent.md"
    ).read_text(encoding="utf-8")
    cheatsheet = (PROMPT_ROOT / "cheatsheet.md").read_text(encoding="utf-8")

    for prompt in (codegen_prompt, cheatsheet):
        assert "canonical explicit cutter patterns" in prompt.lower()
        assert "def make_z_cylindrical_cutter" in prompt
        assert "def cut_through_hole_z" in prompt
        assert "def cut_counterbore_z" in prompt
        assert "def cut_countersink_z" in prompt
        assert "cq.Solid.makeCone" in prompt

    assert "make_z_cylindrical_cutter" in repair_prompt
    assert "cq.Solid.makeCone" in repair_prompt
