from __future__ import annotations

import ast
import json
import logging
import re
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from cadpilotv3.agents.code_generation_infill_agent import (
    CodeGenerationInfillAgent,
)
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.repair import RepairOutput
from cadpilotv3.shared import LLMTextResult, coerce_llm_text_result
from cadpilotv3.shared.llm_trace import update_llm_trace

logger = logging.getLogger(__name__)


class CodeGenerationOutputError(ValueError):
    """Raised when the code generation model returns unusable script text."""


class CodePatchApplicationError(ValueError):
    """Raised when a repair patch cannot be applied without corrupting the script."""


DISALLOWED_IMPLICIT_HOLE_METHODS = frozenset({"hole", "cboreHole", "cskHole"})
CADQUERY_IMPORT_LINE = "import cadquery as cq"
PUBLIC_ENTRYPOINT_RESULT_NAMES = {
    "build_part": "model",
    "build_assembly": "assembly",
}
RESULT_OBJECT_NAMES = frozenset({"model", "assembly", "result", "final_geometry"})
REQUIRED_SUPPORT_FUNCTIONS = frozenset({"validate_geometry", "export_all"})
BUILD_MANIFEST_NAME = "BUILD_MANIFEST"
REQUIRED_BUILD_MANIFEST_KEYS = frozenset(
    {
        "features",
        "part_frames",
        "assembly_constraints",
    }
)
DISALLOWED_VALIDATE_GEOMETRY_CALLS = frozenset(
    {
        "build_part",
        "build_assembly",
        "export_all",
    }
)
DISALLOWED_VALIDATE_GEOMETRY_METHODS = frozenset(
    {
        "cut",
        "union",
        "intersect",
        "fillet",
        "chamfer",
        "shell",
        "extrude",
        "loft",
        "save",
        "export",
    }
)
DISALLOWED_VALIDATION_HEURISTIC_KEYS = frozenset(
    {
        "bbox_matches",
        "bounding_box_matches",
        "dimensions_match",
        "exact_dimensions",
        "expected_bbox",
        "expected_bounding_box",
        "expected_final_volume",
        "expected_final_volume_upper_bound",
        "expected_part_volume",
        "expected_plate_volume",
        "expected_volume",
        "volume_ratio",
        "volume_reasonable",
        "volume_reduced_by_holes",
        "volume_threshold",
    }
)


CodeGenerationStreamEventType = Literal[
    "code_generation_start",
    "code_chunk",
    "code_generation_retry",
    "code_generation_complete",
    "code_generation_error",
]


@dataclass(frozen=True)
class CodeGenerationStreamEvent:
    event_type: CodeGenerationStreamEventType
    attempt_number: int
    payload: dict[str, Any] = field(default_factory=dict)


class CodeGenerationInfillService:
    max_generation_attempts = 3

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.agent = CodeGenerationInfillAgent(settings)

    def execute_script(
        self,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        repair_context: RepairOutput | None = None,
        critic_feedback: str | None = None,
        current_script: str | None = None,
    ) -> str:
        logger.info(
            "Running code_generation_agent for complete script",
            extra={"component": getattr(spec, "component", None)},
        )

        generation_feedback = None
        last_error: CodeGenerationOutputError | None = None
        compact_retry = False

        for attempt_number in range(1, self.max_generation_attempts + 1):
            llm_result = coerce_llm_text_result(
                self.agent.run(
                    spec=spec,
                    geometry_plan=geometry_plan,
                    parameters=parameters,
                    repair_context=repair_context,
                    critic_feedback=critic_feedback,
                    current_script=current_script,
                    generation_feedback=generation_feedback,
                    compact_retry=compact_retry,
                )
            )
            implemented_script = self._extract_generated_code(llm_result.text)
            update_llm_trace(
                llm_result.trace_dir,
                metadata_updates={
                    "extracted_script_length_chars": len(implemented_script),
                },
                files={"extracted_script.py": implemented_script},
            )

            try:
                self._validate_generated_code(implemented_script)
            except CodeGenerationOutputError as exc:
                last_error = exc
                generation_feedback = str(exc)
                compact_retry = self._should_use_compact_retry(exc)
                update_llm_trace(
                    llm_result.trace_dir,
                    metadata_updates={
                        "validation_status": "failed",
                        "validation_error": str(exc),
                        "compact_retry_next": compact_retry,
                    },
                )
                artifact_path = self._write_failed_attempt(
                    llm_result=llm_result,
                    implemented_script=implemented_script,
                    attempt_number=attempt_number,
                    reason=str(exc),
                    compact_retry=compact_retry,
                )
                logger.warning(
                    (
                        "Code generation returned unusable output; retrying "
                        f"reason={exc}"
                    ),
                    extra={
                        "attempt_number": attempt_number,
                        "max_attempts": self.max_generation_attempts,
                        "reason": str(exc),
                        "artifact_path": str(artifact_path) if artifact_path else None,
                        "raw_response_length_chars": len(llm_result.text),
                        "extracted_script_length_chars": len(implemented_script),
                        "compact_retry_next": compact_retry,
                    },
                )
                continue

            update_llm_trace(
                llm_result.trace_dir,
                metadata_updates={"validation_status": "passed"},
            )
            logger.info(
                "Implemented complete CadQuery script",
                extra={
                    "output_length_chars": len(implemented_script),
                    "attempt_number": attempt_number,
                },
            )

            return implemented_script

        raise last_error or CodeGenerationOutputError("Code generation failed validation")

    async def aexecute_script(
        self,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        repair_context: RepairOutput | None = None,
        critic_feedback: str | None = None,
        current_script: str | None = None,
    ) -> str:
        logger.info(
            "Running code_generation_agent for complete script",
            extra={"component": getattr(spec, "component", None)},
        )

        generation_feedback = None
        last_error: CodeGenerationOutputError | None = None
        compact_retry = False

        for attempt_number in range(1, self.max_generation_attempts + 1):
            llm_result = coerce_llm_text_result(
                await self.agent.arun(
                    spec=spec,
                    geometry_plan=geometry_plan,
                    parameters=parameters,
                    repair_context=repair_context,
                    critic_feedback=critic_feedback,
                    current_script=current_script,
                    generation_feedback=generation_feedback,
                    compact_retry=compact_retry,
                )
            )
            implemented_script = self._extract_generated_code(llm_result.text)
            update_llm_trace(
                llm_result.trace_dir,
                metadata_updates={
                    "extracted_script_length_chars": len(implemented_script),
                },
                files={"extracted_script.py": implemented_script},
            )

            try:
                self._validate_generated_code(implemented_script)
            except CodeGenerationOutputError as exc:
                last_error = exc
                generation_feedback = str(exc)
                compact_retry = self._should_use_compact_retry(exc)
                update_llm_trace(
                    llm_result.trace_dir,
                    metadata_updates={
                        "validation_status": "failed",
                        "validation_error": str(exc),
                        "compact_retry_next": compact_retry,
                    },
                )
                artifact_path = self._write_failed_attempt(
                    llm_result=llm_result,
                    implemented_script=implemented_script,
                    attempt_number=attempt_number,
                    reason=str(exc),
                    compact_retry=compact_retry,
                )
                logger.warning(
                    (
                        "Code generation returned unusable output; retrying "
                        f"reason={exc}"
                    ),
                    extra={
                        "attempt_number": attempt_number,
                        "max_attempts": self.max_generation_attempts,
                        "reason": str(exc),
                        "artifact_path": str(artifact_path) if artifact_path else None,
                        "raw_response_length_chars": len(llm_result.text),
                        "extracted_script_length_chars": len(implemented_script),
                        "compact_retry_next": compact_retry,
                    },
                )
                continue

            update_llm_trace(
                llm_result.trace_dir,
                metadata_updates={"validation_status": "passed"},
            )
            logger.info(
                "Implemented complete CadQuery script",
                extra={
                    "output_length_chars": len(implemented_script),
                    "attempt_number": attempt_number,
                },
            )

            return implemented_script

        raise last_error or CodeGenerationOutputError("Code generation failed validation")

    async def astream_script(
        self,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        repair_context: RepairOutput | None = None,
        critic_feedback: str | None = None,
        current_script: str | None = None,
    ) -> AsyncIterator[CodeGenerationStreamEvent]:
        logger.info(
            "Streaming code_generation_agent for complete script",
            extra={"component": getattr(spec, "component", None)},
        )

        generation_feedback = None
        last_error: CodeGenerationOutputError | None = None
        compact_retry = False

        for attempt_number in range(1, self.max_generation_attempts + 1):
            yield CodeGenerationStreamEvent(
                event_type="code_generation_start",
                attempt_number=attempt_number,
                payload={
                    "compact_retry": compact_retry,
                    "has_generation_feedback": generation_feedback is not None,
                },
            )

            llm_result: LLMTextResult | None = None
            async for stream_chunk in self.agent.astream(
                spec=spec,
                geometry_plan=geometry_plan,
                parameters=parameters,
                repair_context=repair_context,
                critic_feedback=critic_feedback,
                current_script=current_script,
                generation_feedback=generation_feedback,
                compact_retry=compact_retry,
            ):
                if stream_chunk.result is not None:
                    llm_result = stream_chunk.result
                    continue
                if stream_chunk.text:
                    yield CodeGenerationStreamEvent(
                        event_type="code_chunk",
                        attempt_number=attempt_number,
                        payload={"text": stream_chunk.text},
                    )

            if llm_result is None:
                llm_result = LLMTextResult(
                    text="",
                    response_metadata={},
                    usage_metadata=None,
                    response_id=None,
                    raw_response_repr="",
                    trace_dir=None,
                )

            implemented_script = self._extract_generated_code(llm_result.text)
            update_llm_trace(
                llm_result.trace_dir,
                metadata_updates={
                    "extracted_script_length_chars": len(implemented_script),
                },
                files={"extracted_script.py": implemented_script},
            )

            try:
                self._validate_generated_code(implemented_script)
            except CodeGenerationOutputError as exc:
                last_error = exc
                generation_feedback = str(exc)
                compact_retry = self._should_use_compact_retry(exc)
                update_llm_trace(
                    llm_result.trace_dir,
                    metadata_updates={
                        "validation_status": "failed",
                        "validation_error": str(exc),
                        "compact_retry_next": compact_retry,
                    },
                )
                artifact_path = self._write_failed_attempt(
                    llm_result=llm_result,
                    implemented_script=implemented_script,
                    attempt_number=attempt_number,
                    reason=str(exc),
                    compact_retry=compact_retry,
                )
                logger.warning(
                    (
                        "Code generation returned unusable output; retrying "
                        f"reason={exc}"
                    ),
                    extra={
                        "attempt_number": attempt_number,
                        "max_attempts": self.max_generation_attempts,
                        "reason": str(exc),
                        "artifact_path": str(artifact_path) if artifact_path else None,
                        "raw_response_length_chars": len(llm_result.text),
                        "extracted_script_length_chars": len(implemented_script),
                        "compact_retry_next": compact_retry,
                    },
                )
                yield CodeGenerationStreamEvent(
                    event_type="code_generation_retry",
                    attempt_number=attempt_number,
                    payload={
                        "reason": str(exc),
                        "compact_retry_next": compact_retry,
                        "will_retry": attempt_number < self.max_generation_attempts,
                    },
                )
                continue

            update_llm_trace(
                llm_result.trace_dir,
                metadata_updates={"validation_status": "passed"},
            )
            logger.info(
                "Implemented complete CadQuery script",
                extra={
                    "output_length_chars": len(implemented_script),
                    "attempt_number": attempt_number,
                },
            )
            yield CodeGenerationStreamEvent(
                event_type="code_generation_complete",
                attempt_number=attempt_number,
                payload={
                    "script": implemented_script,
                    "script_length_chars": len(implemented_script),
                },
            )
            return

        error = last_error or CodeGenerationOutputError("Code generation failed validation")
        yield CodeGenerationStreamEvent(
            event_type="code_generation_error",
            attempt_number=self.max_generation_attempts,
            payload={
                "error_class": type(error).__name__,
                "error_message": str(error),
            },
        )
        raise error

    def _should_use_compact_retry(self, _error: CodeGenerationOutputError) -> bool:
        # Every CodeGenerationOutputError raised here is a pre-execution output
        # contract failure: empty text, non-Python/prose, syntax error, forbidden
        # API usage, missing entrypoints, or an invalid script skeleton. The next
        # attempt should therefore use the compact corrective prompt instead of
        # re-sending the full context that allowed the output to drift.
        return True

    def _write_failed_attempt(
        self,
        *,
        llm_result: LLMTextResult,
        implemented_script: str,
        attempt_number: int,
        reason: str,
        compact_retry: bool,
    ) -> Path | None:
        try:
            settings = getattr(self, "settings", None)
            artifacts_dir = getattr(settings, "cad_artifacts_dir", "artifacts")
            run_dir = (
                Path(artifacts_dir)
                / "codegen_failed_attempts"
                / f"attempt_{uuid.uuid4().hex}"
            )
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "raw_response.txt").write_text(
                llm_result.text,
                encoding="utf-8",
            )
            (run_dir / "generated_script.py").write_text(
                implemented_script,
                encoding="utf-8",
            )
            (run_dir / "metadata.json").write_text(
                json.dumps(
                    {
                        "attempt_number": attempt_number,
                        "max_attempts": self.max_generation_attempts,
                        "reason": reason,
                        "raw_response_length_chars": len(llm_result.text),
                        "extracted_script_length_chars": len(implemented_script),
                        "response_metadata": llm_result.response_metadata,
                        "usage_metadata": llm_result.usage_metadata,
                        "response_id": llm_result.response_id,
                        "compact_retry_next": compact_retry,
                        "raw_response_repr": llm_result.raw_response_repr[:4000],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            return run_dir
        except OSError:
            logger.exception("Failed to persist rejected codegen attempt")
            return None

    def _validate_generated_code(self, implemented_script: str) -> None:
        if not implemented_script.strip():
            raise CodeGenerationOutputError("Code generation returned an empty script")

        script_lines = implemented_script.splitlines()
        if not script_lines or script_lines[0] != CADQUERY_IMPORT_LINE:
            raise CodeGenerationOutputError(
                "Generated script must start with exactly: import cadquery as cq"
            )

        if "cadquery" not in implemented_script:
            raise CodeGenerationOutputError(
                "Code generation returned text that does not appear to import CadQuery"
            )

        self._preflight_generated_code(implemented_script)

    def _preflight_generated_code(self, implemented_script: str) -> None:
        try:
            tree = ast.parse(implemented_script)
        except SyntaxError as exc:
            raise CodeGenerationOutputError(f"Generated script has a syntax error: {exc}") from exc

        function_names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        entrypoint_names = [
            name for name in PUBLIC_ENTRYPOINT_RESULT_NAMES if name in function_names
        ]

        if not entrypoint_names:
            raise CodeGenerationOutputError(
                "Generated script must define build_part() or build_assembly()"
            )
        if len(entrypoint_names) > 1:
            raise CodeGenerationOutputError(
                "Generated script must define exactly one public entrypoint: "
                "build_part() or build_assembly()"
            )

        missing_support_functions = REQUIRED_SUPPORT_FUNCTIONS - function_names
        if missing_support_functions:
            missing = ", ".join(sorted(f"{name}()" for name in missing_support_functions))
            raise CodeGenerationOutputError(f"Generated script must define {missing}")

        validate_geometry_function = self._find_function_def(tree, "validate_geometry")
        if validate_geometry_function is None:
            raise CodeGenerationOutputError("Generated script must define validate_geometry()")
        self._validate_generated_validation_function(validate_geometry_function)

        if any(isinstance(node, ast.Global) for node in ast.walk(tree)):
            raise CodeGenerationOutputError(
                "Generated script must not use global statements; use constants directly"
            )

        if any(self._is_disallowed_implicit_hole_call(node) for node in ast.walk(tree)):
            raise CodeGenerationOutputError(
                "Generated script must avoid Workplane.hole(), "
                "Workplane.cboreHole(), and Workplane.cskHole(); "
                "use explicit cutter solids and .cut()"
            )

        if any(self._is_disallowed_validation_heuristic_key(node) for node in ast.walk(tree)):
            raise CodeGenerationOutputError(
                "Generated script must not include brittle validation heuristic keys "
                "such as volume_reasonable, expected_volume, or expected_bounding_box; "
                "use positive-volume, part-count, and positive bounding-box checks only"
            )

        main_guards = [node for node in tree.body if self._is_main_guard(node)]
        if not main_guards:
            raise CodeGenerationOutputError("Generated script must include a __main__ export block")
        if len(main_guards) > 1:
            raise CodeGenerationOutputError(
                "Generated script must include only one __main__ export block"
            )

        entrypoint_name = entrypoint_names[0]
        self._validate_top_level_result_assignment(tree, main_guards[0])
        self._validate_main_guard_skeleton(main_guards[0], entrypoint_name)
        self._validate_build_manifest_contract(tree, validate_geometry_function)

    def _validate_top_level_result_assignment(
        self,
        tree: ast.Module,
        main_guard: ast.If,
    ) -> None:
        for node in tree.body:
            if node is main_guard:
                continue
            if self._assigns_to_result_name(node):
                raise CodeGenerationOutputError(
                    "Generated script must assign result geometry names "
                    "(model, assembly, result, final_geometry) only inside "
                    "the __main__ export block"
                )

    def _assigns_to_result_name(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Assign):
            return any(
                isinstance(target, ast.Name) and target.id in RESULT_OBJECT_NAMES
                for target in node.targets
            )
        return (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id in RESULT_OBJECT_NAMES
        )

    def _find_function_def(self, tree: ast.Module, function_name: str) -> ast.FunctionDef | None:
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return node
        return None

    def _validate_generated_validation_function(
        self,
        validate_geometry_function: ast.FunctionDef,
    ) -> None:
        for node in ast.walk(validate_geometry_function):
            if isinstance(node, ast.Assert):
                raise CodeGenerationOutputError(
                    "Generated validate_geometry() must not use assert statements; "
                    "return robust boolean checks in a dict"
                )
            if isinstance(node, ast.Raise):
                raise CodeGenerationOutputError(
                    "Generated validate_geometry() must not raise exceptions; "
                    "return robust boolean checks in a dict"
                )
            if self._is_disallowed_validate_geometry_call(node):
                raise CodeGenerationOutputError(
                    "Generated validate_geometry() must be side-effect-free; "
                    "do not rebuild, export, save, or modify geometry there"
                )

    def _is_disallowed_validate_geometry_call(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.Call):
            return False

        func = node.func
        if isinstance(func, ast.Name):
            return func.id in DISALLOWED_VALIDATE_GEOMETRY_CALLS
        return (
            isinstance(func, ast.Attribute)
            and func.attr in DISALLOWED_VALIDATE_GEOMETRY_METHODS
        )

    def _validate_main_guard_skeleton(
        self,
        main_guard: ast.If,
        entrypoint_name: str,
    ) -> None:
        result_name = PUBLIC_ENTRYPOINT_RESULT_NAMES[entrypoint_name]

        if not any(
            self._is_result_assignment_from_entrypoint(stmt, result_name, entrypoint_name)
            for stmt in main_guard.body
        ):
            raise CodeGenerationOutputError(
                "Generated script __main__ block must assign "
                f"{result_name} = {entrypoint_name}()"
            )

        if not self._main_guard_calls_function(main_guard, "validate_geometry", result_name):
            raise CodeGenerationOutputError(
                "Generated script __main__ block must call "
                f"validate_geometry({result_name})"
            )

        if not self._main_guard_calls_function(main_guard, "export_all", result_name):
            raise CodeGenerationOutputError(
                "Generated script __main__ block must call "
                f"export_all({result_name}, ...)"
            )

    def _validate_build_manifest_contract(
        self,
        tree: ast.Module,
        validate_geometry_function: ast.FunctionDef,
    ) -> None:
        manifest_value = self._find_top_level_assignment_value(tree, BUILD_MANIFEST_NAME)
        if manifest_value is None:
            raise CodeGenerationOutputError(
                "Generated script must define a top-level BUILD_MANIFEST dictionary"
            )

        if not isinstance(manifest_value, ast.Dict):
            raise CodeGenerationOutputError(
                "Generated BUILD_MANIFEST must be a literal dictionary"
            )

        manifest_keys = {
            key.value
            for key in manifest_value.keys
            if isinstance(key, ast.Constant) and isinstance(key.value, str)
        }
        missing_keys = REQUIRED_BUILD_MANIFEST_KEYS - manifest_keys
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise CodeGenerationOutputError(
                f"Generated BUILD_MANIFEST must include keys: {missing}"
            )

        for key, value in zip(manifest_value.keys, manifest_value.values, strict=True):
            if (
                isinstance(key, ast.Constant)
                and key.value in REQUIRED_BUILD_MANIFEST_KEYS
                and not isinstance(value, ast.List)
            ):
                raise CodeGenerationOutputError(
                    "Generated BUILD_MANIFEST keys features, part_frames, and "
                    "assembly_constraints must be lists"
                )

        if not any(
            isinstance(node, ast.Name) and node.id == BUILD_MANIFEST_NAME
            for node in ast.walk(validate_geometry_function)
        ):
            raise CodeGenerationOutputError(
                "Generated validate_geometry() must include BUILD_MANIFEST in "
                "its returned validation dictionary"
            )

    def _find_top_level_assignment_value(
        self,
        tree: ast.Module,
        assignment_name: str,
    ) -> ast.AST | None:
        for node in tree.body:
            if isinstance(node, ast.Assign):
                if any(
                    isinstance(target, ast.Name) and target.id == assignment_name
                    for target in node.targets
                ):
                    return node.value
            if (
                isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.target.id == assignment_name
            ):
                return node.value
        return None

    def _is_result_assignment_from_entrypoint(
        self,
        node: ast.AST,
        result_name: str,
        entrypoint_name: str,
    ) -> bool:
        if isinstance(node, ast.Assign):
            assigns_result = any(
                isinstance(target, ast.Name) and target.id == result_name
                for target in node.targets
            )
            return assigns_result and self._is_call_to_name(node.value, entrypoint_name)

        return (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == result_name
            and self._is_call_to_name(node.value, entrypoint_name)
        )

    def _is_call_to_name(self, node: ast.AST, function_name: str) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == function_name
        )

    def _main_guard_calls_function(
        self,
        main_guard: ast.If,
        function_name: str,
        result_name: str,
    ) -> bool:
        return any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == function_name
            and node.args
            and isinstance(node.args[0], ast.Name)
            and node.args[0].id == result_name
            for node in ast.walk(main_guard)
        )

    def _is_disallowed_implicit_hole_call(self, node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in DISALLOWED_IMPLICIT_HOLE_METHODS
        )

    def _is_main_guard(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.If):
            return False

        test = node.test
        if not isinstance(test, ast.Compare):
            return False
        if not isinstance(test.left, ast.Name) or test.left.id != "__name__":
            return False
        if len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
            return False
        if len(test.comparators) != 1:
            return False

        comparator = test.comparators[0]
        return isinstance(comparator, ast.Constant) and comparator.value == "__main__"

    def _is_disallowed_validation_heuristic_key(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value in DISALLOWED_VALIDATION_HEURISTIC_KEYS

        return (
            isinstance(node, ast.Name)
            and node.id in DISALLOWED_VALIDATION_HEURISTIC_KEYS
        )

    def _extract_generated_code(self, generated_text: str) -> str:
        text = generated_text.strip()
        full_fence = re.compile(
            r"^\s*```(?:python|py)?\s*\r?\n(?P<code>.*?)\r?\n```\s*$",
            re.IGNORECASE | re.DOTALL,
        )
        match = full_fence.match(text)
        if match:
            return match.group("code").strip() + "\n"

        python_fence = re.compile(
            r"```(?:python|py)\s*\r?\n(?P<code>.*?)\r?\n```",
            re.IGNORECASE | re.DOTALL,
        )
        match = python_fence.search(text)
        if match:
            return match.group("code").strip() + "\n"

        opening_fence = re.compile(
            r"^\s*```(?:python|py)?\s*\r?\n(?P<code>.*)$",
            re.IGNORECASE | re.DOTALL,
        )
        match = opening_fence.match(text)
        if match:
            return match.group("code").strip() + "\n"

        apostrophe_fence = re.compile(
            r"^\s*'''(?:python|py)?\s*\r?\n(?P<code>.*?)\r?\n'''\s*$",
            re.IGNORECASE | re.DOTALL,
        )
        match = apostrophe_fence.match(text)
        if match:
            return match.group("code").strip() + "\n"

        quoted_language_prefix = re.compile(
            r"^\s*['\"]{0,3}(?:python|py)['\"]{0,3}\s*\r?\n(?P<code>.*)$",
            re.IGNORECASE | re.DOTALL,
        )
        match = quoted_language_prefix.match(text)
        if match:
            return match.group("code").strip() + "\n"

        return text + "\n"

    def apply_function_implementation(
        self,
        current_script: str,
        function_name: str,
        implemented_function_code: str,
    ) -> str:
        updated_script = self._replace_function_definition(
            current_script=current_script,
            function_name=function_name,
            replacement_code=implemented_function_code,
        )

        if updated_script == current_script:
            raise CodePatchApplicationError(
                f"Could not replace function implementation for '{function_name}'"
            )

        return updated_script

    def apply_patch(
        self,
        current_script: str,
        affected_function: str,
        patched_code: str,
    ) -> str:
        if affected_function == "__main__":
            updated_script = self._replace_main_block(
                current_script=current_script,
                replacement_code=patched_code,
            )
        else:
            updated_script = self._replace_function_definition(
                current_script=current_script,
                function_name=affected_function,
                replacement_code=patched_code,
            )

        if updated_script == current_script:
            raise CodePatchApplicationError(
                f"Could not apply patch to function '{affected_function}'"
            )

        return updated_script

    def _replace_function_definition(
        self,
        current_script: str,
        function_name: str,
        replacement_code: str,
    ) -> str:
        lines = current_script.splitlines(keepends=True)
        pattern = re.compile(rf"^\s*def\s+{re.escape(function_name)}\s*\(", re.MULTILINE)
        start_index = next(
            (
                idx
                for idx, line in enumerate(lines)
                if pattern.match(line)
            ),
            None,
        )

        if start_index is None:
            return current_script

        indent = len(lines[start_index]) - len(lines[start_index].lstrip(" \t"))
        end_index = start_index + 1
        while end_index < len(lines):
            line = lines[end_index]
            if line.strip() == "":
                end_index += 1
                continue
            current_indent = len(line) - len(line.lstrip(" \t"))
            if current_indent <= indent:
                break
            end_index += 1

        replacement = replacement_code.rstrip() + "\n"
        return "".join(lines[:start_index] + [replacement] + lines[end_index:])

    def _replace_main_block(
        self,
        current_script: str,
        replacement_code: str,
    ) -> str:
        lines = current_script.splitlines(keepends=True)
        pattern = re.compile(r"""^if\s+__name__\s*==\s*["']__main__["']\s*:""")
        start_index = next(
            (
                idx
                for idx, line in enumerate(lines)
                if pattern.match(line)
            ),
            None,
        )

        if start_index is None:
            return current_script

        end_index = start_index + 1
        while end_index < len(lines):
            line = lines[end_index]
            if line.strip() == "":
                end_index += 1
                continue
            current_indent = len(line) - len(line.lstrip(" \t"))
            if current_indent == 0:
                break
            end_index += 1

        replacement = replacement_code.rstrip() + "\n"
        return "".join(lines[:start_index] + [replacement] + lines[end_index:])
