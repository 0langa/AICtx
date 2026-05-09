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
- changed-scope detection recorded in run plans
- changed-scope targeted context refresh with unaffected shard preservation
- dirty-worktree gate for `--write apply`
- `status --json`
- `verify --json` detailed reports + next-command hints
- deterministic public-doc source map + review patch generation
- public-doc source hashes refresh during context regeneration
- deterministic public-doc review/apply artifact behavior; no prose rewrite
- safe local `clean`
- guarded `apply_patch` helper using `git apply --check`
- guarded provider factory; non-dry providers require `--allow-ai`
- model-transfer safety boundary before provider creation
- input/output/file-count/file-size budget preflight
- provider metadata and run report artifacts without prompt content
- `oci doctor` local readiness check
- test coverage for CLI/scanner/verify/Phase1 run
- lockfile metadata preservation in `init`
- false-positive hardening for secret detector source/examples + test/fixture paths
- `.pytest-tmp` hardening
- generated context artifact detection and source-selection exclusion
- repo-relative fact source paths with known lock section source hashes
- strict generated-context structure checks in `verify --strict`
- preservation of unmanaged second-level sections in generated `AGENTS.md`
- deterministic OCI snapshot/bundle creation, verification, upload/download, cleanup, and remote job orchestration
- optional hook scripts plus verifier/release GitHub workflows
- run-report timing/entropy instrumentation and hostile-repo fixtures

### Current limitations

- `run --scope changed` is targeted at generated-shard level, not fine-grained within large shards
- `verify` remains deterministic and does not perform semantic freshness checks
- `init` does not generate context shards
- contradiction/coverage reports are placeholder JSON
- `compressor.py` deterministic de-dup/truncate only; not semantic compression
- public-doc updates are review artifacts only; manual content edits required
- `llm/oci_genai.py` runtime stub; only `dry_run` calls succeed
- no live OCI tenancy proof in CI and no full cross-platform install matrix proof yet
