"""AICtx CLI entry point."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

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
    from aictx.context.lockfile import build_lockfile_from_inventory, write_lockfile
    from aictx.scan.scanner import scan_repository

    repo_root = _resolve_repo_root(project)

    inventory = scan_repository(repo_root)
    context_dir = repo_root / "docs" / "AIprojectcontext"
    context_dir.mkdir(parents=True, exist_ok=True)
    write_lockfile(context_dir, build_lockfile_from_inventory(inventory))

    ignore_path = repo_root / ".aictxignore"
    if not ignore_path.exists():
        ignore_path.write_text("# AICtx custom ignore patterns\n", encoding="utf-8")

    tracked_files = len(build_lockfile_from_inventory(inventory).source_files)
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

    repo_root = _resolve_repo_root(project)
    config = load_config(repo_root)
    run_id = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ-run")

    try:
        report = run_local_context_pipeline(
            repo_root=repo_root,
            run_id=run_id,
            config=config,
            scope=scope,  # type: ignore[arg-type]
            write_mode=write,  # type: ignore[arg-type]
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
) -> None:
    """Verify generated AI context freshness."""
    from aictx.verify.verifier import verify as run_verify

    repo_root = _resolve_repo_root(project)

    result = run_verify(repo_root, strict=strict)
    if result == "PASS":
        console.print("[bold green]PASS[/bold green]")
        raise typer.Exit(code=0)

    console.print(f"[bold red]{result}[/bold red]")
    raise typer.Exit(code=1)


public_docs_app = typer.Typer(help="Manage public-facing documentation.")
app.add_typer(public_docs_app, name="public-docs")


@public_docs_app.command("update")
def public_docs_update(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
    scope: str = typer.Option("changed", "--scope", help="Update scope: changed or full."),
    write: str = typer.Option("patch", "--write", "-w", help="Write mode: patch or apply."),
) -> None:
    """Update public-facing documentation."""
    console.print(
        f"[bold yellow]public-docs update[/bold yellow] not yet implemented "
        f"(project={project}, scope={scope}, write={write})"
    )
    raise typer.Exit(code=1)


@app.command()
def clean(
    oci: bool = typer.Option(False, "--oci", help="Clean OCI remote artifacts."),
    run_id: str | None = typer.Option(None, "--run-id", help="Specific run ID to clean."),
) -> None:
    """Clean generated or remote artifacts."""
    console.print(
        f"[bold green]clean[/bold green] not yet implemented (oci={oci}, run_id={run_id})"
    )


if __name__ == "__main__":
    app()
