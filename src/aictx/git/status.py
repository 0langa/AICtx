"""Git worktree status inspection."""

from __future__ import annotations

import subprocess
from pathlib import Path


class WorktreeStatus:
    """Represents the current git worktree state."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.branch = self._run(["git", "-C", str(repo_root), "branch", "--show-current"]).strip()
        self.head_commit = self._run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"]
        ).strip()
        self.dirty = bool(self._run(["git", "-C", str(repo_root), "status", "--short"]).strip())
        self.untracked_files: list[str] = []
        self.modified_files: list[str] = []
        self._parse_status()

    def _run(self, cmd: list[str]) -> str:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.stdout

    def _parse_status(self) -> None:
        output = self._run(
            ["git", "-C", str(self.repo_root), "status", "--short"]
        )
        for line in output.splitlines():
            if line.startswith("??"):
                self.untracked_files.append(line[3:])
            elif line.startswith(" M") or line.startswith("M "):
                self.modified_files.append(line[3:])
