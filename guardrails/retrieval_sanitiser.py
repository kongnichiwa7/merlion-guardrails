"""Guardrail 3: clean retrieved chunks before they reach the model.

The injection classifier is deliberately NOT run here. Component testing showed
it scores clean FAQ sections on scams, OTPs and login at 0.97-1.00, because
those pages are written as imperatives ("Freeze your card...", "Call...").
It was trained on user prompts, not reference documents. Instead:
  1. deny-list internal sources,
  2. strip hidden text (HTML comments), the channel indirect injection used,
  3. drop any chunk whose visible text still matches an injection rule.
"""
from __future__ import annotations

import re
from dataclasses import replace
from typing import List, Tuple

from guardrails.rules import match_injection

# Access control: documents that must never reach the model, whatever retrieval finds.
DENY_SOURCES = {"staff-note.md", "customers.md"}
HIDDEN_TEXT = re.compile(r"<!--.*?-->", re.DOTALL)


def sanitise(chunks: list) -> Tuple[list, List[str]]:
    """Return (chunks safe to send, notes on what was dropped or stripped).

    `chunks` are app.retrieval.Chunk objects (with `.source` and `.text`).
    """
    kept, notes = [], []
    for chunk in chunks:
        if chunk.source in DENY_SOURCES:
            notes.append(f"deny list: {chunk.source}")
            continue
        visible = HIDDEN_TEXT.sub("", chunk.text).strip()
        if visible != chunk.text.strip():
            notes.append(f"stripped hidden text from {chunk.source}")
            chunk = replace(chunk, text=visible)
        pattern = match_injection(visible)
        if pattern:
            notes.append(f"injection rule in {chunk.source}: {pattern}")
            continue
        kept.append(chunk)
    return kept, notes
