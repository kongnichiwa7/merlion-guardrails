"""The Merlion Bank support chatbot, with guardrails switchable by GUARDRAILS=on|off."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Optional

from app import llm
from app.retrieval import Chunk, Retriever, default_retriever
from guardrails import input_filter, output_filter, retrieval_sanitiser
from guardrails.verdict import FALLBACK_REPLY

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

Generate = Callable[[str, str], str]


@dataclass
class BotResult:
    reply: str
    blocked_by: Optional[str] = None  # "input_filter" | "output_filter" | None
    reason: str = ""
    chunks_used: List[str] = field(default_factory=list)
    retrieval_notes: List[str] = field(default_factory=list)
    raw_reply: str = ""  # model output before the output filter


def guardrails_on() -> bool:
    return os.environ.get("GUARDRAILS", "on").lower() != "off"


def _prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text()


def _user_content(question: str, chunks: List[Chunk]) -> str:
    docs = "\n\n".join(
        f'<document source="{c.source}">\n{c.text}\n</document>' for c in chunks
    )
    return f"{docs}\n\nCustomer question: {question}"


def answer(
    question: str,
    guarded: Optional[bool] = None,
    retriever: Optional[Retriever] = None,
    generate: Generate = llm.generate,
) -> BotResult:
    guarded = guardrails_on() if guarded is None else guarded
    retriever = retriever or default_retriever()

    if not guarded:
        chunks = retriever.search(question)
        reply = generate(_prompt("system-unguarded.md"), _user_content(question, chunks))
        return BotResult(reply, chunks_used=[c.source for c in chunks], raw_reply=reply)

    verdict = input_filter.check(question)
    if verdict.blocked:
        return BotResult(FALLBACK_REPLY, "input_filter", verdict.reason)

    chunks, dropped = retrieval_sanitiser.sanitise(retriever.search(question))
    raw = generate(_prompt("system.md"), _user_content(question, chunks))

    verdict = output_filter.check(raw, [c.text for c in chunks])
    result = BotResult(
        raw,
        chunks_used=[c.source for c in chunks],
        retrieval_notes=dropped,
        raw_reply=raw,
    )
    if verdict.blocked:
        result.reply, result.blocked_by, result.reason = FALLBACK_REPLY, "output_filter", verdict.reason
    return result
