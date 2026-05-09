"""OCI remote worker job management — Data Science Job submission, polling, and cancellation."""

from __future__ import annotations

import importlib.util
import logging
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aictx.errors import RemoteJobError

logger = logging.getLogger("aictx.oci.remote_job")

_POLL_INTERVAL_SEC = 15
_TERMINAL_STATES = {"SUCCEEDED", "FAILED", "CANCELED"}

JobStatus = str  # "ACCEPTED" | "IN_PROGRESS" | "SUCCEEDED" | "FAILED" | "CANCELED"


@dataclass
class JobResult:
    """Result of a completed remote job."""

    job_id: str
    run_id: str
    status: JobStatus
    lifecycle_state: str
    started_at: str | None = None
    finished_at: str | None = None
    stdout_url: str | None = None
    stderr_url: str | None = None
    log_paths: list[str] = field(default_factory=list)
    result_bundle_path: str | None = None
    error_message: str | None = None


def _require_oci() -> Any:
    if importlib.util.find_spec("oci") is None:
        raise RemoteJobError("OCI SDK not installed. Install with: pip install 'aictx[oci]'")
    import oci

    return oci


def _get_ds_client(config: dict[str, Any]) -> Any:
    """Create OCI Data Science client from config dict."""
    oci = _require_oci()
    return oci.data_science.DataScienceClient(config)


def submit_job(
    config: dict[str, Any],
    compartment_id: str,
    project_id: str,
    run_id: str,
    snapshot_object: str,
    bucket: str,
    subnet_id: str | None = None,
    log_group_id: str | None = None,
    shape: str = "VM.Standard.E4.Flex",
    ocpus: float = 4,
    memory_gbs: float = 16,
    job_timeout_minutes: int = 45,
) -> str:
    """Submit an OCI Data Science job that runs the aictx worker.

    Returns the job OCID.
    """
    oci = _require_oci()
    ds = _get_ds_client(config)
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H%M%SZ")

    job_name = f"aictx-run-{run_id}-{now}"

    job_details = oci.data_science.models.CreateJobDetails(
        project_id=project_id,
        compartment_id=compartment_id,
        display_name=job_name,
        job_infrastructure_configuration_details=oci.data_science.models.JobInfrastructureConfigurationDetails(
            job_infrastructure_type="ME_STANDALONE",
            shape_name=shape,
            subnet_id=subnet_id or "",
            block_storage_size_gbs=50,
        ),
        job_configuration_details=oci.data_science.models.JobConfigurationDetails(
            job_infrastructure_type="ME_STANDALONE",
            environment_variables={
                "AICTX_RUN_ID": run_id,
                "AICTX_SNAPSHOT_OBJECT": snapshot_object,
                "AICTX_BUCKET": bucket,
                "OCI_COMPARTMENT_ID": compartment_id,
                "PYTHONUNBUFFERED": "1",
            },
            command_line_arguments=(
                f"--run-id {run_id} --snapshot-object {snapshot_object} --bucket {bucket}"
            ),
            maximum_runtime_in_minutes=job_timeout_minutes,
        ),
        log_id=log_group_id or "",
    )

    try:
        response = ds.create_job(job_details)
        job_id = response.data.id
        logger.info("job submitted run=%s job_id=%s shape=%s", run_id, job_id, shape)
        return str(job_id)
    except (
        oci.exceptions.ServiceError,
        oci.exceptions.ClientError,
    ) as exc:
        raise RemoteJobError(f"Job submission failed: {exc}") from exc


def get_job_status(ds: Any, job_id: str) -> JobResult:
    """Fetch current job status."""
    try:
        response = ds.get_job(job_id)
        job = response.data
        lifecycle = job.lifecycle_state or "UNKNOWN"
        status = "ACCEPTED"
        if lifecycle == "SUCCEEDED":
            status = "SUCCEEDED"
        elif lifecycle == "FAILED":
            status = "FAILED"
        elif lifecycle == "CANCELED":
            status = "CANCELED"
        elif lifecycle in ("IN_PROGRESS", "ACTIVE"):
            status = "IN_PROGRESS"
        return JobResult(
            job_id=job_id,
            run_id="",
            status=status,
            lifecycle_state=lifecycle,
            started_at=str(job.time_created) if hasattr(job, "time_created") else None,
            finished_at=str(job.time_updated) if hasattr(job, "time_updated") else None,
        )
    except Exception as exc:
        raise RemoteJobError(f"Failed to get job status for {job_id}: {exc}") from exc


def wait_for_job(
    config: dict[str, Any],
    job_id: str,
    timeout_minutes: int = 45,
    poll_interval: int = _POLL_INTERVAL_SEC,
) -> JobResult:
    """Poll *job_id* until completion or timeout.

    Raises RemoteJobError on timeout or failure.
    """
    ds = _get_ds_client(config)
    deadline = time.monotonic() + timeout_minutes * 60

    while time.monotonic() < deadline:
        result = get_job_status(ds, job_id)
        logger.debug("job poll job_id=%s state=%s", job_id, result.lifecycle_state)
        if result.status in _TERMINAL_STATES:
            if result.status == "FAILED":
                raise RemoteJobError(f"Job {job_id} failed. lifecycle={result.lifecycle_state}")
            if result.status == "CANCELED":
                raise RemoteJobError(f"Job {job_id} was canceled.")
            logger.info("job completed job_id=%s status=%s", job_id, result.status)
            return result
        time.sleep(poll_interval)

    raise RemoteJobError(f"Job {job_id} did not complete within {timeout_minutes} minutes")


def cancel_job(config: dict[str, Any], job_id: str) -> None:
    """Cancel an active OCI Data Science job."""
    ds = _get_ds_client(config)
    try:
        ds.cancel_job(job_id)
        logger.info("job canceled job_id=%s", job_id)
    except Exception as exc:
        raise RemoteJobError(f"Failed to cancel job {job_id}: {exc}") from exc


def fetch_job_logs(
    config: dict[str, Any],
    job_id: str,
    dest: Path,
) -> list[Path]:
    """Fetch stdout/stderr logs for a completed job into *dest*.

    Returns list of saved log file paths.
    """
    # OCI Data Science stores logs in object storage under job-specific prefix.
    # This is a best-effort retrieval.
    oci = _require_oci()
    ds = _get_ds_client(config)
    saved: list[Path] = []

    try:
        response = ds.get_job(job_id)
        job = response.data
        log_id = getattr(job, "log_id", None)
        if log_id:
            # Download via Object Storage using the log OCID prefix
            obj_client = oci.object_storage.ObjectStorageClient(config)
            namespace = obj_client.get_namespace().data
            # Attempt common log patterns
            for log_kind in ["stdout", "stderr"]:
                for attempt_name in [
                    f"jobs/{job_id}/{log_kind}.txt",
                    f"jobs/{job_id}/{log_kind}",
                    f"job-logs/{job_id}/{log_kind}.txt",
                ]:
                    try:
                        obj_response = obj_client.get_object(namespace, "aictx-logs", attempt_name)
                        log_path = dest / f"{log_kind}.txt"
                        log_path.write_bytes(obj_response.data.content)
                        saved.append(log_path)
                        logger.info("log retrieved kind=%s path=%s", log_kind, attempt_name)
                        break
                    except Exception:
                        continue
    except Exception as exc:
        logger.warning("log fetch non-fatal error: %s", exc)

    return saved
