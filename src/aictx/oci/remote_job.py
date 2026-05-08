"""OCI remote worker job management."""

from __future__ import annotations


class RemoteJob:
    """Represents an OCI remote execution job."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id

    def submit(self) -> str:
        """Submit the job and return the job OCID."""
        # TODO: implement job submission
        raise NotImplementedError("Remote job submission not yet implemented")

    def wait(self, timeout_minutes: int = 45) -> str:
        """Wait for job completion and return the result status."""
        # TODO: implement polling
        raise NotImplementedError("Remote job polling not yet implemented")
