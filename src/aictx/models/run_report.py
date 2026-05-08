"""Run report data model."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class RunReport(BaseModel):
    """Summary of a single aictx run."""

    run_id: str
    project_path: str
    mode: str
    scope: Literal["full", "changed"]
    execution: Literal["local", "oci-job"]
    write_mode: Literal["patch", "apply"]
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    status: Literal["started", "success", "partial", "failed"] = "started"
    files_scanned: int = 0
    files_selected: int = 0
    tokens_estimated_input: int = 0
    tokens_estimated_output: int = 0
    model_calls: int = 0
    generated_files: list[str] = Field(default_factory=list)
    selected_files: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    output_dir: str | None = None
    patch_path: str | None = None
    error_message: str | None = None
