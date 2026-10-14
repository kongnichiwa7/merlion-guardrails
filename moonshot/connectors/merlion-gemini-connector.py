"""Gemini connector on the current `google-genai` SDK.

Replaces moonshot-data 0.7.6's google-gemini-connector, which depends on the
deprecated `google.generativeai` package. Used for the judge endpoints.
"""
import asyncio
import sys
from pathlib import Path

from moonshot.src.connectors.connector import Connector, perform_retry
from moonshot.src.connectors.connector_response import ConnectorResponse
from moonshot.src.connectors_endpoints.connector_endpoint_arguments import (
    ConnectorEndpointArguments,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class MerlionGeminiConnector(Connector):
    def __init__(self, ep_arguments: ConnectorEndpointArguments):
        super().__init__(ep_arguments)

    @Connector.rate_limited
    @perform_retry
    async def get_response(self, prompt: str) -> ConnectorResponse:
        from app import llm

        text = f"{self.pre_prompt}{prompt}{self.post_prompt}"
        reply = await asyncio.to_thread(llm.generate, self.system_prompt, text, self.model)
        return ConnectorResponse(response=reply.strip())
