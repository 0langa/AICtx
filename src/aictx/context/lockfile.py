""``context.lock.json` I/O helpers."""

from __future__ import annotations

import json
from pathlib import Path

from aictx.models.context_lock import ContextLock


LOCK_FILENAME = "context.lock.json"


def load_lockfile(context_dir: Path) -> ContextLock | None:
    """Load the lockfile from *context_dir* if it exists."""
    path = context_dir / LOCK_FILENAME
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return ContextLock(**data)


def write_lockfile(context_dir: Path, lock: ContextLock) -> None:
    """Write *lock* to *context_dir*/context.lock.json."""
    path = context_dir / LOCK_FILENAME
    with path.open("w", encoding="utf-8") as fh:
        json.dump(lock.model_dump(mode="json"), fh, indent=2)
