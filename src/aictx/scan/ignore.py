""``.gitignore` and `.aictxignore` matching."""

from __future__ import annotations

from pathlib import Path


class IgnoreMatcher:
    """Matches paths against ignore patterns."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        # TODO: load and compile pathspec patterns

    def is_ignored(self, path: Path) -> bool:
        """Return True if *path* should be ignored."""
        return False
