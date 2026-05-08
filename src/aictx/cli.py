"""AICtx CLI entry point."""

from __future__ import annotations

from datetime import UTC

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
    console.print(f"[bold green]init[/bold green] not yet implemented (project={project})")


@app.command()
def scan(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
) -> None:
    """Scan a repository and print/write an inventory."""
    from datetime import datetime
    from pathlib import Path

    from aictx.errors import AictxError
    from aictx.git.repo import find_git_root
    from aictx.scan.scanner import scan_repository

    project_path = Path(project).resolve()
    if not project_path.exists():
        raise typer.BadParameter(f"Project path does not exist: {project}")

    try:
        repo_root = find_git_root(project_path)
    except AictxError as exc:
        console.print(f"[bold red]Error:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

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
    write: str = typer.Option("patch", "--write", "-w", help="Write mode: patch or apply."),
) -> None:
    """Run the aictx pipeline."""
    console.print(
        f"[bold green]run[/bold green] not yet implemented "
        f"(project={project}, mode={mode}, execution={execution}, write={write})"
    )


@app.command()
def verify(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
    strict: bool = typer.Option(False, "--strict", help="Enable strict verification."),
) -> None:
    """Verify generated AI context freshness."""
    console.print(
        f"[bold green]verify[/bold green] not yet implemented (project={project}, strict={strict})"
    )


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
