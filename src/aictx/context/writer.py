"""AI context scaffold writer."""

from __future__ import annotations

from pathlib import Path

from aictx.models.context_lock import ContextLock


def write_context_scaffold(
    out_dir: Path,
    fact_packs: list[dict[str, object]],
    lock: ContextLock,
) -> list[Path]:
    """Write compact AI-facing context files to *out_dir*."""
    # TODO: implement scaffold generation
    return []
