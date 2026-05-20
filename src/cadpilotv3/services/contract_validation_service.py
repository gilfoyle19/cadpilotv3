from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from cadpilotv3.schemas.contract_validation import (
    ContractCheck,
    ContractValidationReport,
)
from cadpilotv3.schemas.geometry_plan import AssemblyContract, FeatureContract, GeometryPlan
from cadpilotv3.schemas.validation import ValidationReport

AXIS_INDEX = {
    "X": 0,
    "Y": 1,
    "Z": 2,
}


class ContractValidationService:
    def execute(
        self,
        *,
        geometry_plan: GeometryPlan | Mapping[str, Any],
        validation: ValidationReport | Mapping[str, Any],
        build_manifest: Mapping[str, Any] | None = None,
    ) -> ContractValidationReport:
        plan = self._coerce_geometry_plan(geometry_plan)
        validation_report = self._coerce_validation_report(validation)
        manifest = self._resolve_build_manifest(validation_report, build_manifest)

        required_features = self._required_feature_contracts(plan)
        required_assembly_contracts = {
            contract.id: contract for contract in plan.assembly_contracts
        }

        if not required_features and not required_assembly_contracts:
            return self._build_report(
                [
                    ContractCheck(
                        id="no_contracts",
                        category="contract_presence",
                        status="skip",
                        severity="info",
                        message="Geometry plan does not contain feature or assembly contracts.",
                    )
                ]
            )

        if manifest is None:
            return self._build_report(
                [
                    ContractCheck(
                        id="build_manifest",
                        category="manifest_presence",
                        status="fail",
                        severity="critical",
                        message=(
                            "Generated script did not expose BUILD_MANIFEST or "
                            "validate_geometry(...)[\"build_manifest\"]."
                        ),
                        evidence={
                            "required_feature_count": len(required_features),
                            "required_assembly_contract_count": len(
                                required_assembly_contracts
                            ),
                        },
                    )
                ]
            )

        checks: list[ContractCheck] = []
        checks.extend(self._check_manifest_shape(manifest))

        manifest_features = self._manifest_items_by_id(manifest.get("features"))
        manifest_constraints = self._manifest_items_by_id(
            manifest.get("assembly_constraints")
        )
        manifest_part_frames = self._manifest_items_by_part(manifest.get("part_frames"))

        checks.extend(
            self._check_feature_contracts(
                required_features=required_features,
                manifest_features=manifest_features,
            )
        )
        checks.extend(
            self._check_assembly_contract_coverage(
                required_assembly_contracts=required_assembly_contracts,
                manifest_constraints=manifest_constraints,
            )
        )
        checks.extend(
            self._check_part_frame_coverage(
                plan=plan,
                validation=validation_report,
                manifest_part_frames=manifest_part_frames,
            )
        )
        checks.extend(
            self._check_spatial_contracts(
                contracts=required_assembly_contracts,
                manifest_constraints=manifest_constraints,
                manifest_features=manifest_features,
                validation=validation_report,
            )
        )

        return self._build_report(checks)

    def _coerce_geometry_plan(
        self,
        geometry_plan: GeometryPlan | Mapping[str, Any],
    ) -> GeometryPlan:
        if isinstance(geometry_plan, GeometryPlan):
            return geometry_plan
        return GeometryPlan.model_validate(geometry_plan)

    def _coerce_validation_report(
        self,
        validation: ValidationReport | Mapping[str, Any],
    ) -> ValidationReport:
        if isinstance(validation, ValidationReport):
            return validation
        return ValidationReport.model_validate(validation)

    def _resolve_build_manifest(
        self,
        validation: ValidationReport,
        build_manifest: Mapping[str, Any] | None,
    ) -> Mapping[str, Any] | None:
        if isinstance(build_manifest, Mapping):
            return build_manifest
        if isinstance(validation.build_manifest, Mapping):
            return validation.build_manifest
        generated_validation = validation.generated_validation
        if isinstance(generated_validation, Mapping):
            manifest = generated_validation.get("build_manifest")
            if isinstance(manifest, Mapping):
                return manifest
        return None

    def _required_feature_contracts(
        self,
        plan: GeometryPlan,
    ) -> dict[str, FeatureContract]:
        explicit_required = set(plan.required_features or [])
        return {
            contract.id: contract
            for contract in plan.feature_contracts
            if contract.required or contract.id in explicit_required
        }

    def _check_manifest_shape(self, manifest: Mapping[str, Any]) -> list[ContractCheck]:
        checks: list[ContractCheck] = []
        for key in ("features", "part_frames", "assembly_constraints"):
            value = manifest.get(key)
            checks.append(
                ContractCheck(
                    id=f"manifest.{key}",
                    category="manifest_shape",
                    status="pass" if isinstance(value, list) else "fail",
                    severity="critical" if not isinstance(value, list) else "info",
                    message=(
                        f"BUILD_MANIFEST[{key!r}] is a list."
                        if isinstance(value, list)
                        else f"BUILD_MANIFEST[{key!r}] must be a list."
                    ),
                    evidence={"actual_type": type(value).__name__},
                )
            )
        return checks

    def _manifest_items_by_id(self, value: Any) -> dict[str, Mapping[str, Any]]:
        if not isinstance(value, list):
            return {}
        result: dict[str, Mapping[str, Any]] = {}
        for item in value:
            if not isinstance(item, Mapping):
                continue
            item_id = item.get("id")
            if isinstance(item_id, str) and item_id:
                result[item_id] = item
        return result

    def _manifest_items_by_part(self, value: Any) -> dict[str, Mapping[str, Any]]:
        if not isinstance(value, list):
            return {}
        result: dict[str, Mapping[str, Any]] = {}
        for item in value:
            if not isinstance(item, Mapping):
                continue
            part = item.get("part")
            if isinstance(part, str) and part:
                result[part] = item
        return result

    def _check_feature_contracts(
        self,
        *,
        required_features: dict[str, FeatureContract],
        manifest_features: dict[str, Mapping[str, Any]],
    ) -> list[ContractCheck]:
        checks: list[ContractCheck] = []
        for feature_id, contract in required_features.items():
            manifest_feature = manifest_features.get(feature_id)
            if manifest_feature is None:
                checks.append(
                    ContractCheck(
                        id=feature_id,
                        category="feature_coverage",
                        status="fail",
                        severity="critical",
                        message="Required feature_contract id is missing from BUILD_MANIFEST.",
                        evidence={
                            "host_part": contract.host_part,
                            "type": contract.type,
                        },
                    )
                )
                continue

            mismatches = {}
            for field_name in ("host_part", "type", "axis", "count_group"):
                expected = getattr(contract, field_name)
                actual = manifest_feature.get(field_name)
                if expected is not None and actual is not None and actual != expected:
                    mismatches[field_name] = {"expected": expected, "actual": actual}

            checks.append(
                ContractCheck(
                    id=feature_id,
                    category="feature_consistency",
                    status="fail" if mismatches else "pass",
                    severity="major" if mismatches else "info",
                    message=(
                        "Manifest feature metadata matches the geometry plan."
                        if not mismatches
                        else "Manifest feature metadata differs from the geometry plan."
                    ),
                    evidence=mismatches or {"host_part": contract.host_part},
                )
            )
        return checks

    def _check_assembly_contract_coverage(
        self,
        *,
        required_assembly_contracts: dict[str, AssemblyContract],
        manifest_constraints: dict[str, Mapping[str, Any]],
    ) -> list[ContractCheck]:
        checks: list[ContractCheck] = []
        for contract_id, contract in required_assembly_contracts.items():
            manifest_constraint = manifest_constraints.get(contract_id)
            checks.append(
                ContractCheck(
                    id=contract_id,
                    category="assembly_contract_coverage",
                    status="pass" if manifest_constraint is not None else "fail",
                    severity="major" if manifest_constraint is None else "info",
                    message=(
                        "Assembly contract id is present in BUILD_MANIFEST."
                        if manifest_constraint is not None
                        else "Assembly contract id is missing from BUILD_MANIFEST."
                    ),
                    evidence={
                        "type": contract.type,
                        "parts": contract.parts,
                    },
                )
            )
        return checks

    def _check_part_frame_coverage(
        self,
        *,
        plan: GeometryPlan,
        validation: ValidationReport,
        manifest_part_frames: dict[str, Mapping[str, Any]],
    ) -> list[ContractCheck]:
        checks: list[ContractCheck] = []
        planned_parts = {frame.part for frame in plan.part_frames if frame.part}
        for part in sorted(planned_parts):
            checks.append(
                ContractCheck(
                    id=f"part_frame.{part}",
                    category="part_frame_coverage",
                    status="pass" if part in manifest_part_frames else "fail",
                    severity="major" if part not in manifest_part_frames else "info",
                    message=(
                        "Planned part frame is present in BUILD_MANIFEST."
                        if part in manifest_part_frames
                        else "Planned part frame is missing from BUILD_MANIFEST."
                    ),
                )
            )

        child_by_name = self._child_metadata_by_name(validation)
        if not child_by_name:
            return checks

        for part, frame in manifest_part_frames.items():
            checks.append(
                ContractCheck(
                    id=f"child_metadata.{part}",
                    category="child_metadata_coverage",
                    status="pass" if part in child_by_name else "fail",
                    severity="major" if part not in child_by_name else "info",
                    message=(
                        "Manifest part frame matches an executed assembly child."
                        if part in child_by_name
                        else "Manifest part frame does not match any executed assembly child."
                    ),
                    evidence={"child_names": sorted(child_by_name)},
                )
            )
            if part in child_by_name:
                checks.extend(
                    self._compare_manifest_frame_to_child(
                        part,
                        frame,
                        child_by_name[part],
                    )
                )

        return checks

    def _compare_manifest_frame_to_child(
        self,
        part: str,
        frame: Mapping[str, Any],
        child: Any,
    ) -> list[ContractCheck]:
        checks: list[ContractCheck] = []
        expected_center = self._as_vector3(frame.get("center_mm"))
        actual_center = self._as_vector3(getattr(child, "center_mm", None))
        expected_bbox = self._as_vector3(frame.get("bbox_mm"))
        actual_bbox = self._as_vector3(getattr(child, "bounding_box_mm", None))

        if expected_center is not None and actual_center is not None:
            center_delta = max(
                abs(a - b)
                for a, b in zip(expected_center, actual_center, strict=True)
            )
            checks.append(
                ContractCheck(
                    id=f"part_frame_center.{part}",
                    category="part_frame_accuracy",
                    status="pass" if center_delta <= 0.25 else "fail",
                    severity="major" if center_delta > 0.25 else "info",
                    message=(
                        "Manifest part center matches executed child center."
                        if center_delta <= 0.25
                        else "Manifest part center differs from executed child center."
                    ),
                    evidence={
                        "expected_center_mm": expected_center,
                        "actual_center_mm": actual_center,
                        "max_delta_mm": center_delta,
                    },
                )
            )

        if expected_bbox is not None and actual_bbox is not None:
            bbox_delta = max(abs(a - b) for a, b in zip(expected_bbox, actual_bbox, strict=True))
            checks.append(
                ContractCheck(
                    id=f"part_frame_bbox.{part}",
                    category="part_frame_accuracy",
                    status="pass" if bbox_delta <= 0.5 else "warn",
                    severity="minor" if bbox_delta > 0.5 else "info",
                    message=(
                        "Manifest part bounding box matches executed child metadata."
                        if bbox_delta <= 0.5
                        else "Manifest part bounding box differs from executed child metadata."
                    ),
                    evidence={
                        "expected_bbox_mm": expected_bbox,
                        "actual_bbox_mm": actual_bbox,
                        "max_delta_mm": bbox_delta,
                    },
                )
            )
        return checks

    def _check_spatial_contracts(
        self,
        *,
        contracts: dict[str, AssemblyContract],
        manifest_constraints: dict[str, Mapping[str, Any]],
        manifest_features: dict[str, Mapping[str, Any]],
        validation: ValidationReport,
    ) -> list[ContractCheck]:
        checks: list[ContractCheck] = []
        child_by_name = self._child_metadata_by_name(validation)
        for contract_id, contract in contracts.items():
            if contract_id not in manifest_constraints:
                continue

            contract_type = contract.type.lower()
            if contract_type == "centered":
                checks.append(self._check_centered_contract(contract, child_by_name))
            elif contract_type == "coaxial":
                checks.append(
                    self._check_coaxial_contract(contract, manifest_features)
                )
            elif contract_type == "above":
                checks.append(self._check_above_contract(contract, child_by_name))
            elif contract_type == "between":
                checks.append(self._check_between_contract(contract, child_by_name))
            elif contract_type == "no_intersection":
                checks.append(
                    self._check_no_intersection_contract(contract, child_by_name)
                )
            else:
                checks.append(
                    ContractCheck(
                        id=contract.id,
                        category="spatial_contract",
                        status="skip",
                        severity="info",
                        message=(
                            f"No deterministic checker is implemented for "
                            f"assembly contract type {contract.type!r}."
                        ),
                    )
                )
        return checks

    def _check_centered_contract(
        self,
        contract: AssemblyContract,
        child_by_name: dict[str, Any],
    ) -> ContractCheck:
        parts = contract.parts
        axes = self._axis_indices(contract.axes or ["X", "Y"])
        centers = self._child_centers(parts, child_by_name)
        if len(centers) != len(parts):
            return self._skip_missing_child_check(contract, "centered")

        tolerance = contract.tolerance_mm if contract.tolerance_mm is not None else 0.25
        deltas = {
            axis: max(center[index] for center in centers.values())
            - min(center[index] for center in centers.values())
            for axis, index in axes.items()
        }
        max_delta = max(deltas.values(), default=0.0)
        passed = max_delta <= tolerance
        return ContractCheck(
            id=contract.id,
            category="spatial_contract",
            status="pass" if passed else "fail",
            severity="major" if not passed else "info",
            message=(
                "Part centers satisfy centered assembly contract."
                if passed
                else "Part centers violate centered assembly contract."
            ),
            evidence={"deltas_mm": deltas, "tolerance_mm": tolerance},
        )

    def _check_coaxial_contract(
        self,
        contract: AssemblyContract,
        manifest_features: dict[str, Mapping[str, Any]],
    ) -> ContractCheck:
        feature_refs = contract.feature_refs
        axis = (contract.axes or ["Z"])[0].upper()
        axis_index = AXIS_INDEX.get(axis)
        if axis_index is None:
            return self._skip_contract(contract, f"Unknown coaxial axis {axis!r}.")

        centers: dict[str, list[float]] = {}
        for feature_ref in feature_refs:
            feature = manifest_features.get(feature_ref)
            if feature is None:
                continue
            center = self._as_vector3(feature.get("center_mm"))
            if center is not None:
                centers[feature_ref] = center

        if len(centers) < 2:
            return self._skip_contract(
                contract,
                "Coaxial check needs at least two numeric feature centers.",
            )

        tolerance = contract.tolerance_mm if contract.tolerance_mm is not None else 0.25
        perpendicular_indices = [
            index for index in range(3) if index != axis_index
        ]
        deltas = {}
        for index in perpendicular_indices:
            values = [center[index] for center in centers.values()]
            deltas[index] = max(values) - min(values)
        max_delta = max(deltas.values(), default=0.0)
        passed = max_delta <= tolerance
        return ContractCheck(
            id=contract.id,
            category="spatial_contract",
            status="pass" if passed else "fail",
            severity="major" if not passed else "info",
            message=(
                "Feature centers satisfy coaxial assembly contract."
                if passed
                else "Feature centers violate coaxial assembly contract."
            ),
            evidence={
                "axis": axis,
                "centers_mm": centers,
                "perpendicular_deltas_mm": deltas,
                "tolerance_mm": tolerance,
            },
        )

    def _check_above_contract(
        self,
        contract: AssemblyContract,
        child_by_name: dict[str, Any],
    ) -> ContractCheck:
        if len(contract.parts) < 2:
            return self._skip_contract(contract, "Above check needs two parts.")
        axis = (contract.axes or ["Z"])[0].upper()
        axis_index = AXIS_INDEX.get(axis)
        if axis_index is None:
            return self._skip_contract(contract, f"Unknown above axis {axis!r}.")
        centers = self._child_centers(contract.parts[:2], child_by_name)
        if len(centers) < 2:
            return self._skip_missing_child_check(contract, "above")

        lower, upper = contract.parts[:2]
        passed = centers[upper][axis_index] > centers[lower][axis_index]
        return ContractCheck(
            id=contract.id,
            category="spatial_contract",
            status="pass" if passed else "fail",
            severity="major" if not passed else "info",
            message=(
                "Second part is above the first on the declared axis."
                if passed
                else "Second part is not above the first on the declared axis."
            ),
            evidence={
                "axis": axis,
                lower: centers[lower],
                upper: centers[upper],
            },
        )

    def _check_between_contract(
        self,
        contract: AssemblyContract,
        child_by_name: dict[str, Any],
    ) -> ContractCheck:
        if len(contract.parts) < 3:
            return self._skip_contract(contract, "Between check needs at least three parts.")
        axis = (contract.axes or ["Z"])[0].upper()
        axis_index = AXIS_INDEX.get(axis)
        if axis_index is None:
            return self._skip_contract(contract, f"Unknown between axis {axis!r}.")
        centers = self._child_centers(contract.parts, child_by_name)
        if len(centers) != len(contract.parts):
            return self._skip_missing_child_check(contract, "between")

        bound_a = centers[contract.parts[0]][axis_index]
        bound_b = centers[contract.parts[1]][axis_index]
        low, high = sorted((bound_a, bound_b))
        out_of_range = {
            part: centers[part][axis_index]
            for part in contract.parts[2:]
            if not low <= centers[part][axis_index] <= high
        }
        passed = not out_of_range
        return ContractCheck(
            id=contract.id,
            category="spatial_contract",
            status="pass" if passed else "fail",
            severity="major" if not passed else "info",
            message=(
                "Intermediate parts lie between the first two parts on the declared axis."
                if passed
                else "One or more parts are not between the declared bounding parts."
            ),
            evidence={
                "axis": axis,
                "bounds": [low, high],
                "out_of_range": out_of_range,
            },
        )

    def _check_no_intersection_contract(
        self,
        contract: AssemblyContract,
        child_by_name: dict[str, Any],
    ) -> ContractCheck:
        if len(contract.parts) < 2:
            return self._skip_contract(contract, "No-intersection check needs two parts.")
        children = [child_by_name.get(part) for part in contract.parts]
        if any(child is None for child in children):
            return self._skip_missing_child_check(contract, "no_intersection")

        intersections: list[list[str]] = []
        for first_index, first_part in enumerate(contract.parts):
            for second_part in contract.parts[first_index + 1 :]:
                first = child_by_name[first_part]
                second = child_by_name[second_part]
                if self._aabb_intersects(first, second):
                    intersections.append([first_part, second_part])

        passed = not intersections
        return ContractCheck(
            id=contract.id,
            category="spatial_contract",
            status="pass" if passed else "fail",
            severity="major" if not passed else "info",
            message=(
                "Declared parts do not intersect by axis-aligned bounding boxes."
                if passed
                else "Declared parts have overlapping axis-aligned bounding boxes."
            ),
            evidence={"intersections": intersections},
        )

    def _child_metadata_by_name(self, validation: ValidationReport) -> dict[str, Any]:
        geometry = validation.geometry_report
        if geometry is None or not geometry.child_metadata:
            return {}
        return {
            child.name: child
            for child in geometry.child_metadata
            if child.name
        }

    def _child_centers(
        self,
        parts: list[str],
        child_by_name: dict[str, Any],
    ) -> dict[str, list[float]]:
        centers: dict[str, list[float]] = {}
        for part in parts:
            child = child_by_name.get(part)
            if child is None:
                continue
            center = self._as_vector3(getattr(child, "center_mm", None))
            if center is not None:
                centers[part] = center
        return centers

    def _axis_indices(self, axes: list[str]) -> dict[str, int]:
        result: dict[str, int] = {}
        for axis in axes:
            axis_key = axis.upper()
            if axis_key in AXIS_INDEX:
                result[axis_key] = AXIS_INDEX[axis_key]
        return result

    def _as_vector3(self, value: Any) -> list[float] | None:
        if not isinstance(value, list) or len(value) != 3:
            return None
        result: list[float] = []
        for item in value:
            if not isinstance(item, int | float):
                return None
            result.append(float(item))
        return result

    def _aabb_intersects(self, first: Any, second: Any) -> bool:
        first_center = self._as_vector3(getattr(first, "center_mm", None))
        second_center = self._as_vector3(getattr(second, "center_mm", None))
        first_bbox = self._as_vector3(getattr(first, "bounding_box_mm", None))
        second_bbox = self._as_vector3(getattr(second, "bounding_box_mm", None))
        if (
            first_center is None
            or second_center is None
            or first_bbox is None
            or second_bbox is None
        ):
            return False

        for index in range(3):
            distance = abs(first_center[index] - second_center[index])
            combined_half_length = (first_bbox[index] + second_bbox[index]) / 2
            if distance >= combined_half_length:
                return False
        return True

    def _skip_missing_child_check(
        self,
        contract: AssemblyContract,
        check_name: str,
    ) -> ContractCheck:
        return self._skip_contract(
            contract,
            f"{check_name} check could not find numeric child metadata for all parts.",
        )

    def _skip_contract(self, contract: AssemblyContract, message: str) -> ContractCheck:
        return ContractCheck(
            id=contract.id,
            category="spatial_contract",
            status="skip",
            severity="info",
            message=message,
            evidence={"parts": contract.parts, "axes": contract.axes},
        )

    def _build_report(self, checks: list[ContractCheck]) -> ContractValidationReport:
        failure_count = sum(1 for check in checks if check.status == "fail")
        warning_count = sum(1 for check in checks if check.status == "warn")
        skipped_count = sum(1 for check in checks if check.status == "skip")

        if failure_count:
            status = "fail"
            passed = False
        elif warning_count:
            status = "warn"
            passed = True
        elif skipped_count == len(checks):
            status = "skip"
            passed = True
        else:
            status = "pass"
            passed = True

        compact_evidence = [
            f"{check.status}:{check.id}:{check.message}"
            for check in checks
            if check.status in {"fail", "warn"}
        ][:12]

        summary = (
            f"{failure_count} failed, {warning_count} warned, "
            f"{skipped_count} skipped, {len(checks)} total contract checks."
        )

        return ContractValidationReport(
            status=status,
            passed=passed,
            summary=summary,
            checks=checks,
            failure_count=failure_count,
            warning_count=warning_count,
            skipped_count=skipped_count,
            compact_evidence=compact_evidence,
        )
