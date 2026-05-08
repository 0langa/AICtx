"""High-confidence secret scanning."""

from __future__ import annotations

from pathlib import Path


def scan_for_secrets(content: str, file_path: Path) -> list[dict[str, str]]:
    """Scan *content* for high-confidence secrets.

    Returns a list of findings with ``type`` and ``line`` keys.
    Does **not** return the secret value itself.
    """
    # TODO: implement secret detection
    return []
