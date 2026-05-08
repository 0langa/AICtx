# AICtx Architecture

This document describes the current and planned architecture of AICtx. The codebase is the source of truth; treat claims here as correct only to the extent they match the code.

## Local-First Design

AICtx is designed to run locally against a Git repository. It never auto-commits, auto-pushes, or silently overwrites user content. Generated changes are produced as reviewable patches by default. OCI usage is optional and per-command.

## Implemented Layers

### CLI Layer (`src/aictx/cli.py`)

Typer-based command surface. Commands:

- `aictx --version` — prints version.
- `aictx scan --project <path>` — scans repository, prints summary, writes inventory JSON.
- `aictx init --project <path>` — **stubbed**; prints "not yet implemented".
- `aictx run --project <path> --mode <mode> --execution <target> --write <mode>` — **stubbed**.
- `aictx verify --project <path> --strict` — **stubbed**; prints "not yet implemented".
- `aictx clean --oci --run-id <id>` — **stubbed**.
- `aictx public-docs update --project <path> --scope <scope> --write <mode>` — **stubbed**; exits with code 1.

### Scanner Pipeline (`src/aictx/scan/`)

Fully implemented deterministic pipeline:

1. **Git root detection** — `git rev-parse --show-toplevel`.
2. **Worktree status** — branch, HEAD commit, dirty flag, tracked/untracked/modified/deleted/renamed files.
3. **Ignore matching** — built-in hard excludes (`.git`, `.aictx`, `node_modules`, build artifacts), `.gitignore`, and `.aictxignore`.
4. **Directory pruning** — ignored directories are skipped before descending.
5. **File classification** — binary check, language detection by extension, manifest detection, test detection, doc detection.
6. **SHA-256 hashing** — skipped for binaries and files over 250KB.
7. **Secret scanning** — regex-based high-confidence detectors (private keys, OCI API keys, GitHub tokens, generic API keys, connection strings, `.env` secrets).
8. **Project classification** — deterministic heuristics for Python, C#, Node, Rust, Go, and docs-heavy repos.
9. **Inventory model** — Pydantic `RepositoryInventory` written to `.aictx/runs/<run-id>/inventory.json`.

### Git Integration (`src/aictx/git/`)

- `repo.py` — `find_git_root()` using `git` subprocess.
- `status.py` — `WorktreeStatus` class parsing `git branch`, `rev-parse HEAD`, `status --short`, `ls-files`.
- `diff.py` — `get_git_diff()` returning unified diff against a base ref.

### Safety Model

Safety measures implemented in the scanner:

- Hard excludes prevent `.aictx/`, `.git/`, build outputs, and credential files from entering inventory.
- Symlinks are skipped.
- Secret findings are reported by path and detector name, not by printing the secret value.
- Higher-level safety gating (blocking model calls on secret detection, blocking apply on dirty worktree) is planned for the `run` and `verify` commands.

## Stubbed / Planned Architecture

### Context Generation Pipeline (`src/aictx/context/`)

- `agents_md.py` — generates a static `AGENTS.md` template.
- `planner.py`, `fact_extractor.py`, `writer.py`, `compressor.py` — all stubbed.
- Planned flow: inventory -> plan -> facts -> scaffold -> `AGENTS.md`.

### Verification (`src/aictx/verify/`)

- `verifier.py` — returns `"PASS"` unconditionally.
- `impact.py`, `reports.py` — stubbed.
- Planned: hash checks, source-to-context impact mapping, stale detection.

### Public Docs Management (`src/aictx/public_docs/`)

All modules stubbed. Planned to map public docs to code areas and generate targeted patches.

### LLM Providers (`src/aictx/llm/`)

- `dry_run.py` — implemented for local testing.
- `oci_genai.py` — stubbed; constructor stores config but `chat()` raises `NotImplementedError`.

### OCI Integration (`src/aictx/oci/`)

All modules stubbed. Planned for optional remote execution, Object Storage exchange, and remote job management.

### Configuration (`src/aictx/config.py`)

Pydantic models exist for all config sections. `load_config()` returns defaults; TOML parsing is not yet implemented.

## Data Models

Pydantic v2 models live in `src/aictx/models/`:

- `inventory.py` — `FileEntry`, `SecretFinding`, `RepositoryInventory`
- `context_lock.py` — `ContextLock`, `GeneratedFileEntry`, `SourceFileEntry`, `SectionEntry`, `PublicDocsMapEntry`, `ChangeImpactMapEntry`
- `docs_map.py` — `DocsMap`, `DocsMapEntry`
- `run_report.py` — `RunReport`

## Current Limitations

- `aictx run` does not generate context.
- `aictx verify` does not verify freshness.
- `aictx public-docs update` is a placeholder.
- OCI model provider is not wired to a real endpoint.
- Config TOML parsing is not implemented.
- Patch application (`apply_patch`) is stubbed.
- No CI workflow generation yet.
- No higher-level command gating (e.g., blocking model calls on secret detection) is implemented yet.
