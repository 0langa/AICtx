"""AICtx CLI entry point."""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, cast

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
        False, "--allow-dirty", help="Permit apply with dirty paths outside planned context files."
    ),
) -> None:
    """Run the aictx pipeline."""
    from aictx.config import load_config
    from aictx.context.pipeline import run_local_context_pipeline

    if mode != "setup-context":
        console.print(f"[bold red]Unsupported mode:[/bold red] {mode}")
        raise typer.Exit(code=1)
    if execution not in {"local", "oci-job"}:
        console.print(f"[bold red]Unsupported execution:[/bold red] {execution}")
        raise typer.Exit(code=1)
    if execution == "oci-job":
        _handle_oci_remote_run(project, mode, scope, write, provider, allow_ai, allow_dirty)
        return
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
        console.print_json(json.dumps(report.to_machine_dict(), indent=2, sort_keys=True))
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


snapshot_app = typer.Typer(help="Snapshot creation and verification.")
app.add_typer(snapshot_app, name="snapshot")


@snapshot_app.command("create")
def snapshot_create(
    project: Annotated[
        str, typer.Option("--project", "-p", help="Path to the target repository.")
    ] = ".",
    output_dir: Annotated[
        Path | None, typer.Option("--output", "-o", help="Output directory.")
    ] = None,
    skip_secret_scan: Annotated[
        bool, typer.Option("--skip-secret-scan", help="Skip secret scanning.")
    ] = False,
) -> None:
    """Create a deterministic, sanitised snapshot of the repository."""
    from aictx.oci.snapshot import create_snapshot
    from aictx.scan.scanner import scan_repository

    repo_root = _resolve_repo_root(project)
    dest = output_dir or (repo_root / ".aictx" / "snapshots")
    dest.mkdir(parents=True, exist_ok=True)
    inventory = scan_repository(repo_root)

    snapshot_path = create_snapshot(
        repo_root=repo_root,
        output_dir=dest,
        inventory=inventory,
        skip_secret_scan=skip_secret_scan,
    )
    console.print("[bold green]Snapshot created[/bold green]")
    console.print(f"path: {snapshot_path}")
    console.print(f"size: {snapshot_path.stat().st_size / 1024:.1f} KiB")
    raise typer.Exit(code=0)


@snapshot_app.command("verify")
def snapshot_verify(
    snapshot_path: Annotated[Path, typer.Argument(help="Path to snapshot zip.")],
) -> None:
    """Verify a snapshot's integrity and safety."""
    from aictx.oci.snapshot import verify_snapshot

    result = verify_snapshot(snapshot_path)
    if result.get("valid"):
        console.print("[bold green]Snapshot valid[/bold green]")
        console.print(f"files: {result.get('file_count', 0)}")
    else:
        console.print("[bold red]Snapshot invalid[/bold red]")
        errors = cast(list[str], result.get("errors", [result.get("error", "unknown")]))
        for err in errors:
            console.print(f"  - {err}")
        raise typer.Exit(code=1)
    raise typer.Exit(code=0)


oci_app = typer.Typer(help="OCI operations: readiness, upload, download, capabilities, cleanup.")
app.add_typer(oci_app, name="oci")


@oci_app.command("doctor")
def oci_doctor(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
    profile: str = typer.Option("DEFAULT", "--profile", help="OCI profile name."),
    config_file: Annotated[
        Path | None, typer.Option("--config-file", help="OCI config path.")
    ] = None,
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON."),
) -> None:
    """Check local OCI readiness without network calls."""
    from aictx.config import load_config
    from aictx.oci.doctor import run_oci_doctor

    repo_root = _resolve_repo_root(project)
    config = load_config(repo_root)

    report = run_oci_doctor(
        profile=profile,
        config_file=config_file,
        model_id=config.llm.model,
        compartment_id=config.llm.compartment_id,
        region=config.oci.region,
        bucket=config.oci.bucket,
    )
    if json_output:
        console.print_json(report.model_dump_json())
    else:
        console.print("[bold green]OCI doctor[/bold green]")
        console.print(f"sdk: {report.sdk_available}")
        console.print(f"config: {report.config_file_exists} ({report.config_file})")
        console.print(f"profile: {report.profile_exists} ({report.profile})")
        console.print(f"compartment: {report.compartment_id_present}")
        console.print(f"model: {report.model_id_present}")
        console.print(f"auth: {report.auth_ok}")
        console.print(f"region: {report.region_matches}")
        console.print(f"bucket: {report.bucket_access}")
        console.print(f"ready: {report.ready}")
        if report.missing:
            console.print("missing:")
            for item in report.missing:
                console.print(f"- {item}")
    raise typer.Exit(code=0 if report.ready else 1)


@oci_app.command("capabilities")
def oci_capabilities(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
    json_output: bool = typer.Option(False, "--json", help="Emit structured JSON."),
) -> None:
    """Validate OCI capability: object storage, bucket access, permissions."""
    from aictx.config import load_config
    from aictx.errors import RemoteJobError
    from aictx.oci.doctor import run_oci_doctor

    repo_root = _resolve_repo_root(project)
    config = load_config(repo_root)

    doctor = run_oci_doctor(
        profile=config.oci.profile,
        config_file=Path(config.oci.config_file),
        model_id=config.llm.model,
        compartment_id=config.oci.compartment_id or config.llm.compartment_id,
        region=config.oci.region,
        bucket=config.oci.bucket,
    )
    if not doctor.ready:
        console.print("[bold red]OCI not ready:[/bold red]")
        for item in doctor.missing:
            console.print(f"  - {item}")
        raise typer.Exit(code=1)

    caps: dict[str, bool | str] = {
        "object_storage": doctor.auth_ok,
        "bucket_access": doctor.bucket_access,
        "job_execution": False,
        "log_retrieval": doctor.bucket_access,
        "cleanup_permissions": doctor.bucket_access,
        "artifact_exchange": doctor.bucket_access,
    }

    # Test object storage access
    try:
        oci_sdk_config = config.oci.to_sdk_config()
        from aictx.oci.object_storage import _get_namespace, _get_object_client

        client = _get_object_client(oci_sdk_config)
        namespace = _get_namespace(client)
        caps["object_storage"] = True

        # Test bucket access
        try:
            client.head_bucket(namespace, config.oci.bucket)
            caps["bucket_access"] = True
        except Exception:
            caps["bucket_access"] = False

        caps["cleanup_permissions"] = caps["bucket_access"]
        caps["artifact_exchange"] = caps["bucket_access"]

        if config.oci.project_id:
            try:
                import oci

                ds_client = oci.data_science.DataScienceClient(oci_sdk_config)
                ds_client.get_project(config.oci.project_id)
                caps["job_execution"] = True
            except Exception:
                caps["job_execution"] = False
    except (RemoteJobError, Exception) as exc:
        caps["object_storage"] = False
        if json_output:
            caps["error"] = str(exc)

    if json_output:
        console.print_json(json.dumps(caps, indent=2, sort_keys=True))
    else:
        console.print("[bold green]OCI capabilities[/bold green]")
        for cap, ok in caps.items():
            if cap == "error":
                continue
            icon = "[green]✓[/green]" if ok else "[red]✗[/red]"
            console.print(f"  {icon} {cap}")
    raise typer.Exit(code=0 if all(bool(v) for k, v in caps.items() if k != "error") else 1)


@oci_app.command("upload-snapshot")
def oci_upload_snapshot(
    project: Annotated[
        str, typer.Option("--project", "-p", help="Path to the target repository.")
    ] = ".",
    run_id: Annotated[str | None, typer.Option("--run-id", help="Run ID for object path.")] = None,
    snapshot_path: Annotated[
        Path | None, typer.Option("--snapshot-path", help="Path to snapshot zip.")
    ] = None,
    max_retries: Annotated[int, typer.Option("--max-retries", help="Upload retry count.")] = 3,
) -> None:
    """Upload a snapshot zip to OCI Object Storage."""
    from aictx.config import load_config
    from aictx.oci.object_storage import upload_snapshot as _upload

    if run_id is None or snapshot_path is None:
        console.print("[bold red]--run-id and --snapshot-path are required[/bold red]")
        raise typer.Exit(code=1)

    repo_root = _resolve_repo_root(project)
    config = load_config(repo_root)

    oci_sdk_config = config.oci.to_sdk_config()
    object_name = _upload(
        oci_sdk_config, config.oci.bucket, snapshot_path, run_id, max_retries=max_retries
    )
    console.print("[bold green]Snapshot uploaded[/bold green]")
    console.print(f"object: {object_name}")
    console.print(f"bucket: {config.oci.bucket}")
    raise typer.Exit(code=0)


@oci_app.command("download-result")
def oci_download_result(
    project: Annotated[
        str, typer.Option("--project", "-p", help="Path to the target repository.")
    ] = ".",
    run_id: Annotated[
        str | None, typer.Option("--run-id", help="Run ID to download results for.")
    ] = None,
    dest: Annotated[Path, typer.Option("--dest", help="Destination directory.")] = Path("."),
    max_retries: Annotated[int, typer.Option("--max-retries", help="Download retry count.")] = 3,
) -> None:
    """Download a result bundle from OCI Object Storage."""
    from aictx.config import load_config
    from aictx.oci.bundle import unpack_result_bundle, verify_bundle
    from aictx.oci.object_storage import download_result as _download

    if run_id is None:
        console.print("[bold red]--run-id is required[/bold red]")
        raise typer.Exit(code=1)

    repo_root = _resolve_repo_root(project)
    config = load_config(repo_root)
    dest_dir = dest.resolve() if dest.exists() else repo_root / ".aictx" / "runs" / run_id

    oci_sdk_config = config.oci.to_sdk_config()
    result_path = _download(
        oci_sdk_config, config.oci.bucket, run_id, dest_dir, max_retries=max_retries
    )
    verify_result = verify_bundle(result_path)
    if not verify_result.get("valid"):
        console.print(
            f"[bold red]Bundle verification failed:[/bold red] {verify_result.get('errors')}"
        )
        raise typer.Exit(code=1)
    unpack_result_bundle(result_path, dest_dir)
    console.print("[bold green]Result downloaded[/bold green]")
    console.print(f"path: {result_path}")
    raise typer.Exit(code=0)


@oci_app.command("estimate")
def oci_estimate(
    project: Annotated[
        str, typer.Option("--project", "-p", help="Path to the target repository.")
    ] = ".",
    snapshot_path: Annotated[
        Path | None, typer.Option("--snapshot-path", help="Existing snapshot to estimate.")
    ] = None,
) -> None:
    """Estimate cost and resource usage for a remote OCI run."""
    from aictx.config import load_config
    from aictx.oci.runtime import RuntimeBudget, estimate_remote_cost

    repo_root = _resolve_repo_root(project)
    config = load_config(repo_root)

    budget = RuntimeBudget(
        max_runtime_minutes=config.oci.max_remote_runtime_minutes,
        max_snapshot_mb=config.oci.max_snapshot_size_mb,
        max_upload_retries=config.oci.max_upload_retries,
        max_download_retries=config.oci.max_download_retries,
    )

    estimate = estimate_remote_cost(snapshot_path=snapshot_path)
    console.print("[bold green]OCI cost estimate[/bold green]")
    console.print(estimate.format_summary())
    console.print(f"budget runtime: {budget.max_runtime_minutes} min")
    console.print(f"budget snapshot: {budget.max_snapshot_mb} MiB")

    if estimate.above_threshold:
        console.print("[yellow]Cost exceeds default threshold ($5.00)[/yellow]")
    raise typer.Exit(code=0)


@app.command()
def clean(
    project: str = typer.Option(".", "--project", "-p", help="Path to the target repository."),
    oci: bool = typer.Option(False, "--oci", help="Clean OCI remote artifacts."),
    run_id: str | None = typer.Option(None, "--run-id", help="Specific run ID to clean."),
    keep_runs: int | None = typer.Option(None, "--keep-runs", help="Keep newest N local runs."),
    yes: bool = typer.Option(False, "--yes", help="Apply local cleanup."),
    max_age_days: int = typer.Option(7, "--max-age-days", help="Remote artifact max age in days."),
) -> None:
    """Clean generated or remote artifacts."""
    if oci:
        _handle_oci_cleanup(project, run_id, yes=yes, max_age_days=max_age_days)
        return
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


def _handle_oci_remote_run(
    project: str,
    mode: str,
    scope: str,
    write: str,
    provider: str | None,
    allow_ai: bool,
    allow_dirty: bool,
) -> None:
    """Execute the pipeline remotely via OCI Data Science Jobs."""
    from datetime import UTC, datetime

    from aictx.config import load_config
    from aictx.oci.object_storage import upload_snapshot as _upload
    from aictx.oci.remote_job import submit_job, wait_for_job
    from aictx.oci.runtime import RuntimeBudget, estimate_remote_cost, require_runtime_confirmation
    from aictx.oci.snapshot import create_snapshot
    from aictx.scan.scanner import scan_repository

    if (
        mode != "setup-context"
        or scope not in {"full", "changed"}
        or write not in {"patch", "apply"}
    ):
        console.print(
            "[bold red]Remote OCI run only supports setup-context with full/changed and patch/apply options[/bold red]"
        )
        raise typer.Exit(code=1)
    if write != "patch":
        console.print("[bold red]Remote OCI execution requires --write patch[/bold red]")
        raise typer.Exit(code=1)

    repo_root = _resolve_repo_root(project)
    config = load_config(repo_root)
    run_id = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ-oci-run")

    if not config.oci.enabled:
        console.print(
            "[bold red]OCI is not enabled. Set [oci] enabled = true in .aictx/config.toml[/bold red]"
        )
        raise typer.Exit(code=1)

    # Validate OCI config
    errors = config.oci.validate_settings() + config.oci.validate_runtime_access()
    if errors:
        for err in errors:
            console.print(f"[bold red]OCI config error:[/bold red] {err}")
        raise typer.Exit(code=1)

    console.print("[bold]Creating repository snapshot...[/bold]")
    inventory = scan_repository(repo_root)
    snapshot_dir = repo_root / ".aictx" / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = create_snapshot(repo_root, snapshot_dir, inventory=inventory)

    # Estimate cost
    budget = RuntimeBudget(
        max_runtime_minutes=config.oci.max_remote_runtime_minutes,
        max_snapshot_mb=config.oci.max_snapshot_size_mb,
        max_upload_retries=config.oci.max_upload_retries,
        max_download_retries=config.oci.max_download_retries,
    )
    estimate = estimate_remote_cost(
        snapshot_path=snapshot_path,
        input_tokens=inventory.files
        and sum(f.size_bytes for f in inventory.files if not f.is_ignored) // 4
        or 0,
        runtime_minutes=config.oci.max_remote_runtime_minutes,
    )
    console.print("[bold]Cost estimate:[/bold]")
    console.print(estimate.format_summary())
    try:
        require_runtime_confirmation(estimate, budget)
    except Exception as exc:
        console.print(f"[bold red]OCI runtime budget failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    # Upload snapshot
    console.print("[bold]Uploading snapshot...[/bold]")
    oci_sdk_config = config.oci.to_sdk_config()
    snapshot_object = _upload(
        oci_sdk_config,
        config.oci.bucket,
        snapshot_path,
        run_id,
        max_retries=config.oci.max_upload_retries,
    )
    console.print(f"[green]Snapshot uploaded: {snapshot_object}[/green]")

    # Submit job
    console.print("[bold]Submitting remote job...[/bold]")
    if not config.oci.project_id:
        console.print("[bold red]oci.project_id is required for remote execution[/bold red]")
        raise typer.Exit(code=1)

    job_id = submit_job(
        config=oci_sdk_config,
        compartment_id=config.oci.resolve_compartment_id(),
        project_id=config.oci.project_id,
        run_id=run_id,
        snapshot_object=snapshot_object,
        bucket=config.oci.bucket,
        subnet_id=config.oci.subnet_id or None,
        log_group_id=config.oci.log_group_id or None,
        job_timeout_minutes=config.oci.max_remote_runtime_minutes,
    )
    console.print(f"[green]Job submitted: {job_id}[/green]")

    # Wait for completion
    console.print("[bold]Waiting for job completion...[/bold]")
    try:
        result = wait_for_job(
            oci_sdk_config,
            job_id,
            timeout_minutes=config.oci.max_remote_runtime_minutes,
        )
    except Exception as exc:
        console.print(f"[bold red]Remote job failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    console.print(f"[bold green]Job completed: {result.status}[/bold green]")

    # Download result
    console.print("[bold]Downloading result bundle...[/bold]")
    dest_dir = repo_root / ".aictx" / "runs" / run_id
    from aictx.oci.object_storage import download_result as _download

    result_path = _download(
        oci_sdk_config,
        config.oci.bucket,
        run_id,
        dest_dir,
        max_retries=config.oci.max_download_retries,
    )

    # Unpack bundle
    from aictx.oci.bundle import unpack_result_bundle, verify_bundle

    verify_bundle_result = verify_bundle(result_path)
    if not verify_bundle_result.get("valid"):
        console.print(
            f"[bold red]Bundle verification failed: {verify_bundle_result.get('errors')}[/bold red]"
        )
        raise typer.Exit(code=1)

    extracted = unpack_result_bundle(result_path, dest_dir)
    console.print("[bold green]Remote run complete[/bold green]")
    console.print(f"run id: {run_id}")
    console.print(f"job id: {job_id}")
    if "patch" in extracted:
        console.print(f"patch: {extracted['patch']}")
    if "validation_report" in extracted:
        console.print(f"validation report: {extracted['validation_report']}")
    if "generated" in extracted:
        console.print(f"generated: {extracted['generated']}")
    raise typer.Exit(code=0)


def _handle_oci_cleanup(project: str, run_id: str | None, yes: bool, max_age_days: int) -> None:
    """Handle the OCI artifact cleanup workflow."""
    from aictx.config import load_config
    from aictx.oci.cleanup import cleanup_run, cleanup_stale, list_stale_objects

    repo_root = _resolve_repo_root(project)
    config = load_config(repo_root)
    oci_sdk_config = config.oci.to_sdk_config()

    if run_id:
        result = cleanup_run(oci_sdk_config, config.oci.bucket, run_id, dry_run=not yes)
        console.print("[bold green]OCI cleanup complete[/bold green]")
        console.print(f"run: {result['run_id']}")
        console.print(f"deleted: {result['deleted_count']} objects")
    else:
        if not yes:
            stale = list_stale_objects(oci_sdk_config, config.oci.bucket, max_age_days=max_age_days)
            console.print("[bold yellow]OCI cleanup dry run[/bold yellow]")
            for item in stale[:20]:
                console.print(f"would delete: {item['name']} ({item['size']} bytes)")
            console.print("rerun with --yes to apply")
            raise typer.Exit(code=0)
        result = cleanup_stale(
            oci_sdk_config, config.oci.bucket, max_age_days=max_age_days, dry_run=False
        )
        console.print("[bold green]OCI stale cleanup complete[/bold green]")
        console.print(f"deleted: {result['deleted_count']} objects")
        console.print(f"bytes: {result['total_bytes']}")
    raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
