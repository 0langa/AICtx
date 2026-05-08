"""Project classification without LLM calls."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ProjectClassification:
    """Deterministic classification of a repository."""

    primary_language: str = "unknown"
    project_type: str = "unknown"
    build_system: str = "unknown"
    test_system: str = "unknown"
    package_system: str = "unknown"
    app_type: str = "unknown"
    docs_layout: str = "unknown"
    ci_layout: str = "unknown"


def classify_project(repo_root: Path) -> ProjectClassification:
    """Classify *repo_root* using deterministic heuristics."""
    # TODO: implement classification logic
    return ProjectClassification()
