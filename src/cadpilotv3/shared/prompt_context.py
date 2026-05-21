from __future__ import annotations

import re
from collections.abc import Iterable


def select_relevant_few_shot_examples(
    *,
    few_shot_prompt: str,
    query_values: Iterable[object],
    heading: str,
    max_examples: int,
) -> str:
    sections = split_example_sections(few_shot_prompt)
    if not sections:
        return few_shot_prompt

    query_terms = build_query_terms(query_values)
    scored_sections = [
        (score_example_section(section, query_terms), index, section)
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

    return "\n\n".join([heading, *selected])


def split_example_sections(few_shot_prompt: str) -> list[str]:
    matches = list(re.finditer(r"(?m)^###\s+", few_shot_prompt))
    if not matches:
        return []

    sections: list[str] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(few_shot_prompt)
        sections.append(few_shot_prompt[start:end].strip())
    return sections


def build_query_terms(values: Iterable[object]) -> set[str]:
    terms: set[str] = set()
    for value in values:
        if value is None:
            continue
        if isinstance(value, (list, tuple, set)):
            terms.update(build_query_terms(value))
            continue
        terms.update(tokenize_for_example_search(str(value)))
    return terms


def tokenize_for_example_search(text: str) -> set[str]:
    stopwords = {
        "and",
        "are",
        "for",
        "from",
        "into",
        "part",
        "static",
        "that",
        "the",
        "this",
        "with",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))
        if len(token) > 2 and token not in stopwords
    }


def score_example_section(section: str, query_terms: set[str]) -> int:
    section_l = section.lower().replace("_", " ")
    title = section.splitlines()[0].lower() if section.splitlines() else ""
    score = 0
    for term in query_terms:
        if term in section_l:
            score += section_l.count(term)
        if term in title:
            score += 4
    return score
