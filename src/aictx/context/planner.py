"""Context planning stage."""

from __future__ import annotations

from pathlib import Path

from aictx.models.inventory import RepositoryInventory


def plan_context(
    inventory: RepositoryInventory,
    existing_context_dir: Path | None = None,
    existing_agents_md: Path | None = None,
) -> dict[str, object]:
    """Plan which files to include in the context generation."""
    # TODO: implement context planning
    return {}
