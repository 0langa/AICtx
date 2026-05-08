"""Repository scanner implementation."""

from __future__ import annotations

from pathlib import Path

from aictx.models.inventory import RepositoryInventory


def scan_repository(repo_root: Path) -> RepositoryInventory:
    """Scan *repo_root* and return a deterministic inventory."""
    # TODO: implement full scanner
    return RepositoryInventory(
        repo_root=str(repo_root),
        branch="unknown",
        head_commit="unknown",
        dirty_state=False,
    )
