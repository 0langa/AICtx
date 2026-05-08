"""Strict verifier implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from aictx.context.lockfile import SUPPORTED_SCHEMA_VERSIONS, load_lockfile
from aictx.verify.hashes import sha256_file

VerificationResult = Literal[
    "PASS",
    "FAIL_STALE_AI_CONTEXT",
    "FAIL_PUBLIC_DOCS_IMPACT",
    "FAIL_LOCK_MISMATCH",
    "FAIL_MISSING_SOURCE",
    "FAIL_UNSUPPORTED_SCHEMA",
]


def verify(repo_root: Path, strict: bool = False) -> VerificationResult:
    """Run verification against the repository."""
    context_dir = repo_root / "docs" / "AIprojectcontext"
    lock = load_lockfile(context_dir)
    if lock is None:
        return "FAIL_LOCK_MISMATCH"

    if lock.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        return "FAIL_UNSUPPORTED_SCHEMA"

    for source_file in lock.source_files:
        path = repo_root / source_file.path
        if not path.exists():
            return "FAIL_MISSING_SOURCE"
        if sha256_file(path) != source_file.sha256:
            return "FAIL_STALE_AI_CONTEXT"

    for generated_file in lock.generated_files:
        path = repo_root / generated_file.path
        if not path.exists():
            return "FAIL_LOCK_MISMATCH"
        if sha256_file(path) != generated_file.sha256:
            return "FAIL_LOCK_MISMATCH"

    return "PASS"
