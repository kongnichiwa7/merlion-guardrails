"""Pattern rules shared by the input filter and the retrieval sanitiser."""
from __future__ import annotations

import re

INJECTION_PATTERNS = [
    r"ignore (all |any )?(the )?(previous|prior|above|earlier) (instructions|rules|prompts?)",
    r"disregard (all |any )?(the )?(previous|prior|above|your) (instructions|rules|prompts?)",
    r"forget (all |everything|your) (previous |prior )?(instructions|rules|you were told)",
    r"you are now (in )?(dan|developer mode|maintenance mode|jailbreak|unrestricted)",
    r"\b(dan|developer|maintenance|god) mode\b",
    r"(reveal|print|show|repeat|output) (me )?(your|the) (system prompt|instructions|hidden prompt)",
    r"pretend (that )?you (have no|are not bound by|don't have) (rules|restrictions|guidelines)",
    r"act as (an? )?(unrestricted|unfiltered|uncensored)",
    r"note for the ai assistant",
    r"<\s*/?\s*(system|instructions?)\s*>",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def match_injection(text: str) -> str | None:
    """Return the first injection pattern that matches, or None."""
    for pattern in _COMPILED:
        if pattern.search(text):
            return pattern.pattern
    return None
