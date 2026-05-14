from __future__ import annotations

import ast
import asyncio
import contextlib
import io
import json
import os
import time
import traceback
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class SandboxErrorLocation:
    line: int | None
    function: str | None
    code_line: str | None


@dataclass
class SandboxGeometryReport:
    part_count: int
    bounding_box_mm: list[float]
    volume_mm3: float
    is_manifold: bool
    face_count: int
    has_zero_volume_parts: bool
    assembly_valid: bool


@dataclass
class SandboxExecutionArtifacts:
    syntax_ok: bool
    execution_succeeded: bool
    stdout: str
    stderr: str
    execution_time_s: float
    error_type: str | None
    error_message: str | None
    traceback_text: str | None
    error_location: SandboxErrorLocation
    geometry_report: SandboxGeometryReport | None
    result_object_name: str | None
    workspace_dir: str


class CadQueryExecutionSandboxService:
    def __init__(
        self,
        base_work_dir: str = ".sandbox_runs",
    ) -> None:
        self.base_work_dir = Path(base_work_dir)
        self.base_work_dir.mkdir(parents=True, exist_ok=True)

    def execute(self, script: str) -> SandboxExecutionArtifacts:
        run_dir = self.base_work_dir / f"run_{uuid.uuid4().hex}"
        run_dir.mkdir(parents=True, exist_ok=True)

        syntax_error = self._precheck_syntax(script)
        if syntax_error is not None:
            return SandboxExecutionArtifacts(
                syntax_ok=False,
                execution_succeeded=False,
                stdout="",
                stderr=syntax_error["traceback_text"] or "",
                execution_time_s=0.0,
                error_type=syntax_error["error_type"],
                error_message=syntax_error["error_message"],
                traceback_text=syntax_error["traceback_text"],
                error_location=SandboxErrorLocation(
                    line=syntax_error["line"],
                    function=syntax_error["function"],
                    code_line=syntax_error["code_line"],
                ),
                geometry_report=None,
                result_object_name=None,
                workspace_dir=str(run_dir),
            )

        script_path = run_dir / "generated_script.py"
        script_path.write_text(script, encoding="utf-8")

        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        start = time.perf_counter()

        globals_dict: dict[str, Any] = {
            "__name__": "__main__",
            "__file__": str(script_path),
        }

        original_cwd = Path.cwd()
        result_object_name: str | None = None
        geometry_report: SandboxGeometryReport | None = None

        try:
            os.chdir(run_dir)
            with (
                contextlib.redirect_stdout(stdout_buffer),
                contextlib.redirect_stderr(stderr_buffer),
            ):
                exec(compile(script, str(script_path), "exec"), globals_dict, globals_dict)

            result_object_name = self._find_result_object_name(globals_dict)
            if result_object_name is None:
                result_object_name = self._materialize_result_object(globals_dict)
            if result_object_name is not None:
                geometry_report = self._inspect_geometry(globals_dict[result_object_name])

            execution_succeeded = True
            error_type = None
            error_message = None
            traceback_text = None
            error_location = SandboxErrorLocation(line=None, function=None, code_line=None)

        except Exception as exc:
            tb = traceback.TracebackException.from_exception(exc)
            traceback_text = "".join(tb.format())
            line, function, code_line = self._extract_error_location(exc, script.splitlines())

            execution_succeeded = False
            error_type = exc.__class__.__name__
            error_message = str(exc)
            error_location = SandboxErrorLocation(
                line=line,
                function=function,
                code_line=code_line,
            )

        finally:
            os.chdir(original_cwd)

        elapsed = time.perf_counter() - start

        artifacts = SandboxExecutionArtifacts(
            syntax_ok=True,
            execution_succeeded=execution_succeeded,
            stdout=stdout_buffer.getvalue(),
            stderr=stderr_buffer.getvalue(),
            execution_time_s=elapsed,
            error_type=error_type,
            error_message=error_message,
            traceback_text=traceback_text,
            error_location=error_location,
            geometry_report=geometry_report,
            result_object_name=result_object_name,
            workspace_dir=str(run_dir),
        )

        (run_dir / "execution_artifacts.json").write_text(
            json.dumps(self._to_jsonable(artifacts), indent=2),
            encoding="utf-8",
        )

        return artifacts

    async def aexecute(self, script: str) -> SandboxExecutionArtifacts:
        return await asyncio.to_thread(self.execute, script)

    def _precheck_syntax(self, script: str) -> dict[str, Any] | None:
        try:
            ast.parse(script)
            return None
        except SyntaxError as exc:
            lines = script.splitlines()
            line = exc.lineno
            code_line = lines[line - 1] if line and 1 <= line <= len(lines) else None
            return {
                "error_type": exc.__class__.__name__,
                "error_message": str(exc),
                "traceback_text": "".join(traceback.format_exception_only(type(exc), exc)),
                "line": line,
                "function": None,
                "code_line": code_line,
            }

    def _extract_error_location(
        self,
        exc: Exception,
        script_lines: list[str],
    ) -> tuple[int | None, str | None, str | None]:
        tb = exc.__traceback__
        extracted = traceback.extract_tb(tb)
        if not extracted:
            return None, None, None

        frame = extracted[-1]
        line = frame.lineno
        function = frame.name
        code_line = (
            script_lines[line - 1]
            if line and 1 <= line <= len(script_lines)
            else frame.line
        )
        return line, function, code_line

    def _find_result_object_name(self, globals_dict: dict[str, Any]) -> str | None:
        priority_names = [
            "assembly",
            "result",
            "model",
            "final_geometry",
        ]
        for name in priority_names:
            if name in globals_dict:
                return name

        for name, value in globals_dict.items():
            cls_name = value.__class__.__name__
            if cls_name in {"Assembly", "Workplane", "Shape", "Compound"}:
                return name

        return None

    def _materialize_result_object(self, globals_dict: dict[str, Any]) -> str | None:
        fallback_builders = [
            ("assembly", "build_assembly"),
            ("model", "build_part"),
        ]

        for result_name, builder_name in fallback_builders:
            builder = globals_dict.get(builder_name)
            if callable(builder):
                globals_dict[result_name] = builder()
                return result_name

        return None

    def _inspect_geometry(self, obj: Any) -> SandboxGeometryReport | None:
        try:
            __import__("cadquery")
        except Exception:
            return None

        try:
            if obj.__class__.__name__ == "Assembly":
                solids = self._extract_assembly_solids(obj)
                if not solids:
                    return SandboxGeometryReport(
                        part_count=0,
                        bounding_box_mm=[0.0, 0.0, 0.0],
                        volume_mm3=0.0,
                        is_manifold=False,
                        face_count=0,
                        has_zero_volume_parts=True,
                        assembly_valid=False,
                    )

                bbox = self._combined_bounding_box(solids)
                volume = sum(self._safe_volume(s) for s in solids)
                face_count = sum(self._safe_face_count(s) for s in solids)
                zero_volume = any(self._safe_volume(s) <= 1e-6 for s in solids)
                manifold = all(self._safe_is_valid(s) for s in solids)

                return SandboxGeometryReport(
                    part_count=len(solids),
                    bounding_box_mm=[bbox[0], bbox[1], bbox[2]],
                    volume_mm3=volume,
                    is_manifold=manifold,
                    face_count=face_count,
                    has_zero_volume_parts=zero_volume,
                    assembly_valid=manifold and not zero_volume,
                )

            shape = self._coerce_to_shape(obj)
            if shape is None:
                return None

            bb = shape.BoundingBox()
            volume = self._safe_volume(shape)
            face_count = self._safe_face_count(shape)
            manifold = self._safe_is_valid(shape)
            zero_volume = volume <= 1e-6

            return SandboxGeometryReport(
                part_count=1,
                bounding_box_mm=[bb.xlen, bb.ylen, bb.zlen],
                volume_mm3=volume,
                is_manifold=manifold,
                face_count=face_count,
                has_zero_volume_parts=zero_volume,
                assembly_valid=manifold and not zero_volume,
            )
        except Exception:
            return None

    def _extract_assembly_solids(self, assembly: Any) -> list[Any]:
        solids: list[Any] = []

        def walk(node: Any) -> None:
            obj = getattr(node, "obj", None)
            shape = self._coerce_to_shape(obj)
            if shape is not None:
                solids.append(shape)

            children = getattr(node, "children", None)
            if isinstance(children, list):
                for child in children:
                    walk(child)
            elif isinstance(children, dict):
                for child in children.values():
                    walk(child)

        walk(assembly)
        return solids

    def _coerce_to_shape(self, obj: Any) -> Any | None:
        if obj is None:
            return None

        if hasattr(obj, "val") and callable(obj.val):
            try:
                return obj.val()
            except Exception:
                pass

        if hasattr(obj, "BoundingBox") and hasattr(obj, "Volume"):
            return obj

        return None

    def _combined_bounding_box(self, shapes: list[Any]) -> tuple[float, float, float]:
        xmins, ymins, zmins = [], [], []
        xmaxs, ymaxs, zmaxs = [], [], []

        for shape in shapes:
            bb = shape.BoundingBox()
            xmins.append(bb.xmin)
            ymins.append(bb.ymin)
            zmins.append(bb.zmin)
            xmaxs.append(bb.xmax)
            ymaxs.append(bb.ymax)
            zmaxs.append(bb.zmax)

        return (
            max(xmaxs) - min(xmins),
            max(ymaxs) - min(ymins),
            max(zmaxs) - min(zmins),
        )

    def _safe_volume(self, shape: Any) -> float:
        try:
            return float(shape.Volume())
        except Exception:
            return 0.0

    def _safe_face_count(self, shape: Any) -> int:
        try:
            return len(shape.Faces())
        except Exception:
            return 0

    def _safe_is_valid(self, shape: Any) -> bool:
        try:
            if hasattr(shape, "isValid"):
                return bool(shape.isValid())
            return True
        except Exception:
            return False

    def _to_jsonable(self, artifacts: SandboxExecutionArtifacts) -> dict[str, Any]:
        data = asdict(artifacts)
        return data
