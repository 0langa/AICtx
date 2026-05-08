"""Integration tests for repository scanner hardening."""

from __future__ import annotations

from aictx.scan.scanner import scan_repository
from tests.fixtures.git_repos import create_git_repo


def _all_paths(inv) -> list[str]:
    return sorted(f.path for f in inv.files)


def _included_paths(inv) -> list[str]:
    return sorted(f.path for f in inv.files if not f.is_ignored)


def test_scan_excludes_aictx_runtime_artifacts() -> None:
    """Generated AICtx runtime files must never enter inventory."""
    repo = create_git_repo(
        {
            "README.md": "# Test",
            "src/main.py": "print('hello')",
            ".aictx/runs/fake-run/inventory.json": "{}",
            ".aictx/cache/cache.json": "{}",
            ".aictx/tmp/temp.txt": "tmp",
        }
    )
    inv = scan_repository(repo)
    included = _included_paths(inv)

    assert "README.md" in included
    assert "src/main.py" in included
    assert not any(p.startswith(".aictx/runs/") for p in included)
    assert not any(p.startswith(".aictx/cache/") for p in included)
    assert not any(p.startswith(".aictx/tmp/") for p in included)


def test_scan_prunes_hard_excluded_directories() -> None:
    """Ignored directories like node_modules must not be traversed."""
    repo = create_git_repo(
        {
            "README.md": "# Test",
            "src/main.py": "print('hello')",
            "node_modules/pkg/index.js": "module.exports = {}",
            "node_modules/pkg/package.json": "{}",
            "build/output.js": "// built",
        }
    )
    inv = scan_repository(repo)
    included = _included_paths(inv)

    assert "README.md" in included
    assert "src/main.py" in included
    assert not any(p.startswith("node_modules/") for p in included)
    assert not any(p.startswith("build/") for p in included)


def test_repeated_scan_file_paths_are_stable() -> None:
    """Two consecutive scans on the same repo must produce identical file lists."""
    repo = create_git_repo(
        {
            "README.md": "# Test",
            "src/aictx_sample.py": "print('hello')",
        }
    )
    inv1 = scan_repository(repo)
    inv2 = scan_repository(repo)

    assert _included_paths(inv1) == _included_paths(inv2)
    assert not any(p.startswith(".aictx/runs/") for p in _included_paths(inv1))
    assert not any(p.startswith(".aictx/runs/") for p in _included_paths(inv2))
