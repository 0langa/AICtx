"""Patch creation and application helpers."""

from __future__ import annotations

import difflib
from pathlib import Path


def make_unified_diff(original: str, updated: str, original_path: str, updated_path: str) -> str:
    """Return a unified diff between *original* and *updated*."""
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            updated.splitlines(keepends=True),
            fromfile=original_path,
            tofile=updated_path,
        )
    )


def apply_patch(patch_text: str, target_dir: Path) -> None:
    """Apply a unified diff patch to files in *target_dir*."""
    # TODO: implement patch application
    pass
