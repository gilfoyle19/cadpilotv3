from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cadquery as cq


@dataclass
class GeometryExportArtifact:
    format: str
    filename: str
    filepath: str
    size_kb: float
    contents: str


class GeometryExportService:
    def __init__(self, output_dir: str = "output") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(
        self,
        geometry_object: Any,
        component_name: str,
        output_format: str,
    ) -> list[GeometryExportArtifact]:
        fmt = output_format.upper()
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

        if fmt == "STEP":
            return self._export_step(geometry_object, component_name, timestamp)
        if fmt == "STL":
            return self._export_stl(geometry_object, component_name, timestamp)
        if fmt == "DXF":
            return self._export_dxf(geometry_object, component_name, timestamp)
        if fmt == "IGES":
            return self._export_iges(geometry_object, component_name, timestamp)

        raise ValueError(f"Unsupported export format: {output_format}")

    def _export_step(
        self,
        geometry_object: Any,
        component_name: str,
        timestamp: str,
    ) -> list[GeometryExportArtifact]:
        artifacts: list[GeometryExportArtifact] = []

        assembly_path = self.output_dir / f"{component_name}_assembly.step"
        assembly_ts_path = self.output_dir / f"{component_name}_assembly_{timestamp}.step"

        root_shape = self._coerce_exportable_shape(geometry_object)
        cq.exporters.export(root_shape, str(assembly_path))
        cq.exporters.export(root_shape, str(assembly_ts_path))

        artifacts.append(self._artifact("STEP", assembly_path, "Full assembly STEP export"))
        artifacts.append(self._artifact("STEP", assembly_ts_path, "Timestamped assembly STEP export"))

        for part_name, part_shape in self._iter_named_parts(geometry_object):
            part_path = self.output_dir / f"{component_name}_{part_name}.step"
            cq.exporters.export(part_shape, str(part_path))
            artifacts.append(self._artifact("STEP", part_path, f"Individual part STEP export: {part_name}"))

        return artifacts

    def _export_stl(
        self,
        geometry_object: Any,
        component_name: str,
        timestamp: str,
    ) -> list[GeometryExportArtifact]:
        artifacts: list[GeometryExportArtifact] = []

        for part_name, part_shape in self._iter_named_parts(geometry_object):
            part_path = self.output_dir / f"{component_name}_{part_name}.stl"
            cq.exporters.export(part_shape, str(part_path), opt={"ascii": True})
            artifacts.append(self._artifact("STL", part_path, f"Individual part STL export: {part_name}"))

        if not artifacts:
            assembly_path = self.output_dir / f"{component_name}_assembly_{timestamp}.stl"
            root_shape = self._coerce_exportable_shape(geometry_object)
            cq.exporters.export(root_shape, str(assembly_path), opt={"ascii": True})
            artifacts.append(self._artifact("STL", assembly_path, "Assembly STL export"))

        return artifacts

    def _export_dxf(
        self,
        geometry_object: Any,
        component_name: str,
        timestamp: str,
    ) -> list[GeometryExportArtifact]:
        root_shape = self._coerce_exportable_shape(geometry_object)
        bb = root_shape.BoundingBox()

        if bb.zlen > 1e-3:
            raise ValueError("DXF export is only valid for flat or 2D geometry.")

        dxf_path = self.output_dir / f"{component_name}_assembly_{timestamp}.dxf"
        cq.exporters.export(root_shape, str(dxf_path))

        return [self._artifact("DXF", dxf_path, "2D projection DXF export")]

    def _export_iges(
        self,
        geometry_object: Any,
        component_name: str,
        timestamp: str,
    ) -> list[GeometryExportArtifact]:
        iges_path = self.output_dir / f"{component_name}_assembly_{timestamp}.iges"
        root_shape = self._coerce_exportable_shape(geometry_object)
        cq.exporters.export(root_shape, str(iges_path))

        return [self._artifact("IGES", iges_path, "Assembly IGES export")]

    def _iter_named_parts(self, geometry_object: Any) -> list[tuple[str, Any]]:
        parts: list[tuple[str, Any]] = []

        if geometry_object.__class__.__name__ != "Assembly":
            shape = self._coerce_exportable_shape(geometry_object)
            return [("part", shape)]

        children = getattr(geometry_object, "children", None)

        if isinstance(children, dict):
            for name, child in children.items():
                shape = self._coerce_exportable_shape(getattr(child, "obj", None))
                if shape is not None:
                    parts.append((self._safe_name(name), shape))
        elif isinstance(children, list):
            for idx, child in enumerate(children, start=1):
                name = getattr(child, "name", None) or f"part_{idx}"
                shape = self._coerce_exportable_shape(getattr(child, "obj", None))
                if shape is not None:
                    parts.append((self._safe_name(name), shape))

        return parts

    def _coerce_exportable_shape(self, obj: Any) -> Any:
        if obj is None:
            raise ValueError("No geometry object available for export.")

        if hasattr(obj, "val") and callable(obj.val):
            return obj.val()

        if hasattr(obj, "BoundingBox") and hasattr(obj, "Volume"):
            return obj

        if obj.__class__.__name__ == "Assembly":
            if hasattr(obj, "toCompound") and callable(obj.toCompound):
                return obj.toCompound()
            if hasattr(obj, "compound") and callable(obj.compound):
                return obj.compound()

        if hasattr(obj, "obj") and obj.obj is not None:
            return self._coerce_exportable_shape(obj.obj)

        raise ValueError(f"Unsupported geometry object type for export: {type(obj)!r}")

    def _artifact(self, fmt: str, path: Path, contents: str) -> GeometryExportArtifact:
        size_kb = path.stat().st_size / 1024 if path.exists() else 0.0
        return GeometryExportArtifact(
            format=fmt,
            filename=path.name,
            filepath=str(path),
            size_kb=round(size_kb, 2),
            contents=contents,
        )

    def _safe_name(self, raw: str) -> str:
        return (
            raw.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )