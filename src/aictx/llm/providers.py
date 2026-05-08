"""Model provider factory."""

from __future__ import annotations

from aictx.config import LLMConfig
from aictx.errors import ConfigError
from aictx.llm.base import ModelProvider
from aictx.llm.dry_run import DryRunProvider
from aictx.llm.oci_genai import OCIGenAIProvider


def create_model_provider(config: LLMConfig, allow_ai: bool = False) -> ModelProvider:
    """Create a configured model provider.

    Non-dry-run providers require explicit opt-in so local commands never
    accidentally send repository context to an external service.
    """
    if config.provider == "dry_run":
        return DryRunProvider()

    if not allow_ai:
        raise ConfigError(f"Provider '{config.provider}' requires explicit --allow-ai.")

    if config.provider == "oci_genai":
        if not config.compartment_id:
            raise ConfigError("OCI GenAI provider requires llm.compartment_id.")
        return OCIGenAIProvider(compartment_id=config.compartment_id, model_id=config.model)

    raise ConfigError(f"Unsupported provider: {config.provider}")
