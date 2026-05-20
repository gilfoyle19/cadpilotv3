from cadpilotv3.agents.execution_validation_agent import ExecutionValidationAgent
from cadpilotv3.services.cadquery_execution_sandbox_service import (
    CadQueryExecutionSandboxService,
)


def test_sandbox_reports_per_child_assembly_bounding_boxes(tmp_path) -> None:
    service = CadQueryExecutionSandboxService(base_work_dir=str(tmp_path))

    artifacts = service.execute(
        "\n".join(
            [
                "import cadquery as cq",
                "base = cq.Workplane('XY').box(40, 30, 4)",
                "lid = cq.Workplane('XY').box(40, 30, 2)",
                "assembly = cq.Assembly(name='demo')",
                "assembly.add(base, name='base')",
                "assembly.add(lid, name='lid', loc=cq.Location(cq.Vector(0, 0, 5)))",
                "",
            ]
        )
    )

    assert artifacts.execution_succeeded is True
    assert artifacts.geometry_report is not None
    assert artifacts.geometry_report.part_count == 2
    assert artifacts.geometry_report.bounding_box_mm == [40.0, 30.0, 8.0]

    child_metadata = artifacts.geometry_report.child_metadata
    assert child_metadata is not None
    assert [child.name for child in child_metadata] == ["base", "lid"]
    assert child_metadata[0].bounding_box_mm == [40.0, 30.0, 4.0]
    assert child_metadata[0].center_mm == [0.0, 0.0, 0.0]
    assert child_metadata[1].bounding_box_mm == [40.0, 30.0, 2.0]
    assert child_metadata[1].center_mm == [0.0, 0.0, 5.0]
    assert child_metadata[0].volume_mm3 > child_metadata[1].volume_mm3


def test_validation_report_preserves_child_metadata(tmp_path) -> None:
    service = CadQueryExecutionSandboxService(base_work_dir=str(tmp_path))
    artifacts = service.execute(
        "\n".join(
            [
                "import cadquery as cq",
                "lower = cq.Workplane('XY').box(20, 20, 4)",
                "upper = cq.Workplane('XY').box(20, 20, 4)",
                "assembly = cq.Assembly()",
                "assembly.add(lower, name='lower')",
                "assembly.add(upper, name='upper', loc=cq.Location(cq.Vector(0, 0, 4)))",
                "",
            ]
        )
    )

    report = ExecutionValidationAgent(settings=None).run(artifacts)

    assert report.status == "success"
    assert report.geometry_report is not None
    assert report.geometry_report.child_metadata is not None
    assert [child.name for child in report.geometry_report.child_metadata] == [
        "lower",
        "upper",
    ]
    assert report.geometry_report.child_metadata[1].center_mm == [0.0, 0.0, 4.0]


def test_sandbox_captures_build_manifest_from_generated_validation(tmp_path) -> None:
    service = CadQueryExecutionSandboxService(base_work_dir=str(tmp_path))
    artifacts = service.execute(
        "\n".join(
            [
                "import cadquery as cq",
                "BUILD_MANIFEST = {",
                "    'features': [],",
                "    'part_frames': [],",
                "    'assembly_constraints': [],",
                "}",
                "def build_part():",
                "    return cq.Workplane('XY').box(10, 10, 2)",
                "def validate_geometry(model):",
                "    return {'build_manifest': BUILD_MANIFEST, 'positive_volume': True}",
                "model = build_part()",
                "validate_geometry(model)",
                "",
            ]
        )
    )

    report = ExecutionValidationAgent(settings=None).run(artifacts)

    assert artifacts.build_manifest == {
        "features": [],
        "part_frames": [],
        "assembly_constraints": [],
    }
    assert artifacts.generated_validation is not None
    assert report.build_manifest == artifacts.build_manifest
    assert report.generated_validation == artifacts.generated_validation
