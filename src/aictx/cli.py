"""AICtx CLI entry point."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from aictx import __version__

app = typer.Typer(
    name="aictx",
    help="Prepare Git repositories for low-token AI-agent work.",
    no_args_is_help=True,
    invoke_without_command=True,
)
console = Console()


def _resolve_repo_root(project: str) -> Path:
    from aictx.errors import AictxError
    from aictx.git.repo import find_git_root

    project_path = Path(project).resolve()
    if not project_path.exists():
        raise typer.BadParameter(f"Project path does not exist: {project}")

    try:
        return find_git_root(project_path)
    except AictxError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc


@app.callback()
def main(
    version: bool = typer.Option(False, "--version", help="Show version and exit."),
) -> None:
    """AICtx - Local-first CLI tool for AI-agent repository context."""
    if version:
        console.print(f"aictx {__version__}")
        raise typer.Exit()


@app.command()
def init(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
) -> None:
    """Initialize a repository for aictx processing."""
    from aictx.context.lockfile import (
        build_lockfile_from_inventory,
        load_lockfile,
        write_lockfile,
    )
    from aictx.scan.scanner import scan_repository

    repo_root = _resolve_repo_root(project)
    ignore_path = repo_root / ".aictxignore"
    if not ignore_path.exists():
        ignore_path.write_text("# AICtx custom ignore patterns\n", encoding="utf-8")

    inventory = scan_repository(repo_root)
    context_dir = repo_root / "docs" / "AIprojectcontext"
    context_dir.mkdir(parents=True, exist_ok=True)
    existing_lock = load_lockfile(context_dir)
    lock = build_lockfile_from_inventory(inventory)
    if existing_lock is not None and existing_lock.generated_files:
        lock = existing_lock.model_copy(
            update={
                "tool_version": lock.tool_version,
                "repo_head_commit": lock.repo_head_commit,
                "generated_at": lock.generated_at,
                "scanner_config_hash": lock.scanner_config_hash,
                "source_files": lock.source_files,
                "generated_files": existing_lock.generated_files,
                "sections": existing_lock.sections,
                "public_docs_map": existing_lock.public_docs_map,
                "change_impact_map": existing_lock.change_impact_map,
                "model_provider": existing_lock.model_provider,
                "model_name": existing_lock.model_name,
                "last_validation": existing_lock.last_validation,
            }
        )
    write_lockfile(context_dir, lock)

    tracked_files = len(lock.source_files)
    console.print("[bold green]AICtx initialized[/bold green]")
    console.print(f"repo: {repo_root}")
    console.print(f"context dir: {context_dir.relative_to(repo_root).as_posix()}")
    console.print(
        f"lockfile: {(context_dir / 'context.lock.json').relative_to(repo_root).as_posix()}"
    )
    console.print(f"source files tracked: {tracked_files}")


@app.command()
def scan(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
) -> None:
    """Scan a repository and print/write an inventory."""
    from aictx.scan.scanner import scan_repository

    repo_root = _resolve_repo_root(project)

    inventory = scan_repository(repo_root)

    # Build summary
    included = [f for f in inventory.files if not f.is_ignored]
    ignored = [f for f in inventory.files if f.is_ignored]
    docs = inventory.docs
    manifests = inventory.manifests
    secrets = inventory.secrets

    console.print("[bold green]AICtx scan complete[/bold green]")
    console.print(f"repo: {inventory.repo_root}")
    console.print(f"branch: {inventory.branch}")
    console.print(f"head: {inventory.head_commit}")
    console.print(f"dirty: {inventory.dirty_state}")
    console.print(f"files included: {len(included)}")
    console.print(f"files ignored: {len(ignored)}")
    console.print(f"docs: {len(docs)}")
    console.print(f"source: {len([f for f in included if f.is_source])}")
    console.print(f"tests: {len([f for f in included if f.is_test])}")
    console.print(f"manifests: {len(manifests)}")
    console.print(f"secrets: {len(secrets)}")
    if secrets:
        for s in secrets:
            console.print(f"  [yellow]{s.path}[/yellow] ({s.detector_name}, severity={s.severity})")

    # Write inventory JSON
    run_id = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ-scan")
    runs_dir = repo_root / ".aictx" / "runs" / run_id
    runs_dir.mkdir(parents=True, exist_ok=True)
    inv_path = runs_dir / "inventory.json"
    inv_path.write_text(inventory.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"inventory: {inv_path}")


@app.command()
def run(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
    mode: str = typer.Option("setup-context", "--mode", help="Run mode."),
    execution: str = typer.Option("local", "--execution", "-e", help="Execution target."),
    scope: str = typer.Option("full", "--scope", help="Run scope: full or changed."),
    write: str = typer.Option("patch", "--write", "-w", help="Write mode: patch or apply."),
    provider: str | None = typer.Option(None, "--provider", help="Model provider override."),
    allow_ai: bool = typer.Option(False, "--allow-ai", help="Permit non-dry-run AI providers."),
    allow_dirty: bool = typer.Option(
        False, "--allow-dirty", help="Permit apply on dirty worktree."
    ),
) -> None:
    """Run the aictx pipeline."""
    from aictx.config import load_config
    from aictx.context.pipeline import run_local_context_pipeline

    if mode != "setup-context":
        console.print(f"[bold red]Unsupported mode:[/bold red] {mode}")
        raise typer.Exit(code=1)
    if execution != "local":
        console.print(f"[bold red]Unsupported execution:[/bold red] {execution}")
        raise typer.Exit(code=1)
    if scope not in {"full", "changed"}:
        console.print(f"[bold red]Unsupported scope:[/bold red] {scope}")
        raise typer.Exit(code=1)
    if write not in {"patch", "apply"}:
        console.print(f"[bold red]Unsupported write mode:[/bold red] {write}")
        raise typer.Exit(code=1)
    if provider is not None and provider not in {"dry_run", "oci_genai"}:
        console.print(f"[bold red]Unsupported provider:[/bold red] {provider}")
        raise typer.Exit(code=1)

    repo_root = _resolve_repo_root(project)
    config = load_config(repo_root)
    if provider is not None:
        config = config.model_copy(
            update={"llm": config.llm.model_copy(update={"provider": provider})}
        )
    if allow_dirty:
        config = config.model_copy(
            update={"execution": config.execution.model_copy(update={"allow_dirty": True})}
        )
    run_id = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ-run")

    try:
        report = run_local_context_pipeline(
            repo_root=repo_root,
            run_id=run_id,
            config=config,
            scope=scope,  # type: ignore[arg-type]
            write_mode=write,  # type: ignore[arg-type]
            allow_ai=allow_ai,
            allow_dirty=allow_dirty,
        )
    except Exception as exc:
        console.print(f"[bold red]run failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print("[bold green]AICtx run complete[/bold green]")
    console.print(f"repo: {repo_root}")
    console.print(f"run id: {report.run_id}")
    console.print(f"status: {report.status}")
    console.print(f"files scanned: {report.files_scanned}")
    console.print(f"files selected: {report.files_selected}")
    console.print(f"estimated input tokens: {report.tokens_estimated_input}")
    console.print(f"generated files: {len(report.generated_files)}")
    if report.output_dir:
        console.print(f"output dir: {report.output_dir}")
    if report.patch_path:
        console.print(f"patch: {report.patch_path}")
    for warning in report.warnings:
        console.print(f"[yellow]warning:[/yellow] {warning}")

    raise typer.Exit(code=0 if report.status == "success" else 1)


@app.command()
def verify(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict verification."),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON."),
) -> None:
    """Verify generated AI context freshness."""
    from aictx.verify.verifier import verify_detailed

    repo_root = _resolve_repo_root(project)

    report = verify_detailed(repo_root, strict=strict)
    if json_output:
        console.print_json(report.model_dump_json())
    elif report.result == "PASS":
        console.print("[bold green]PASS[/bold green]")
    else:
        console.print(f"[bold red]{report.result}[/bold red]")
        if report.next_command:
            console.print(f"next: {report.next_command}")

    if report.result == "PASS":
        raise typer.Exit(code=0)

    raise typer.Exit(code=1)


@app.command()
def status(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict verification."),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON."),
) -> None:
    """Show repository and context readiness status."""
    from aictx.context.lockfile import load_lockfile
    from aictx.scan.scanner import scan_repository
    from aictx.verify.verifier import determine_changed_source_paths, verify_detailed

    repo_root = _resolve_repo_root(project)
    inventory = scan_repository(repo_root)
    lock = load_lockfile(repo_root / "docs" / "AIprojectcontext")
    report = verify_detailed(repo_root, strict=strict)
    changed_paths = determine_changed_source_paths(inventory, lock)
    payload = {
        "repo": str(repo_root),
        "branch": inventory.branch,
        "head": inventory.head_commit,
        "dirty": inventory.dirty_state,
        "files": len([file for file in inventory.files if not file.is_ignored]),
        "changed_sources": changed_paths,
        "verification": report.model_dump(mode="json"),
    }
    if json_output:
        console.print_json(json.dumps(payload, indent=2, sort_keys=True))
        raise typer.Exit(code=0 if report.result == "PASS" else 1)

    console.print("[bold green]AICtx status[/bold green]")
    console.print(f"repo: {repo_root}")
    console.print(f"branch: {inventory.branch}")
    console.print(f"head: {inventory.head_commit}")
    console.print(f"dirty: {inventory.dirty_state}")
    console.print(f"changed sources: {len(changed_paths)}")
    console.print(f"verify: {report.result}")
    if report.next_command:
        console.print(f"next: {report.next_command}")
    raise typer.Exit(code=0 if report.result == "PASS" else 1)


public_docs_app = typer.Typer(help="Manage public-facing documentation.")
app.add_typer(public_docs_app, name="public-docs")


@public_docs_app.command("update")
def public_docs_update(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
    scope: str = typer.Option("changed", "--scope", help="Update scope: changed or full."),
    write: str = typer.Option("patch", "--write", "-w", help="Write mode: patch or apply."),
) -> None:
    """Update public-facing documentation."""
    from aictx.public_docs.updater import update_public_docs

    if scope not in {"changed", "full"}:
        console.print(f"[bold red]Unsupported scope:[/bold red] {scope}")
        raise typer.Exit(code=1)
    if write not in {"patch", "apply"}:
        console.print(f"[bold red]Unsupported write mode:[/bold red] {write}")
        raise typer.Exit(code=1)

    repo_root = _resolve_repo_root(project)
    try:
        patch_path = update_public_docs(
            repo_root=repo_root,
            scope=scope,  # type: ignore[arg-type]
            write_mode=write,  # type: ignore[arg-type]
        )
    except Exception as exc:
        console.print(f"[bold red]public-docs update failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    if patch_path is None:
        console.print("[bold green]No public docs updates needed[/bold green]")
    else:
        console.print("[bold green]Public docs review generated[/bold green]")
        console.print(f"patch: {patch_path}")
        if write == "apply":
            console.print("review: docs/AIprojectcontext/public-docs-review.md")
    raise typer.Exit(code=0)


oci_app = typer.Typer(help="OCI readiness helpers.")
app.add_typer(oci_app, name="oci")


@oci_app.command("doctor")
def oci_doctor(
    profile: str = typer.Option("DEFAULT", "--profile", help="OCI profile name."),
    config_file: Annotated[
        Path | None, typer.Option("--config-file", help="OCI config path.")
    ] = None,
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON."),
) -> None:
    """Check local OCI readiness without network calls."""
    from aictx.oci.doctor import run_oci_doctor

    report = run_oci_doctor(profile=profile, config_file=config_file)
    if json_output:
        console.print_json(report.model_dump_json())
    else:
        console.print("[bold green]OCI doctor[/bold green]")
        console.print(f"sdk: {report.sdk_available}")
        console.print(f"config: {report.config_file_exists} ({report.config_file})")
        console.print(f"profile: {report.profile_exists} ({report.profile})")
        console.print(f"compartment: {report.compartment_id_present}")
        console.print(f"ready: {report.ready}")
        if report.missing:
            console.print("missing:")
            for item in report.missing:
                console.print(f"- {item}")
    raise typer.Exit(code=0 if report.ready else 1)


@app.command()
def clean(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
    oci: bool = typer.Option(False, "--oci", help="Clean OCI remote artifacts."),
    run_id: str | None = typer.Option(None, "--run-id", help="Specific run ID to clean."),
    keep_runs: int | None = typer.Option(None, "--keep-runs", help="Keep newest N local runs."),
    yes: bool = typer.Option(False, "--yes", help="Apply local cleanup."),
) -> None:
    """Clean generated or remote artifacts."""
    if oci:
        console.print("[bold red]OCI cleanup not implemented; local clean only.[/bold red]")
        raise typer.Exit(code=1)
    if keep_runs is not None and keep_runs < 0:
        console.print("[bold red]--keep-runs must be >= 0[/bold red]")
        raise typer.Exit(code=1)

    repo_root = _resolve_repo_root(project)
    runs_dir = repo_root / ".aictx" / "runs"
    if not runs_dir.exists():
        console.print("[bold green]No local runs to clean[/bold green]")
        raise typer.Exit(code=0)

    targets: list[Path] = []
    if run_id:
        target = runs_dir / run_id
        if not target.exists() or not target.is_dir():
            console.print(f"[bold red]Unknown run id:[/bold red] {run_id}")
            raise typer.Exit(code=1)
        targets = [target]
    elif keep_runs is not None:
        run_dirs = sorted([path for path in runs_dir.iterdir() if path.is_dir()])
        targets = run_dirs[: max(0, len(run_dirs) - keep_runs)]
    else:
        console.print("[bold red]clean requires --run-id or --keep-runs[/bold red]")
        raise typer.Exit(code=1)

    if not targets:
        console.print("[bold green]No local runs to clean[/bold green]")
        raise typer.Exit(code=0)

    if not yes:
        console.print("[bold yellow]Dry run[/bold yellow]")
        for target in targets:
            console.print(f"would remove: {target}")
        console.print("rerun with --yes to apply")
        raise typer.Exit(code=0)

    for target in targets:
        shutil.rmtree(target)
        console.print(f"removed: {target}")
    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
