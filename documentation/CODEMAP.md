# AICtx Code Map

This file maps the repository layout to help future agents and contributors navigate the codebase.

## Package Layout

    src/aictx/                 — Main Python package
      __init__.py              — Package version (0.1.0)
      cli.py                   — Typer CLI entry point (all commands)
      config.py                — Pydantic configuration models (stubbed loading)
      errors.py                — Exception hierarchy
      logging.py               — Rich-based logging setup

      git/                     — Git operations
        repo.py                — Git root detection
        status.py              — Worktree status (branch, head, dirty, file lists)
        diff.py                — Unified diff against a base ref

      scan/                    — Repository scanning
        scanner.py             — Full repository walk, inventory build, secret scan
        classify.py            — Deterministic project classification
        ignore.py              — Built-in, .gitignore, and .aictxignore matching
        secrets.py             — Regex-based secret detection

      models/                  — Pydantic data models
        inventory.py           — FileEntry, SecretFinding, RepositoryInventory
        context_lock.py        — ContextLock and sub-entry models
        docs_map.py            — DocsMap and DocsMapEntry
        run_report.py          — RunReport model

      llm/                     — Model provider interface
        base.py                — ModelProvider ABC, ChatRequest, ChatResponse
        dry_run.py             — Local test provider (implemented)
        oci_genai.py           — OCI Generative AI provider (stubbed)

      context/                 — Context generation pipeline (mostly stubbed)
        agents_md.py           — AGENTS.md template generator
        planner.py             — Context planning (stubbed)
        fact_extractor.py      — Structured fact extraction (stubbed)
        writer.py              — AI context scaffold writer (stubbed)
        compressor.py          — Text compression (stubbed)
        lockfile.py            — context.lock.json I/O helpers

      verify/                  — Freshness verification (mostly stubbed)
        verifier.py            — Strict verifier (returns PASS stub)
        hashes.py              — SHA-256 helpers for lockfile verification
        impact.py              — Change-impact mapping (stubbed)
        reports.py             — Validation report writer (stubbed)

      public_docs/             — Public docs management (all stubbed)
        mapper.py              — Public docs map builder
        updater.py             — Public docs update mode
        patcher.py             — Doc patch generation

      oci/                     — OCI integration (all stubbed)
        config.py              — OCI config loading from env/file
        object_storage.py      — Upload/download stubs
        remote_job.py          — Remote job submit/wait stubs
        cleanup.py             — Artifact cleanup stub

      io/                      — File I/O utilities
        files.py               — safe_write and read_text helpers
        jsonl.py               — JSON Lines read/write
        patches.py             — Unified diff creation, patch application stub

    tests/
      conftest.py              — pytest configuration (sys.path setup for fixtures)
      fixtures/
        git_repos.py           — Dynamic git repo fixture helper
      unit/
        test_cli.py            — CLI version test
        test_scanner.py        — Scanner utility and secret-scan tests
        test_scan_integration.py — Integration tests for scan hardening

## Generated / Runtime Directories

    .aictx/                  — Runtime directory (excluded from inventory)
      runs/<run-id>/         — Per-run outputs (inventory.json)
      config.toml            — Planned config file (not yet parsed)
    .aictxignore             — Custom ignore patterns
    docs/AIprojectcontext/   — Planned AI context scaffold output (not yet created)

## Config Files

    pyproject.toml           — Package metadata, dependencies, tool configs
    uv.lock                  — uv lockfile
    .gitignore               — Standard git ignore

## Important Conventions

- Python 3.12+ with `from __future__ import annotations` in every module.
- Pydantic v2 for all data models.
- Direct `git` subprocess calls for repository state.
- `pathspec` for ignore-pattern matching.
