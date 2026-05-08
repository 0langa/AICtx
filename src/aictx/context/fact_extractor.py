"""Fact extraction from selected repository files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aictx.llm.base import ChatRequest, ModelProvider


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


def _extract_fact_packs(file_paths: list[Path]) -> list[FactPack]:
    """Extract structured facts from *file_paths*."""
    packs: dict[str, FactPack] = {
        "project_identity": FactPack("project_identity"),
        "architecture": FactPack("architecture"),
        "feature": FactPack("feature"),
        "workflow": FactPack("workflow"),
        "docs": FactPack("docs"),
        "risk": FactPack("risk"),
    }
    for path in sorted(file_paths):
        rel = path.as_posix()
        suffix = path.suffix.lower()
        if path.name == "README.md":
            packs["project_identity"].add_fact(
                claim=f"Repository includes root README at {rel}",
                confidence=1.0,
                source_paths=[rel],
            )
        if suffix in {".py", ".cs", ".rs", ".go", ".ts", ".js"}:
            packs["architecture"].add_fact(
                claim=f"Source file present: {rel}",
                confidence=0.9,
                source_paths=[rel],
            )
            packs["feature"].add_fact(
                claim=f"Implementation file selected for context: {rel}",
                confidence=0.8,
                source_paths=[rel],
            )
        if "test" in path.name.lower() or "tests/" in rel:
            packs["workflow"].add_fact(
                claim=f"Test coverage artifact present: {rel}",
                confidence=0.9,
                source_paths=[rel],
            )
        if suffix == ".md" and rel != "README.md":
            packs["docs"].add_fact(
                claim=f"Documentation file selected: {rel}",
                confidence=0.9,
                source_paths=[rel],
            )
        if suffix in {".yml", ".yaml", ".toml", ".json"}:
            packs["workflow"].add_fact(
                claim=f"Configuration or workflow manifest selected: {rel}",
                confidence=0.85,
                source_paths=[rel],
            )

    return [pack for pack in packs.values() if pack.facts]


def extract_facts(
    repo_root: Path,
    plan: dict[str, Any],
    provider: ModelProvider,
    run_id: str,
) -> list[dict[str, object]]:
    """Extract deterministic structured facts for the selected plan."""
    selected = [repo_root / path for path in plan["selected_files"]]
    packs = _extract_fact_packs(selected)
    output: list[dict[str, object]] = []
    for pack in packs:
        response = provider.chat(
            ChatRequest(
                system_prompt="Summarize repository facts deterministically.",
                messages=[{"role": "user", "content": pack.name}],
                run_id=run_id,
                purpose=f"fact-pack:{pack.name}",
            )
        )
        output.append(
            {
                "name": pack.name,
                "facts": pack.facts,
                "summary": response.content,
                "estimated_output_tokens": response.output_tokens,
            }
        )
    return output
