"""Repository inventory data model."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class FileEntry(BaseModel):
    """A single file in the repository inventory."""

    path: str
    kind: Literal["source", "doc", "manifest", "test", "generated", "binary", "ignored", "other"]
    language: str | None = None
    size_bytes: int
    sha256: str
    is_doc: bool = False
    is_source: bool = False
    is_test: bool = False
    is_generated: bool = False
    is_binary: bool = False
    is_ignored: bool = False
    include_reason: str | None = None
    exclude_reason: str | None = None


class RepositoryInventory(BaseModel):
    """Complete repository inventory snapshot."""

    repo_root: str
    branch: str
    head_commit: str
    dirty_state: bool
    files: list[FileEntry] = Field(default_factory=list)
    docs: list[FileEntry] = Field(default_factory=list)
    manifests: list[FileEntry] = Field(default_factory=list)
    build_systems: list[str] = Field(default_factory=list)
    detected_languages: list[str] = Field(default_factory=list)
    entrypoints: list[str] = Field(default_factory=list)
    test_projects: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    scanner_version: str = Field(default="0.1.0")
