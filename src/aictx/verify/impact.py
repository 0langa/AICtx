"""Change-impact mapping and stale detection."""

from __future__ import annotations

from pathlib import Path

from aictx.models.context_lock import ContextLock


def detect_impact(
    changed_files: list[Path],
    lock: ContextLock,
) -> dict[str, list[str]]:
    """Map changed files to impacted AI context and public docs."""
    # TODO: implement impact detection
    return {"ai_context": [], "public_docs": []}
