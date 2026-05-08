# AICtx Code Map

## Source tree

    src/aictx/
      __init__.py      package version
      cli.py           Typer command surface
      config.py        config models + `.aictx/config.toml` load
      errors.py        exception hierarchy
      logging.py       Rich logging

      git/
        repo.py        git root detect
        status.py      worktree status snapshot
        diff.py        unified diff against base ref

      scan/
        scanner.py     repo walk + inventory + generated-artifact detection + secret scan
        classify.py    deterministic project classification
        ignore.py      hard excludes + `.gitignore` + `.aictxignore`
        secrets.py     regex secret detection + inline suppression + self-protection

      models/
        inventory.py   inventory models
        context_lock.py lockfile models
        docs_map.py    docs map models
        run_report.py  run report model

      llm/
        base.py        provider ABC + request/response types
        dry_run.py     only working provider
        oci_genai.py   stub; `chat()` raises `NotImplementedError`

      context/
        agents_md.py   static `AGENTS.md` generator
        pipeline.py    local Phase 1 run orchestration
        planner.py     deterministic file-selection plan + token estimate
        fact_extractor.py deterministic fact extraction via provider
        writer.py      context scaffold + generated lock builder
        compressor.py  pass-through stub
        lockfile.py    baseline lock build/load/write

      verify/
        verifier.py    strict verifier for hashes + generated context structure
        hashes.py      SHA-256 helpers
        impact.py      stub; empty change-impact mapping
        reports.py     stub; placeholder validation report

      public_docs/
        mapper.py      stub
        updater.py     stub
        patcher.py     stub

      oci/
        config.py      stub
        object_storage.py stub
        remote_job.py  stub
        cleanup.py     stub

      io/
        files.py       `safe_write`, `read_text`
        jsonl.py       JSONL helpers
        patches.py     `make_unified_diff`; `apply_patch` no-op stub

## Tests

    tests/
      conftest.py              repo-root path bootstrap
      fixtures/git_repos.py    temp git repo fixture helper
      unit/test_cli.py         CLI/version tests
      unit/test_scanner.py     scanner utility + secret tests
      unit/test_scan_integration.py integration scanner tests
      unit/test_verify.py      init + verifier tests
      unit/test_run_phase1.py  local Phase 1 pipeline tests

## Runtime / generated

    .aictx/
      runs/<run-id>/   per-run inventory / facts / staged out / patch
      cache/           runtime cache
      tmp/             runtime temp

    .aictxignore       custom ignore patterns
    docs/AIprojectcontext/ generated context shards + committed `context.lock.json`

## Repo config

    pyproject.toml     package metadata + tool config
    uv.lock            uv lockfile
    .gitignore         git ignore

## Conventions

- Python 3.12+
- `from __future__ import annotations` in modules
- Pydantic v2 models
- direct `git` subprocess usage
- `pathspec` ignore matching
