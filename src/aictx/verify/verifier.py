"""Strict verifier implementation."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from aictx.context.lockfile import SUPPORTED_SCHEMA_VERSIONS, load_lockfile
from aictx.models.context_lock import ContextLock
from aictx.verify.hashes import sha256_file

VerificationResult = Literal[
    "PASS",
    "FAIL_STALE_AI_CONTEXT",
    "FAIL_PUBLIC_DOCS_IMPACT",
    "FAIL_LOCK_MISMATCH",
    "FAIL_MISSING_SOURCE",
    "FAIL_UNSUPPORTED_SCHEMA",
]

REQUIRED_GENERATED_CONTEXT_FILES = {
    "AGENTS.md",
    "docs/AIprojectcontext/ai-index.md",
    "docs/AIprojectcontext/project-state.md",
    "docs/AIprojectcontext/code-map.md",
    "docs/AIprojectcontext/architecture.md",
    "docs/AIprojectcontext/workflows.md",
    "docs/AIprojectcontext/public-docs-map.md",
    "docs/AIprojectcontext/change-impact-map.md",
    "docs/AIprojectcontext/schema.md",
    "docs/AIprojectcontext/validation-report.md",
}


def verify(repo_root: Path, strict: bool = False) -> VerificationResult:
    """Run verification against the repository."""
    context_dir = repo_root / "docs" / "AIprojectcontext"
    lock = load_lockfile(context_dir)
    if lock is None:
        return "FAIL_LOCK_MISMATCH"

    if lock.schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        return "FAIL_UNSUPPORTED_SCHEMA"

    source_hashes_by_path = {
        source_file.path: source_file.sha256 for source_file in lock.source_files
    }
    for source_file in lock.source_files:
        path = repo_root / source_file.path
        if not path.exists():
            return "FAIL_MISSING_SOURCE"
        if sha256_file(path) != source_file.sha256:
            return "FAIL_STALE_AI_CONTEXT"

    generated_paths: set[str] = set()
    for generated_file in lock.generated_files:
        generated_paths.add(generated_file.path)
        path = repo_root / generated_file.path
        if not path.exists():
            return "FAIL_LOCK_MISMATCH"
        if sha256_file(path) != generated_file.sha256:
            return "FAIL_LOCK_MISMATCH"

    if strict:
        return _verify_strict_structure(repo_root, lock, source_hashes_by_path, generated_paths)

    return "PASS"


def _verify_strict_structure(
    repo_root: Path,
    lock: ContextLock,
    source_hashes_by_path: dict[str, str],
    generated_paths: set[str],
) -> VerificationResult:
    """Verify deterministic lock structure beyond raw file hashes."""
    if lock.generated_files:
        missing_generated = REQUIRED_GENERATED_CONTEXT_FILES - generated_paths
        if missing_generated:
            return "FAIL_LOCK_MISMATCH"

    section_ids: set[str] = set()
    for section in lock.sections:
        if section.section_id in section_ids:
            return "FAIL_LOCK_MISMATCH"
        section_ids.add(section.section_id)

        if section.generated_file not in generated_paths:
            return "FAIL_LOCK_MISMATCH"
        if len(section.source_paths) != len(section.source_hashes):
            return "FAIL_LOCK_MISMATCH"
        for source_path, source_hash in zip(
            section.source_paths, section.source_hashes, strict=True
        ):
            if source_hashes_by_path.get(source_path) != source_hash:
                return "FAIL_LOCK_MISMATCH"

    if "AGENTS.md" in generated_paths:
        agents_path = repo_root / "AGENTS.md"
        try:
            agents_text = agents_path.read_text(encoding="utf-8")
        except OSError:
            return "FAIL_LOCK_MISMATCH"
        if "docs/AIprojectcontext/ai-index.md" not in agents_text:
            return "FAIL_LOCK_MISMATCH"

    return "PASS"
