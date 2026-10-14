"""Moonshot connector for the Merlion Bank chatbot and each of its guardrails.

The endpoint's `model` field picks the target:
  bot                  full chatbot, guardrails on   (IMDA output testing)
  bot-unguarded        full chatbot, guardrails off  (baseline)
  input-filter         input filter alone            (IMDA component testing)
  retrieval-sanitiser  sanitiser alone, on one chunk
  output-filter        output filter alone; prompt is JSON {"reply", "context"}

Component targets return a label (ALLOWED / BLOCKED, or KEPT / STRIPPED / DROPPED)
and make no model calls.
"""
import asyncio
import json
import sys
from pathlib import Path

from moonshot.src.connectors.connector import Connector, perform_retry
from moonshot.src.connectors.connector_response import ConnectorResponse
from moonshot.src.connectors_endpoints.connector_endpoint_arguments import (
    ConnectorEndpointArguments,
)

# The repo root, so `app` and `guardrails` import when Moonshot loads this file from its workspace.
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _sanitiser_label(text: str) -> str:
    from app.retrieval import Chunk
    from guardrails import retrieval_sanitiser

    source, _, body = text.partition("\n")
    kept, notes = retrieval_sanitiser.sanitise([Chunk(source.strip(), "", body)])
    if not kept:
        return "DROPPED"
    return "STRIPPED" if notes else "KEPT"


def _respond(target: str, prompt: str) -> str:
    if target in ("bot", "bot-unguarded"):
        from app.bot import answer

        return answer(prompt, guarded=(target == "bot")).reply
    if target == "input-filter":
        from guardrails import input_filter

        return input_filter.check(prompt).label
    if target == "retrieval-sanitiser":
        return _sanitiser_label(prompt)
    if target == "output-filter":
        from guardrails import output_filter

        case = json.loads(prompt)
        return output_filter.check(case["reply"], case.get("context", []), case.get("question", "")).label
    raise ValueError(f"unknown merlion target: {target}")


class MerlionConnector(Connector):
    def __init__(self, ep_arguments: ConnectorEndpointArguments):
        super().__init__(ep_arguments)

    @Connector.rate_limited
    @perform_retry
    async def get_response(self, prompt: str) -> ConnectorResponse:
        reply = await asyncio.to_thread(_respond, self.model, prompt)
        return ConnectorResponse(response=reply)
