"""Unit tests for init and hash-only verification behavior."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from aictx.cli import app
from aictx.context.lockfile import load_lockfile
from aictx.verify.verifier import verify
from tests.fixtures.git_repos import create_git_repo

runner = CliRunner()


def test_verify_fails_when_lockfile_missing() -> None:
    repo = create_git_repo({"README.md": "# Test"})
    assert verify(repo, strict=True) == "FAIL_LOCK_MISMATCH"


def test_verify_passes_after_init_lockfile() -> None:
    repo = create_git_repo({"README.md": "# Test", "src/main.py": "print('ok')"})
    result = runner.invoke(app, ["init", "--project", str(repo)])

    assert result.exit_code == 0
    assert verify(repo, strict=True) == "PASS"


def test_verify_fails_when_tracked_source_file_changes() -> None:
    repo = create_git_repo({"README.md": "# Test", "src/main.py": "print('ok')"})
    runner.invoke(app, ["init", "--project", str(repo)])
    (repo / "src" / "main.py").write_text("print('changed')", encoding="utf-8")

    assert verify(repo, strict=True) == "FAIL_STALE_AI_CONTEXT"


def test_verify_fails_when_source_file_is_deleted() -> None:
    repo = create_git_repo({"README.md": "# Test", "src/main.py": "print('ok')"})
    runner.invoke(app, ["init", "--project", str(repo)])
    (repo / "src" / "main.py").unlink()

    assert verify(repo, strict=True) == "FAIL_MISSING_SOURCE"


def test_verify_rejects_unsupported_schema() -> None:
    repo = create_git_repo({"README.md": "# Test"})
    runner.invoke(app, ["init", "--project", str(repo)])
    lockfile_path = repo / "docs" / "AIprojectcontext" / "context.lock.json"
    data = json.loads(lockfile_path.read_text(encoding="utf-8"))
    data["schema_version"] = "999.0"
    lockfile_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    assert verify(repo, strict=True) == "FAIL_UNSUPPORTED_SCHEMA"


def test_init_creates_lockfile_and_ignore_file() -> None:
    repo = create_git_repo({"README.md": "# Test", "src/main.py": "print('ok')"})
    result = runner.invoke(app, ["init", "--project", str(repo)])

    assert result.exit_code == 0
    assert (repo / ".aictxignore").exists()
    lock = load_lockfile(repo / "docs" / "AIprojectcontext")
    assert lock is not None
    assert lock.model_provider == "none"
    assert lock.model_name == "none"
    assert any(entry.path == "README.md" for entry in lock.source_files)


def test_init_refreshes_existing_generated_lockfile_sources() -> None:
    repo = create_git_repo({"README.md": "# Test", "src/main.py": "print('ok')"})
    run_result = runner.invoke(
        app,
        [
            "run",
            "--project",
            str(repo),
            "--mode",
            "setup-context",
            "--execution",
            "local",
            "--scope",
            "full",
            "--write",
            "apply",
        ],
    )
    assert run_result.exit_code == 0, run_result.output

    result = runner.invoke(app, ["init", "--project", str(repo)])

    assert result.exit_code == 0
    assert verify(repo, strict=True) == "PASS"
    lock = load_lockfile(repo / "docs" / "AIprojectcontext")
    assert lock is not None
    assert lock.generated_files
    assert lock.model_provider == "dry_run"
    assert any(entry.path == "docs/AIprojectcontext/ai-index.md" for entry in lock.generated_files)
    assert not any(entry.path == "AGENTS.md" for entry in lock.source_files)
    assert not any(entry.path.startswith("docs/AIprojectcontext/") for entry in lock.source_files)


def test_strict_verify_rejects_broken_section_source_linkage() -> None:
    repo = create_git_repo({"README.md": "# Test", "src/main.py": "print('ok')"})
    run_result = runner.invoke(
        app,
        [
            "run",
            "--project",
            str(repo),
            "--mode",
            "setup-context",
            "--execution",
            "local",
            "--scope",
            "full",
            "--write",
            "apply",
        ],
    )
    assert run_result.exit_code == 0, run_result.output

    lockfile_path = repo / "docs" / "AIprojectcontext" / "context.lock.json"
    data = json.loads(lockfile_path.read_text(encoding="utf-8"))
    data["sections"][0]["source_hashes"] = ["unknown"]
    lockfile_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    assert verify(repo, strict=True) == "FAIL_LOCK_MISMATCH"


def test_verify_cli_fails_when_lockfile_missing() -> None:
    repo = create_git_repo({"README.md": "# Test"})
    result = runner.invoke(app, ["verify", "--project", str(repo), "--strict"])

    assert result.exit_code != 0
    assert "FAIL_LOCK_MISMATCH" in result.output


def test_verify_cli_can_emit_json() -> None:
    repo = create_git_repo({"README.md": "# Test"})
    result = runner.invoke(app, ["verify", "--project", str(repo), "--strict", "--json"])

    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload["status"] == "FAIL_LOCK_MISMATCH"
    assert payload["next_command"] == "aictx init --project ."


def test_status_cli_reports_changed_sources_json() -> None:
    repo = create_git_repo({"README.md": "# Test", "src/main.py": "print('ok')\n"})
    runner.invoke(app, ["init", "--project", str(repo)])
    (repo / "src" / "main.py").write_text("print('changed')\n", encoding="utf-8")

    result = runner.invoke(app, ["status", "--project", str(repo), "--strict", "--json"])

    assert result.exit_code != 0
    payload = json.loads(result.output)
    assert payload["verification"]["result"] == "FAIL_STALE_AI_CONTEXT"
    assert payload["changed_sources"] == ["src/main.py"]
