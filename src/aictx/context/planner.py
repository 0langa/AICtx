"""Context planning stage."""

from __future__ import annotations

from pathlib import Path

from aictx.config import AictxConfig
from aictx.models.inventory import RepositoryInventory


def plan_context(
    inventory: RepositoryInventory,
    existing_context_dir: Path | None = None,
    existing_agents_md: Path | None = None,
    scope: str = "full",
    config: AictxConfig | None = None,
) -> dict[str, object]:
    """Plan which files to include in the context generation."""
    selected_entries = []
    reasons: dict[str, str] = {}
    warnings: list[str] = []

    for entry in sorted(inventory.manifests, key=lambda item: item.path):
        if entry.is_generated:
            continue
        selected_entries.append(entry)
        reasons[entry.path] = "manifest"

    important_docs = {"README.md", "CHANGELOG.md", "ROADMAP.md", "AGENTS.md"}
    for entry in sorted(inventory.docs, key=lambda item: item.path):
        if entry.is_generated:
            continue
        if (
            entry.path in important_docs or entry.path.startswith("docs/")
        ) and entry.path not in reasons:
            selected_entries.append(entry)
            reasons[entry.path] = "doc"

    for entry in sorted(inventory.files, key=lambda item: item.path):
        if entry.is_ignored or entry.is_binary or entry.is_generated:
            continue
        if entry.is_source and entry.path not in reasons:
            selected_entries.append(entry)
            reasons[entry.path] = "source"
        elif entry.is_test and entry.path not in reasons:
            selected_entries.append(entry)
            reasons[entry.path] = "test"

    if existing_context_dir and existing_context_dir.exists():
        for path in sorted(existing_context_dir.glob("*.md")):
            rel = path.relative_to(inventory.repo_root).as_posix()
            reasons[rel] = "existing_context"
    if existing_agents_md and existing_agents_md.exists():
        rel = existing_agents_md.relative_to(inventory.repo_root).as_posix()
        reasons[rel] = "existing_agents"

    selected_entries = sorted(selected_entries, key=lambda item: item.path)
    selected_files = [entry.path for entry in selected_entries]
    if config and len(selected_files) > config.limits.max_files_per_run:
        warnings.append("selection exceeds configured max_files_per_run")

    estimated_token_cost = sum(max(entry.size_bytes // 4, 1) for entry in selected_entries)

    return {
        "scope": scope,
        "critical_source_files": [entry.path for entry in selected_entries if entry.is_source],
        "critical_doc_files": [entry.path for entry in selected_entries if entry.is_doc],
        "manifest_files": [entry.path for entry in selected_entries if entry.is_manifest],
        "build_files": [entry.path for entry in selected_entries if entry.is_manifest],
        "test_files": [entry.path for entry in selected_entries if entry.is_test],
        "files_excluded_from_llm": [
            entry.path
            for entry in inventory.files
            if entry.is_ignored or entry.is_binary or entry.is_generated
        ],
        "reason_per_selected_file": reasons,
        "estimated_token_cost": estimated_token_cost,
        "selected_files": selected_files,
        "warnings": warnings,
    }
