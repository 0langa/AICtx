# Changelog

## Unreleased

### Added

- CLI skeleton with Typer (`init`, `scan`, `run`, `verify`, `clean`, `public-docs`).
- `aictx scan` — full repository scanner that produces a deterministic inventory.
- Git integration — root detection, branch/head/dirty status, tracked/untracked/modified/deleted/renamed file lists.
- Ignore matcher — built-in hard excludes plus `.gitignore` and `.aictxignore` support via `pathspec`.
- Project classification — deterministic heuristics for Python, C#/.NET, Node, Rust, Go, and docs-heavy repositories.
- File classification — language detection by extension, manifest detection, test detection, doc detection, binary detection.
- Secret scanning — regex-based high-confidence detectors for private keys, OCI API keys, GitHub tokens, generic API keys, connection strings, and `.env` secrets.
- Inventory model (`RepositoryInventory`, `FileEntry`, `SecretFinding`) with Pydantic v2, written to `.aictx/runs/<run-id>/inventory.json`.
- LLM provider interface (`ModelProvider`) with dry-run implementation.
- Pydantic configuration models (`AictxConfig`, `ProjectConfig`, `ExecutionConfig`, `LimitsConfig`, `LLMConfig`).
- Context lockfile model (`ContextLock`) and I/O helpers.
- `AGENTS.md` template generator.
- File I/O helpers (`safe_write`, `read_text`), JSONL helpers, and unified diff helper.
- Exception hierarchy (`AictxError`, `SafetyError`, `ConfigError`, `ScanError`, `SecretScanError`, `TokenBudgetExceededError`, `VerificationError`, `RemoteJobError`).
- Unit and integration tests covering CLI version, scanner utilities, secret scanning, and scan hardening.

### Known Limitations

- `init`, `run`, `verify`, `clean`, and `public-docs update` commands are stubbed and do not perform meaningful work.
- OCI Generative AI provider is not yet implemented.
- Context planning, fact extraction, scaffold writing, and compression are stubbed.
- The strict verifier always returns `PASS`.
- Public docs mapper, updater, and patcher are stubbed.
- OCI Object Storage, remote jobs, and cleanup are stubbed.
- Configuration TOML parsing is not implemented; defaults are always used.
- Patch application is not implemented.
