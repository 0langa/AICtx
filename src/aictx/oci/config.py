"""OCI configuration loading."""

from __future__ import annotations

import os
from pathlib import Path


class OCIConfig:
    """OCI connection settings."""

    def __init__(self) -> None:
        self.compartment_id = os.getenv("OCI_COMPARTMENT_ID", "")
        self.config_file = Path.home() / ".oci/config"
