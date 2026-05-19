from types import SimpleNamespace

from cadpilotv3.agents.repair_agent import RepairAgent
from cadpilotv3.schemas.validation import ErrorLocation, ValidationReport


def test_repair_agent_prompt_includes_relevant_cheatsheet(monkeypatch) -> None:
    captured = {}

    class FakeLLM:
        def invoke(self, prompt: str) -> str:
            captured["prompt"] = prompt
            return """
{
  "action": "patch",
  "error_class": "api_misuse",
  "root_cause": "The script used Workplane.hole where explicit cutter solids are required.",
  "fix_description": "Replace the hole call with an explicit cylindrical cutter.",
  "patch_type": "api",
  "affected_function": "build_part",
  "patched_code": "def build_part():\\n    return cq.Workplane('XY').box(1, 1, 1)",
  "confidence": "high",
  "confidence_note": null
}
"""

    class FakeLLMFactory:
        def get_for_agent(self, _agent_name):
            return FakeLLM()

    prompts = {
        "repair_agent.md": "repair system prompt",
        "repair_agent_examples.md": "repair examples",
        "cheatsheet.md": """
cadquery_cheatsheet:
"All dimensions are in mm"

**Rule**: Import CadQuery.
**Method**:
```python
import cadquery as cq
```

**Rule**: Use explicit cutter solids when making holes.
**Method**:
```python
cutter = cq.Workplane("XY").cylinder(height, radius)
body = body.cut(cutter)
```

**Rule**: Use when adding decorative text.
**Method**:
```python
.text(txt, fontsize, distance)
```
""",
    }
    monkeypatch.setattr(
        "cadpilotv3.agents.repair_agent.load_prompt_text",
        lambda _settings, name: prompts[name],
    )

    agent = RepairAgent(settings=SimpleNamespace())
    agent.llm_factory = FakeLLMFactory()

    result = agent.run(
        script="def build_part():\n    return cq.Workplane('XY').box(1, 1, 1).hole(0.5)\n",
        geometry_plan=SimpleNamespace(
            artifact_type="single_part",
            parts=[
                SimpleNamespace(
                    name="mounting_plate",
                    modeling_strategy="primitive_csg",
                    geometric_role="flat plate with through holes",
                    key_features=[
                        SimpleNamespace(
                            feature="m4_clearance_holes",
                            description="four through holes",
                        )
                    ],
                )
            ],
            model_dump_json=lambda indent=2: "{}",
        ),
        parameters=SimpleNamespace(
            parameters={"M4_CLEAR_D": object()},
            model_dump_json=lambda indent=2: "{}",
        ),
        validation=ValidationReport(
            status="runtime_error",
            error_class="api_misuse",
            error_location=ErrorLocation(
                function="build_part",
                code_line=".hole(0.5)",
            ),
            error_message="Workplane.hole is disallowed",
            error_summary="Use explicit cutter solids for holes.",
            geometry_valid=False,
            repair_needed=True,
        ),
        repair_attempt_count=1,
    )

    assert result.action == "patch"
    assert "Selected CadQuery 2.x API reference for repair:" in captured["prompt"]
    assert "Use explicit cutter solids when making holes" in captured["prompt"]
    assert ".text(txt, fontsize, distance)" not in captured["prompt"]


def test_repair_agent_prompt_includes_compact_previous_attempts(monkeypatch) -> None:
    captured = {}

    class FakeLLM:
        def invoke(self, prompt: str) -> str:
            captured["prompt"] = prompt
            return """
{
  "action": "replan",
  "error_class": "empty_selection",
  "root_cause": "The selected faces are not stable after the previous patch.",
  "cannot_patch_reason": "The same selector assumption has already failed.",
  "replan_instructions": "Rebuild the tab with explicit references.",
  "affected_part": "mounting_tab",
  "repair_attempt_count": 2
}
"""

    class FakeLLMFactory:
        def get_for_agent(self, _agent_name):
            return FakeLLM()

    monkeypatch.setattr(
        "cadpilotv3.agents.repair_agent.load_prompt_text",
        lambda _settings, _name: "repair prompt",
    )

    agent = RepairAgent(settings=SimpleNamespace())
    agent.llm_factory = FakeLLMFactory()

    result = agent.run(
        script="def build_part():\n    return cq.Workplane('XY').box(1, 1, 1)\n",
        geometry_plan=SimpleNamespace(
            artifact_type="single_part",
            parts=[],
            model_dump_json=lambda indent=2: "{}",
        ),
        parameters=SimpleNamespace(
            parameters={},
            model_dump_json=lambda indent=2: "{}",
        ),
        validation=ValidationReport(
            status="runtime_error",
            error_class="empty_selection",
            error_summary="A selector did not find the expected face.",
            geometry_valid=False,
            repair_needed=True,
        ),
        repair_attempt_count=2,
        max_repair_attempts=2,
        repair_history=[
            {
                "attempt_index": 0,
                "validation_error_class": "empty_selection",
                "action": "patch",
                "affected_function": "build_part",
                "root_cause": "The selector assumed a top face that no longer exists.",
                "irrelevant_large_blob": "x" * 400,
            }
        ],
    )

    assert result.action == "replan"
    assert "Previous repair attempts:" in captured["prompt"]
    assert "Repair attempt budget: 2" in captured["prompt"]
    assert "attempt_index: 0" in captured["prompt"]
    assert "validation_error_class: empty_selection" in captured["prompt"]
    assert "irrelevant_large_blob" not in captured["prompt"]


def test_repair_agent_prompt_uses_targeted_script_context(monkeypatch) -> None:
    captured = {}

    class FakeLLM:
        def invoke(self, prompt: str) -> str:
            captured["prompt"] = prompt
            return """
{
  "action": "patch",
  "error_class": "api_misuse",
  "root_cause": "The through hole was created with a forbidden helper.",
  "fix_description": "Replace the helper call with an explicit cutter.",
  "patch_type": "api",
  "affected_function": "build_part",
  "patched_code": "def build_part():\\n    return cq.Workplane('XY').box(1, 1, 1)",
  "confidence": "high",
  "confidence_note": null
}
"""

    class FakeLLMFactory:
        def get_for_agent(self, _agent_name):
            return FakeLLM()

    prompts = {
        "repair_agent.md": "repair system prompt",
        "repair_agent_examples.md": """
### Example 1 - Patch Hole Helper
INPUT: hole helper api_misuse
OUTPUT: patch explicit cutter

### Example 2 - Replan Sheet Metal
INPUT: sheet metal bend failed
OUTPUT: replan
""",
        "cheatsheet.md": "cadquery_cheatsheet:",
    }
    monkeypatch.setattr(
        "cadpilotv3.agents.repair_agent.load_prompt_text",
        lambda _settings, name: prompts[name],
    )

    agent = RepairAgent(settings=SimpleNamespace())
    agent.llm_factory = FakeLLMFactory()
    script = "\n\n".join(
        [
            "import cadquery as cq",
            "PLATE_T = 4.0",
            "def unused_large_helper():\n    return 'do not include me' * 500",
            (
                "def build_part():\n"
                "    return cq.Workplane('XY').box(40, 20, PLATE_T).hole(4)"
            ),
        ]
    )

    agent.run(
        script=script,
        geometry_plan=SimpleNamespace(
            artifact_type="single_part",
            parts=[],
            model_dump_json=lambda indent=2: "{}",
        ),
        parameters=SimpleNamespace(
            parameters={},
            model_dump_json=lambda indent=2: "{}",
        ),
        validation=ValidationReport(
            status="runtime_error",
            error_class="api_misuse",
            error_location=ErrorLocation(
                function="build_part",
                code_line="return cq.Workplane('XY').box(40, 20, PLATE_T).hole(4)",
            ),
            error_message="Workplane.hole is disallowed",
            error_summary="Use explicit cutter solids for holes.",
            geometry_valid=False,
            repair_needed=True,
        ),
        repair_attempt_count=1,
    )

    assert "Targeted script context:" in captured["prompt"]
    assert "PLATE_T = 4.0" in captured["prompt"]
    assert "def build_part" in captured["prompt"]
    assert "unused_large_helper" not in captured["prompt"]
    assert "Patch Hole Helper" in captured["prompt"]
    assert "Replan Sheet Metal" not in captured["prompt"]


def test_repair_cheatsheet_retrieval_selects_error_related_blocks() -> None:
    agent = object.__new__(RepairAgent)
    cheatsheet = """
cadquery_cheatsheet:
"All dimensions are in mm"

**Rule**: Use when creating rectangular solids.
**Method**:
```python
.box(length, width, height)
```

**Rule**: Use when a selector failed during fillet or chamfer.
**Method**:
```python
.edges(selector).fillet(radius)
```

**Rule**: Use when creating assemblies.
**Method**:
```python
cq.Assembly()
```
"""

    selected = agent._select_relevant_cheatsheet(
        cheatsheet=cheatsheet,
        script="part = part.edges('|Z').fillet(2.0)",
        geometry_plan=SimpleNamespace(artifact_type="single_part", parts=[]),
        parameters=SimpleNamespace(parameters={}),
        validation=ValidationReport(
            status="runtime_error",
            error_class="fillet_radius_overflow",
            error_summary="The fillet radius exceeds the local wall thickness.",
            geometry_valid=False,
            repair_needed=True,
        ),
        max_blocks=3,
    )

    assert ".edges(selector).fillet(radius)" in selected
    assert "cq.Assembly()" not in selected


def test_repair_cheatsheet_retrieval_quarantines_forbidden_hole_helpers() -> None:
    agent = object.__new__(RepairAgent)
    cheatsheet = """
cadquery_cheatsheet:
"All dimensions are in mm"

**Rule**: Use when user wants to drill simple holes.
**Method**:
```python
.hole(diameter[, depth=None])
```

**Rule**: Use when user wants to create a counterbored hole.
**Method**:
```python
.cboreHole(diameter, cboreDiameter[, depth=None])
```

**Rule**: Use when user wants to create a countersunk hole.
**Method**:
```python
.cskHole(diameter, cskDiameter[, depth=None])
```

**Rule**: Canonical explicit cutter patterns for repairing holes.
**Method**:
```python
def cut_through_hole_z(body, x, y, bottom_z, top_z, diameter):
    depth = (top_z - bottom_z) + 0.4
    cutter = cq.Workplane("XY").center(x, y).cylinder(depth, diameter / 2)
    return body.cut(cutter)

cutter = cq.Workplane("XY").cylinder(cut_depth, hole_radius)
body = body.cut(cutter)
```
"""

    selected = agent._select_relevant_cheatsheet(
        cheatsheet=cheatsheet,
        script="part = part.faces('>Z').workplane().hole(4)",
        geometry_plan=SimpleNamespace(
            artifact_type="single_part",
            parts=[
                SimpleNamespace(
                    name="mounting_plate",
                    modeling_strategy="primitive_csg",
                    geometric_role="plate with through holes",
                    key_features=[
                        SimpleNamespace(
                            feature="m4_clearance_holes",
                            description="four through holes",
                        )
                    ],
                )
            ],
        ),
        parameters=SimpleNamespace(parameters={"M4_CLEAR_D": object()}),
        validation=ValidationReport(
            status="runtime_error",
            error_class="api_misuse",
            error_message="Workplane.hole is disallowed",
            error_summary="Use explicit cutter solids for holes.",
            geometry_valid=False,
            repair_needed=True,
        ),
        max_blocks=6,
    )

    assert "Canonical explicit cutter patterns" in selected
    assert "def cut_through_hole_z" in selected
    assert ".hole(" not in selected
    assert ".cboreHole(" not in selected
    assert ".cskHole(" not in selected
