"""Validation report generation."""

from __future__ import annotations

from pathlib import Path


def write_validation_report(
    out_path: Path,
    result: str,
    details: dict[str, object],
) -> None:
    """Write a human-readable validation report to *out_path*."""
    # TODO: implement report formatting
    out_path.write_text(f"# Validation Report\\n\\nResult: {result}\\n", encoding="utf-8")
