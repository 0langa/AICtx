# AICtx Code Map

This file maps the repository layout to help future agents and contributors navigate the codebase.

## Package Layout

    src/aictx/                 — Main Python package
      __init__.py              — Package version (0.1.0)
      cli.py                   — Typer CLI entry point (all commands)
      config.py                — Pydantic configuration models and `.aictx/config.toml` loading
      errors.py                — Exception hierarchy
      logging.py               — Rich-based logging setup

      git/                     — Git operations
        repo.py                — Git root detection via `git rev-parse --show-toplevel`
        status.py              — Worktree status (branch, head, dirty, tracked/untracked/modified/deleted/renamed)
        diff.py                — Unified diff against a base ref via `git diff`

      scan/                    — Repository scanning (fully implemented)
        scanner.py             — Full repository walk, inventory build, secret scan
        classify.py            — Deterministic project classification
        ignore.py              — Built-in hard excludes, `.gitignore`, and `.aictxignore` matching via `pathspec`
        secrets.py             — Regex-based secret detection with inline suppression (`aictx-secret-ignore`) and self-protection

      models/                  — Pydantic v2 data models
        inventory.py           — FileEntry, SecretFinding, GitStatusSnapshot, RepositoryInventory
        context_lock.py        — ContextLock and sub-entry models (GeneratedFileEntry, SourceFileEntry, SectionEntry, etc.)
        docs_map.py            — DocsMap and DocsMapEntry
        run_report.py          — RunReport model

      llm/                     — Model provider interface
        base.py                — ModelProvider ABC, ChatRequest, ChatResponse
        dry_run.py             — Local test provider (implemented and used by the run pipeline)
        oci_genai.py           — OCI Generative AI provider (stubbed; `chat()` raises NotImplementedError)

      context/                 — Context generation pipeline (local Phase 1 implemented)
        agents_md.py           — Static `AGENTS.md` template generator
        pipeline.py            — Local Phase 1 run orchestration, artifact staging, patch creation, apply via file copy
        planner.py             — Deterministic file-selection planning with token-cost estimation
        fact_extractor.py      — Deterministic structured fact extraction using provider calls
        writer.py              — AI context scaffold writer and generated lock builder
        compressor.py          — Text compression (pass-through stub)
        lockfile.py            — Baseline `context.lock.json` builder and I/O helpers

      verify/                  — Freshness verification
        verifier.py            — Hash-only strict verifier MVP (implemented)
        hashes.py              — SHA-256 helpers for lockfile verification (implemented)
        impact.py              — Change-impact mapping (stubbed; returns empty lists)
        reports.py             — Validation report writer (stubbed; writes one-line placeholder)

      public_docs/             — Public docs management (all stubbed)
        mapper.py              — Public docs map builder stub
        updater.py             — Public docs update mode stub
        patcher.py             — Doc patch generation stub

      oci/                     — OCI integration (all stubbed)
        config.py              — OCI config loading from env/file stub
        object_storage.py      — Upload/download stub
        remote_job.py          — Remote job submit/wait stub
        cleanup.py             — Artifact cleanup stub

      io/                      — File I/O utilities
        files.py               — `safe_write` and `read_text` helpers
        jsonl.py               — JSON Lines read/write helpers
        patches.py             — `make_unified_diff` (implemented); `apply_patch` (no-op stub)

    tests/
      conftest.py              — pytest bootstrap that injects the repo root into `sys.path`
      fixtures/
        git_repos.py           — Dynamic git repo fixture helper
      unit/
        test_cli.py            — CLI version test, verify command exit tests
        test_scanner.py        — Scanner utility and secret-scan tests
        test_scan_integration.py — Integration-style tests for scan hardening and git-status serialization
        test_verify.py          — Init and verifier behavior tests
        test_run_phase1.py      — Phase 1 local context generation tests

## Generated / Runtime Directories

    .aictx/                  — Runtime directory (excluded from inventory)
      runs/<run-id>/         — Per-run outputs (inventory.json, staged context, patch files)
      cache/                 — Runtime cache (ignored)
      tmp/                   — Runtime temp files (ignored)
    .aictxignore             — Custom ignore patterns
    docs/AIprojectcontext/   — Generated AI context shards plus committed `context.lock.json`

## Config Files

    pyproject.toml           — Package metadata, dependencies, tool configs
    uv.lock                  — uv lockfile
    .gitignore               — Standard git ignore

## Important Conventions

- Python 3.12+ with `from __future__ import annotations` in every module.
- Pydantic v2 for all data models.
- Direct `git` subprocess calls for repository state.
- `pathspec` for ignore-pattern matching.
