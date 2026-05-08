"""AI context scaffold writer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aictx import __version__
from aictx.context.agents_md import generate_agents_md
from aictx.io.files import safe_write
from aictx.models.context_lock import (
    ContextLock,
    GeneratedFileEntry,
    SectionEntry,
    SourceFileEntry,
)
from aictx.models.inventory import RepositoryInventory
from aictx.verify.hashes import sha256_file, sha256_text


def write_context_scaffold(
    repo_root: Path,
    out_dir: Path,
    inventory: RepositoryInventory,
    plan: dict[str, Any],
    fact_packs: list[dict[str, Any]],
) -> list[Path]:
    """Write compact AI-facing context files to *out_dir*."""
    generated: list[Path] = []
    selected_files = plan["selected_files"]
    reasons = plan["reason_per_selected_file"]
    fact_map = {pack["name"]: pack for pack in fact_packs}

    files_to_content = {
        "docs/AIprojectcontext/ai-index.md": _render_ai_index(),
        "docs/AIprojectcontext/project-state.md": _render_project_state(inventory, plan, fact_map),
        "docs/AIprojectcontext/code-map.md": _render_code_map(plan),
        "docs/AIprojectcontext/architecture.md": _render_architecture(fact_map),
        "docs/AIprojectcontext/workflows.md": _render_workflows(inventory, fact_map),
        "docs/AIprojectcontext/public-docs-map.md": _render_public_docs_map(inventory),
        "docs/AIprojectcontext/change-impact-map.md": _render_change_impact_map(
            selected_files, reasons
        ),
        "docs/AIprojectcontext/schema.md": _render_schema(),
        "docs/AIprojectcontext/validation-report.md": _render_validation_report(fact_packs),
        "AGENTS.md": generate_agents_md(repo_root.name),
    }

    for relative_name, content in files_to_content.items():
        target = out_dir / relative_name
        safe_write(target, content)
        generated.append(target)
    return generated


def build_context_lock(
    repo_root: Path,
    out_dir: Path,
    inventory: RepositoryInventory,
    plan: dict[str, Any],
    fact_packs: list[dict[str, Any]],
    generated_paths: list[Path],
    model_provider: str,
    model_name: str,
) -> ContextLock:
    """Build a Phase 1 lockfile for generated context artifacts."""
    selected_set = set(plan["selected_files"])
    source_files = [
        SourceFileEntry(
            path=file.path,
            sha256=file.sha256,
            kind=file.kind,
            included_in_generation=file.path in selected_set,
        )
        for file in inventory.files
        if not file.is_ignored
        and not file.is_binary
        and file.sha256 != "skipped"
        and file.path != "docs/AIprojectcontext/context.lock.json"
    ]
    source_files.sort(key=lambda entry: entry.path)

    sections: list[SectionEntry] = []
    for pack in fact_packs:
        for fact in pack["facts"]:
            source_hashes = []
            for source_path in fact["source_paths"]:
                match = next(
                    (entry.sha256 for entry in source_files if entry.path == source_path), "unknown"
                )
                source_hashes.append(match)
            sections.append(
                SectionEntry(
                    section_id=fact["id"],
                    generated_file=_target_file_for_pack(pack["name"]),
                    heading=pack["name"],
                    source_paths=fact["source_paths"],
                    source_hashes=source_hashes,
                    fact_ids=[fact["id"]],
                    status="current",
                )
            )

    generated_files = [
        GeneratedFileEntry(
            path=path.relative_to(out_dir).as_posix(),
            sha256=sha256_file(path),
            generated_from_sections=[
                section.section_id
                for section in sections
                if section.generated_file == path.relative_to(out_dir).as_posix()
            ],
        )
        for path in sorted(generated_paths, key=lambda item: item.name)
    ]

    return ContextLock(
        tool_version=__version__,
        repo_head_commit=inventory.head_commit,
        model_provider=model_provider,
        model_name=model_name,
        scanner_config_hash=sha256_text("\n".join(sorted(plan["selected_files"]))),
        generated_files=generated_files,
        source_files=source_files,
        sections=sections,
    )


def _render_ai_index() -> str:
    return """# AI Index

- `project-state.md` — project identity, status, selected scope
- `code-map.md` — selected source and test files
- `architecture.md` — source-traced architecture facts
- `workflows.md` — build, test, and manifest workflow facts
- `public-docs-map.md` — mapped public docs
- `change-impact-map.md` — selected file to context mapping
- `validation-report.md` — fact-pack and validation summary
"""


def _render_project_state(
    inventory: RepositoryInventory,
    plan: dict[str, Any],
    fact_map: dict[str, dict[str, Any]],
) -> str:
    lines = [
        "# Project State",
        "",
        f"- repo_root: `{inventory.repo_root}`",
        f"- branch: `{inventory.branch}`",
        f"- head_commit: `{inventory.head_commit}`",
        f"- dirty_state: `{inventory.dirty_state}`",
        f"- project_type: `{inventory.project_classification.get('project_type', 'unknown')}`",
        f"- primary_language: `{inventory.project_classification.get('primary_language', 'unknown')}`",
        f"- selected_files: `{len(plan['selected_files'])}`",
        f"- estimated_token_cost: `{plan['estimated_token_cost']}`",
        "",
        "## Identity Facts",
    ]
    for fact in fact_map.get("project_identity", {}).get("facts", []):
        lines.append(f"- {fact['claim']} [source: {', '.join(fact['source_paths'])}]")
    return "\n".join(lines) + "\n"


def _render_code_map(plan: dict[str, Any]) -> str:
    lines = ["# Code Map", "", "## Selected Files"]
    reasons = plan["reason_per_selected_file"]
    for path in plan["selected_files"]:
        lines.append(f"- `{path}` — {reasons[path]}")
    return "\n".join(lines) + "\n"


def _render_architecture(fact_map: dict[str, dict[str, Any]]) -> str:
    lines = ["# Architecture", "", "## Architecture Facts"]
    for fact in fact_map.get("architecture", {}).get("facts", []):
        lines.append(f"- {fact['claim']} [source: {', '.join(fact['source_paths'])}]")
    if len(lines) == 3:
        lines.append("- unknown")
    return "\n".join(lines) + "\n"


def _render_workflows(inventory: RepositoryInventory, fact_map: dict[str, dict[str, Any]]) -> str:
    lines = ["# Workflows", "", "## Build and Test Signals"]
    lines.append(f"- build_systems: {', '.join(inventory.build_systems) or 'unknown'}")
    lines.append(f"- test_system: {inventory.project_classification.get('test_system', 'unknown')}")
    for fact in fact_map.get("workflow", {}).get("facts", []):
        lines.append(f"- {fact['claim']} [source: {', '.join(fact['source_paths'])}]")
    return "\n".join(lines) + "\n"


def _render_public_docs_map(inventory: RepositoryInventory) -> str:
    lines = ["# Public Docs Map", "", "## Docs"]
    for entry in inventory.docs:
        lines.append(f"- `{entry.path}` — markdown/doc source")
    return "\n".join(lines) + "\n"


def _render_change_impact_map(selected_files: list[str], reasons: dict[str, str]) -> str:
    lines = ["# Change Impact Map", "", "## Selected File Impact"]
    for path in selected_files:
        lines.append(f"- `{path}` -> ai:{reasons[path]}")
    return "\n".join(lines) + "\n"


def _render_schema() -> str:
    return """# Schema

- fact packs: project_identity, architecture, feature, workflow, docs, risk
- lockfile schema version: 1.0
- verification mode: deterministic hashes plus generated section/source linkage
"""


def _render_validation_report(fact_packs: list[dict[str, Any]]) -> str:
    lines = ["# Validation Report", "", "## Fact Packs"]
    for pack in fact_packs:
        lines.append(f"- `{pack['name']}` — facts: {len(pack['facts'])}")
    return "\n".join(lines) + "\n"


def _target_file_for_pack(pack_name: str) -> str:
    return {
        "project_identity": "docs/AIprojectcontext/project-state.md",
        "architecture": "docs/AIprojectcontext/architecture.md",
        "feature": "docs/AIprojectcontext/code-map.md",
        "workflow": "docs/AIprojectcontext/workflows.md",
        "docs": "docs/AIprojectcontext/public-docs-map.md",
        "risk": "docs/AIprojectcontext/validation-report.md",
    }.get(pack_name, "docs/AIprojectcontext/validation-report.md")
