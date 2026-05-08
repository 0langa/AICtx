# AICtx Architecture

This document describes the current and planned architecture of AICtx. The codebase is the source of truth; treat claims here as correct only to the extent they match the code.

## Local-First Design

AICtx is designed to run locally against a Git repository. It never auto-commits, auto-pushes, or silently overwrites user content. Generated changes are produced as reviewable patches by default. OCI-backed execution is planned as an optional future mode; the currently implemented run behavior is local-only.

The committed baseline file is `docs/AIprojectcontext/context.lock.json`. Runtime scan artifacts under `.aictx/` are local-only and ignored.

## Implemented Layers

### CLI Layer (`src/aictx/cli.py`)

Typer-based command surface. Commands:

- `aictx --version` — prints version.
- `aictx scan --project <path>` — scans repository, prints summary, writes inventory JSON.
- `aictx init --project <path>` — creates or refreshes `docs/AIprojectcontext/context.lock.json`, preserving generated lock metadata when present, and creates `.aictxignore` if missing.
- `aictx run --project <path> --mode setup-context --execution local --scope <scope> --write <mode>` — implemented local Phase 1 pipeline.
- `aictx verify --project <path> --strict` — hash-only verifier MVP for baseline lockfile validation.
- `aictx clean --oci --run-id <id>` — **stubbed**.
- `aictx public-docs update --project <path> --scope <scope> --write <mode>` — **stubbed**; exits with code 1.

### Scanner Pipeline (`src/aictx/scan/`)

Fully implemented deterministic pipeline:

1. **Git root detection** — `git rev-parse --show-toplevel`.
2. **Worktree status** — branch, HEAD commit, dirty flag, tracked/untracked/modified/deleted/renamed files serialized into inventory.
3. **Ignore matching** — built-in hard excludes (`.git`, `.aictx`, `.pytest-tmp`, `node_modules`, build artifacts), `.gitignore`, and `.aictxignore`.
4. **Directory pruning** — ignored directories are skipped before descending.
5. **File classification** — binary check, language detection by extension, manifest detection, test detection, doc detection.
6. **SHA-256 hashing** — skipped for binaries and files over 250KB.
7. **Secret scanning** — regex-based high-confidence detectors (private keys, OCI API keys, GitHub tokens, generic API keys, connection strings, `.env` secrets).
	Detector source/examples under `src/aictx/scan/secrets.py` and test/fixture-style paths are skipped to avoid self-matching false positives.
8. **Project classification** — deterministic heuristics for Python, C#, Node, Rust, Go, and docs-heavy repos.
9. **Inventory model** — Pydantic `RepositoryInventory` written to `.aictx/runs/<run-id>/inventory.json`.

### Git Integration (`src/aictx/git/`)

- `repo.py` — `find_git_root()` using `git` subprocess.
- `status.py` — `WorktreeStatus` class parsing `git branch`, `rev-parse HEAD`, `status --short`, `ls-files`.
- `diff.py` — `get_git_diff()` returning unified diff against a base ref.

### Context Generation Pipeline (`src/aictx/context/`)

Implemented local Phase 1 flow:

1. Rescan repository and stop on detected secrets.
2. Load `.aictx/config.toml` if present.
3. Build a deterministic file-selection plan.
4. Estimate token cost and fail if over configured input budget.
5. Use the dry-run provider to build deterministic fact-pack summaries.
6. Generate AI context markdown shards plus a generated `AGENTS.md`.
7. Build `context.lock.json` with source and generated file linkage.
8. Write staged outputs under `.aictx/runs/<run-id>/out/` and create `aictx.patch`.
9. Optionally apply staged outputs into the repository when `--write apply` is used.

Current generated files:

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

### Safety Model

Safety measures implemented in the scanner:

- Hard excludes prevent `.aictx/`, `.git/`, build outputs, and credential files from entering inventory.
- Symlinks are skipped.
- Secret findings are reported by path and detector name, not by printing the secret value.
- The local run pipeline blocks generation when scanner secret findings are present.
- Dirty-worktree blocking and contradiction/coverage failure gates are not implemented yet, even though configuration fields exist for future enforcement.

### Lockfile Refresh Behavior

`aictx init` rebuilds tracked source hashes from the current repository scan. If the existing lockfile already contains generated-file metadata from `aictx run --write apply`, `init` preserves that generated metadata while refreshing source-side verification state.

## Stubbed / Planned Architecture

### Remaining Stubbed / Planned Context Work

- `agents_md.py` — generates a static `AGENTS.md` template.
- `compressor.py` — stubbed.
- Planned additions: contradiction reports, coverage reports, richer source spans, refresh prioritization, and semantic compression.

### Verification (`src/aictx/verify/`)

- `verifier.py` — validates baseline `context.lock.json` deterministically using source and generated file hashes.
- `impact.py`, `reports.py` — stubbed.
- Current scope: hash-only file-state verification.
- Planned: source-to-context impact mapping, semantic stale detection, and public-docs impact checks.

Current failure mappings:

- missing lockfile → `FAIL_LOCK_MISMATCH`
- unsupported schema → `FAIL_UNSUPPORTED_SCHEMA`
- missing locked source path → `FAIL_MISSING_SOURCE`
- source hash mismatch → `FAIL_STALE_AI_CONTEXT`
- generated file mismatch → `FAIL_LOCK_MISMATCH`

### Public Docs Management (`src/aictx/public_docs/`)

All modules stubbed. Planned to map public docs to code areas and generate targeted patches.

### LLM Providers (`src/aictx/llm/`)

- `dry_run.py` — implemented for local testing.
- `oci_genai.py` — stubbed; constructor stores config but `chat()` raises `NotImplementedError`.

### OCI Integration (`src/aictx/oci/`)

All modules stubbed. Planned for optional remote execution, Object Storage exchange, and remote job management.

### Configuration (`src/aictx/config.py`)

Pydantic models exist for all config sections. `load_config()` reads `.aictx/config.toml` when present and falls back to defaults when missing.

## Data Models

Pydantic v2 models live in `src/aictx/models/`:

- `inventory.py` — `FileEntry`, `SecretFinding`, `RepositoryInventory`
- `context_lock.py` — `ContextLock`, `GeneratedFileEntry`, `SourceFileEntry`, `SectionEntry`, `PublicDocsMapEntry`, `ChangeImpactMapEntry`
- `docs_map.py` — `DocsMap`, `DocsMapEntry`
- `run_report.py` — `RunReport`

## Current Limitations

- `aictx run` only supports local `setup-context`; other modes and OCI execution are not implemented.
- `aictx verify` only verifies deterministic file hashes; it does not perform semantic freshness checks yet.
- `aictx init` refreshes the verification lockfile only; it does not generate AI context markdown shards.
- `aictx public-docs update` is a placeholder.
- OCI model provider is not wired to a real endpoint.
- Patch application (`apply_patch`) is stubbed.
- No CI workflow generation yet.
- No contradiction/coverage JSON reports or semantic freshness checks are implemented yet.
