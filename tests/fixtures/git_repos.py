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


def create_monorepo_fixture() -> Path:
    return create_git_repo(
        {
            "README.md": "# Monorepo\n",
            "apps/web/package.json": '{"name":"web"}\n',
            "apps/web/src/index.ts": "export const app = 1;\n",
            "packages/core/src/lib.py": "def core():\n    return 1\n",
            "docs/guide.md": "# Guide\n\nShared docs.\n",
        }
    )


def create_docs_heavy_fixture() -> Path:
    return create_git_repo(
        {
            "README.md": "# Docs Heavy\n",
            "documentation/ARCHITECTURE.md": "# Architecture\n\nDetails\n",
            "documentation/CODEMAP.md": "# Codemap\n\nDetails\n",
            "src/app.py": "print('ok')\n",
        }
    )


def create_binary_heavy_fixture() -> Path:
    return create_git_repo(
        {
            "README.md": "# Binary Heavy\n",
            "src/app.py": "print('ok')\n",
            "assets/blob.bin": "\u0000\u0001\u0002\u0003",
            "assets/image.png": "PNGDATA",
        }
    )


def create_secret_heavy_fixture() -> Path:
    return create_git_repo(
        {
            "README.md": "# Secret Heavy\n",
            "src/app.py": "print('ok')\n",
            ".env.example": "API_KEY=redacted\n",
            "docs/ops.md": "rotate credentials\n",
        }
    )


def create_broken_docs_fixture() -> Path:
    return create_git_repo(
        {
            "README.md": "# Broken Docs\n",
            "documentation/README.md": "# Docs\n\nBroken link: [missing](missing.md)\n",
            "src/app.py": "print('ok')\n",
        }
    )


def create_generated_output_heavy_fixture() -> Path:
    return create_git_repo(
        {
            "README.md": "# Generated Output Heavy\n",
            "src/app.py": "print('ok')\n",
            "dist/bundle.js": "console.log('bundle');\n",
            "build/output.js": "console.log('build');\n",
            ".aictx/runs/old/run-report.json": '{"status":"success"}\n',
        }
    )


def create_large_dependency_fixture() -> Path:
    files = {
        "README.md": "# Large Dependency Fixture\n",
        "src/app.py": "print('ok')\n",
        "package.json": '{"name":"fixture"}\n',
    }
    for idx in range(20):
        files[f"vendor/lib{idx}.txt"] = f"dependency-{idx}\n"
    return create_git_repo(files)
