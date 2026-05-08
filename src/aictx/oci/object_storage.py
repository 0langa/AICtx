"""OCI Object Storage exchange."""

from __future__ import annotations

from pathlib import Path


def upload_snapshot(bucket: str, snapshot_path: Path, run_id: str) -> str:
    """Upload a snapshot to OCI Object Storage."""
    # TODO: implement OCI upload
    raise NotImplementedError("OCI upload not yet implemented")


def download_result(bucket: str, run_id: str, dest: Path) -> None:
    """Download a result bundle from OCI Object Storage."""
    # TODO: implement OCI download
    raise NotImplementedError("OCI download not yet implemented")
