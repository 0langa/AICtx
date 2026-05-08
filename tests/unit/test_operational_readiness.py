"""Unit tests for readiness helpers and safe workflows."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from aictx.cli import app
from aictx.config import LLMConfig
from aictx.errors import ConfigError, PatchApplyError
from aictx.io.patches import apply_patch, make_unified_diff
from aictx.llm.dry_run import DryRunProvider
from aictx.llm.providers import create_model_provider
from aictx.oci.doctor import run_oci_doctor
from aictx.verify.verifier import verify_detailed
from tests.fixtures.git_repos import create_git_repo

runner = CliRunner()


def test_model_provider_defaults_to_dry_run_and_blocks_oci_without_opt_in() -> None:
    provider = create_model_provider(LLMConfig())
    assert isinstance(provider, DryRunProvider)

    with pytest.raises(ConfigError, match="--allow-ai"):
        create_model_provider(LLMConfig(provider="oci_genai", compartment_id="ocid1.compartment"))


def test_oci_doctor_reports_missing_local_prerequisites(tmp_path: Path) -> None:
    report = run_oci_doctor(config_file=tmp_path / "missing-config")

    assert report.config_file_exists is False
    assert report.ready is False
    assert str(tmp_path / "missing-config") in report.missing


def test_apply_patch_validates_then_applies_git_patch() -> None:
    repo = create_git_repo({"README.md": "old\n"})
    patch_text = make_unified_diff("old\n", "new\n", "a/README.md", "b/README.md")

    apply_patch(patch_text, repo)

    assert (repo / "README.md").read_text(encoding="utf-8") == "new\n"


def test_apply_patch_rejects_escaping_paths() -> None:
    repo = create_git_repo({"README.md": "old\n"})
    patch_text = make_unified_diff("", "bad\n", "/dev/null", "b/../bad.md")

    with pytest.raises(PatchApplyError):
        apply_patch(patch_text, repo)


def test_public_docs_update_generates_review_patch_for_changed_sources() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo\n",
            "src/main.py": "print('ok')\n",
        }
    )
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
    (repo / "src" / "main.py").write_text("print('changed')\n", encoding="utf-8")

    update_result = runner.invoke(
        app,
        [
            "public-docs",
            "update",
            "--project",
            str(repo),
            "--scope",
            "changed",
            "--write",
            "patch",
        ],
    )

    assert update_result.exit_code == 0, update_result.output
    assert "Public docs review generated" in update_result.output
    assert not (repo / "docs" / "AIprojectcontext" / "public-docs-review.md").exists()
    latest = sorted(
        [
            path
            for path in (repo / ".aictx" / "runs").iterdir()
            if path.is_dir() and path.name.endswith("-public-docs")
        ]
    )[-1]
    impact = json.loads((latest / "public-docs-impact.json").read_text(encoding="utf-8"))
    assert impact["impacted_docs"] == {"README.md": ["src/main.py"]}
    assert (latest / "public-docs.patch").exists()


def test_public_docs_map_is_targeted_not_all_source_files() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo\n",
            "documentation/ARCHITECTURE.md": "# Arch\n",
            "src/main.py": "print('ok')\n",
            "src/helper.py": "def helper():\n    return 1\n",
            "tests/test_main.py": "def test_ok():\n    assert True\n",
            "pyproject.toml": "[project]\nname='demo'\nversion='0.1.0'\n",
        }
    )

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

    report = verify_detailed(repo, strict=True)
    assert report.result == "PASS"

    lock_path = repo / "docs" / "AIprojectcontext" / "context.lock.json"
    payload = json.loads(lock_path.read_text(encoding="utf-8"))
    docs_map = {entry["path"]: entry for entry in payload["public_docs_map"]}

    assert docs_map["README.md"]["source_paths"] == ["src/main.py"]
    assert "tests/test_main.py" not in docs_map["documentation/ARCHITECTURE.md"]["source_paths"]


def test_context_regen_preserves_public_doc_impact_until_doc_changes() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo\n",
            "src/main.py": "print('ok')\n",
        }
    )
    apply_result = runner.invoke(
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
    assert apply_result.exit_code == 0, apply_result.output
    (repo / "src" / "main.py").write_text("print('changed')\n", encoding="utf-8")

    regen_result = runner.invoke(
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
            "changed",
            "--write",
            "apply",
            "--allow-dirty",
        ],
    )
    assert regen_result.exit_code == 0, regen_result.output

    report = verify_detailed(repo, strict=True)
    assert report.result == "FAIL_PUBLIC_DOCS_IMPACT"
    assert report.public_docs_impacts == {"README.md": ["src/main.py"]}


def test_clean_keep_runs_is_dry_run_until_confirmed() -> None:
    repo = create_git_repo({"README.md": "# Test repo\n"})
    runs_dir = repo / ".aictx" / "runs"
    (runs_dir / "001").mkdir(parents=True)
    (runs_dir / "002").mkdir(parents=True)

    dry_result = runner.invoke(app, ["clean", "--project", str(repo), "--keep-runs", "1"])
    assert dry_result.exit_code == 0, dry_result.output
    assert (runs_dir / "001").exists()

    apply_result = runner.invoke(
        app, ["clean", "--project", str(repo), "--keep-runs", "1", "--yes"]
    )
    assert apply_result.exit_code == 0, apply_result.output
    assert not (runs_dir / "001").exists()
    assert (runs_dir / "002").exists()
