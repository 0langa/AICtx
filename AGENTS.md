# AGENTS.md — AI Agent Instructions for AICtx

> **Primary context source:** Root docs (`README.md`, `documentation/CODEMAP.md`, `documentation/ARCHITECTURE.md`, `aictx_development_plan.md`).
> **Note:** `aictx run --mode setup-context --execution local` now generates AI context markdown and `AGENTS.md`, but semantic freshness and public-docs sync are still incomplete.

## Current Project State

AICtx is an early-alpha local-first CLI tool (v0.1.0). The repository scanner, baseline lockfile bootstrap, hash-only verification MVP, and local Phase 1 context generation pipeline are implemented. Semantic verification and public-docs update remain incomplete. Do not claim features are implemented unless the code supports it.

## Conventions

- Python 3.12+ with `src/` layout (`src/aictx/`).
- Use `from __future__ import annotations` in every module.
- Pydantic v2 for all data models.
- Direct `git` subprocess calls for important Git operations.
- All safety checks fail closed: report `unknown` or `needs-source` rather than guess.

## Build and Test

```bash
# Install in editable mode
pip install -e ".[dev]"
# or
uv sync --extra dev

# Lint and typecheck
ruff check .
mypy src

# Run tests
pytest
```

## Implemented Modules

- `src/aictx/cli.py` — Typer CLI entry point.
- `src/aictx/scan/` — Repository scanning, classification, secret detection (fully implemented).
- `src/aictx/git/` — Git root detection and worktree status.
- `src/aictx/models/` — Pydantic inventory, lockfile, docs-map, and run-report models.
- `src/aictx/llm/base.py`, `llm/dry_run.py` — Model provider ABC and dry-run implementation.
- `src/aictx/io/` — File I/O, patches, JSONL helpers.
- `src/aictx/context/agents_md.py` — Static `AGENTS.md` template generator.
- `src/aictx/context/pipeline.py` — local Phase 1 run orchestration.
- `src/aictx/context/lockfile.py` — baseline `context.lock.json` builder and I/O helpers.
- `src/aictx/context/planner.py`, `fact_extractor.py`, `writer.py` — deterministic Phase 1 planning, fact extraction, and scaffold generation.
- `src/aictx/verify/verifier.py` — hash-only strict verifier MVP.

## Stubbed / Planned Modules

- `src/aictx/context/compressor.py` — context generation compression stage (stubbed).
- `src/aictx/verify/impact.py`, `reports.py` — impact mapping and reports (stubbed).
- `src/aictx/public_docs/` — mapper, updater, patcher (stubbed).
- `src/aictx/oci/` — OCI config, Object Storage, remote jobs, cleanup (stubbed).
- `src/aictx/llm/oci_genai.py` — OCI GenAI provider (stubbed).

## Rules for all agents

1. Read `documentation/CODEMAP.md` and `documentation/ARCHITECTURE.md` first to understand the layout and what is implemented.
2. The actual codebase is the source of truth. Do not rely on this file alone.
3. Do not fabricate facts. If information is unavailable, mark it `unknown` or `needs-source`.
4. Preserve source references for all important claims.
5. `aictx verify --strict` now performs deterministic hash-only file-state validation. `aictx run` works only for local `setup-context` generation and is still limited to deterministic Phase 1 behavior.
6. Before calling work finished, ensure tests pass (`uv run pytest`) and no lint errors exist (`uv run ruff check .`, `uv run mypy src`).

## Accuracy Rules

- Source-trace all critical claims.
- No unsupported assumptions.
- Mark uncertainty explicitly.
- Fail closed: report `unknown` rather than guess.
