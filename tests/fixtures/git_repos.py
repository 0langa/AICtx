"""Dynamic git repo fixtures for testing."""

from __future__ import annotations

import atexit
import shutil
import subprocess
import tempfile
from pathlib import Path

_TEMP_GIT_REPOS: set[Path] = set()


def _cleanup_temp_git_repos() -> None:
    for repo_path in list(_TEMP_GIT_REPOS):
        shutil.rmtree(repo_path, ignore_errors=True)
        _TEMP_GIT_REPOS.discard(repo_path)


atexit.register(_cleanup_temp_git_repos)


def create_git_repo(files: dict[str, str]) -> Path:
    """Create a temporary git repo with *files* (relative path -> content).

    The repo is initialised with a master/main commit so that git status queries
    (e.g. branch detection) work.  Returns the repo root path.
    """
    tmpdir = Path(tempfile.mkdtemp(prefix="aictx-git-fix-"))
    _TEMP_GIT_REPOS.add(tmpdir)

    # default branch name varies by git version; init then rename
    def _run(cmd: list[str]) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(cmd, cwd=tmpdir, check=True, capture_output=True)

    _run(["git", "init"])
    _run(["git", "checkout", "-b", "main"])
    for rel_path, content in files.items():
        target = tmpdir / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    _run(["git", "add", "."])
    _run(
        ["git", "-c", "user.email=test@test.com", "-c", "user.name=Test", "commit", "-m", "initial"]
    )
    return tmpdir
