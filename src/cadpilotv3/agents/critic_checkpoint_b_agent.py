from __future__ import annotations

import json
import re

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.contract_validation import ContractValidationReport
from cadpilotv3.schemas.critic import CriticBReport, CriticReport
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.schemas.validation import ValidationReport
from cadpilotv3.shared import ainvoke_pydantic, invoke_pydantic, load_prompt_text


class CriticCheckpointBAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        validation: ValidationReport,
        contract_validation: ContractValidationReport | None,
        critic_a_report: CriticReport,
        repair_count: int,
    ) -> CriticBReport:
        llm = self.llm_factory.get_for_agent(AgentName.CRITIC_B)
        prompt = self._build_prompt(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            parameters=parameters,
            validation=validation,
            contract_validation=contract_validation,
            critic_a_report=critic_a_report,
            repair_count=repair_count,
        )

        return invoke_pydantic(
            llm,
            prompt,
            CriticBReport,
            agent_name=AgentName.CRITIC_B.value,
            trace_metadata={
                "repair_count": repair_count,
                "contract_validation_status": getattr(
                    contract_validation,
                    "status",
                    None,
                ),
            },
        )

    async def arun(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        validation: ValidationReport,
        contract_validation: ContractValidationReport | None,
        critic_a_report: CriticReport,
        repair_count: int,
    ) -> CriticBReport:
        llm = self.llm_factory.get_for_agent(AgentName.CRITIC_B)
        prompt = self._build_prompt(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            parameters=parameters,
            validation=validation,
            contract_validation=contract_validation,
            critic_a_report=critic_a_report,
            repair_count=repair_count,
        )

        return await ainvoke_pydantic(
            llm,
            prompt,
            CriticBReport,
            agent_name=AgentName.CRITIC_B.value,
            trace_metadata={
                "repair_count": repair_count,
                "contract_validation_status": getattr(
                    contract_validation,
                    "status",
                    None,
                ),
            },
        )

    def _build_prompt(
        self,
        *,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        parameters: ParameterSchema,
        validation: ValidationReport,
        contract_validation: ContractValidationReport | None,
        critic_a_report: CriticReport,
        repair_count: int,
    ) -> str:
        system_prompt = load_prompt_text(self.settings, "critic_checkpoint_b.md")
        few_shot_prompt = load_prompt_text(
            self.settings,
            "critic_b_examples.md",
        )
        selected_examples = self._select_relevant_examples(
            few_shot_prompt=few_shot_prompt,
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            validation=validation,
        )

        prompt = "\n\n".join(
            [
                system_prompt.strip(),
                selected_examples.strip(),
                "Original user prompt:",
                user_prompt.strip(),
                "Structured spec:",
                spec.model_dump_json(indent=2),
                "Geometry plan:",
                geometry_plan.model_dump_json(indent=2),
                "Parameter schema:",
                parameters.model_dump_json(indent=2),
                "Validation report:",
                validation.model_dump_json(indent=2),
                "Deterministic contract validation report:",
                self._format_contract_validation_evidence(contract_validation),
                "Checkpoint A report:",
                critic_a_report.model_dump_json(indent=2),
                f"Repair history count: {repair_count}",
            ]
        )
        return prompt

    def _format_contract_validation_evidence(
        self,
        contract_validation: ContractValidationReport | None,
    ) -> str:
        if contract_validation is None:
            return json.dumps(
                {
                    "status": "missing",
                    "summary": "No deterministic contract validation report was provided.",
                },
                indent=2,
            )

        checks = [
            check.model_dump(mode="json")
            for check in contract_validation.checks
            if check.status in {"fail", "warn"}
        ][:8]
        payload = {
            "status": contract_validation.status,
            "passed": contract_validation.passed,
            "summary": contract_validation.summary,
            "failure_count": contract_validation.failure_count,
            "warning_count": contract_validation.warning_count,
            "compact_evidence": contract_validation.compact_evidence[:12],
        }
        if checks:
            payload["failed_or_warning_checks"] = checks

        return json.dumps(payload, indent=2)

    def _select_relevant_examples(
        self,
        *,
        few_shot_prompt: str,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        validation: ValidationReport,
        max_examples: int = 2,
    ) -> str:
        sections = self._split_example_sections(few_shot_prompt)
        if not sections:
            return few_shot_prompt

        query_terms = self._build_example_query_terms(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            validation=validation,
        )
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

        return "\n\n".join(["## Selected Critic B Few-Shots", *selected])

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
        *,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        validation: ValidationReport,
    ) -> set[str]:
        raw_values = [
            user_prompt,
            getattr(spec, "component", "") or "",
            getattr(spec, "component_type", "") or "",
            getattr(spec, "style", "") or "",
            " ".join(getattr(spec, "parts", []) or []),
            " ".join(getattr(spec, "constraints", []) or []),
            getattr(geometry_plan, "artifact_type", "") or "",
            getattr(validation, "status", "") or "",
            getattr(validation, "error_class", "") or "",
        ]

        geometry_report = getattr(validation, "geometry_report", None)
        raw_values.append(str(getattr(geometry_report, "part_count", "") or ""))
        for child in getattr(geometry_report, "child_metadata", []) or []:
            raw_values.append(getattr(child, "name", "") or "")

        for part in getattr(geometry_plan, "parts", []) or []:
            raw_values.append(getattr(part, "name", "") or "")
            raw_values.append(getattr(part, "geometric_role", "") or "")
            for feature in getattr(part, "key_features", []) or []:
                raw_values.append(getattr(feature, "feature", "") or "")

        terms: set[str] = set()
        for value in raw_values:
            terms.update(self._tokenize_for_example_search(value))
        if getattr(geometry_report, "child_metadata", None):
            terms.update({"child", "metadata", "center", "spatial", "placement"})
            if self._looks_like_side_by_side_stack_error(geometry_report):
                terms.update({"side", "beside", "stacked", "top", "lid", "base"})
        return terms

    def _looks_like_side_by_side_stack_error(self, geometry_report) -> bool:
        child_metadata = getattr(geometry_report, "child_metadata", []) or []
        centers = []
        for child in child_metadata:
            center = getattr(child, "center_mm", None)
            if center and len(center) >= 3:
                centers.append(center)
        if len(centers) < 2:
            return False

        x_values = [float(center[0]) for center in centers]
        y_values = [float(center[1]) for center in centers]
        z_values = [float(center[2]) for center in centers]
        xy_span = max(max(x_values) - min(x_values), max(y_values) - min(y_values))
        z_span = max(z_values) - min(z_values)
        return xy_span > max(25.0, z_span * 3)

    def _tokenize_for_example_search(self, text: str) -> set[str]:
        stopwords = {
            "and",
            "for",
            "from",
            "part",
            "static",
            "the",
            "with",
        }
        return {
            token
            for token in re.findall(r"[a-z0-9]+", str(text).lower().replace("_", " "))
            if len(token) > 2 and token not in stopwords
        }

    def _score_example_section(self, section: str, query_terms: set[str]) -> int:
        section_l = section.lower().replace("_", " ")
        title = section.splitlines()[0].lower() if section.splitlines() else ""
        score = 0
        for term in query_terms:
            if term in section_l:
                score += section_l.count(term)
            if term in title:
                score += 4
        return score
