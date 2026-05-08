"""OCI Generative AI provider stub."""

from __future__ import annotations

from aictx.llm.base import ChatRequest, ChatResponse, ModelProvider


class OCIGenAIProvider(ModelProvider):
    """Guarded OCI GenAI placeholder. No network calls are implemented."""

    def __init__(self, compartment_id: str, model_id: str = "default") -> None:
        self.compartment_id = compartment_id
        self.model_id = model_id

    def metadata(self) -> dict[str, str]:
        """Return safe provider metadata without prompt content."""
        return {"provider": "oci_genai", "model": self.model_id, "network": "not_implemented"}

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Fail before any network call until OCI runtime is implemented."""
        raise NotImplementedError(
            "OCI GenAI provider is not implemented in this milestone; no network call was made."
        )

    def count_tokens(self, text: str) -> int | None:
        """Return rough local estimate until OCI tokenizer is implemented."""
        return len(text) // 4
