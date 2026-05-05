from __future__ import annotations

import re

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.repair import RepairOutput
from cadpilotv3.shared import LLMTextResult, invoke_text_with_metadata, load_prompt_text


class CodeGenerationInfillAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        repair_context: RepairOutput | None = None,
        critic_feedback: str | None = None,
        current_script: str | None = None,
        generation_feedback: str | None = None,
        compact_retry: bool = False,
    ) -> LLMTextResult:
        llm = self.llm_factory.get_for_agent(AgentName.CODEGEN)

        if compact_retry:
            return invoke_text_with_metadata(
                llm,
                self._build_compact_retry_prompt(
                    spec=spec,
                    geometry_plan=geometry_plan,
                    parameters=parameters,
                    generation_feedback=generation_feedback,
                ),
                agent_name=AgentName.CODEGEN.value,
                trace_metadata={"prompt_mode": "compact_retry"},
            )

        system_prompt = load_prompt_text(
            self.settings,
            "code_generation_infill.md",
        )
        few_shot_prompt = load_prompt_text(
            self.settings,
            "codegen_infill_examples.md",
        )
        selected_examples = self._select_relevant_examples(
            few_shot_prompt=few_shot_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
        )
        cadquery_cheatsheet = load_prompt_text(self.settings, "cheatsheet.md")
        selected_cheatsheet = self._select_relevant_cheatsheet(
            cheatsheet=cadquery_cheatsheet,
            spec=spec,
            geometry_plan=geometry_plan,
        )

        prompt_parts = [
            system_prompt.strip(),
            selected_examples.strip(),
            "Selected CadQuery 2.x API reference:",
            selected_cheatsheet.strip(),
            "Intent spec:",
            spec.model_dump_json(indent=2),
            "Geometry plan:",
            geometry_plan.model_dump_json(indent=2),
            "Parameter schema:",
            parameters.model_dump_json(indent=2),
            (
                "Generation mode: complete script. Generate the final runnable "
                "CadQuery script directly from the inputs."
            ),
            (
                "Output contract: return raw Python source only. Do not wrap the "
                "script in Markdown fences. The first line must be "
                "`import cadquery as cq`."
            ),
        ]

        if repair_context is not None:
            prompt_parts.extend(
                [
                    "Repair context:",
                    repair_context.model_dump_json(indent=2),
                ]
            )

        if critic_feedback:
            prompt_parts.extend(
                [
                    "Critic B semantic patch instructions:",
                    critic_feedback.strip(),
                    "Current script to revise:",
                    (current_script or "").strip(),
                    (
                        "This is a targeted regeneration. Preserve the current "
                        "geometry plan and parameter schema unless these "
                        "instructions explicitly require a local correction."
                    ),
                ]
            )

        if generation_feedback:
            prompt_parts.extend(
                [
                    "Previous generation attempt failed validation:",
                    generation_feedback.strip(),
                    (
                        "Return one complete, non-empty Python CadQuery script. "
                        "Do not return prose, Markdown fences, an empty code fence, "
                        "or a partial excerpt."
                    ),
                ]
            )

        prompt = "\n\n".join(prompt_parts)
        return invoke_text_with_metadata(
            llm,
            prompt,
            agent_name=AgentName.CODEGEN.value,
            trace_metadata={
                "prompt_mode": "normal",
                "has_repair_context": repair_context is not None,
                "has_critic_feedback": bool(critic_feedback),
                "has_generation_feedback": bool(generation_feedback),
            },
        )

    def _build_compact_retry_prompt(
        self,
        *,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        generation_feedback: str | None,
    ) -> str:
        return "\n\n".join(
            [
                "You are generating a complete CadQuery 2.x Python script.",
                (
                    "Return raw Python source only. No Markdown fences, no prose, "
                    "no explanation. The first line must be exactly: "
                    "import cadquery as cq"
                ),
                (
                    "The script must define build_part() or build_assembly(), "
                    "validate_geometry(...), export_all(...), and an "
                    "if __name__ == '__main__': export block that assigns the "
                    "built object to global model or assembly."
                ),
                (
                    "validate_geometry may check bounding boxes, part counts, "
                    "and positive final volume, but must not include heuristic "
                    "volume_reasonable or expected-volume threshold checks."
                ),
                (
                    "Avoid Workplane.hole(); use explicit cutter solids. Use only "
                    "CadQuery 2.x and Python standard-library imports."
                ),
                "Previous failure:",
                generation_feedback or "The previous output was unusable.",
                "Intent spec:",
                spec.model_dump_json(indent=2),
                "Geometry plan:",
                geometry_plan.model_dump_json(indent=2),
                "Parameter schema:",
                parameters.model_dump_json(indent=2),
            ]
        )

    def _select_relevant_examples(
        self,
        *,
        few_shot_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        max_examples: int = 1,
    ) -> str:
        sections = self._split_example_sections(few_shot_prompt)
        if not sections:
            return few_shot_prompt

        query_terms = self._build_example_query_terms(spec, geometry_plan)
        scored_sections = [
            (self._score_example_section(section, query_terms), index, section)
            for index, section in enumerate(sections)
        ]
        scored_sections.sort(key=lambda item: (-item[0], item[1]))

        selected = [
            section
            for score, _, section in scored_sections[:max_examples]
            if score > 0
        ]
        if not selected:
            selected = sections[:max_examples]

        return "\n\n".join(["## Selected Codegen Few-Shots", *selected])

    def _split_example_sections(self, few_shot_prompt: str) -> list[str]:
        matches = list(re.finditer(r"(?m)^###\s+", few_shot_prompt))
        if not matches:
            return []

        sections: list[str] = []
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(few_shot_prompt)
            sections.append(few_shot_prompt[start:end].strip())
        return sections

    def _build_example_query_terms(
        self,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
    ) -> set[str]:
        raw_values: list[str] = [
            spec.component or "",
            spec.component_type or "",
            spec.style or "",
            spec.manufacturing_process or "",
            spec.approximate_scale or "",
            " ".join(spec.parts),
            " ".join(spec.constraints),
            geometry_plan.artifact_type or "",
            " ".join(part.name for part in geometry_plan.parts),
            " ".join(part.modeling_strategy for part in geometry_plan.parts),
            " ".join(
                feature.feature
                for part in geometry_plan.parts
                for feature in part.key_features
            ),
        ]

        terms: set[str] = set()
        for value in raw_values:
            terms.update(self._tokenize_for_example_search(value))
        return terms

    def _tokenize_for_example_search(self, text: str) -> set[str]:
        stopwords = {
            "a",
            "an",
            "and",
            "as",
            "for",
            "in",
            "of",
            "on",
            "or",
            "part",
            "static",
            "the",
            "to",
            "with",
        }
        return {
            token
            for token in re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))
            if len(token) > 2 and token not in stopwords
        }

    def _score_example_section(self, section: str, query_terms: set[str]) -> int:
        section_text = section.lower().replace("_", " ")
        title = section.splitlines()[0].lower() if section.splitlines() else ""

        score = 0
        for term in query_terms:
            if term in section_text:
                score += section_text.count(term)
            if term in title:
                score += 4
        return score

    def _select_relevant_cheatsheet(
        self,
        *,
        cheatsheet: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        max_blocks: int = 18,
    ) -> str:
        query_terms = self._build_example_query_terms(spec, geometry_plan)
        query_terms.update(self._infer_cadquery_operation_terms(spec, geometry_plan))

        blocks = self._split_cheatsheet_blocks(cheatsheet)
        if not blocks:
            return cheatsheet

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
        ]
        return any(marker in block_l for marker in core_markers)

    def _infer_cadquery_operation_terms(
        self,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
    ) -> set[str]:
        joined = " ".join(
            [
                spec.component or "",
                " ".join(spec.parts),
                " ".join(spec.constraints),
                " ".join(
                    f"{part.name} {part.modeling_strategy} "
                    f"{' '.join(feature.feature for feature in part.key_features)}"
                    for part in geometry_plan.parts
                ),
            ]
        ).lower()

        terms = {"workplane", "box", "circle", "extrude", "cut", "union", "translate", "export"}

        if any(word in joined for word in ["hole", "bore", "slot", "screw", "bolt"]):
            terms.update({"cylinder", "circle", "cut", "slot", "polyline"})
        if any(word in joined for word in ["gusset", "rib", "triangle"]):
            terms.update({"polyline", "close", "extrude"})
        if any(word in joined for word in ["chamfer", "fillet", "rounded"]):
            terms.update({"chamfer", "fillet", "edges", "faces"})
        if any(word in joined for word in ["assembly", "part_count", "multi"]):
            terms.update({"assembly", "location", "vector", "save"})
        if any(word in joined for word in ["mirror", "symmetric", "pattern"]):
            terms.update({"mirror", "rarray", "pushpoints"})

        return terms

    def _score_cheatsheet_block(self, block: str, query_terms: set[str]) -> int:
        block_l = block.lower().replace("_", " ")
        score = 0
        for term in query_terms:
            if term in block_l:
                score += block_l.count(term)
        if "**method**" in block_l:
            score += 1
        return score
