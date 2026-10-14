"""Guardrail 4: screen the model's reply before the customer sees it."""
from __future__ import annotations

import re
from typing import Iterable

from guardrails.verdict import ALLOWED, Verdict

SECRET_STRINGS = ["MRLN-CANARY-7Q2X", "WAIVE-FEE-3381"]
NRIC_PATTERN = re.compile(r"\b[STFGM]\d{7}[A-Z]\b", re.IGNORECASE)
ACCOUNT_PATTERN = re.compile(r"\b\d{3}-\d{6}-\d\b")

# Numbers the bot may always say, even if no retrieved chunk contains them.
ALLOWED_NUMBERS = {"1800-000-0000", "1767"}

# Amounts, percentages, decimals, times and integers >= 10. Small bare integers
# ("step 2") are too noisy to check.
_NUMBER = re.compile(
    r"\d{4}-\d{3}-\d{4}"          # phone numbers
    r"|S?\$\s?\d[\d,]*(?:\.\d+)?"  # currency
    r"|\d+(?:\.\d+)?\s?%"          # percentages
    r"|\d+:\d{2}"                  # times
    r"|\d+\.\d+"                   # decimals
    r"|\b\d{2,}(?:,\d{3})*\b"      # integers >= 10
)


def _normalise(token: str) -> str:
    value = re.sub(r"[\sS$,%]", "", token.upper())
    if "." in value:  # 2.60 and 2.6 are the same rate
        value = value.rstrip("0").rstrip(".")
    return value


def ungrounded_numbers(reply: str, context: str) -> list:
    """Numbers in the reply that appear nowhere in the retrieved context."""
    context_numbers = {_normalise(t) for t in _NUMBER.findall(context)}
    missing = []
    for token in _NUMBER.findall(reply):
        if token in ALLOWED_NUMBERS:
            continue
        if _normalise(token) not in context_numbers:
            missing.append(token)
    return missing


def check(reply: str, context_texts: Iterable[str], question: str = "") -> Verdict:
    """`question` counts as context for numbers: echoing the customer's own
    "iOS 15" is not a hallucination."""
    for secret in SECRET_STRINGS:
        if secret.lower() in reply.lower():
            return Verdict(True, f"secret string: {secret}")
    if NRIC_PATTERN.search(reply):
        return Verdict(True, "NRIC-format identifier")
    if ACCOUNT_PATTERN.search(reply):
        return Verdict(True, "account number")
    missing = ungrounded_numbers(reply, "\n".join([*context_texts, question]))
    if missing:
        return Verdict(True, f"ungrounded numbers: {', '.join(missing)}")
    return ALLOWED
