"""OCI Object Storage exchange — upload/download artifacts with retry, checksum, and bounds."""

from __future__ import annotations

import base64
import hashlib
import importlib.util
import logging
import time
from pathlib import Path
from typing import Any

from aictx.errors import RemoteJobError

logger = logging.getLogger("aictx.oci.object_storage")

_MAX_RETRIES_DEFAULT = 3
_RETRY_BACKOFF_SEC = 2.0
_MULTIPART_THRESHOLD_BYTES = 100 * 1024 * 1024  # 100 MiB
_PART_SIZE_BYTES = 10 * 1024 * 1024  # 10 MiB


def _require_oci() -> Any:
    """Lazy OCI SDK import; raise if absent."""
    if importlib.util.find_spec("oci") is None:
        raise RemoteJobError("OCI SDK not installed. Install with: pip install 'aictx[oci]'")
    import oci

    return oci


def _get_object_client(config: dict[str, Any]) -> Any:
    """Create an OCI Object Storage client from SDK config dict."""
    oci = _require_oci()
    return oci.object_storage.ObjectStorageClient(config)


def _checksum_file(path: Path) -> str:
    """Return hex-encoded SHA-256 of *path* for OCI metadata."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _make_object_path(run_id: str, kind: str, filename: str) -> str:
    """Build standardised OCI object name under aictx-runs/<run_id>/<kind>/."""
    return f"aictx-runs/{run_id}/{kind}/{filename}"


def _retry_upload(
    client: Any, namespace: str, bucket: str, object_name: str, file_path: Path, max_retries: int
) -> str:
    """Upload *file_path* with retries and return the OCI object OCID."""
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            with file_path.open("rb") as fh:
                client.put_object(
                    namespace,
                    bucket,
                    object_name,
                    fh,
                    opc_meta={"sha256": _checksum_file(file_path)},
                )
            logger.info(
                "upload success attempt=%d/%d object=%s size=%d",
                attempt,
                max_retries,
                object_name,
                file_path.stat().st_size,
            )
            return object_name
        except Exception as exc:
            last_exc = exc
            logger.warning("upload attempt %d/%d failed: %s", attempt, max_retries, exc)
            if attempt < max_retries:
                time.sleep(_RETRY_BACKOFF_SEC * attempt)
    raise RemoteJobError(f"Upload failed after {max_retries} retries: {last_exc}")


def _retry_download(
    client: Any, namespace: str, bucket: str, object_name: str, dest: Path, max_retries: int
) -> None:
    """Download *object_name* to *dest* with retries and checksum validation."""
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.get_object(namespace, bucket, object_name)
            data = response.data.content
            dest.write_bytes(data)
            # Optional checksum verification from metadata
            expected_sha = response.headers.get("opc-meta-sha256", "")
            if expected_sha:
                actual = hashlib.sha256(data).hexdigest()
                # Normalise base64-encoded metadata to hex for comparison
                try:
                    expected_hex = base64.b64decode(expected_sha).hex()
                except Exception:
                    expected_hex = expected_sha
                if actual != expected_hex:
                    raise RemoteJobError(
                        f"Checksum mismatch for {object_name}: expected {expected_hex}, got {actual}"
                    )
            logger.info(
                "download success attempt=%d/%d object=%s size=%d",
                attempt,
                max_retries,
                object_name,
                len(data),
            )
            return
        except Exception as exc:
            last_exc = exc
            logger.warning("download attempt %d/%d failed: %s", attempt, max_retries, exc)
            if attempt < max_retries:
                time.sleep(_RETRY_BACKOFF_SEC * attempt)
    raise RemoteJobError(f"Download failed after {max_retries} retries: {last_exc}")


def upload_snapshot(
    config: dict[str, Any],
    bucket: str,
    snapshot_path: Path,
    run_id: str,
    max_retries: int = _MAX_RETRIES_DEFAULT,
) -> str:
    """Upload a snapshot zip to OCI Object Storage.

    Returns the OCI object name for the uploaded snapshot.
    """
    if not snapshot_path.is_file():
        raise RemoteJobError(f"Snapshot path is not a file: {snapshot_path}")

    client = _get_object_client(config)
    namespace = _get_namespace(client)
    object_name = _make_object_path(run_id, "input", snapshot_path.name)

    # Multipart upload for large files
    size = snapshot_path.stat().st_size
    if size > _MULTIPART_THRESHOLD_BYTES:
        _multipart_upload(client, namespace, bucket, object_name, snapshot_path, max_retries)
    else:
        _retry_upload(client, namespace, bucket, object_name, snapshot_path, max_retries)

    logger.info("snapshot uploaded bucket=%s run=%s object=%s", bucket, run_id, object_name)
    return object_name


def download_result(
    config: dict[str, Any],
    bucket: str,
    run_id: str,
    dest: Path,
    object_name: str | None = None,
    max_retries: int = _MAX_RETRIES_DEFAULT,
) -> Path:
    """Download the result bundle from OCI for *run_id* into *dest* directory.

    Returns the path to the downloaded result zip.
    """
    resolved_object_name = object_name or _make_object_path(run_id, "output", "aictx-result.zip")
    dest_path = dest / Path(resolved_object_name).name

    client = _get_object_client(config)
    namespace = _get_namespace(client)
    _retry_download(client, namespace, bucket, resolved_object_name, dest_path, max_retries)

    logger.info(
        "result downloaded run=%s object=%s dest=%s", run_id, resolved_object_name, dest_path
    )
    return dest_path


def upload_result(
    config: dict[str, Any],
    bucket: str,
    result_path: Path,
    run_id: str,
    max_retries: int = _MAX_RETRIES_DEFAULT,
) -> str:
    """Upload a result bundle zip to OCI Object Storage.

    Returns the OCI object name for the uploaded result.
    """
    if not result_path.is_file():
        raise RemoteJobError(f"Result path is not a file: {result_path}")

    client = _get_object_client(config)
    namespace = _get_namespace(client)
    object_name = _make_object_path(run_id, "output", result_path.name)

    size = result_path.stat().st_size
    if size > _MULTIPART_THRESHOLD_BYTES:
        _multipart_upload(client, namespace, bucket, object_name, result_path, max_retries)
    else:
        _retry_upload(client, namespace, bucket, object_name, result_path, max_retries)

    logger.info("result uploaded bucket=%s run=%s object=%s", bucket, run_id, object_name)
    return object_name


def upload_logs(
    config: dict[str, Any],
    bucket: str,
    log_path: Path,
    run_id: str,
    max_retries: int = _MAX_RETRIES_DEFAULT,
) -> str:
    """Upload a log archive to OCI Object Storage."""
    client = _get_object_client(config)
    namespace = _get_namespace(client)
    object_name = _make_object_path(run_id, "logs", log_path.name)
    _retry_upload(client, namespace, bucket, object_name, log_path, max_retries)
    return object_name


def list_run_objects(
    config: dict[str, Any],
    bucket: str,
    run_id: str,
) -> list[dict[str, Any]]:
    """List all OCI objects for *run_id* in *bucket*."""
    client = _get_object_client(config)
    namespace = _get_namespace(client)
    prefix = f"aictx-runs/{run_id}/"
    try:
        response = client.list_objects(namespace, bucket, prefix=prefix)
        objects = response.data.objects
        return [
            {
                "name": obj.name,
                "size": obj.size,
                "md5": obj.md5,
                "time_modified": str(obj.time_modified),
            }
            for obj in (objects or [])
        ]
    except Exception as exc:
        raise RemoteJobError(f"Failed to list objects for run {run_id}: {exc}") from exc


def delete_run_objects(
    config: dict[str, Any],
    bucket: str,
    run_id: str,
    dry_run: bool = False,
) -> list[str]:
    """Delete all OCI objects under aictx-runs/<run_id>/.

    Returns list of deleted object names.  In dry_run mode, only lists them.
    """
    objects = list_run_objects(config, bucket, run_id)
    if not objects:
        return []

    deleted: list[str] = []
    client = _get_object_client(config)
    namespace = _get_namespace(client)
    for obj in objects:
        name: str = obj["name"]
        if dry_run:
            deleted.append(name)
        else:
            try:
                client.delete_object(namespace, bucket, name)
                deleted.append(name)
                logger.info("deleted object: %s", name)
            except Exception as exc:
                logger.warning("failed to delete %s: %s", name, exc)
    return deleted


def _get_namespace(client: Any) -> str:
    """Retrieve the tenancy object storage namespace."""
    try:
        response = client.get_namespace()
        return str(response.data)
    except Exception as exc:
        raise RemoteJobError(f"Failed to get OCI namespace: {exc}") from exc


def _multipart_upload(
    client: Any,
    namespace: str,
    bucket: str,
    object_name: str,
    file_path: Path,
    max_retries: int,
) -> str:
    """Upload a large file using OCI multipart upload."""
    _require_oci()
    try:
        upload_id = _create_multipart_upload(client, namespace, bucket, object_name)
        parts: list[dict[str, Any]] = []
        part_number = 1
        with file_path.open("rb") as fh:
            while True:
                chunk = fh.read(_PART_SIZE_BYTES)
                if not chunk:
                    break
                part = _upload_part(
                    client,
                    namespace,
                    bucket,
                    object_name,
                    upload_id,
                    part_number,
                    chunk,
                    max_retries,
                )
                parts.append(part)
                part_number += 1
        _commit_multipart_upload(client, namespace, bucket, object_name, upload_id, parts)
        logger.info(
            "multipart upload complete parts=%d size=%d", part_number - 1, file_path.stat().st_size
        )
        return object_name
    except Exception as exc:
        logger.error("multipart upload failed: %s", exc)
        raise RemoteJobError(f"Multipart upload failed: {exc}") from exc


def _create_multipart_upload(client: Any, namespace: str, bucket: str, object_name: str) -> str:
    response = client.create_multipart_upload(
        namespace,
        bucket,
        _require_oci().object_storage.models.CreateMultipartUploadDetails(
            object=object_name,
            opc_meta={"sha256": _checksum_file(Path(object_name))} if False else None,
        ),
    )
    return str(response.data.upload_id)


def _upload_part(
    client: Any,
    namespace: str,
    bucket: str,
    object_name: str,
    upload_id: str,
    part_number: int,
    data: bytes,
    max_retries: int,
) -> dict[str, Any]:
    last_exc: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.upload_part(
                namespace,
                bucket,
                object_name,
                upload_id,
                part_number,
                data,
            )
            etag = response.headers.get("etag", "")
            return {"part_num": part_number, "etag": etag}
        except Exception as exc:
            last_exc = exc
            if attempt < max_retries:
                time.sleep(_RETRY_BACKOFF_SEC * attempt)
    raise RemoteJobError(
        f"Part {part_number} upload failed after {max_retries} retries: {last_exc}"
    )


def _commit_multipart_upload(
    client: Any,
    namespace: str,
    bucket: str,
    object_name: str,
    upload_id: str,
    parts: list[dict[str, Any]],
) -> None:
    oci = _require_oci()
    client.commit_multipart_upload(
        namespace,
        bucket,
        object_name,
        upload_id,
        oci.object_storage.models.CommitMultipartUploadDetails(
            parts_to_commit=parts,
        ),
    )
