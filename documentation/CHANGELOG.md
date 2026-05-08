# Changelog

## Unreleased

### Added

- CLI skeleton with Typer (`init`, `scan`, `run`, `verify`, `clean`, and `public-docs update`).
- `aictx scan` — full repository scanner that produces a deterministic inventory.
- `aictx init` MVP — creates `docs/AIprojectcontext/context.lock.json` baseline and `.aictxignore` if missing.
- `aictx run` local Phase 1 — deterministic planning, fact extraction, AI context scaffold generation, staged patch output, optional apply mode, and generated `AGENTS.md`.
- `aictx verify --strict` MVP — deterministic hash-only verifier for baseline file-state validation.
- Git integration — root detection, branch/head/dirty status, tracked/untracked/modified/deleted/renamed file lists.
- Structured Git status snapshot serialized in scanner inventory.
- Ignore matcher — built-in hard excludes plus `.gitignore` and `.aictxignore` support via `pathspec`.
- Project classification — deterministic heuristics for Python, C#/.NET, Node, Rust, Go, and docs-heavy repositories.
- File classification — language detection by extension, manifest detection, test detection, doc detection, binary detection.
- Secret scanning — regex-based high-confidence detectors for private keys, OCI API keys, GitHub tokens, generic API keys, connection strings, and `.env` secrets.
- Inventory model (`RepositoryInventory`, `FileEntry`, `SecretFinding`) with Pydantic v2, written to `.aictx/runs/<run-id>/inventory.json`.
- LLM provider interface (`ModelProvider`) with dry-run implementation.
- Pydantic configuration models (`AictxConfig`, `ProjectConfig`, `ExecutionConfig`, `LimitsConfig`, `LLMConfig`).
- Context lockfile model (`ContextLock`) and I/O helpers.
- Baseline lockfile bootstrap from scanner inventory.
- Versioned baseline `docs/AIprojectcontext/context.lock.json` for cross-clone verification.
- `AGENTS.md` template generator.
- `.aictx/config.toml` loading.
- File I/O helpers (`safe_write`, `read_text`), JSONL helpers, and unified diff helper.
- Exception hierarchy (`AictxError`, `SafetyError`, `ConfigError`, `ScanError`, `SecretScanError`, `TokenBudgetExceededError`, `VerificationError`, `RemoteJobError`).
- Unit and integration tests covering CLI version, scanner utilities, secret scanning, and scan hardening.
- Lockfile refresh behavior in `init` that preserves generated metadata while updating source verification state.
- Secret scan false-positive hardening for detector source/examples and test/fixture-style paths.
- Repository-local pytest temp directory hardening via `.pytest-tmp` exclusions for pytest, Ruff, and scanner inventory.

### Known Limitations

- `clean` prints a stub message and does not perform cleanup.
- `public-docs update` prints "not yet implemented" and exits with code 1.
- `run` supports only `--mode setup-context --execution local --scope full`. `--scope changed` and any other mode or execution target raise an error.
- Contradiction and coverage reports are deterministic empty JSON placeholders; they are not populated with real analysis yet.
- `init` refreshes `context.lock.json` only; it does not generate AI context markdown shards.
- `verify` is hash-only and deterministic; semantic freshness and public-docs impact validation are not implemented yet.
- `.aictx/runs/`, `.aictx/cache/`, and `.aictx/tmp/` remain local runtime artifacts and are not part of the committed verification baseline.
- OCI Generative AI provider (`oci_genai.py`) is stubbed; `chat()` raises `NotImplementedError`. The only working provider is `dry_run`.
- Context compression (`compressor.py`) is a pass-through stub.
- Change-impact mapping (`verify/impact.py`) returns empty lists.
- Validation report writer (`verify/reports.py`) writes a one-line placeholder.
- Public docs mapper, updater, and patcher are stubs.
- OCI Object Storage, remote jobs, and cleanup are stubs.
- `apply_patch` is a no-op stub; `--write apply` copies staged files into the repo instead of replaying patches.
