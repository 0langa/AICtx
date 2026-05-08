"""Unit tests for Phase 1 local context generation."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from aictx.cli import app
from aictx.config import load_config
from aictx.context.lockfile import load_lockfile
from tests.fixtures.git_repos import create_git_repo

runner = CliRunner()


def test_load_config_reads_toml_values() -> None:
    repo = create_git_repo({"README.md": "# Test"})
    config_dir = repo / ".aictx"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "config.toml").write_text(
        """
[project]
context_dir = "docs/AIprojectcontext"
agents_file = "AGENTS.md"
public_docs_dirs = ["docs", "."]

[execution]
default_execution = "local"
write_mode = "apply"
allow_dirty = true

[limits]
max_input_tokens_per_run = 1234
max_output_tokens_per_run = 4321
max_files_per_run = 42
max_file_bytes = 98765
max_remote_runtime_minutes = 11

[llm]
provider = "dry_run"
model = "demo"
temperature = 0.0
""".strip(),
        encoding="utf-8",
    )

    config = load_config(repo)

    assert config.execution.write_mode == "apply"
    assert config.execution.allow_dirty is True
    assert config.limits.max_input_tokens_per_run == 1234
    assert config.llm.provider == "dry_run"
    assert config.llm.model == "demo"


def test_run_phase1_patch_writes_staged_outputs_only() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo",
            "src/main.py": "print('ok')\n",
            "tests/test_main.py": "def test_ok():\n    assert True\n",
        }
    )

    result = runner.invoke(
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
            "patch",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "AICtx run complete" in result.output

    runs_dir = repo / ".aictx" / "runs"
    run_dirs = sorted([path for path in runs_dir.iterdir() if path.is_dir()])
    assert run_dirs
    latest = run_dirs[-1]

    assert (latest / "aictx.patch").exists()
    assert (latest / "inventory.json").exists()
    assert (latest / "context-plan.json").exists()
    assert (latest / "coverage-report.json").exists()
    assert (latest / "contradictions.json").exists()
    assert (latest / "facts" / "project_identity_facts.json").exists()
    assert (latest / "out" / "docs" / "AIprojectcontext" / "ai-index.md").exists()
    assert (latest / "out" / "docs" / "AIprojectcontext" / "project-state.md").exists()
    assert (latest / "out" / "docs" / "AIprojectcontext" / "context.lock.json").exists()
    assert (latest / "out" / "AGENTS.md").exists()

    assert not (repo / "docs" / "AIprojectcontext" / "ai-index.md").exists()
    assert not (repo / "AGENTS.md").exists()


def test_run_phase1_apply_writes_repo_outputs_and_lockfile() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo",
            "src/main.py": "print('ok')\n",
            "tests/test_main.py": "def test_ok():\n    assert True\n",
        }
    )

    result = runner.invoke(
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

    assert result.exit_code == 0, result.output
    context_dir = repo / "docs" / "AIprojectcontext"
    assert (context_dir / "ai-index.md").exists()
    assert (context_dir / "project-state.md").exists()
    assert (context_dir / "code-map.md").exists()
    assert (context_dir / "architecture.md").exists()
    assert (context_dir / "workflows.md").exists()
    assert (context_dir / "public-docs-map.md").exists()
    assert (context_dir / "change-impact-map.md").exists()
    assert (context_dir / "schema.md").exists()
    assert (context_dir / "validation-report.md").exists()
    assert (context_dir / "context.lock.json").exists()
    assert not (repo / "context.lock.json").exists()
    assert (repo / "AGENTS.md").exists()

    lock = load_lockfile(context_dir)
    assert lock is not None
    assert lock.model_provider == "dry_run"
    assert lock.model_name == "dry_run"
    assert any(
        entry.path == "docs/AIprojectcontext/project-state.md" for entry in lock.generated_files
    )
    assert any(
        section.generated_file == "docs/AIprojectcontext/architecture.md"
        for section in lock.sections
    )

    ai_index = (context_dir / "ai-index.md").read_text(encoding="utf-8")
    assert "project-state.md" in ai_index
    assert "validation-report.md" in ai_index

    agents_md = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "docs/AIprojectcontext/ai-index.md" in agents_md


def test_run_phase1_apply_preserves_custom_agents_sections() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo",
            "AGENTS.md": (
                "# AGENTS.md — AI Agent Instructions for Test\n\n"
                "> **Generated by:** `aictx`\n\n"
                "## Rules for all agents\n\n"
                "1. Old managed rule.\n\n"
                "## Repo style policy\n\n"
                "- Keep terse repo-specific guidance.\n"
            ),
            "src/main.py": "print('ok')\n",
        }
    )

    result = runner.invoke(
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

    assert result.exit_code == 0, result.output
    agents_md = (repo / "AGENTS.md").read_text(encoding="utf-8")
    assert "## Repo style policy" in agents_md
    assert "Keep terse repo-specific guidance." in agents_md
    assert "Old managed rule" not in agents_md


def test_run_phase1_generated_context_records_verifiable_outputs_after_apply() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo",
            "src/main.py": "print('ok')\n",
            "tests/test_main.py": "def test_ok():\n    assert True\n",
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

    lock = load_lockfile(repo / "docs" / "AIprojectcontext")
    assert lock is not None
    generated_paths = {entry.path for entry in lock.generated_files}
    assert "docs/AIprojectcontext/ai-index.md" in generated_paths
    assert "docs/AIprojectcontext/architecture.md" in generated_paths
    assert any(section.source_paths for section in lock.sections)
    assert all(
        not source_path.startswith(str(repo))
        for section in lock.sections
        for source_path in section.source_paths
    )
    assert all(
        source_hash != "unknown"
        for section in lock.sections
        for source_hash in section.source_hashes
    )


def test_run_phase1_rerun_does_not_select_generated_context_as_source() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo",
            "src/main.py": "print('ok')\n",
            "tests/test_main.py": "def test_ok():\n    assert True\n",
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

    patch_result = runner.invoke(
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
            "patch",
        ],
    )
    assert patch_result.exit_code == 0, patch_result.output

    latest = sorted([path for path in (repo / ".aictx" / "runs").iterdir() if path.is_dir()])[-1]
    plan = json.loads((latest / "context-plan.json").read_text(encoding="utf-8"))
    selected_files = set(plan["selected_files"])

    assert "AGENTS.md" not in selected_files
    assert not any(path.startswith("docs/AIprojectcontext/") for path in selected_files)


def test_run_phase1_apply_does_not_create_root_context_lock() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo",
            "src/main.py": "print('ok')\n",
        }
    )

    result = runner.invoke(
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

    assert result.exit_code == 0, result.output
    assert not (repo / "context.lock.json").exists()
    assert (repo / "docs" / "AIprojectcontext" / "context.lock.json").exists()


def test_run_phase1_patch_does_not_target_root_context_lock() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo",
            "src/main.py": "print('ok')\n",
        }
    )

    result = runner.invoke(
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
            "patch",
        ],
    )

    assert result.exit_code == 0, result.output
    latest = sorted([path for path in (repo / ".aictx" / "runs").iterdir() if path.is_dir()])[-1]
    patch_text = (latest / "aictx.patch").read_text(encoding="utf-8")
    assert "b/docs/AIprojectcontext/context.lock.json" in patch_text
    assert "b/context.lock.json" not in patch_text


def test_run_phase1_writes_expected_fact_artifacts() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo",
            "src/main.py": "print('ok')\n",
            "tests/test_main.py": "def test_ok():\n    assert True\n",
        }
    )

    result = runner.invoke(
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
            "patch",
        ],
    )

    assert result.exit_code == 0, result.output
    latest = sorted([path for path in (repo / ".aictx" / "runs").iterdir() if path.is_dir()])[-1]
    facts_dir = latest / "facts"
    assert (facts_dir / "project_identity_facts.json").exists()
    assert (facts_dir / "architecture_facts.json").exists()
    assert (facts_dir / "feature_facts.json").exists()
    assert (facts_dir / "workflow_facts.json").exists()
    assert (facts_dir / "docs_facts.json").exists()
    assert (facts_dir / "risk_facts.json").exists()


def test_run_changed_scope_records_changed_files() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo",
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
    patch_result = runner.invoke(
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
            "patch",
        ],
    )
    assert patch_result.exit_code == 0, patch_result.output
    latest = sorted([path for path in (repo / ".aictx" / "runs").iterdir() if path.is_dir()])[-1]
    plan = json.loads((latest / "context-plan.json").read_text(encoding="utf-8"))

    assert plan["changed_files"] == ["src/main.py"]
    assert plan["selected_files"] == ["README.md", "src/main.py"]
    assert plan["reason_per_selected_file"]["src/main.py"] == "source:changed"


def test_run_apply_refuses_dirty_worktree_without_override() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo",
            "src/main.py": "print('ok')\n",
        }
    )
    (repo / "src" / "main.py").write_text("print('dirty')\n", encoding="utf-8")

    result = runner.invoke(
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

    assert result.exit_code == 1
    assert "--allow-dirty" in result.output


def test_run_apply_allows_dirty_worktree_with_override() -> None:
    repo = create_git_repo(
        {
            "README.md": "# Test repo",
            "src/main.py": "print('ok')\n",
        }
    )
    (repo / "src" / "main.py").write_text("print('dirty')\n", encoding="utf-8")

    result = runner.invoke(
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
            "--allow-dirty",
        ],
    )

    assert result.exit_code == 0, result.output
    assert (repo / "docs" / "AIprojectcontext" / "context.lock.json").exists()
