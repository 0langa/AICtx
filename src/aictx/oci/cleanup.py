"""OCI artifact cleanup — stale snapshot, bundle, and log removal."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from aictx.errors import RemoteJobError

logger = logging.getLogger("aictx.oci.cleanup")


def list_stale_objects(
    oci_config: dict[str, Any],
    bucket: str,
    max_age_days: int = 7,
) -> list[dict[str, object]]:
    """Return OCI objects older than max_age_days."""
    from aictx.oci.object_storage import _get_namespace, _get_object_client

    client = _get_object_client(oci_config)
    namespace = _get_namespace(client)
    cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
    response = client.list_objects(
        namespace, bucket, prefix="aictx-runs/", fields="timeModified,size"
    )
    objects = response.data.objects or []
    stale: list[dict[str, object]] = []
    for obj in objects:
        if obj.time_modified and obj.time_modified < cutoff:
            stale.append(
                {
                    "name": obj.name,
                    "size": obj.size or 0,
                    "time_modified": str(obj.time_modified),
                }
            )
    return stale


def cleanup_run(
    oci_config: dict[str, Any],
    bucket: str,
    run_id: str,
    dry_run: bool = False,
) -> dict[str, object]:
    """Delete all OCI objects associated with *run_id*.

    Returns stats summary dict.
    """
    from aictx.oci.object_storage import delete_run_objects, list_run_objects

    objects = list_run_objects(oci_config, bucket, run_id)
    if not objects:
        logger.info("no objects found for run %s", run_id)
        return {"run_id": run_id, "deleted_count": 0, "dry_run": dry_run}

    deleted = delete_run_objects(oci_config, bucket, run_id, dry_run=dry_run)
    total_bytes = sum(obj.get("size", 0) for obj in objects)

    logger.info(
        "cleanup %s run=%s objects=%d bytes=%d",
        "dry-run" if dry_run else "deleted",
        run_id,
        len(deleted),
        total_bytes,
    )
    return {
        "run_id": run_id,
        "deleted_count": len(deleted),
        "total_bytes": total_bytes,
        "dry_run": dry_run,
        "deleted_objects": deleted if dry_run else [],
    }


def cleanup_stale(
    oci_config: dict[str, Any],
    bucket: str,
    max_age_days: int = 7,
    dry_run: bool = False,
) -> dict[str, object]:
    """Delete all run artifacts older than *max_age_days*.

    Iterates all aictx-runs/ prefixes and checks modification time.
    """
    from aictx.oci.object_storage import _get_namespace, _get_object_client

    client = _get_object_client(oci_config)
    namespace = _get_namespace(client)

    cutoff = datetime.now(UTC) - timedelta(days=max_age_days)
    deleted_count = 0
    total_bytes = 0
    scanned_runs = 0

    try:
        response = client.list_objects(
            namespace, bucket, prefix="aictx-runs/", fields="timeModified"
        )
        objects = response.data.objects or []
        for obj in objects:
            if obj.time_modified and obj.time_modified < cutoff:
                scanned_runs += 1
                if not dry_run:
                    try:
                        client.delete_object(namespace, bucket, obj.name)
                        logger.info("stale deleted: %s", obj.name)
                    except Exception as exc:
                        logger.warning("stale delete failed %s: %s", obj.name, exc)
                deleted_count += 1
                total_bytes += obj.size or 0
    except Exception as exc:
        logger.error("stale cleanup failed: %s", exc)
        if not dry_run:
            raise RemoteJobError(f"Stale cleanup failed: {exc}") from exc

    logger.info(
        "stale cleanup %s scanned=%d deleted=%d bytes=%d max_age_days=%d",
        "dry-run" if dry_run else "completed",
        scanned_runs,
        deleted_count,
        total_bytes,
        max_age_days,
    )
    return {
        "max_age_days": max_age_days,
        "deleted_count": deleted_count,
        "total_bytes": total_bytes,
        "dry_run": dry_run,
    }
