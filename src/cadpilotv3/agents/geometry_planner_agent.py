from __future__ import annotations

import re

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.llm import AgentName, get_llm_factory
from cadpilotv3.schemas.critic import CriticReport
from cadpilotv3.schemas.geometry_plan import GeometryPlan
from cadpilotv3.schemas.intent_spec import IntentSpec
from cadpilotv3.shared import ainvoke_pydantic, invoke_pydantic, load_prompt_text


class GeometryPlannerAgent:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.llm_factory = get_llm_factory()

    def run(
        self,
        spec: IntentSpec,
        critique: CriticReport | None = None,
        critic_b_replan_instructions: str | None = None,
        repair_replan_instructions: str | None = None,
    ) -> GeometryPlan:
        llm = self.llm_factory.get_for_agent(AgentName.GEOMETRY_PLANNER)
        prompt = self._build_prompt(
            spec=spec,
            critique=critique,
            critic_b_replan_instructions=critic_b_replan_instructions,
            repair_replan_instructions=repair_replan_instructions,
        )

        return invoke_pydantic(
            llm,
            prompt,
            GeometryPlan,
            agent_name=AgentName.GEOMETRY_PLANNER.value,
        )

    async def arun(
        self,
        spec: IntentSpec,
        critique: CriticReport | None = None,
        critic_b_replan_instructions: str | None = None,
        repair_replan_instructions: str | None = None,
    ) -> GeometryPlan:
        llm = self.llm_factory.get_for_agent(AgentName.GEOMETRY_PLANNER)
        prompt = self._build_prompt(
            spec=spec,
            critique=critique,
            critic_b_replan_instructions=critic_b_replan_instructions,
            repair_replan_instructions=repair_replan_instructions,
        )

        return await ainvoke_pydantic(
            llm,
            prompt,
            GeometryPlan,
            agent_name=AgentName.GEOMETRY_PLANNER.value,
        )

    def _build_prompt(
        self,
        *,
        spec: IntentSpec,
        critique: CriticReport | None,
        critic_b_replan_instructions: str | None,
        repair_replan_instructions: str | None,
    ) -> str:
        system_prompt = load_prompt_text(self.settings, "geometry_planner_agent.md")
        few_shot_prompt = load_prompt_text(
            self.settings,
            "geometry_planner_examples.md",
        )
        selected_examples = self._select_relevant_examples(
            few_shot_prompt=few_shot_prompt,
            spec=spec,
            critic_b_replan_instructions=critic_b_replan_instructions,
            repair_replan_instructions=repair_replan_instructions,
        )

        prompt_sections = [
            system_prompt.strip(),
            selected_examples.strip(),
            "Structured spec:",
            spec.model_dump_json(indent=2),
        ]

        if critique is not None:
            prompt_sections.extend(
                [
                    "Critic Checkpoint A critique:",
                    critique.model_dump_json(indent=2),
                    "This is a replan. Address every flagged issue explicitly.",
                ]
            )

        if critic_b_replan_instructions:
            prompt_sections.extend(
                [
                    "Critic Checkpoint B replan instructions:",
                    critic_b_replan_instructions.strip(),
                    (
                        "This is a final-output replan. Address these semantic "
                        "fidelity issues explicitly in replan_changes."
                    ),
                ]
            )

        if repair_replan_instructions:
            prompt_sections.extend(
                [
                    "Repair agent replan instructions:",
                    repair_replan_instructions.strip(),
                    (
                        "This replan follows an execution or geometry validation "
                        "failure. Address the repair root cause explicitly and "
                        "avoid recreating the same implementation failure."
                    ),
                ]
            )

        return "\n\n".join(prompt_sections)

    def _select_relevant_examples(
        self,
        *,
        few_shot_prompt: str,
        spec: IntentSpec,
        critic_b_replan_instructions: str | None = None,
        repair_replan_instructions: str | None = None,
        max_examples: int = 1,
    ) -> str:
        sections = self._split_example_sections(few_shot_prompt)
        if not sections:
            return few_shot_prompt

        query_terms = self._build_example_query_terms(
            spec=spec,
            critic_b_replan_instructions=critic_b_replan_instructions,
            repair_replan_instructions=repair_replan_instructions,
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

        return "\n\n".join(
            [
                "## Selected Geometry Planner Few-Shots",
                (
                    "Use these examples only as pattern references. The current "
                    "structured spec and critique/replan instructions override "
                    "all example dimensions and part names."
                ),
                *selected,
            ]
        )

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
        spec: IntentSpec,
        critic_b_replan_instructions: str | None,
        repair_replan_instructions: str | None,
    ) -> set[str]:
        raw_values = [
            getattr(spec, "component", "") or "",
            getattr(spec, "component_type", "") or "",
            getattr(spec, "style", "") or "",
            getattr(spec, "manufacturing_process", "") or "",
            getattr(spec, "approximate_scale", "") or "",
            " ".join(getattr(spec, "parts", []) or []),
            " ".join(getattr(spec, "constraints", []) or []),
            critic_b_replan_instructions or "",
            repair_replan_instructions or "",
        ]

        terms: set[str] = set()
        for value in raw_values:
            terms.update(self._tokenize_for_example_search(value))

        joined = " ".join(raw_values).lower()
        if any(word in joined for word in ["camera", "spacer", "rear", "front"]):
            terms.update({"camera", "spacer", "rear", "front", "plate", "coaxial"})
        if any(word in joined for word in ["lid", "base", "enclosure"]):
            terms.update({"lid", "base", "enclosure", "closed", "stacked"})
        if any(word in joined for word in ["servo", "bracket", "gusset"]):
            terms.update({"servo", "bracket", "gusset"})

        return terms

    def _tokenize_for_example_search(self, text: str) -> set[str]:
        stopwords = {
            "and",
            "for",
            "from",
            "into",
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
