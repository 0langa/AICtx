# Changelog

## Unreleased

### Added

- CLI skeleton with Typer (`init`, `scan`, `run`, `verify`, `clean`, `public-docs`).
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

### Known Limitations

- `clean` and `public-docs update` commands are stubbed and do not perform meaningful work.
- `run` currently supports only local `setup-context`; contradiction reports, coverage reports, semantic verification, and OCI execution are not implemented.
- `init` creates only a baseline file-state lockfile; it does not generate AI context shards.
- `verify` is hash-only and deterministic; it does not perform semantic freshness or public-docs impact validation yet.
- `.aictx/runs/`, `.aictx/cache/`, and `.aictx/tmp/` remain local runtime artifacts and are not part of the committed verification baseline.
- OCI Generative AI provider is not yet implemented.
- Context compression is stubbed.
- Public docs mapper, updater, and patcher are stubbed.
- OCI Object Storage, remote jobs, and cleanup are stubbed.
- Patch application is not implemented.
