"""Fact extraction from selected repository files."""

from __future__ import annotations

from pathlib import Path


class FactPack:
    """Collection of structured facts for a context pass."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.facts: list[dict[str, object]] = []

    def add_fact(
        self,
        claim: str,
        confidence: float,
        source_paths: list[str],
        source_spans: list[str] | None = None,
        derived_from: list[str] | None = None,
        needs_source: bool = False,
    ) -> None:
        self.facts.append(
            {
                "id": f"{self.name}-{len(self.facts)}",
                "claim": claim,
                "confidence": confidence,
                "source_paths": source_paths,
                "source_spans": source_spans or [],
                "derived_from": derived_from or [],
                "needs_source": needs_source,
            }
        )


def extract_facts(file_paths: list[Path]) -> list[FactPack]:
    """Extract structured facts from *file_paths*."""
    # TODO: implement fact extraction passes
    return []
