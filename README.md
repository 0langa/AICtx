# AICtx

A local-first CLI tool that prepares Git repositories for low-token AI-agent work.

## Current Status (v0.1.0)

AICtx is at an early alpha stage. The repository scanner, baseline lockfile bootstrap, hash-only verifier MVP, and a local Phase 1 context generation pipeline are implemented and tested. Semantic verification, contradiction/coverage enforcement, and public-docs update remain planned.

### What works today

- `aictx scan` — scans a Git repository, classifies files, detects secrets, and writes a deterministic inventory to `.aictx/runs/<run-id>/inventory.json`.
- `aictx init` — creates `docs/AIprojectcontext/context.lock.json` as a baseline verification lockfile and creates `.aictxignore` if missing.
- `aictx run --mode setup-context --execution local` — plans a local run, extracts deterministic fact packs, generates AI context markdown under `docs/AIprojectcontext/`, stages a patch by default, and can apply generated files.
- `aictx verify --strict` — performs deterministic hash-only validation against the committed baseline lockfile.
- Git integration — branch, HEAD commit, dirty-state, and file-change detection.
- Structured Git status inventory — tracked, untracked, modified, deleted, and renamed file lists are serialized into inventory output.
- Ignore matching — built-in hard excludes, `.gitignore`, and `.aictxignore`.
- Project classification — deterministic heuristics for Python, C#/.NET, Node, Rust, Go, and docs-heavy repos.
- Secret scanning — regex-based high-confidence detection without printing secret values.
- Linting, formatting, and tests pass.

### What is planned

- Semantic freshness verification beyond file hashes — planned for a later milestone.
- Change-impact mapping and cheap refresh — planned for v0.4.0.
- Public-docs updater — planned for v0.5.0.
- CI workflow generation — planned for v0.6.0.
- OCI remote execution — planned for v0.7.0.

## Installation

Requires Python 3.12+.

```bash
# Clone and install in editable mode
git clone https://github.com/0langa/AICtx.git
cd AICtx
uv sync --extra dev
# or
pip install -e ".[dev]"
```

## Quick Start

```bash
# Show version
uv run aictx --version

# Scan the current repository
uv run aictx scan --project .

# Create or refresh the baseline lockfile
uv run aictx init --project .

# Verify the repository against the committed baseline
uv run aictx verify --project . --strict

# Generate AI context as a reviewable patch
uv run aictx run --project . --mode setup-context --execution local --scope full --write patch

# Apply generated AI context into the repository
uv run aictx run --project . --mode setup-context --execution local --scope full --write apply
```

## CLI Commands

| Command | Status | Description |
| --- | --- | --- |
| `scan` | **Implemented** | Walks the repo, builds inventory, detects secrets, writes JSON. |
| `init` | **Implemented (MVP)** | Creates `docs/AIprojectcontext/context.lock.json` and `.aictxignore` if missing. |
| `run` | **Implemented (local Phase 1)** | Runs local planning, fact extraction, scaffold generation, and lockfile output for `setup-context` in local mode. |
| `verify` | **Implemented (hash-only MVP)** | Verifies locked source and generated file hashes. No semantic validation yet. |
| `clean` | Stubbed | Will clean generated or remote artifacts. |
| `public-docs update` | Stubbed | Will update human-facing public docs. Note: subcommand under `aictx public-docs`. |

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .

# Typecheck
uv run mypy src
```

## Documentation

- `documentation/DOCUMENTATION.md` — User and developer guide.
- `documentation/CODEMAP.md` — File-by-file code map.
- `documentation/ARCHITECTURE.md` — System architecture and current limitations.
- `aictx_development_plan.md` — Full roadmap and milestone plan.
- `documentation/CHANGELOG.md` — Unreleased changes.

## Safety Notes

- The scanner never prints secret values; it only reports file paths and detector names.
- The tool does not auto-commit, auto-push, or silently overwrite files.
- `docs/AIprojectcontext/context.lock.json` is generated but versioned; `.aictx/runs/`, `.aictx/cache/`, and `.aictx/tmp/` are runtime-only and should not be committed.
- `verify --strict` is currently deterministic file-state validation only; semantic freshness and public-docs impact checks are planned later.
- `aictx run` currently supports only `--mode setup-context --execution local` and generates deterministic scaffold files. Contradiction reports, coverage reports, semantic freshness, and provider-backed OCI generation are not implemented yet.
- `aictx public-docs update` remains stubbed.

## License

MIT. See `LICENSE`.
