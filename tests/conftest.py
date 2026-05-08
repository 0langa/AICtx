from __future__ import annotations

import sys
from pathlib import Path

# Ensure repo root is importable so tests.fixtures can be reached
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
