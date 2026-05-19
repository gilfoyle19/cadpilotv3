from __future__ import annotations

import re

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.critic import CriticReport
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.schemas.parameters import ParameterSchema
from cadpilotv3.shared import ainvoke_pydantic, invoke_pydantic, load_prompt_text


class ParameterAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_a_report: CriticReport | None = None,
    ) -> ParameterSchema:
        llm = self.llm_factory.get_for_agent(AgentName.PARAMETER)
        prompt = self._build_prompt(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            critic_a_report=critic_a_report,
        )

        return invoke_pydantic(
            llm,
            prompt,
            ParameterSchema,
            agent_name=AgentName.PARAMETER.value,
        )

    async def arun(
        self,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_a_report: CriticReport | None = None,
    ) -> ParameterSchema:
        llm = self.llm_factory.get_for_agent(AgentName.PARAMETER)
        prompt = self._build_prompt(
            user_prompt=user_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
            critic_a_report=critic_a_report,
        )

        return await ainvoke_pydantic(
            llm,
            prompt,
            ParameterSchema,
            agent_name=AgentName.PARAMETER.value,
        )

    def _build_prompt(
        self,
        *,
        user_prompt: str,
        spec: IntentSpec,
        geometry_plan: GeometryPlan,
        critic_a_report: CriticReport | None,
    ) -> str:
        system_prompt = load_prompt_text(self.settings, "parameter_agent.md")
        few_shot_prompt = load_prompt_text(
            self.settings,
            "parameter_agent_examples.md",
        )
        selected_examples = self._select_relevant_examples(
            few_shot_prompt=few_shot_prompt,
            spec=spec,
            geometry_plan=geometry_plan,
        )

        return "\n\n".join(
            [
                system_prompt.strip(),
                selected_examples.strip(),
                "Original user prompt:",
                user_prompt.strip(),
                "Numeric facts extracted from original prompt:",
                "\n".join(self._extract_numeric_fact_sentences(user_prompt)) or "None",
                "Structured spec:",
                spec.model_dump_json(indent=2),
                "Geometry plan:",
                geometry_plan.model_dump_json(indent=2),
                "Critic A report:",
                (
                    critic_a_report.model_dump_json(indent=2)
                    if critic_a_report is not None
                    else "{}"
                ),
            ]
        )

    def _extract_numeric_fact_sentences(self, user_prompt: str) -> list[str]:
        sentences = re.split(r"(?<=[.!?])\s+", user_prompt.strip())
        return [
            sentence.strip()
            for sentence in sentences
            if sentence.strip() and re.search(r"\d", sentence)
        ]

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

        return "\n\n".join(["## Selected Parameter Few-Shots", *selected])

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
        raw_values = [
            getattr(spec, "component", "") or "",
            getattr(spec, "component_type", "") or "",
            getattr(spec, "style", "") or "",
            getattr(spec, "manufacturing_process", "") or "",
            " ".join(getattr(spec, "parts", []) or []),
            " ".join(getattr(spec, "constraints", []) or []),
            getattr(geometry_plan, "artifact_type", "") or "",
        ]

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

        terms: set[str] = set()
        for value in raw_values:
            terms.update(self._tokenize_for_example_search(value))
        return terms

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
            for token in re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))
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
