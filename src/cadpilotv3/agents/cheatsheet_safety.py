from __future__ import annotations

import re

DISALLOWED_IMPLICIT_HOLE_HELPERS = frozenset({"hole", "cboreHole", "cskHole"})

_DISALLOWED_IMPLICIT_HOLE_CALL_RE = re.compile(
    r"\.(?:hole|cboreHole|cskHole)\s*\(",
    re.IGNORECASE,
)


def contains_disallowed_implicit_hole_helper(text: str) -> bool:
    return bool(_DISALLOWED_IMPLICIT_HOLE_CALL_RE.search(text))


def filter_forbidden_cheatsheet_blocks(blocks: list[str]) -> list[str]:
    return [
        block
        for block in blocks
        if not contains_disallowed_implicit_hole_helper(block)
    ]
