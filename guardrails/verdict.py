from __future__ import annotations

from dataclasses import dataclass

FALLBACK_REPLY = (
    "Sorry, I can't help with that. "
    "For account matters please call Merlion Bank on 1800-000-0000."
)


@dataclass(frozen=True)
class Verdict:
    """Outcome of one guardrail check. `reason` is empty when allowed."""

    blocked: bool
    reason: str = ""

    @property
    def label(self) -> str:
        return "BLOCKED" if self.blocked else "ALLOWED"


ALLOWED = Verdict(blocked=False)
