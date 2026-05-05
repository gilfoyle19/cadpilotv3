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
