"""Open-source prompt-injection classifier, loaded lazily and run locally.

Set MERLION_CLASSIFIER=off to skip it (rules still apply). Useful for quick
local runs without the ~1 GB model download; CI always runs it.
"""
from __future__ import annotations

import os
from functools import lru_cache

MODEL_ID = "protectai/deberta-v3-base-prompt-injection-v2"
MODEL_REVISION = "90c9989b1a342275dd0d1a95aad283c04e075671"
THRESHOLD = 0.5


def enabled() -> bool:
    return os.environ.get("MERLION_CLASSIFIER", "on").lower() != "off"


@lru_cache(maxsize=1)
def _pipeline():
    from transformers import pipeline

    return pipeline(
        "text-classification",
        model=MODEL_ID,
        revision=MODEL_REVISION,
        truncation=True,
        max_length=512,
    )


def injection_score(text: str) -> float:
    """Probability (0-1) that `text` is a prompt injection."""
    result = _pipeline()(text)[0]
    score = float(result["score"])
    return score if result["label"] == "INJECTION" else 1.0 - score
