"""Thin Gemini client with retry on rate limits."""
from __future__ import annotations

import os
import random
import threading
import time
from functools import lru_cache
from pathlib import Path

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

# Confirm current free-tier model IDs in Google AI Studio; override via env.
CHAT_MODEL = os.environ.get("MERLION_CHAT_MODEL", "gemini-flash-lite-latest")
MAX_RETRIES = 6
# Client-side throttle per model, to stay under the free tier's requests-per-minute.
RPM = float(os.environ.get("MERLION_RPM", "10"))
_last_call: dict = {}
CALLS: dict = {}  # model -> requests sent this process, reported in the brief
_throttle_lock = threading.Lock()


def _throttle(model: str) -> None:
    with _throttle_lock:
        wait = _last_call.get(model, 0) + 60 / RPM - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_call[model] = time.monotonic()
        CALLS[model] = CALLS.get(model, 0) + 1


@lru_cache(maxsize=1)
def _client():
    from dotenv import load_dotenv
    from google import genai

    load_dotenv(ENV_FILE)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set (put it in .env for local runs)")
    return genai.Client(api_key=api_key)


def generate(system_prompt: str, user_content: str, model: str = CHAT_MODEL) -> str:
    from google.genai import errors, types

    config = types.GenerateContentConfig(system_instruction=system_prompt, temperature=0)
    for attempt in range(MAX_RETRIES):
        _throttle(model)
        try:
            response = _client().models.generate_content(
                model=model, contents=user_content, config=config
            )
            return response.text or ""
        except errors.APIError as exc:
            if exc.code not in (429, 500, 503) or attempt == MAX_RETRIES - 1:
                raise
            time.sleep(min(60, 2 ** attempt) + random.uniform(0, 1))
    raise AssertionError("unreachable")
