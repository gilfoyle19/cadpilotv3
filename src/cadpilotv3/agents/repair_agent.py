from __future__ import annotations

import re
from typing import Any

from cadpilotv3.agents.cheatsheet_safety import filter_forbidden_cheatsheet_blocks
from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.repair import RepairOutput
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.shared import ainvoke_pydantic, invoke_pydantic, load_prompt_text


class RepairAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        script: str,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        validation: ValidationReport,
        repair_attempt_count: int,
        repair_history: list[dict[str, Any]] | None = None,
        max_repair_attempts: int | None = None,
    ) -> RepairOutput:
        llm = self.llm_factory.get_for_agent(AgentName.REPAIR)
        prompt = self._build_prompt(
            script=script,
            geometry_plan=geometry_plan,
            parameters=parameters,
            validation=validation,
            repair_attempt_count=repair_attempt_count,
            repair_history=repair_history,
            max_repair_attempts=max_repair_attempts,
        )

        return invoke_pydantic(
            llm,
            prompt,
            RepairOutput,
            agent_name=AgentName.REPAIR.value,
            trace_metadata={"repair_attempt_count": repair_attempt_count},
        )

    async def arun(
        self,
        script: str,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        validation: ValidationReport,
        repair_attempt_count: int,
        repair_history: list[dict[str, Any]] | None = None,
        max_repair_attempts: int | None = None,
    ) -> RepairOutput:
        llm = self.llm_factory.get_for_agent(AgentName.REPAIR)
        prompt = self._build_prompt(
            script=script,
            geometry_plan=geometry_plan,
            parameters=parameters,
            validation=validation,
            repair_attempt_count=repair_attempt_count,
            repair_history=repair_history,
            max_repair_attempts=max_repair_attempts,
        )

        return await ainvoke_pydantic(
            llm,
            prompt,
            RepairOutput,
            agent_name=AgentName.REPAIR.value,
            trace_metadata={"repair_attempt_count": repair_attempt_count},
        )

    def _build_prompt(
        self,
        *,
        script: str,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        validation: ValidationReport,
        repair_attempt_count: int,
        repair_history: list[dict[str, Any]] | None = None,
        max_repair_attempts: int | None = None,
    ) -> str:
        system_prompt = load_prompt_text(self.settings, "repair_agent.md")
        few_shot_prompt = load_prompt_text(
            self.settings,
            "repair_agent_examples.md",
        )
        cadquery_cheatsheet = load_prompt_text(self.settings, "cheatsheet.md")
        selected_cheatsheet = self._select_relevant_cheatsheet(
            cheatsheet=cadquery_cheatsheet,
            script=script,
            geometry_plan=geometry_plan,
            parameters=parameters,
            validation=validation,
        )

        prompt = "\n\n".join(
            [
                system_prompt.strip(),
                few_shot_prompt.strip(),
                "Selected CadQuery 2.x API reference for repair:",
                selected_cheatsheet.strip(),
                "Current script:",
                script.strip(),
                "Geometry plan:",
                geometry_plan.model_dump_json(indent=2),
                "Parameter schema:",
                parameters.model_dump_json(indent=2),
                "Validation report:",
                validation.model_dump_json(indent=2),
                f"Repair attempt count: {repair_attempt_count}",
                self._format_repair_budget(max_repair_attempts),
                "Previous repair attempts:",
                self._format_repair_history(repair_history),
            ]
        )
        return prompt

    def _format_repair_budget(self, max_repair_attempts: int | None) -> str:
        if max_repair_attempts is None:
            return "Repair attempt budget: not provided"
        return f"Repair attempt budget: {max_repair_attempts}"

    def _format_repair_history(self, repair_history: list[dict[str, Any]] | None) -> str:
        if not repair_history:
            return "[]"

        compact_entries: list[dict[str, Any]] = []
        for entry in repair_history[-5:]:
            compact_entries.append(
                {
                    key: value
                    for key, value in entry.items()
                    if _has_repair_history_value(value)
                    and key
                    in {
                        "attempt_index",
                        "validation_error_class",
                        "validation_error_summary",
                        "action",
                        "root_cause",
                        "fix_description",
                        "affected_function",
                        "cannot_patch_reason",
                        "replan_instructions",
                        "patch_application_error",
                    }
                }
            )

        lines = []
        for entry in compact_entries:
            lines.append(
                "- "
                + "; ".join(
                    f"{key}: {str(value).strip()[:240]}" for key, value in entry.items()
                )
            )
        return "\n".join(lines)

    def _select_relevant_cheatsheet(
        self,
        *,
        cheatsheet: str,
        script: str,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        validation: ValidationReport,
        max_blocks: int = 14,
    ) -> str:
        query_terms = self._build_repair_query_terms(
            script=script,
            geometry_plan=geometry_plan,
            parameters=parameters,
            validation=validation,
        )

        raw_blocks = self._split_cheatsheet_blocks(cheatsheet)
        if not raw_blocks:
            return cheatsheet
        blocks = filter_forbidden_cheatsheet_blocks(raw_blocks)
        if not blocks:
            return "cadquery_cheatsheet:"

        selected: list[str] = []
        for block in blocks:
            if self._is_core_cheatsheet_block(block):
                selected.append(block)

        scored_blocks = [
            (self._score_cheatsheet_block(block, query_terms), index, block)
            for index, block in enumerate(blocks)
            if block not in selected
        ]
        scored_blocks.sort(key=lambda item: (-item[0], item[1]))

        for score, _, block in scored_blocks:
            if len(selected) >= max_blocks:
                break
            if score <= 0:
                continue
            selected.append(block)

        return "\n\n".join(["cadquery_cheatsheet:", *selected])

    def _build_repair_query_terms(
        self,
        *,
        script: str,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        validation: ValidationReport,
    ) -> set[str]:
        raw_values: list[str] = [
            getattr(validation, "status", "") or "",
            getattr(validation, "error_class", "") or "",
            getattr(validation, "error_message", "") or "",
            getattr(validation, "error_summary", "") or "",
            getattr(geometry_plan, "artifact_type", "") or "",
            " ".join(getattr(parameters, "parameters", {}).keys()),
        ]

        error_location = getattr(validation, "error_location", None)
        if error_location is not None:
            raw_values.append(getattr(error_location, "function", "") or "")
            raw_values.append(getattr(error_location, "code_line", "") or "")

        for part in getattr(geometry_plan, "parts", []) or []:
            raw_values.extend(
                [
                    getattr(part, "name", "") or "",
                    getattr(part, "modeling_strategy", "") or "",
                    getattr(part, "geometric_role", "") or "",
                ]
            )
            for feature in getattr(part, "key_features", []) or []:
                raw_values.append(getattr(feature, "feature", "") or "")
                raw_values.append(getattr(feature, "description", "") or "")

        raw_values.append(self._extract_script_operation_text(script))

        terms: set[str] = set()
        for value in raw_values:
            terms.update(self._tokenize_for_cheatsheet_search(value))

        terms.update(self._infer_repair_operation_terms(script, validation))
        return terms

    def _extract_script_operation_text(self, script: str) -> str:
        operations = re.findall(r"\.([A-Za-z_][A-Za-z0-9_]*)\s*\(", script)
        names = re.findall(r"\b(cq|Workplane|Assembly|Location|Vector|exporters)\b", script)
        return " ".join([*operations, *names])

    def _tokenize_for_cheatsheet_search(self, text: str) -> set[str]:
        stopwords = {
            "and",
            "for",
            "from",
            "into",
            "not",
            "the",
            "this",
            "use",
            "when",
            "with",
        }
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))
            if len(token) > 2 and token not in stopwords
        }

    def _infer_repair_operation_terms(
        self,
        script: str,
        validation: ValidationReport,
    ) -> set[str]:
        joined = " ".join(
            [
                script,
                getattr(validation, "error_class", "") or "",
                getattr(validation, "error_message", "") or "",
                getattr(validation, "error_summary", "") or "",
            ]
        ).lower()

        terms = {"workplane", "box", "circle", "extrude", "cut", "union", "export"}

        if any(word in joined for word in ["hole", "bore", "clearance", "cutter"]):
            terms.update({"cylinder", "circle", "cut", "pushpoints"})
        if any(word in joined for word in ["fillet", "chamfer", "edge", "selector"]):
            terms.update({"fillet", "chamfer", "edges", "faces", "selectors"})
        if any(word in joined for word in ["assembly", "location", "misalignment"]):
            terms.update({"assembly", "location", "vector", "save"})
        if any(word in joined for word in ["extrude", "pending sketch", "wire"]):
            terms.update({"rect", "polyline", "close", "extrude"})
        if any(word in joined for word in ["export", "step", "stl", "path"]):
            terms.update({"exporters", "export", "save"})

        return terms

    def _split_cheatsheet_blocks(self, cheatsheet: str) -> list[str]:
        chunks = re.split(r"(?=\n\*\*(?:Rule|Description)\*\*:)", cheatsheet)
        blocks: list[str] = []
        for chunk in chunks:
            stripped = chunk.strip()
            if not stripped:
                continue
            if stripped.startswith("cadquery_cheatsheet:"):
                lines = stripped.splitlines()
                preamble: list[str] = []
                current: list[str] = []
                for line in lines:
                    if line.startswith("# "):
                        if preamble:
                            blocks.append("\n".join(preamble).strip())
                            preamble = []
                        current.append(line)
                    elif current:
                        current.append(line)
                    else:
                        preamble.append(line)
                if preamble:
                    blocks.append("\n".join(preamble).strip())
                if current:
                    blocks.append("\n".join(current).strip())
            else:
                blocks.append(stripped)
        return blocks

    def _is_core_cheatsheet_block(self, block: str) -> bool:
        block_l = block.lower()
        core_markers = [
            "all dimensions are in mm",
            "import cadquery as cq",
            'cq.workplane("plane_name")',
            ".box(length, width, height)",
            ".circle(radius",
            ".rect(xlen, ylen",
            ".extrude(until",
            ".cut(tocut",
            ".union(",
            ".translate(vec",
            "exporters.export",
            "canonical explicit cutter patterns",
        ]
        return any(marker in block_l for marker in core_markers)

    def _score_cheatsheet_block(self, block: str, query_terms: set[str]) -> int:
        block_l = block.lower().replace("_", " ")
        score = 0
        for term in query_terms:
            if term in block_l:
                score += block_l.count(term)
        if score > 0 and "**method**" in block_l:
            score += 1
        return score


def _has_repair_history_value(value: Any) -> bool:
    return value is not None and value != "" and value != []
