"""OCI runtime budgeting — estimate costs, enforce caps, require confirmation.

No unbounded OCI usage allowed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from aictx.errors import SafetyError

logger = logging.getLogger("aictx.oci.runtime")


@dataclass
class RuntimeBudget:
    """Budget constraints for a remote OCI run."""

    max_runtime_minutes: int = 45
    max_snapshot_mb: int = 250
    max_upload_retries: int = 3
    max_download_retries: int = 3
    max_input_tokens: int = 500_000
    max_output_tokens: int = 100_000

    def validate(self) -> list[str]:
        """Return list of validation errors.  Empty means valid."""
        errors: list[str] = []
        if self.max_runtime_minutes < 1 or self.max_runtime_minutes > 120:
            errors.append(f"max_runtime_minutes must be 1-120, got {self.max_runtime_minutes}")
        if self.max_snapshot_mb < 1 or self.max_snapshot_mb > 1024:
            errors.append(f"max_snapshot_mb must be 1-1024, got {self.max_snapshot_mb}")
        if self.max_upload_retries < 0 or self.max_upload_retries > 10:
            errors.append(f"max_upload_retries must be 0-10, got {self.max_upload_retries}")
        if self.max_download_retries < 0 or self.max_download_retries > 10:
            errors.append(f"max_download_retries must be 0-10, got {self.max_download_retries}")
        return errors


@dataclass
class CostEstimate:
    """Estimated cost and resource usage for a remote run."""

    snapshot_size_bytes: int = 0
    estimated_runtime_minutes: int = 0
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    estimated_oci_cost_usd: float = 0.0
    above_threshold: bool = False

    def format_summary(self) -> str:
        """Return a human-readable summary string."""
        return (
            f"  snapshot size: {self.snapshot_size_bytes / 1024 / 1024:.1f} MiB\n"
            f"  estimated runtime: {self.estimated_runtime_minutes} min\n"
            f"  estimated input tokens: {self.estimated_input_tokens:,}\n"
            f"  estimated output tokens: {self.estimated_output_tokens:,}\n"
            f"  estimated OCI cost: ${self.estimated_oci_cost_usd:.2f}\n"
            f"  above threshold: {'YES' if self.above_threshold else 'no'}"
        )


def estimate_remote_cost(
    snapshot_path: Path | None = None,
    snapshot_size_bytes: int = 0,
    input_tokens: int = 0,
    output_tokens: int = 0,
    runtime_minutes: int = 0,
) -> CostEstimate:
    """Estimate cost and resource usage for a remote run.

    Uses actual snapshot size or provided metrics.
    Cost estimate is conservative (overestimate).
    """
    size = snapshot_size_bytes
    if snapshot_path and snapshot_path.is_file():
        size = snapshot_path.stat().st_size

    # Rough OCI cost: ~$0.10/GB-month storage, ~$0.05/GB egress, ~$0.08/1K tokens
    storage_cost = (size / (1024**3)) * 0.10
    token_cost = ((input_tokens + output_tokens) / 1000) * 0.08
    compute_cost = (runtime_minutes / 60) * 0.50  # ~$0.50/hr for small instances
    estimated_cost = storage_cost + token_cost + compute_cost

    # Conservative runtime estimate: 1 min per 10K tokens + 2 min overhead
    est_runtime = max(runtime_minutes, (input_tokens // 10000) + 2)

    threshold = 5.0  # USD
    return CostEstimate(
        snapshot_size_bytes=size,
        estimated_runtime_minutes=est_runtime,
        estimated_input_tokens=input_tokens,
        estimated_output_tokens=output_tokens,
        estimated_oci_cost_usd=round(estimated_cost, 2),
        above_threshold=estimated_cost > threshold,
    )


def require_runtime_confirmation(estimate: CostEstimate, budget: RuntimeBudget) -> bool:
    """Check if the estimate fits within budget.  Returns True if OK."""
    errors: list[str] = []
    if estimate.snapshot_size_bytes > budget.max_snapshot_mb * 1024 * 1024:
        errors.append(
            f"Snapshot size {estimate.snapshot_size_bytes / 1024 / 1024:.1f} MiB "
            f"exceeds limit {budget.max_snapshot_mb} MiB"
        )
    if estimate.estimated_runtime_minutes > budget.max_runtime_minutes:
        errors.append(
            f"Estimated runtime {estimate.estimated_runtime_minutes} min "
            f"exceeds limit {budget.max_runtime_minutes} min"
        )
    if estimate.estimated_input_tokens > budget.max_input_tokens:
        errors.append(
            f"Estimated input tokens {estimate.estimated_input_tokens:,} "
            f"exceeds limit {budget.max_input_tokens:,}"
        )
    if estimate.estimated_output_tokens > budget.max_output_tokens:
        errors.append(
            f"Estimated output tokens {estimate.estimated_output_tokens:,} "
            f"exceeds limit {budget.max_output_tokens:,}"
        )

    if errors:
        raise SafetyError("Runtime budget exceeded:\n" + "\n".join(f"  - {e}" for e in errors))

    if estimate.above_threshold:
        logger.warning(
            "Estimated cost $%.2f exceeds default threshold", estimate.estimated_oci_cost_usd
        )

    return True
