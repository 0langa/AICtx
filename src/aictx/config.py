"""Configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Project-level settings."""

    context_dir: str = Field(default="docs/AIprojectcontext")
    agents_file: str = Field(default="AGENTS.md")
    public_docs_dirs: list[str] = Field(default_factory=lambda: ["docs", "."])


class ExecutionConfig(BaseModel):
    """Execution behavior settings."""

    default_execution: Literal["local", "oci-job"] = Field(default="local")
    write_mode: Literal["patch", "apply"] = Field(default="patch")
    allow_dirty: bool = Field(default=False)


class LimitsConfig(BaseModel):
    """Safety limits."""

    max_input_tokens_per_run: int = Field(default=500_000)
    max_output_tokens_per_run: int = Field(default=100_000)
    max_files_per_run: int = Field(default=5_000)
    max_file_bytes: int = Field(default=250_000)
    max_remote_runtime_minutes: int = Field(default=45)


class LLMConfig(BaseModel):
    """LLM provider settings."""

    provider: Literal["dry_run", "oci_genai"] = Field(default="oci_genai")
    model: str = Field(default="default")
    temperature: float = Field(default=0.0)


class AictxConfig(BaseModel):
    """Top-level configuration model."""

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    limits: LimitsConfig = Field(default_factory=LimitsConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


CONFIG_FILENAME = ".aictx/config.toml"


def load_config(repo_root: Path) -> AictxConfig:
    """Load configuration from repository or defaults."""
    # TODO: implement TOML config parsing
    return AictxConfig()
