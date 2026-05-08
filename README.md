# AICtx

A local-first CLI tool that prepares Git repositories for low-token AI-agent work.

## Current Status (v0.1.0)

AICtx is at an early alpha stage. The repository scanner, baseline lockfile bootstrap, hash-only verifier MVP, and a local Phase 1 context generation pipeline are implemented and tested. Semantic verification, contradiction/coverage enforcement, and public-docs update remain planned.

### What works today

- `aictx scan` — scans a Git repository, classifies files, detects secrets, and writes a deterministic inventory to `.aictx/runs/<run-id>/inventory.json`.
- `aictx init` — creates or refreshes `docs/AIprojectcontext/context.lock.json`, preserves generated lock metadata when present, and creates `.aictxignore` if missing.
- `aictx run --mode setup-context --execution local` — plans a local run, extracts deterministic fact packs, generates AI context markdown under `docs/AIprojectcontext/`, writes a generated `AGENTS.md`, stages repo-relative outputs and a reviewable patch by default, and can copy those staged outputs plus the generated lockfile into the repository.
- `aictx verify --strict` — performs deterministic hash-only validation against the committed baseline lockfile.
- Git integration — branch, HEAD commit, dirty-state, and file-change detection.
- Structured Git status inventory — tracked, untracked, modified, deleted, and renamed file lists are serialized into inventory output.
- Ignore matching — built-in hard excludes, `.gitignore`, and `.aictxignore`.
- Project classification — deterministic heuristics for Python, C#/.NET, Node, Rust, Go, and docs-heavy repos.
- Secret scanning — regex-based high-confidence detection without printing secret values.
- Secret-scan self-protection — skips detector source/examples in `src/aictx/scan/secrets.py` and test/fixture-style paths to avoid false positives.
- Windows test temp hardening — `.pytest-tmp` is excluded from linting, scanning, and test discovery.
- Repository tooling — Ruff, mypy, and pytest are configured for local validation.

### What is stubbed or not yet implemented

- `aictx clean` — stubbed; prints a message and does not perform cleanup.
- `aictx public-docs update` — stubbed; exits with code 1.
- `aictx run --scope changed` — not implemented; only `--scope full` works.
- `io.patches.apply_patch` — stubbed; apply mode copies staged files instead of replaying patches.
- OCI GenAI provider — stubbed; `dry_run` is the only working provider.
- Context compression — stubbed (pass-through).
- Change-impact mapping — stubbed.
- Semantic freshness verification — planned for a later milestone.
- CI workflow generation — planned for a later milestone.
- OCI remote execution — planned for a later milestone.

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
| `scan` | Implemented | Walks the repo, builds inventory, detects secrets, writes JSON. |
| `init` | Implemented | Creates or refreshes `docs/AIprojectcontext/context.lock.json`, preserving generated lock metadata when present, and creates `.aictxignore` if missing. |
| `run` | Implemented (local Phase 1) | Runs local planning, fact extraction, scaffold generation, and lockfile output for `setup-context` in local mode. Only `--scope full` works. |
| `verify` | Implemented (hash-only MVP) | Verifies locked source and generated file hashes. No semantic validation yet. |
| `clean` | Stubbed | Prints a stub message and does not perform cleanup. |
| `public-docs update` | Stubbed | Prints "not yet implemented" and exits with code 1. Subcommand under `aictx public-docs`. |

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
- `aictx run` currently supports only `--mode setup-context --execution local --scope full`. `--scope changed` is not implemented yet.
- Contradiction reports and coverage reports are written as deterministic placeholders (empty) during each run; they are not yet populated with real analysis.
- `aictx public-docs update` is a stub that prints "not yet implemented" and exits with code 1.
- `io.patches.apply_patch` is a stub; `--write apply` copies staged generated files into the repo instead of replaying a patch file.
- The OCI GenAI provider (`oci_genai.py`) is stubbed; the only working provider is `dry_run`.

## License

MIT. See `LICENSE`.
