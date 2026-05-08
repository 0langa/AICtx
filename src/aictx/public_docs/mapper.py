"""Public docs map generation."""

from __future__ import annotations

from pathlib import Path

from aictx.models.docs_map import DocsMap


def build_public_docs_map(repo_root: Path) -> DocsMap:
    """Scan *repo_root* and build a compact public docs map."""
    # TODO: implement docs mapping
    return DocsMap()
