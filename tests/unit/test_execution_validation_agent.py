from cadpilotv3.agents.execution_validation_agent import ExecutionValidationAgent
from cadpilotv3.services.cadquery_execution_sandbox_service import (
    SandboxErrorLocation,
    SandboxExecutionArtifacts,
)


def _agent() -> ExecutionValidationAgent:
    return object.__new__(ExecutionValidationAgent)


def _failed_artifacts(
    *,
    error_type: str,
    error_message: str,
    traceback_text: str | None = None,
    code_line: str | None = None,
) -> SandboxExecutionArtifacts:
    return SandboxExecutionArtifacts(
        syntax_ok=True,
        execution_succeeded=False,
        stdout="",
        stderr="",
        execution_time_s=0.01,
        error_type=error_type,
        error_message=error_message,
        traceback_text=traceback_text,
        error_location=SandboxErrorLocation(
            line=12,
            function="build_part",
            code_line=code_line,
        ),
        geometry_report=None,
        result_object_name=None,
        workspace_dir=".",
    )


def test_execution_classifier_routes_export_dispatch_errors_as_patchable_export_failures() -> None:
    agent = _agent()
    artifacts = _failed_artifacts(
        error_type="DispatchError",
        error_message=(
            "Function <cadquery.occ_impl.exporters.export> has no method found "
            "for signature export(Assembly, str)"
        ),
        traceback_text="multimethod.DispatchError: no method found",
        code_line="cq.exporters.export(assembly, 'assembly.step')",
    )

    report = agent.run(artifacts)

    assert report.error_class == "export_format_error"
    assert report.repair_complexity == "patch"
    assert report.repair_needed is True


def test_execution_classifier_routes_selector_assumption_failures_to_replan() -> None:
    agent = _agent()
    artifacts = _failed_artifacts(
        error_type="IndexError",
        error_message="list index out of range",
        traceback_text="IndexError: list index out of range",
        code_line="model.faces('>Z').edges('|X').item(0)",
    )

    report = agent.run(artifacts)

    assert report.error_class == "empty_selection"
    assert report.repair_complexity == "replan"


def test_execution_classifier_routes_occ_boolean_failures_to_replan() -> None:
    agent = _agent()
    artifacts = _failed_artifacts(
        error_type="Standard_Failure",
        error_message="BRepAlgoAPI boolean cut failed during solid construction",
        traceback_text="OCP.Standard.Standard_Failure: BRepAlgoAPI cut failed",
        code_line="body = body.cut(cutter)",
    )

    report = agent.run(artifacts)

    assert report.error_class == "topology_error"
    assert report.repair_complexity == "replan"


def test_execution_classifier_routes_oversized_fillet_before_generic_topology() -> None:
    agent = _agent()
    artifacts = _failed_artifacts(
        error_type="StdFail_NotDone",
        error_message="BRepFilletAPI failed because the fillet radius is too large",
        traceback_text="StdFail_NotDone: BRepFilletAPI_MakeFillet",
        code_line="model = model.edges('|Z').fillet(12)",
    )

    report = agent.run(artifacts)

    assert report.error_class == "fillet_radius_overflow"
    assert report.repair_complexity == "patch"


def test_execution_classifier_preserves_import_errors_as_patchable() -> None:
    agent = _agent()
    artifacts = _failed_artifacts(
        error_type="ModuleNotFoundError",
        error_message="No module named 'cadquery_helpers'",
        traceback_text="ModuleNotFoundError: No module named 'cadquery_helpers'",
        code_line="from cadquery_helpers import make_plate",
    )

    report = agent.run(artifacts)

    assert report.error_class == "import_error"
    assert report.repair_complexity == "patch"


def test_execution_classifier_routes_invalid_sketch_profiles_to_replan() -> None:
    agent = _agent()
    artifacts = _failed_artifacts(
        error_type="ValueError",
        error_message="BRepBuilderAPI_MakeFace failed because wire is not closed",
        traceback_text="ValueError: invalid wire; cannot build face",
        code_line="profile = cq.Workplane('XY').polyline(points).close().extrude(8)",
    )

    report = agent.run(artifacts)

    assert report.error_class == "degenerate_sketch"
    assert report.repair_complexity == "replan"
