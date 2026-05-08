"""AICtx CLI entry point."""

from __future__ import annotations

import typer
from rich.console import Console

from aictx import __version__

app = typer.Typer(
    name="aictx",
    help="Prepare Git repositories for low-token AI-agent work.",
    no_args_is_help=True,
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
    console.print(f"[bold green]scan[/bold green] not yet implemented (project={project})")


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
