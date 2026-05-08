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

The serialized inventory now includes `dirty_state` plus `git_status` with deterministic tracked, untracked, modified, deleted, and renamed file lists.

### Generating AI Context

`run` implements the local Phase 1 pipeline. Only `--mode setup-context --execution local --scope full` is supported.

```bash
uv run aictx run --project <path-to-repo> --mode setup-context --execution local --scope full --write patch
```

Supported values today:

- `--mode setup-context`
- `--execution local`
- `--scope full`
- `--write patch|apply`

Current behavior:

1. Validate supported mode/execution/scope/write values.
2. Load `.aictx/config.toml` when present.
3. Scan the repository and stop if secrets are detected.
4. Build a deterministic selection plan.
5. Extract deterministic fact packs using the dry-run provider.
6. Generate AI context files and `AGENTS.md` into `.aictx/runs/<timestamp>-run/out/` using repo-relative paths.
7. Write `.aictx/runs/<timestamp>-run/aictx.patch` from those staged outputs.
8. If `--write apply` is used, copy the staged generated files into the repository. The current implementation does not replay the patch file.

Current generated repository files on `--write apply`:

- `docs/AIprojectcontext/ai-index.md`
- `docs/AIprojectcontext/project-state.md`
- `docs/AIprojectcontext/code-map.md`
- `docs/AIprojectcontext/architecture.md`
- `docs/AIprojectcontext/workflows.md`
- `docs/AIprojectcontext/public-docs-map.md`
- `docs/AIprojectcontext/change-impact-map.md`
- `docs/AIprojectcontext/schema.md`
- `docs/AIprojectcontext/validation-report.md`
- `docs/AIprojectcontext/context.lock.json`
- `AGENTS.md`

Important current behavior:

- `--write patch` writes staged outputs plus `.aictx/runs/<timestamp>-run/aictx.patch`
- `--write apply` copies the staged generated outputs into the repository, including `docs/AIprojectcontext/context.lock.json`
- `src/aictx/io/patches.py:apply_patch` is still stubbed and is not used yet for repo updates

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
	If the lockfile already contains generated context metadata from a prior apply run, that generated metadata is preserved while source hashes are refreshed.
5. Create `.aictxignore` if missing.

This command does not call any model provider, does not generate new AI context markdown, and does not auto-commit anything.

The generated `docs/AIprojectcontext/context.lock.json` is intended to be committed. Runtime artifacts under `.aictx/` are local-only.

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

Typical workflows:

Baseline-only verification workflow:

1. change code or docs
2. run `uv run aictx verify --project . --strict`
3. if verification fails because locked source hashes changed, refresh the baseline with `uv run aictx init --project .`
4. commit the code/doc changes together with the updated `docs/AIprojectcontext/context.lock.json`

Generated-context workflow:

1. change code or docs that affect generated AI context
2. run `uv run aictx run --project . --mode setup-context --execution local --scope full --write apply`
3. run `uv run aictx verify --project . --strict`
4. commit the code/doc changes together with the refreshed generated context files and `docs/AIprojectcontext/context.lock.json`

`init` refreshes the verification lockfile and preserves generated metadata when present, but it does not regenerate AI context markdown shards.

### Other Commands

The following commands are stubbed:

- `aictx clean --oci --run-id <id>` — prints a stub message and does not perform cleanup.
- `aictx public-docs update --project <path> --scope <scope> --write <mode>` — prints "not yet implemented" and exits with code 1.
- `aictx run --scope changed` — accepted by the CLI but the pipeline raises `NotImplementedError`.

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
- Verifier tests covering missing lockfiles, successful verification after init, source changes, deleted files, and unsupported schema.
- Phase 1 run tests covering config loading, staged patch output, applied scaffold output, and generated lockfile/source linkage.

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

### Secrets are detected in real files but not in test fixtures

The scanner uses regex-based detection, but it skips detector source/examples in `src/aictx/scan/secrets.py`, test/fixture-style paths, and lines intentionally annotated with `aictx-secret-ignore` to avoid false positives. If findings appear, they should now be treated as more likely to be actionable project files rather than intentional examples. Real secrets should be removed, not suppressed.

### Why is `.pytest-tmp` ignored?

The repository excludes `.pytest-tmp` from test discovery, linting, and repository scanning so transient local test artifacts do not create drift or false positives.

### `aictx run` does not support the mode I passed

Only local `setup-context` is implemented. Any other mode or execution target currently exits with an error.

### `aictx verify --strict` fails immediately in a fresh clone

This is expected if `docs/AIprojectcontext/context.lock.json` has not been created or committed yet. Run `uv run aictx init --project .`, then commit the resulting lockfile.

If you want the generated AI context scaffold instead of a baseline lock only, run `uv run aictx run --project . --mode setup-context --execution local --write apply`. That command writes the generated context shards, `AGENTS.md`, and the generated `docs/AIprojectcontext/context.lock.json` into the repository.

## Repository Layout

See [`CODEMAP.md`](./CODEMAP.md) for a detailed file-by-file map.

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the system architecture and current limitations.

See [`../aictx_development_plan.md`](../aictx_development_plan.md) for the full roadmap.
