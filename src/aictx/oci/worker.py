"""OCI worker runtime — runs the exact same local pipeline remotely.

This module is executed on OCI Data Science Jobs and MUST NOT contain any
OCI-only generation logic.  It downloads the snapshot, unpacks, runs the
pipeline, creates a result bundle, and uploads it.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path

from aictx.config import load_config
from aictx.context.pipeline import run_local_context_pipeline
from aictx.errors import RemoteJobError
from aictx.oci.bundle import create_result_bundle
from aictx.oci.object_storage import download_result, upload_result
from aictx.oci.runtime import RuntimeBudget
from aictx.oci.snapshot import verify_snapshot

logger = logging.getLogger("aictx.oci.worker")


def run_remote_pipeline(
    config: dict[str, object],
    run_id: str,
    snapshot_object: str | None = None,
    bucket: str | None = None,
    budget: RuntimeBudget | None = None,
) -> dict[str, object]:
    """Execute the aictx pipeline in a remote OCI context.

    Flow:
        1. If snapshot_object is provided, download and verify snapshot.
        2. Otherwise create snapshot from local checkout.
        3. Run the standard local pipeline.
        4. Create result bundle.
        5. Upload result bundle to OCI bucket.
    """
    work_dir = Path(tempfile.mkdtemp(prefix=f"aictx-worker-{run_id}-"))
    repo_root = work_dir / "repo"

    logger.info("worker start run_id=%s work_dir=%s", run_id, work_dir)

    if snapshot_object and bucket:
        oci_sdk_config = _load_oci_sdk_config(config)
        snapshot_path = download_result(
            oci_sdk_config,
            bucket,
            run_id,
            work_dir,
            object_name=snapshot_object,
        )

        # Verify snapshot integrity
        verify_result = verify_snapshot(snapshot_path)
        if not verify_result.get("valid"):
            raise RemoteJobError(f"Snapshot verification failed: {verify_result.get('errors')}")

        logger.info("snapshot verified files=%d", verify_result.get("file_count", 0))
        _extract_snapshot(snapshot_path, repo_root)
    else:
        raise RemoteJobError("snapshot_object and bucket are required for remote worker execution")

    # Run the standard local pipeline
    report = run_local_context_pipeline(
        repo_root=repo_root,
        run_id=run_id,
        config=load_config(repo_root),
        scope="full",
        write_mode="patch",
        allow_ai=True,
    )

    # Create result bundle
    runs_dir = repo_root / ".aictx" / "runs" / run_id
    out_dir = runs_dir / "out"
    logs_dir = runs_dir / "logs" if (runs_dir / "logs").exists() else None
    patch_path = runs_dir / "aictx.patch"

    validation_report: str | None = None
    vr_path = repo_root / "docs" / "AIprojectcontext" / "validation-report.md"
    if vr_path.exists():
        validation_report = vr_path.read_text(encoding="utf-8")

    bundle_path = create_result_bundle(
        output_dir=runs_dir,
        patch_path=patch_path if patch_path.exists() else None,
        validation_report=validation_report,
        run_report=report.model_dump(mode="json") if hasattr(report, "model_dump") else None,
        generated_dir=out_dir if out_dir.exists() else None,
        logs_dir=logs_dir,
    )

    # Upload result bundle
    if bucket:
        oci_sdk_config = _load_oci_sdk_config(config)
        upload_result(oci_sdk_config, bucket, bundle_path, run_id)

    result = {
        "run_id": run_id,
        "status": report.status if hasattr(report, "status") else "unknown",
        "bundle_path": str(bundle_path),
        "files_scanned": report.files_scanned if hasattr(report, "files_scanned") else 0,
        "files_selected": report.files_selected if hasattr(report, "files_selected") else 0,
    }
    shutil.rmtree(work_dir, ignore_errors=True)
    return result


def _load_oci_sdk_config(config: dict[str, object]) -> dict[str, object]:
    """Load OCI SDK config dict from environment or config."""
    import oci

    config_file = os.getenv("OCI_CONFIG_FILE", str(Path.home() / ".oci" / "config"))
    profile = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
    return dict(oci.config.from_file(config_file, profile))


def _extract_snapshot(snapshot_path: Path, repo_root: Path) -> None:
    repo_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(snapshot_path, "r") as zf:
        for name in zf.namelist():
            if not name.startswith("repo/"):
                continue
            relative = Path(name).relative_to("repo")
            target = repo_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(name))
