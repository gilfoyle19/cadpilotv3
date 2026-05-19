import json
from types import SimpleNamespace

import pytest

from cadpilotv3.agents.code_generation_infill_agent import CodeGenerationInfillAgent
from cadpilotv3.graph.nodes import PipelineNodes
from cadpilotv3.graph.routing import route_repair
from cadpilotv3.services.code_generation_infill_service import (
    CodeGenerationInfillService,
    CodeGenerationOutputError,
    CodePatchApplicationError,
)
from cadpilotv3.shared import LLMTextResult, LLMTextStreamChunk


def test_codegen_node_passes_critic_b_patch_instructions() -> None:
    captured = {}

    class FakeCodeGenerationService:
        def execute_script(self, **kwargs):
            captured.update(kwargs)
            return "import cadquery as cq\n"

    nodes = object.__new__(PipelineNodes)
    nodes.code_generation_infill_service = FakeCodeGenerationService()

    state = {
        "spec": object(),
        "geometry_plan": object(),
        "parameters": object(),
        "script": "import cadquery as cq\nold_model = cq.Workplane('XY').box(1, 1, 1)\n",
        "repair_decision": None,
        "critic_b_report": SimpleNamespace(
            routing="patch",
            patch_instructions="Move the gussets outboard and preserve the hole pattern.",
        ),
    }

    result = nodes.code_generation_infill_agent(state)

    assert captured["critic_feedback"] == (
        "Move the gussets outboard and preserve the hole pattern."
    )
    assert captured["current_script"] == (
        "import cadquery as cq\nold_model = cq.Workplane('XY').box(1, 1, 1)\n"
    )
    assert result["script"] == "import cadquery as cq\n"


def test_geometry_planner_node_passes_critic_b_replan_instructions() -> None:
    captured = {}
    planned = object()

    class FakeGeometryPlannerService:
        def execute(self, **kwargs):
            captured.update(kwargs)
            return planned

    nodes = object.__new__(PipelineNodes)
    nodes.geometry_planner_service = FakeGeometryPlannerService()

    state = {
        "spec": object(),
        "critic_a_report": {},
        "critic_b_report": SimpleNamespace(
            routing="replan",
            replan_instructions="Use an outboard gusset strategy with clear M3 holes.",
        ),
    }

    result = nodes.geometry_planner_agent(state)

    assert captured["critic_b_replan_instructions"] == (
        "Use an outboard gusset strategy with clear M3 holes."
    )
    assert result["geometry_plan"] is planned


def test_critic_b_node_passes_geometry_plan_and_parameters() -> None:
    captured = {}

    class FakeCriticBService:
        def execute(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(user_facing_warnings=[])

    nodes = object.__new__(PipelineNodes)
    nodes.critic_checkpoint_b_service = FakeCriticBService()

    geometry_plan = object()
    parameters = object()
    state = {
        "user_prompt": "make a bracket",
        "spec": object(),
        "geometry_plan": geometry_plan,
        "parameters": parameters,
        "validation": object(),
        "critic_a_report": object(),
        "repair_count": 0,
    }

    nodes.critic_checkpoint_b(state)

    assert captured["geometry_plan"] is geometry_plan
    assert captured["parameters"] is parameters


def test_codegen_output_guard_rejects_empty_script() -> None:
    service = object.__new__(CodeGenerationInfillService)

    with pytest.raises(CodeGenerationOutputError):
        service._validate_generated_code("\n")


def test_codegen_output_guard_rejects_non_cadquery_text() -> None:
    service = object.__new__(CodeGenerationInfillService)

    with pytest.raises(CodeGenerationOutputError):
        service._validate_generated_code("print('not a cad script')\n")


def test_extract_generated_code_strips_apostrophe_python_fence() -> None:
    service = object.__new__(CodeGenerationInfillService)

    code = service._extract_generated_code(
        "'''python\nimport cadquery as cq\nmodel = cq.Workplane('XY').box(1, 1, 1)\n'''"
    )

    assert code.startswith("import cadquery as cq")
    assert "'''python" not in code


def test_extract_generated_code_strips_unclosed_markdown_python_fence() -> None:
    service = object.__new__(CodeGenerationInfillService)

    code = service._extract_generated_code(
        "```python\nimport cadquery as cq\nmodel = cq.Workplane('XY').box(1, 1, 1)"
    )

    assert code.startswith("import cadquery as cq")
    assert "```python" not in code


def test_extract_generated_code_strips_bare_python_prefix() -> None:
    service = object.__new__(CodeGenerationInfillService)

    code = service._extract_generated_code(
        "python\nimport cadquery as cq\nmodel = cq.Workplane('XY').box(1, 1, 1)"
    )

    assert code.startswith("import cadquery as cq")
    assert not code.startswith("python")


@pytest.mark.parametrize(
    ("method_name", "arguments"),
    [
        ("hole", "0.5"),
        ("cboreHole", "0.5, 0.8, 0.2"),
        ("cskHole", "0.5, 0.8, 82.0"),
    ],
)
def test_codegen_preflight_rejects_implicit_hole_helpers(
    method_name: str,
    arguments: str,
) -> None:
    service = object.__new__(CodeGenerationInfillService)

    with pytest.raises(CodeGenerationOutputError, match=method_name):
        service._validate_generated_code(
            "\n".join(
                [
                    "import cadquery as cq",
                    "def build_part():",
                    "    return (",
                    "        cq.Workplane('XY')",
                    "        .box(1, 1, 1)",
                    "        .faces('>Z')",
                    "        .workplane()",
                    f"        .{method_name}({arguments})",
                    "    )",
                    "def validate_geometry(model):",
                    "    return {}",
                    "def export_all(model, output_dir='.'):",
                    "    return []",
                    "if __name__ == '__main__':",
                    "    model = build_part()",
                    "",
                ]
            )
        )


def test_codegen_preflight_rejects_volume_reasonable_heuristic() -> None:
    service = object.__new__(CodeGenerationInfillService)

    with pytest.raises(CodeGenerationOutputError, match="volume_reasonable"):
        service._validate_generated_code(
            "\n".join(
                [
                    "import cadquery as cq",
                    "def build_part():",
                    "    return cq.Workplane('XY').box(1, 1, 1)",
                    "def validate_geometry(model):",
                    "    return {'volume_reasonable': True}",
                    "def export_all(model, output_dir='.'):",
                    "    return []",
                    "if __name__ == '__main__':",
                    "    model = build_part()",
                    "",
                ]
            )
        )


def test_apply_patch_raises_when_target_missing() -> None:
    service = object.__new__(CodeGenerationInfillService)

    with pytest.raises(CodePatchApplicationError):
        service.apply_patch(
            current_script="def build_part():\n    return None\n",
            affected_function="missing_function",
            patched_code="def missing_function():\n    return None\n",
        )


def test_route_repair_sends_regenerate_to_codegen() -> None:
    state = {
        "repair_decision": SimpleNamespace(action="regenerate"),
        "repair_count": 0,
    }

    assert route_repair(state) == "code_generation_infill_agent"


def test_execute_script_retries_after_empty_generation(tmp_path) -> None:
    class FakeAgent:
        def __init__(self) -> None:
            self.calls = []

        def run(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return "```python\n\n```"
            return "\n".join(
                [
                    "import cadquery as cq",
                    "def build_part():",
                    "    return cq.Workplane('XY').box(1, 1, 1)",
                    "def validate_geometry(model):",
                    "    return {}",
                    "def export_all(model, output_dir='.'):",
                    "    return []",
                    "if __name__ == '__main__':",
                    "    model = build_part()",
                    "",
                ]
            )

    service = object.__new__(CodeGenerationInfillService)
    service.settings = SimpleNamespace(cad_artifacts_dir=str(tmp_path))
    service.agent = FakeAgent()

    script = service.execute_script(
        spec=SimpleNamespace(component="test_part"),
        geometry_plan=object(),
        parameters=object(),
    )

    assert "import cadquery as cq" in script
    assert len(service.agent.calls) == 2
    assert service.agent.calls[0]["generation_feedback"] is None
    assert service.agent.calls[1]["generation_feedback"] == (
        "Code generation returned an empty script"
    )
    assert service.agent.calls[1]["compact_retry"] is True


async def test_astream_script_yields_code_chunks_and_complete_event(tmp_path) -> None:
    valid_chunks = [
        "import cadquery as cq\n",
        "def build_part():\n    return cq.Workplane('XY').box(1, 1, 1)\n",
        "def validate_geometry(model):\n    return {}\n",
        "def export_all(model, output_dir='.'): \n    return []\n",
        "if __name__ == '__main__':\n    model = build_part()\n",
    ]

    class FakeAgent:
        async def astream(self, **kwargs):
            text = "".join(valid_chunks)
            for chunk in valid_chunks:
                yield LLMTextStreamChunk(text=chunk)
            yield LLMTextStreamChunk(
                text="",
                result=LLMTextResult(
                    text=text,
                    response_metadata={},
                    usage_metadata=None,
                    response_id=None,
                    raw_response_repr="<streamed response>",
                ),
            )

    service = object.__new__(CodeGenerationInfillService)
    service.settings = SimpleNamespace(cad_artifacts_dir=str(tmp_path))
    service.agent = FakeAgent()

    events = [
        event
        async for event in service.astream_script(
            spec=SimpleNamespace(component="test_part"),
            geometry_plan=object(),
            parameters=object(),
        )
    ]

    assert [event.event_type for event in events] == [
        "code_generation_start",
        "code_chunk",
        "code_chunk",
        "code_chunk",
        "code_chunk",
        "code_chunk",
        "code_generation_complete",
    ]
    streamed_text = "".join(
        event.payload["text"]
        for event in events
        if event.event_type == "code_chunk"
    )
    assert streamed_text.startswith("import cadquery as cq")
    assert events[-1].payload["script"] == streamed_text


async def test_astream_script_retries_after_empty_streamed_generation(tmp_path) -> None:
    class FakeAgent:
        def __init__(self) -> None:
            self.calls = []

        async def astream(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                text = "```python\n\n```"
                yield LLMTextStreamChunk(text=text)
                yield LLMTextStreamChunk(
                    text="",
                    result=LLMTextResult(
                        text=text,
                        response_metadata={},
                        usage_metadata=None,
                        response_id=None,
                        raw_response_repr="<empty response>",
                    ),
                )
                return

            text = "\n".join(
                [
                    "import cadquery as cq",
                    "def build_part():",
                    "    return cq.Workplane('XY').box(1, 1, 1)",
                    "def validate_geometry(model):",
                    "    return {}",
                    "def export_all(model, output_dir='.'):",
                    "    return []",
                    "if __name__ == '__main__':",
                    "    model = build_part()",
                    "",
                ]
            )
            yield LLMTextStreamChunk(text=text)
            yield LLMTextStreamChunk(
                text="",
                result=LLMTextResult(
                    text=text,
                    response_metadata={},
                    usage_metadata=None,
                    response_id=None,
                    raw_response_repr="<valid response>",
                ),
            )

    service = object.__new__(CodeGenerationInfillService)
    service.settings = SimpleNamespace(cad_artifacts_dir=str(tmp_path))
    service.agent = FakeAgent()

    events = [
        event
        async for event in service.astream_script(
            spec=SimpleNamespace(component="test_part"),
            geometry_plan=object(),
            parameters=object(),
        )
    ]

    assert "code_generation_retry" in [event.event_type for event in events]
    assert events[-1].event_type == "code_generation_complete"
    assert service.agent.calls[1]["generation_feedback"] == (
        "Code generation returned an empty script"
    )
    assert service.agent.calls[1]["compact_retry"] is True


def test_execute_script_persists_raw_failed_codegen_response(tmp_path) -> None:
    class FakeAgent:
        def __init__(self) -> None:
            self.calls = []

        def run(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return SimpleNamespace(
                    text="```python\n\n```",
                    response_metadata={"finish_reason": "stop"},
                    usage_metadata={"output_tokens": 3},
                    response_id="response-1",
                    raw_response_repr="<fake response>",
                )
            return "\n".join(
                [
                    "import cadquery as cq",
                    "def build_part():",
                    "    return cq.Workplane('XY').box(1, 1, 1)",
                    "def validate_geometry(model):",
                    "    return {}",
                    "def export_all(model, output_dir='.'):",
                    "    return []",
                    "if __name__ == '__main__':",
                    "    model = build_part()",
                    "",
                ]
            )

    service = object.__new__(CodeGenerationInfillService)
    service.settings = SimpleNamespace(cad_artifacts_dir=str(tmp_path))
    service.agent = FakeAgent()

    service.execute_script(
        spec=SimpleNamespace(component="test_part"),
        geometry_plan=object(),
        parameters=object(),
    )

    failed_attempts = list((tmp_path / "codegen_failed_attempts").iterdir())
    assert len(failed_attempts) == 1
    attempt_dir = failed_attempts[0]
    assert (attempt_dir / "raw_response.txt").read_text(encoding="utf-8") == (
        "```python\n\n```"
    )
    assert not (attempt_dir / "generated_script.py").read_text(encoding="utf-8").strip()

    metadata = json.loads((attempt_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["response_metadata"] == {"finish_reason": "stop"}
    assert metadata["usage_metadata"] == {"output_tokens": 3}
    assert metadata["raw_response_length_chars"] == len("```python\n\n```")
    assert metadata["extracted_script_length_chars"] == 1
    assert metadata["compact_retry_next"] is True


def test_codegen_selects_relevant_few_shots() -> None:
    agent = object.__new__(CodeGenerationInfillAgent)
    few_shots = """
## Examples

### Static Example 1 - Micro Servo Bracket
INPUT: servo bracket
OUTPUT: servo code

### Static Example 2 - 608 Bearing Pillow Block
INPUT: bearing pillow block
OUTPUT: bearing code

### Static Example 3 - Electronics Lid
INPUT: electronics lid
OUTPUT: lid code
"""

    selected = agent._select_relevant_examples(
        few_shot_prompt=few_shots,
        spec=SimpleNamespace(
            component="bearing_pillow_block_608",
            component_type="single_part",
            style="solid_block",
            manufacturing_process="CNC",
            approximate_scale="small",
            parts=["central_bearing_boss", "press_fit_bearing_seat"],
            constraints=["through_holes_only"],
        ),
        geometry_plan=SimpleNamespace(
            artifact_type="single_part",
            parts=[
                SimpleNamespace(
                    name="central_bearing_boss",
                    modeling_strategy="primitive_csg",
                    key_features=[
                        SimpleNamespace(feature="bearing_seat"),
                    ],
                )
            ],
        ),
        max_examples=1,
    )

    assert "608 Bearing Pillow Block" in selected
    assert "Micro Servo Bracket" not in selected


def test_codegen_selects_relevant_cheatsheet_blocks() -> None:
    agent = object.__new__(CodeGenerationInfillAgent)
    cheatsheet = """
cadquery_cheatsheet:
"All dimensions are in mm"

**Rule**: Import CadQuery.
**Method**:
```python
import cadquery as cq
```

**Rule**: Use when user wants to create a rectangular box solid.
**Method**:
```python
.box(length, width, height)
```

**Rule**: Use when user wants to draw decorative text.
**Method**:
```python
.text(txt, fontsize, distance)
```

**Rule**: Use when the user wants to create a slot.
**Method**:
```python
.slot2D(length, diameter)
```

**Rule**: Use when user wants to add a chamfer.
**Method**:
```python
.chamfer(d)
```
"""

    selected = agent._select_relevant_cheatsheet(
        cheatsheet=cheatsheet,
        spec=SimpleNamespace(
            component="belt_tensioner_bracket",
            component_type="single_part",
            style="lightweight_structural",
            manufacturing_process="FDM",
            approximate_scale="small",
            parts=["base_plate", "vertical_tab", "m4_slot", "gussets"],
            constraints=["chamfered_edges"],
        ),
        geometry_plan=SimpleNamespace(
            artifact_type="single_part",
            parts=[
                SimpleNamespace(
                    name="vertical_tab_with_slot",
                    modeling_strategy="primitive_csg",
                    key_features=[SimpleNamespace(feature="m4_slot")],
                )
            ],
        ),
        max_blocks=5,
    )

    assert ".box(length, width, height)" in selected
    assert ".slot2D(length, diameter)" in selected
    assert ".chamfer(d)" in selected
    assert ".text(txt, fontsize, distance)" not in selected


def test_codegen_cheatsheet_retrieval_quarantines_forbidden_hole_helpers() -> None:
    agent = object.__new__(CodeGenerationInfillAgent)
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

**Rule**: Canonical explicit cutter patterns for holes.
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
        spec=SimpleNamespace(
            component="mounting_plate",
            component_type="single_part",
            style="flat_plate",
            manufacturing_process="FDM",
            approximate_scale="small",
            parts=["plate", "m4_clearance_holes"],
            constraints=["four through holes"],
        ),
        geometry_plan=SimpleNamespace(
            artifact_type="single_part",
            parts=[
                SimpleNamespace(
                    name="plate_with_holes",
                    modeling_strategy="primitive_csg",
                    key_features=[
                        SimpleNamespace(feature="explicit through hole cutters"),
                    ],
                )
            ],
        ),
        max_blocks=6,
    )

    assert "Canonical explicit cutter patterns" in selected
    assert "def cut_through_hole_z" in selected
    assert ".hole(" not in selected
    assert ".cboreHole(" not in selected
    assert ".cskHole(" not in selected
