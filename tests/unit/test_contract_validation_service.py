from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.services.contract_validation_service import ContractValidationService


def _geometry_plan() -> GeometryPlan:
    return GeometryPlan.model_validate(
        {
            "artifact_type": "assembly",
            "parts": [
                {
                    "name": "base",
                    "modeling_strategy": "primitive_csg",
                    "strategy_selection": {
                        "candidates": [
                            {
                                "strategy": "primitive_csg",
                                "advantage": "simple base",
                                "disadvantage": "requires explicit cutters",
                            }
                        ],
                        "winner": "primitive_csg",
                        "rationale": "stable construction",
                    },
                },
                {
                    "name": "lid",
                    "modeling_strategy": "primitive_csg",
                    "strategy_selection": {
                        "candidates": [
                            {
                                "strategy": "primitive_csg",
                                "advantage": "simple lid",
                                "disadvantage": "requires explicit placement",
                            }
                        ],
                        "winner": "primitive_csg",
                        "rationale": "stable construction",
                    },
                },
            ],
            "feature_contracts": [
                {
                    "id": "base_m4_hole_1",
                    "host_part": "base",
                    "type": "through_hole",
                    "operation": "cut",
                    "axis": "Z",
                    "center": [0, 0, 2],
                    "dimensions": {"diameter": "M4_CLEARANCE_D"},
                    "count_group": "base_m4_pattern",
                    "required": True,
                },
                {
                    "id": "lid_m4_hole_1",
                    "host_part": "lid",
                    "type": "through_hole",
                    "operation": "cut",
                    "axis": "Z",
                    "center": [0, 0, 6],
                    "dimensions": {"diameter": "M4_CLEARANCE_D"},
                    "count_group": "base_m4_pattern",
                    "required": True,
                },
            ],
            "part_frames": [
                {
                    "part": "base",
                    "local_origin": "center",
                    "world_center": "[0,0,2]",
                    "approximate_bounding_box_mm": [40, 30, 4],
                },
                {
                    "part": "lid",
                    "local_origin": "center",
                    "world_center": "[0,0,6]",
                    "approximate_bounding_box_mm": [40, 30, 2],
                },
            ],
            "assembly_contracts": [
                {
                    "id": "base_lid_centered_xy",
                    "type": "centered",
                    "parts": ["base", "lid"],
                    "axes": ["X", "Y"],
                    "feature_refs": ["base_m4_hole_1", "lid_m4_hole_1"],
                    "target": "base and lid share X/Y center",
                    "tolerance_mm": 0.25,
                    "description": "lid sits centered over base",
                },
                {
                    "id": "m4_holes_coaxial",
                    "type": "coaxial",
                    "parts": ["base", "lid"],
                    "axes": ["Z"],
                    "feature_refs": ["base_m4_hole_1", "lid_m4_hole_1"],
                    "target": "holes share Z axis",
                    "tolerance_mm": 0.25,
                    "description": "hole centers align vertically",
                },
            ],
        }
    )


def _manifest() -> dict:
    return {
        "features": [
            {
                "id": "base_m4_hole_1",
                "host_part": "base",
                "type": "through_hole",
                "operation": "cut",
                "axis": "Z",
                "center_mm": [0.0, 0.0, 2.0],
                "dimensions_mm": {"diameter": 4.5},
                "count_group": "base_m4_pattern",
                "required": True,
            },
            {
                "id": "lid_m4_hole_1",
                "host_part": "lid",
                "type": "through_hole",
                "operation": "cut",
                "axis": "Z",
                "center_mm": [0.0, 0.0, 6.0],
                "dimensions_mm": {"diameter": 4.5},
                "count_group": "base_m4_pattern",
                "required": True,
            },
        ],
        "part_frames": [
            {
                "part": "base",
                "center_mm": [0.0, 0.0, 2.0],
                "bbox_mm": [40.0, 30.0, 4.0],
            },
            {
                "part": "lid",
                "center_mm": [0.0, 0.0, 6.0],
                "bbox_mm": [40.0, 30.0, 2.0],
            },
        ],
        "assembly_constraints": [
            {
                "id": "base_lid_centered_xy",
                "type": "centered",
                "parts": ["base", "lid"],
                "axes": ["X", "Y"],
                "feature_refs": ["base_m4_hole_1", "lid_m4_hole_1"],
                "target": "base and lid share X/Y center",
                "tolerance_mm": 0.25,
            },
            {
                "id": "m4_holes_coaxial",
                "type": "coaxial",
                "parts": ["base", "lid"],
                "axes": ["Z"],
                "feature_refs": ["base_m4_hole_1", "lid_m4_hole_1"],
                "target": "holes share Z axis",
                "tolerance_mm": 0.25,
            },
        ],
    }


def _validation(*, lid_center_x: float = 0.0) -> ValidationReport:
    return ValidationReport.model_validate(
        {
            "status": "success",
            "geometry_valid": True,
            "repair_needed": False,
            "geometry_report": {
                "part_count": 2,
                "bounding_box_mm": [40.0, 30.0, 8.0],
                "volume_mm3": 1000.0,
                "is_manifold": True,
                "face_count": 12,
                "has_zero_volume_parts": False,
                "assembly_valid": True,
                "child_metadata": [
                    {
                        "name": "base",
                        "bounding_box_mm": [40.0, 30.0, 4.0],
                        "center_mm": [0.0, 0.0, 2.0],
                        "volume_mm3": 500.0,
                    },
                    {
                        "name": "lid",
                        "bounding_box_mm": [40.0, 30.0, 2.0],
                        "center_mm": [lid_center_x, 0.0, 6.0],
                        "volume_mm3": 250.0,
                    },
                ],
            },
            "build_manifest": _manifest(),
        }
    )


def test_contract_validation_passes_when_manifest_and_child_metadata_match() -> None:
    report = ContractValidationService().execute(
        geometry_plan=_geometry_plan(),
        validation=_validation(),
    )

    assert report.status == "pass"
    assert report.passed is True
    assert report.failure_count == 0


def test_contract_validation_fails_when_required_feature_is_missing() -> None:
    validation = _validation()
    manifest = _manifest()
    manifest["features"] = manifest["features"][:1]

    report = ContractValidationService().execute(
        geometry_plan=_geometry_plan(),
        validation=validation,
        build_manifest=manifest,
    )

    assert report.status == "fail"
    assert "lid_m4_hole_1" in "\n".join(report.compact_evidence)


def test_contract_validation_fails_when_centered_constraint_is_violated() -> None:
    report = ContractValidationService().execute(
        geometry_plan=_geometry_plan(),
        validation=_validation(lid_center_x=8.0),
    )

    assert report.status == "fail"
    assert any(
        check.id == "base_lid_centered_xy" and check.status == "fail"
        for check in report.checks
    )


def test_contract_validation_fails_when_build_manifest_is_missing() -> None:
    validation = _validation()
    validation.build_manifest = None

    report = ContractValidationService().execute(
        geometry_plan=_geometry_plan(),
        validation=validation,
    )

    assert report.status == "fail"
    assert report.checks[0].id == "build_manifest"
