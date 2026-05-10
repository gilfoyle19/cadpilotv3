from __future__ import annotations

import logging
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

from cadpilotv3.config.settings import AppSettings
from cadpilotv3.shared.json_utils import JSONExtractionError, parse_json

logger = logging.getLogger(__name__)


PRODUCT_INTERFACE_TERMS = (
    "phone",
    "iphone",
    "android",
    "charger",
    "charging",
    "magsafe",
    "qi",
    "pcb",
    "circuit board",
    "connector",
    "usb",
    "usb-c",
    "usbc",
    "lightning",
    "hdmi",
    "displayport",
    "ethernet",
    "rj45",
    "jack",
    "barrel plug",
    "battery",
    "camera",
    "lens",
    "raspberry pi",
    "arduino",
    "esp32",
    "nema",
    "stepper",
    "servo",
    "bearing",
    "extrusion",
)

INTERFACE_ACTION_TERMS = (
    "fit",
    "fits",
    "hold",
    "holds",
    "holder",
    "mount",
    "mounting",
    "dock",
    "stand",
    "case",
    "enclosure",
    "bracket",
    "adapter",
    "slot",
    "cutout",
    "clearance",
    "bolt pattern",
    "hole pattern",
    "footprint",
    "interface",
    "mate",
    "mating",
)

NO_RESEARCH_PATTERNS = (
    r"\bdo not (?:use )?(?:web|search|research)\b",
    r"\bwithout (?:web|search|research)\b",
    r"\bno (?:web|search|research)\b",
)


class WebResearchContext(BaseModel):
    queries: list[str] = Field(default_factory=list)
    researched_dimensions: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    warning: str | None = None

    @field_validator("queries", "researched_dimensions", "sources", mode="before")
    @classmethod
    def _normalize_list_fields(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value

    @property
    def has_facts(self) -> bool:
        return bool(self.researched_dimensions)

    def to_prompt_block(self) -> str:
        if not self.has_facts:
            return "No web research context was used."

        lines = ["Web research context for real-world product interfaces:"]
        if self.queries:
            lines.append("Queries:")
            lines.extend(f"- {query}" for query in self.queries)
        lines.append("Researched dimensions:")
        lines.extend(f"- {fact}" for fact in self.researched_dimensions)
        if self.sources:
            lines.append("Sources:")
            lines.extend(f"- {source}" for source in self.sources)
        if self.warning:
            lines.append(f"Research warning: {self.warning}")
        return "\n".join(lines)


class WebResearchService:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings

    def research_if_needed(self, user_prompt: str) -> WebResearchContext:
        if not self.needs_research(user_prompt):
            return WebResearchContext()

        if not self.settings.intent_web_research_enabled:
            logger.info("Intent web research skipped because it is disabled")
            return WebResearchContext()

        if self.settings.llm_provider.lower() != "openai":
            logger.info(
                "Intent web research skipped because provider does not support it",
                extra={"llm_provider": self.settings.llm_provider},
            )
            return WebResearchContext()

        try:
            return self._run_openai_web_search(user_prompt)
        except Exception as exc:
            logger.warning(
                "Intent web research failed; continuing without research context",
                extra={"error_class": type(exc).__name__, "reason": str(exc)},
            )
            return WebResearchContext(warning=str(exc))

    def needs_research(self, user_prompt: str) -> bool:
        normalized = user_prompt.casefold()
        if any(re.search(pattern, normalized) for pattern in NO_RESEARCH_PATTERNS):
            return False

        has_product_term = any(term in normalized for term in PRODUCT_INTERFACE_TERMS)
        has_interface_term = any(term in normalized for term in INTERFACE_ACTION_TERMS)
        return has_product_term and has_interface_term

    def _run_openai_web_search(self, user_prompt: str) -> WebResearchContext:
        from openai import OpenAI

        kwargs: dict[str, Any] = {
            "timeout": self.settings.intent_web_research_timeout_seconds,
        }
        if self.settings.openai_api_key:
            kwargs["api_key"] = self.settings.openai_api_key
        if self.settings.openai_base_url:
            kwargs["base_url"] = self.settings.openai_base_url

        client = OpenAI(**kwargs)
        prompt = self._build_research_prompt(user_prompt)
        response = client.responses.create(
            model=self.settings.intent_web_research_model or self.settings.llm_model,
            input=prompt,
            tools=[
                {
                    "type": "web_search",
                    "search_context_size": self.settings.intent_web_research_context_size,
                }
            ],
            include=["web_search_call.action.sources"],
            max_output_tokens=self.settings.intent_web_research_max_output_tokens,
            temperature=0,
        )

        response_text = getattr(response, "output_text", "") or ""
        context = self._parse_research_response(response_text)
        response_sources = self._extract_response_sources(response)
        context.sources = self._dedupe([*context.sources, *response_sources])
        return context

    def _build_research_prompt(self, user_prompt: str) -> str:
        return "\n\n".join(
            [
                "Research real-world interface dimensions for a CAD intent extractor.",
                "Only search for product, standard, connector, PCB, mounting, or clearance "
                "dimensions needed for the requested object to physically mate with real items.",
                "Prefer manufacturer specifications, standards, datasheets, and official "
                "mechanical drawings. Ignore broad marketing pages unless they contain exact "
                "dimensions.",
                "Return ONLY valid JSON with this shape:",
                (
                    '{"queries":["search terms used"],'
                    '"researched_dimensions":["item: dimension/value/unit/source note"],'
                    '"sources":["https://..."]}'
                ),
                "Keep researched_dimensions concise and include numeric units. If no reliable "
                "dimension is found, return an empty researched_dimensions array.",
                "User CAD request:",
                user_prompt.strip(),
            ]
        )

    def _parse_research_response(self, response_text: str) -> WebResearchContext:
        try:
            data = parse_json(response_text)
        except JSONExtractionError as exc:
            logger.warning(
                "Intent web research response was not JSON",
                extra={"reason": str(exc)},
            )
            return WebResearchContext(
                warning="web research response was not valid JSON",
            )

        if not isinstance(data, dict):
            return WebResearchContext(warning="web research response was not an object")

        return WebResearchContext.model_validate(data)

    def _extract_response_sources(self, response: Any) -> list[str]:
        sources: list[str] = []
        for output in getattr(response, "output", []) or []:
            output_type = getattr(output, "type", None)
            if output_type == "web_search_call":
                action = getattr(output, "action", None)
                action_sources = getattr(action, "sources", None) or []
                sources.extend(
                    source.url
                    for source in action_sources
                    if getattr(source, "url", None)
                )
            if output_type == "message":
                for content in getattr(output, "content", []) or []:
                    for annotation in getattr(content, "annotations", []) or []:
                        if getattr(annotation, "type", None) == "url_citation":
                            url = getattr(annotation, "url", None)
                            if url:
                                sources.append(url)
        return self._dedupe(sources)

    def _dedupe(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for value in values:
            normalized = value.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique.append(normalized)
        return unique
