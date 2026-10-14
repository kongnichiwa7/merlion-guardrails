"""Guardrail 2: screen the user's message before it reaches the model."""
from __future__ import annotations

from typing import Callable, Optional

from guardrails import classifier
from guardrails.rules import match_injection
from guardrails.verdict import ALLOWED, Verdict

Scorer = Callable[[str], float]


def check_injection(text: str, scorer: Optional[Scorer] = None) -> Verdict:
    """Rules first (cheap, explainable), then the classifier."""
    pattern = match_injection(text)
    if pattern:
        return Verdict(True, f"rule: {pattern}")
    if scorer is None and classifier.enabled():
        scorer = classifier.injection_score
    if scorer is not None:
        score = scorer(text)
        if score >= classifier.THRESHOLD:
            return Verdict(True, f"classifier: injection score {score:.2f}")
    return ALLOWED


def check(user_message: str, scorer: Optional[Scorer] = None) -> Verdict:
    return check_injection(user_message, scorer)
