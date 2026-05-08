# AICtx Documentation

User and developer documentation for AICtx.

## Installation

Requires Python 3.12+.

```bash
# Clone the repository
git clone https://github.com/0langa/AICtx.git
cd AICtx

# Install with uv (recommended)
uv sync --extra dev

# Or with pip
pip install -e ".[dev]"
```

## Running the CLI

```bash
# Show version
uv run aictx --version

# Show help
uv run aictx --help
```

### Scanning a Repository

The only fully implemented command is `scan`.

```bash
uv run aictx scan --project <path-to-repo>
```

This will:

1. Detect the Git root.
2. Walk the repository, skipping ignored directories and files.
3. Classify files (source, test, doc, manifest, binary, ignored).
4. Detect languages and project type.
5. Scan non-binary files for high-confidence secrets.
6. Print a summary to the terminal.
7. Write the full inventory to `.aictx/runs/<timestamp>-scan/inventory.json`.

### Initializing Baseline Lockfile

`init` is now minimally implemented.

```bash
uv run aictx init --project <path-to-repo>
```

This will:

1. Validate the target is inside a Git repository.
2. Run the scanner.
3. Create `docs/AIprojectcontext/` if missing.
4. Write `docs/AIprojectcontext/context.lock.json` as a baseline file-state lockfile.
5. Create `.aictxignore` if missing.

This command does not call any model provider, does not generate AI context markdown, and does not auto-commit anything.

### Verifying Baseline State

`verify --strict` is now a hash-only verifier MVP.

```bash
uv run aictx verify --project <path-to-repo> --strict
```

It currently checks:

- lockfile exists
- schema version is supported
- each locked source file still exists
- each locked source file hash still matches
- generated file hashes if generated files are present in the lockfile

It does not yet perform semantic AI validation or public-docs impact verification.

### Other Commands

The following commands exist in the CLI but are currently stubbed:

- `aictx run --project <path> --mode <mode> --execution <target> --write <mode>`
- `aictx clean --oci --run-id <id>`
- `aictx public-docs update --project <path> --scope <scope> --write <mode>`

## Interpreting Scanner Output

A typical scan summary looks like:

```
AICtx scan complete
repo: /path/to/repo
branch: main
head: abc123...
dirty: False
files included: 62
files ignored: 1
docs: 7
source: 44
tests: 7
manifests: 1
secrets: 0
inventory: /path/to/repo/.aictx/runs/2026-05-08T032538Z-scan/inventory.json
```

If secrets are found, the summary lists each path with the detector name and severity. The secret value is never printed.

## Running Tests

```bash
uv run pytest
```

The test suite includes:

- CLI version output test.
- Scanner utility tests (binary detection, language detection, manifest/test/doc classification, SHA-256, secret scanning).
- Integration tests ensuring `.aictx/` runtime artifacts and hard-excluded directories are not included in inventory.

## Lint, Format, and Typecheck

```bash
# Check formatting
uv run ruff format --check .

# Format code
uv run ruff format .

# Lint
uv run ruff check .

# Typecheck
uv run mypy src
```

## Troubleshooting

### Scan fails with "Not a git repository"

Ensure the target path is inside a Git repository with at least one commit.

### Secrets are detected in test fixtures

The scanner uses regex-based detection. Test fixtures containing fake secrets will be reported. This is expected and safe because the scanner only reports findings; it does not block or modify anything.

### `aictx run` does nothing useful yet

This command is currently stubbed. It will print a "not yet implemented" message. Context generation remains a planned feature.

## Repository Layout

See `CODEMAP.md` for a detailed file-by-file map.

See `ARCHITECTURE.md` for the system architecture and current limitations.

See `../aictx_development_plan.md` for the full roadmap.
