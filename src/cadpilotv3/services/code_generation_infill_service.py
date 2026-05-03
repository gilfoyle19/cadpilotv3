from __future__ import annotations

import logging
import re

from cadpilotv3.agents.code_generation_infill_agent import (
    CodeGenerationInfillAgent,
)
from cadpilotv3.config.settings import AppSettings


from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.repair import RepairOutput

logger = logging.getLogger(__name__)


class CodeGenerationInfillService:
    def __init__(self, settings: AppSettings) -> None:
        self.agent = CodeGenerationInfillAgent(settings)

    def execute(
        self,
        skeleton_script: str,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        function_name: str,
        repair_context: RepairOutput | None = None,
    ) -> str:
        logger.info(
            "Running code_generation_agent_stage_b",
            extra={"function_name": function_name},
        )

        implemented_function = self.agent.run(
            skeleton_script=skeleton_script,
            geometry_plan=geometry_plan,
            parameters=parameters,
            function_name=function_name,
            repair_context=repair_context,
        )

        logger.info(
            "Implemented CadQuery function",
            extra={
                "function_name": function_name,
                "output_length_chars": len(implemented_function),
            },
        )

        return implemented_function

    def list_functions_to_implement(
        self,
        skeleton_script: str,
        spec: IntentSpec | None = None,
    ) -> list[str]:
        logger.info(
            "Listing functions to implement from skeleton script",
            extra={"script_length_chars": len(skeleton_script)},
        )

        return self._extract_function_names_from_script(skeleton_script)

    def _extract_function_names_from_script(self, skeleton_script: str) -> list[str]:
        regex = re.compile(r"^\s*def\s+([A-Za-z_]\w*)\s*\(", re.MULTILINE)
        return list(dict.fromkeys(regex.findall(skeleton_script)))

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
            logger.warning(
                "Could not replace function implementation; appending implemented code",
                extra={"function_name": function_name},
            )
            updated_script = f"{current_script.rstrip()}\n\n{implemented_function_code.strip()}\n"

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
            logger.warning(
                "Could not apply patch to function; appending patched code",
                extra={"affected_function": affected_function},
            )
            updated_script = f"{current_script.rstrip()}\n\n{patched_code.strip()}\n"

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
