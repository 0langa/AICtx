"""OCI Generative AI provider implementation."""

from __future__ import annotations

from aictx.llm.base import ChatRequest, ChatResponse, ModelProvider


class OCIGenAIProvider(ModelProvider):
    """Provider that calls OCI Generative AI endpoints."""

    def __init__(self, compartment_id: str, model_id: str = "default") -> None:
        self.compartment_id = compartment_id
        self.model_id = model_id

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Send a request to OCI Generative AI."""
        # TODO: implement OCI SDK integration
        raise NotImplementedError("OCI GenAI provider not yet implemented")

    def count_tokens(self, text: str) -> int | None:
        """Return token count using OCI tokenizer."""
        # TODO: implement OCI token counting
        return len(text) // 4
