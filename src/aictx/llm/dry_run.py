"""Dry-run model provider for local development and tests."""

from __future__ import annotations

from aictx.llm.base import ChatRequest, ChatResponse, ModelProvider


class DryRunProvider(ModelProvider):
    """Provider that returns placeholder responses without network calls."""

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Return a deterministic dry-run response."""
        return ChatResponse(
            content=f"[dry-run] purpose={request.purpose} run_id={request.run_id}",
            finish_reason="stop",
            input_tokens=len(request.system_prompt) // 4,
            output_tokens=10,
        )

    def count_tokens(self, text: str) -> int | None:
        """Return a rough character-based estimate."""
        return len(text) // 4
