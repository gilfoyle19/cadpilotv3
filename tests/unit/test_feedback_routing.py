import json
from types import SimpleNamespace

import pytest

from cadpilotv3.agents.code_generation_infill_agent import CodeGenerationInfillAgent
from cadpilotv3.graph import routing
from cadpilotv3.graph.nodes import PipelineNodes
from cadpilotv3.graph.routing import (
    route_contract_validation,
    route_critic_a,
    route_critic_b,
    route_repair,
    route_validation,
)
from cadpilotv3.schemas.contract_validation import ContractValidationReport
from cadpilotv3.services.code_generation_infill_service import (
    CodeGenerationInfillService,
    CodeGenerationOutputError,
    CodePatchApplicationError,
)
from cadpilotv3.shared import LLMTextResult, LLMTextStreamChunk


def _valid_single_part_script() -> str:
    return "\n".join(
        [
            "import cadquery as cq",
            "BUILD_MANIFEST = {",
            "    'features': [],",
            "    'part_frames': [],",
            "    'assembly_constraints': [],",
            "}",
            "def build_part():",
            "    return cq.Workplane('XY').box(1, 1, 1)",
            "def validate_geometry(model):",
            "    return {'build_manifest': BUILD_MANIFEST}",
            "def export_all(model, output_dir='.'):",
            "    return []",
            "if __name__ == '__main__':",
            "    model = build_part()",
            "    validate_geometry(model)",
            "    export_all(model, '.')",
            "",
        ]
    )


def _critic_b_skip_state() -> dict:
    return {
        "geometry_plan": SimpleNamespace(artifact_type="single_part"),
        "validation": SimpleNamespace(
            status="success",
            repair_needed=False,
            geometry_valid=True,
            geometry_report=SimpleNamespace(
                artifact_type="single_part",
                part_count=1,
            ),
        ),
        "contract_validation": SimpleNamespace(
            status="pass",
            passed=True,
            failure_count=0,
            warning_count=0,
        ),
        "repair_count": 0,
        "user_facing_warnings": [],
    }


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
    contract_validation = SimpleNamespace(status="pass", compact_evidence=[])
    state = {
        "user_prompt": "make a bracket",
        "spec": object(),
        "geometry_plan": geometry_plan,
        "parameters": parameters,
        "validation": object(),
        "contract_validation": contract_validation,
        "critic_a_report": object(),
        "repair_count": 0,
    }

    nodes.critic_checkpoint_b(state)

    assert captured["geometry_plan"] is geometry_plan
    assert captured["parameters"] is parameters
    assert captured["contract_validation"] is contract_validation


def test_contract_validation_node_runs_before_critic_b() -> None:
    captured = {}
    report = ContractValidationReport(
        status="fail",
        passed=False,
        summary="1 failed, 0 warned, 0 skipped, 1 total contract checks.",
        failure_count=1,
        compact_evidence=["fail:mount_hole:Required feature missing."],
    )

    class FakeContractValidationService:
        def execute(self, **kwargs):
            captured.update(kwargs)
            return report

    nodes = object.__new__(PipelineNodes)
    nodes.contract_validation_service = FakeContractValidationService()

    geometry_plan = object()
    validation = object()
    state = {
        "geometry_plan": geometry_plan,
        "validation": validation,
    }

    result = nodes.contract_validation_node(state)

    assert captured == {
        "geometry_plan": geometry_plan,
        "validation": validation,
    }
    assert result["contract_validation"] is report


def test_contract_validation_node_sets_skipped_critic_b_report(monkeypatch) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_enable_conditional_critic_b=True),
    )

    class FakeContractValidationService:
        def execute(self, **kwargs):
            return SimpleNamespace(
                status="pass",
                passed=True,
                failure_count=0,
                warning_count=0,
            )

    nodes = object.__new__(PipelineNodes)
    nodes.contract_validation_service = FakeContractValidationService()

    state = _critic_b_skip_state()

    result = nodes.contract_validation_node(state)

    assert result["critic_b_report"].routing == "export"
    assert result["critic_b_report"].verdict == "pass"
    assert result["critic_b_report"].overall_fidelity_score == 1.0


def test_repair_node_passes_and_records_repair_history() -> None:
    captured = {}

    class FakeRepairService:
        def execute(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                action="replan",
                root_cause="The selector failure repeated after a patch.",
                fix_description=None,
                affected_function=None,
                cannot_patch_reason="Same error class already failed.",
                replan_instructions="Use explicit construction references.",
            )

    nodes = object.__new__(PipelineNodes)
    nodes.repair_service = FakeRepairService()

    state = {
        "script": "import cadquery as cq\n",
        "geometry_plan": object(),
        "parameters": object(),
        "validation": SimpleNamespace(
            error_class="empty_selection",
            error_summary="Selector did not find expected faces.",
        ),
        "repair_count": 1,
        "repair_history": [
            {
                "attempt_index": 0,
                "validation_error_class": "empty_selection",
                "action": "patch",
            }
        ],
    }

    result = nodes.repair_agent(state)

    assert captured["repair_history"] == [
        {
            "attempt_index": 0,
            "validation_error_class": "empty_selection",
            "action": "patch",
        }
    ]
    assert result["repair_count"] == 2
    assert result["repair_history"][-1] == {
        "attempt_index": 1,
        "validation_error_class": "empty_selection",
        "validation_error_summary": "Selector did not find expected faces.",
        "action": "replan",
        "root_cause": "The selector failure repeated after a patch.",
        "cannot_patch_reason": "Same error class already failed.",
        "replan_instructions": "Use explicit construction references.",
    }


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


def test_codegen_preflight_accepts_required_single_part_skeleton() -> None:
    service = object.__new__(CodeGenerationInfillService)

    service._validate_generated_code(_valid_single_part_script())


def test_codegen_preflight_rejects_missing_build_manifest() -> None:
    service = object.__new__(CodeGenerationInfillService)
    script = _valid_single_part_script().replace(
        (
            "BUILD_MANIFEST = {\n"
            "    'features': [],\n"
            "    'part_frames': [],\n"
            "    'assembly_constraints': [],\n"
            "}\n"
        ),
        "",
    )

    with pytest.raises(CodeGenerationOutputError, match="BUILD_MANIFEST"):
        service._validate_generated_code(script)


def test_codegen_preflight_rejects_validate_geometry_not_using_manifest() -> None:
    service = object.__new__(CodeGenerationInfillService)
    script = _valid_single_part_script().replace(
        "    return {'build_manifest': BUILD_MANIFEST}",
        "    return {'positive_volume': True}",
    )

    with pytest.raises(CodeGenerationOutputError, match="BUILD_MANIFEST"):
        service._validate_generated_code(script)


def test_codegen_preflight_rejects_script_not_starting_with_cadquery_import() -> None:
    service = object.__new__(CodeGenerationInfillService)
    script = "from cadquery import exporters\n" + _valid_single_part_script()

    with pytest.raises(CodeGenerationOutputError, match="start with exactly"):
        service._validate_generated_code(script)


def test_codegen_preflight_rejects_multiple_public_entrypoints() -> None:
    service = object.__new__(CodeGenerationInfillService)
    script = _valid_single_part_script().replace(
        "def validate_geometry(model):",
        "def build_assembly():\n    return cq.Assembly()\ndef validate_geometry(model):",
    )

    with pytest.raises(CodeGenerationOutputError, match="exactly one public entrypoint"):
        service._validate_generated_code(script)


@pytest.mark.parametrize(
    ("main_body_line", "message"),
    [
        ("    validate_geometry(model)", "validate_geometry"),
        ("    export_all(model, '.')", "export_all"),
    ],
)
def test_codegen_preflight_rejects_incomplete_main_block(
    main_body_line: str,
    message: str,
) -> None:
    service = object.__new__(CodeGenerationInfillService)
    script = _valid_single_part_script().replace(f"{main_body_line}\n", "")

    with pytest.raises(CodeGenerationOutputError, match=message):
        service._validate_generated_code(script)


def test_codegen_preflight_rejects_top_level_result_assignment() -> None:
    service = object.__new__(CodeGenerationInfillService)
    script = _valid_single_part_script().replace(
        "def build_part():",
        "model = cq.Workplane('XY').box(1, 1, 1)\ndef build_part():",
    )

    with pytest.raises(CodeGenerationOutputError, match="only inside"):
        service._validate_generated_code(script)


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
                    "    validate_geometry(model)",
                    "    export_all(model, '.')",
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
                    "    validate_geometry(model)",
                    "    export_all(model, '.')",
                    "",
                ]
            )
        )


@pytest.mark.parametrize(
    "validation_body",
    [
        "    assert model.val().Volume() > 0\n    return {}",
        "    raise ValueError('invalid geometry')",
    ],
)
def test_codegen_preflight_rejects_throwing_validate_geometry(
    validation_body: str,
) -> None:
    service = object.__new__(CodeGenerationInfillService)
    script = _valid_single_part_script().replace(
        "def validate_geometry(model):\n    return {'build_manifest': BUILD_MANIFEST}",
        f"def validate_geometry(model):\n{validation_body}",
    )

    with pytest.raises(CodeGenerationOutputError, match="validate_geometry"):
        service._validate_generated_code(script)


@pytest.mark.parametrize(
    "validation_body",
    [
        "    return {'saved': model.save('bad.step')}",
        "    return {'exported': export_all(model, '.')}",
        "    return {'rebuilt': build_part().val().Volume() > 0}",
        "    return {'modified': model.cut(cq.Workplane('XY').box(1, 1, 1))}",
    ],
)
def test_codegen_preflight_rejects_side_effects_inside_validate_geometry(
    validation_body: str,
) -> None:
    service = object.__new__(CodeGenerationInfillService)
    script = _valid_single_part_script().replace(
        "def validate_geometry(model):\n    return {'build_manifest': BUILD_MANIFEST}",
        f"def validate_geometry(model):\n{validation_body}",
    )

    with pytest.raises(CodeGenerationOutputError, match="side-effect-free"):
        service._validate_generated_code(script)


@pytest.mark.parametrize(
    "heuristic_key",
    [
        "bbox_matches",
        "dimensions_match",
        "expected_bounding_box",
        "expected_final_volume",
        "volume_ratio",
        "volume_threshold",
    ],
)
def test_codegen_preflight_rejects_brittle_validation_heuristic_keys(
    heuristic_key: str,
) -> None:
    service = object.__new__(CodeGenerationInfillService)
    script = _valid_single_part_script().replace(
        "def validate_geometry(model):\n    return {'build_manifest': BUILD_MANIFEST}",
        f"def validate_geometry(model):\n    return {{{heuristic_key!r}: True}}",
    )

    with pytest.raises(CodeGenerationOutputError, match="brittle validation"):
        service._validate_generated_code(script)


def test_apply_patch_raises_when_target_missing() -> None:
    service = object.__new__(CodeGenerationInfillService)

    with pytest.raises(CodePatchApplicationError):
        service.apply_patch(
            current_script="def build_part():\n    return None\n",
            affected_function="missing_function",
            patched_code="def missing_function():\n    return None\n",
        )


def test_route_validation_sends_success_to_contract_validation() -> None:
    state = {"validation": SimpleNamespace(repair_needed=False)}

    assert route_validation(state) == "contract_validation_node"


def test_route_validation_sends_repair_needed_to_repair() -> None:
    state = {"validation": SimpleNamespace(repair_needed=True)}

    assert route_validation(state) == "repair_agent"


def test_route_contract_validation_keeps_critic_b_by_default(monkeypatch) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_enable_conditional_critic_b=False),
    )

    assert route_contract_validation(_critic_b_skip_state()) == "critic_checkpoint_b"


def test_route_contract_validation_skips_critic_b_for_clean_single_part(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_enable_conditional_critic_b=True),
    )

    assert route_contract_validation(_critic_b_skip_state()) == "export_summary_agent"


def test_route_contract_validation_keeps_critic_b_for_assemblies(monkeypatch) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_enable_conditional_critic_b=True),
    )
    state = _critic_b_skip_state()
    state["geometry_plan"] = SimpleNamespace(artifact_type="assembly")
    state["validation"].geometry_report.artifact_type = "assembly"
    state["validation"].geometry_report.part_count = 2

    assert route_contract_validation(state) == "critic_checkpoint_b"


def test_route_contract_validation_keeps_critic_b_for_contract_warnings(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_enable_conditional_critic_b=True),
    )
    state = _critic_b_skip_state()
    state["contract_validation"].status = "warn"
    state["contract_validation"].warning_count = 1

    assert route_contract_validation(state) == "critic_checkpoint_b"


def test_route_contract_validation_keeps_critic_b_after_repairs(monkeypatch) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_enable_conditional_critic_b=True),
    )
    state = _critic_b_skip_state()
    state["repair_count"] = 1

    assert route_contract_validation(state) == "critic_checkpoint_b"


def test_route_contract_validation_keeps_critic_b_for_existing_warnings(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_enable_conditional_critic_b=True),
    )
    state = _critic_b_skip_state()
    state["user_facing_warnings"] = ["Proceeding with a known issue."]

    assert route_contract_validation(state) == "critic_checkpoint_b"


def test_route_critic_a_replans_when_attempt_budget_remains(monkeypatch) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_max_critic_a_attempts=2),
    )
    state = {
        "critic_a_report": SimpleNamespace(
            verdict="fail",
            routing="replan",
            issues=[],
        ),
        "critic_a_attempts": 1,
        "user_facing_warnings": [],
    }

    assert route_critic_a(state) == "geometry_planner_agent"
    assert state["user_facing_warnings"] == []


def test_route_critic_a_stops_when_attempt_budget_is_exhausted(monkeypatch) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_max_critic_a_attempts=2),
    )
    state = {
        "critic_a_report": SimpleNamespace(
            verdict="fail",
            routing="replan",
            issues=[SimpleNamespace(description="Plan is missing the mounting holes.")],
        ),
        "critic_a_attempts": 2,
        "user_facing_warnings": [],
    }

    assert route_critic_a(state) == "parameter_agent"
    assert state["user_facing_warnings"] == [
        "Plan is missing the mounting holes.",
    ]


def test_route_critic_b_patches_when_attempt_budget_remains(monkeypatch) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_max_critic_b_attempts=2),
    )
    state = {
        "critic_b_report": SimpleNamespace(
            routing="patch",
            issues=[],
        ),
        "critic_b_attempts": 1,
        "user_facing_warnings": [],
    }

    assert route_critic_b(state) == "code_generation_infill_agent"
    assert state["user_facing_warnings"] == []


def test_route_critic_b_stops_when_attempt_budget_is_exhausted(monkeypatch) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_max_critic_b_attempts=2),
    )
    state = {
        "critic_b_report": SimpleNamespace(
            routing="replan",
            issues=[SimpleNamespace(description="Final part violates the requested scale.")],
        ),
        "critic_b_attempts": 2,
        "user_facing_warnings": [],
    }

    assert route_critic_b(state) == "export_summary_agent"
    assert state["user_facing_warnings"] == [
        "Final part violates the requested scale.",
    ]


def test_route_repair_sends_regenerate_to_codegen() -> None:
    state = {
        "repair_decision": SimpleNamespace(action="regenerate"),
        "repair_count": 0,
    }

    assert route_repair(state) == "code_generation_infill_agent"


def test_route_repair_stops_when_attempt_budget_is_exhausted(monkeypatch) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_max_repair_attempts=2),
    )
    state = {
        "repair_decision": SimpleNamespace(action="patch"),
        "repair_count": 2,
    }

    assert route_repair(state) == "contract_validation_node"


def test_route_repair_patches_when_attempt_budget_remains(monkeypatch) -> None:
    monkeypatch.setattr(
        routing,
        "get_settings",
        lambda: SimpleNamespace(cad_max_repair_attempts=2),
    )
    state = {
        "repair_decision": SimpleNamespace(action="patch"),
        "repair_count": 1,
    }

    assert route_repair(state) == "execution_validation_node"


def test_execute_script_retries_after_empty_generation(tmp_path) -> None:
    class FakeAgent:
        def __init__(self) -> None:
            self.calls = []

        def run(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return "```python\n\n```"
            return _valid_single_part_script()

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


def test_execute_script_uses_compact_retry_after_structural_preflight_failure(
    tmp_path,
) -> None:
    class FakeAgent:
        def __init__(self) -> None:
            self.calls = []

        def run(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return "\n".join(
                    [
                        "import cadquery as cq",
                        "def build_part():",
                        "    return cq.Workplane('XY').box(1, 1, 1)",
                        "",
                    ]
                )
            return _valid_single_part_script()

    service = object.__new__(CodeGenerationInfillService)
    service.settings = SimpleNamespace(cad_artifacts_dir=str(tmp_path))
    service.agent = FakeAgent()

    script = service.execute_script(
        spec=SimpleNamespace(component="test_part"),
        geometry_plan=object(),
        parameters=object(),
    )

    assert script == _valid_single_part_script()
    assert len(service.agent.calls) == 2
    assert service.agent.calls[0]["compact_retry"] is False
    assert service.agent.calls[1]["generation_feedback"].startswith(
        "Generated script must define"
    )
    assert service.agent.calls[1]["compact_retry"] is True


@pytest.mark.parametrize(
    "error_message",
    [
        "Generated script must start with exactly: import cadquery as cq",
        "Generated script has a syntax error: invalid syntax",
        "Generated script must define build_part() or build_assembly()",
        "Generated script must define validate_geometry()",
        "Generated script must include a __main__ export block",
        "Generated script must avoid Workplane.hole(); use explicit cutter solids",
        "Generated script must not include heuristic volume_reasonable checks",
    ],
)
def test_codegen_uses_compact_retry_for_all_output_contract_failures(
    error_message: str,
) -> None:
    service = object.__new__(CodeGenerationInfillService)

    assert service._should_use_compact_retry(
        CodeGenerationOutputError(error_message)
    ) is True


async def test_astream_script_yields_code_chunks_and_complete_event(tmp_path) -> None:
    valid_script = _valid_single_part_script()
    valid_chunks = [f"{line}\n" for line in valid_script.splitlines()]

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
        *(["code_chunk"] * len(valid_chunks)),
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

            text = _valid_single_part_script()
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
            return _valid_single_part_script()

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
