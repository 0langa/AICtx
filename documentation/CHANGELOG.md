# Changelog

## Unreleased

### Implemented

- Typer CLI skeleton: `init`, `scan`, `run`, `verify`, `clean`, `public-docs update`
- deterministic repo scanner
- `init` baseline lockfile generation / refresh
- local Phase 1 context pipeline
- `verify --strict` hash-only verifier MVP
- git root + status integration
- ignore matching via hard excludes + `.gitignore` + `.aictxignore`
- project/file classification
- regex-based high-confidence secret scanning
- inventory / lockfile / run-report models (Pydantic v2)
- dry-run LLM provider
- context scaffold + generated `AGENTS.md`
- run artifact output + staged patch output
- apply-by-copy mode
- test coverage for CLI/scanner/verify/Phase1 run
- lockfile metadata preservation in `init`
- false-positive hardening for secret detector source/examples + test/fixture paths
- `.pytest-tmp` hardening

### Current limitations

- `clean` stub
- `public-docs update` stub
- `run --scope changed` not implemented
- `verify` hash-only
- `init` does not generate context shards
- contradiction/coverage reports are placeholder JSON
- `apply_patch` helper is no-op stub
- `compressor.py` pass-through stub
- `verify/impact.py` empty-list stub
- `verify/reports.py` one-line placeholder
- `public_docs/*` stubs
- `oci/*` stubs
- `llm/oci_genai.py` stub; only `dry_run` works