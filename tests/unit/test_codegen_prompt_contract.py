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


def test_codegen_prompt_defines_strict_script_skeleton() -> None:
    system_prompt = (
        PROMPT_ROOT / "system" / "code_generation_infill.md"
    ).read_text(encoding="utf-8")

    assert "first line must be exactly `import cadquery as cq`" in system_prompt
    assert "Define exactly one public entry point" in system_prompt
    assert "REQUIRED MAIN BLOCK SHAPE" in system_prompt
    assert "model = build_part()" in system_prompt
    assert "assembly = build_assembly()" in system_prompt
    assert "validate_geometry(model)" in system_prompt
    assert "export_all(model, \"./output\")" in system_prompt
    assert "validate_geometry(assembly)" in system_prompt
    assert "export_all(assembly, \"./output\")" in system_prompt
    assert "do not call exporters.export" in system_prompt


def test_codegen_prompt_makes_generated_validation_robust() -> None:
    system_prompt = (
        PROMPT_ROOT / "system" / "code_generation_infill.md"
    ).read_text(encoding="utf-8")

    assert "validate_geometry must be side-effect-free" in system_prompt
    assert "must not use assert statements or raise exceptions" in system_prompt
    assert "positive volume" in system_prompt
    assert "positive bounding-box dimensions" in system_prompt
    assert "expected_bounding_box" in system_prompt
    assert "dimensions_match" in system_prompt
    assert "volume_ratio" in system_prompt
    assert "operation-local before/after" in system_prompt
    assert "checks near the cut operation" in system_prompt


def test_critic_b_prompt_uses_child_metadata_for_spatial_fidelity() -> None:
    critic_b_prompt = (
        PROMPT_ROOT / "system" / "critic_checkpoint_b.md"
    ).read_text(encoding="utf-8")
    critic_b_examples = (
        PROMPT_ROOT / "examples" / "critic_b_examples.md"
    ).read_text(encoding="utf-8")

    assert "child_metadata" in critic_b_prompt
    assert "center_mm" in critic_b_prompt
    assert "stacked parts accidentally side-by-side" in critic_b_prompt.lower()
    assert "coaxial fasteners/spacers" in critic_b_prompt.lower()
    assert "Side-by-Side Parts That Should Be Stacked" in critic_b_examples
    assert "base center [0,0,15] and lid center [105,0,1.5]" in critic_b_examples


def test_codegen_and_critic_prompts_use_face_axis_contracts() -> None:
    codegen_prompt = (
        PROMPT_ROOT / "system" / "code_generation_infill.md"
    ).read_text(encoding="utf-8")
    critic_b_prompt = (
        PROMPT_ROOT / "system" / "critic_checkpoint_b.md"
    ).read_text(encoding="utf-8")

    for prompt in (codegen_prompt, critic_b_prompt):
        assert "assembly_axes" in prompt
        assert "part_frames" in prompt
        assert "assembly_placement_constraints" in prompt
        assert "alignment_groups" in prompt
        assert "forbidden_layouts" in prompt

    assert "binding spatial contracts" in codegen_prompt
    assert "Planned face-axis contract" in critic_b_prompt
