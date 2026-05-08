# AICtx

A local-first CLI tool that prepares Git repositories for low-token AI-agent work.

## Current Status (v0.1.0)

AICtx is at an early alpha stage. The repository scanner is fully implemented and tested. Context generation, verification, and public-docs update modes are stubbed and will be built in upcoming milestones.

### What works today

- `aictx scan` — scans a Git repository, classifies files, detects secrets, and writes a deterministic inventory to `.aictx/runs/<run-id>/inventory.json`.
- Git integration — branch, HEAD commit, dirty-state, and file-change detection.
- Ignore matching — built-in hard excludes, `.gitignore`, and `.aictxignore`.
- Project classification — deterministic heuristics for Python, C#/.NET, Node, Rust, Go, and docs-heavy repos.
- Secret scanning — regex-based high-confidence detection without printing secret values.
- CLI skeleton — `init`, `run`, `verify`, `clean`, and `public-docs` commands exist as placeholders.
- Linting, formatting, and tests pass.

### What is planned

- Context generation pipeline (`aictx run`) — planned for v0.2.0.
- Strict verification (`aictx verify --strict`) — planned for v0.3.0.
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

# Other commands exist as stubs and print "not yet implemented"
uv run aictx init --project .
uv run aictx run --project . --mode setup-context --execution local --write patch
uv run aictx verify --project . --strict
```

## CLI Commands

| Command | Status | Description |
| --- | --- | --- |
| `scan` | **Implemented** | Walks the repo, builds inventory, detects secrets, writes JSON. |
| `init` | Stubbed | Will initialize `.aictx/config.toml` and `.aictxignore`. |
| `run` | Stubbed | Will run the context generation pipeline. |
| `verify` | Stubbed | Will verify AI context freshness. |
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
- The `run` and `public-docs update` commands accept a `--write` flag (patch/apply), but these commands are currently stubbed and produce no output.

## License

MIT. See `LICENSE`.
