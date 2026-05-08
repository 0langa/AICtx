# AICtx Architecture

Codebase is source of truth.

## Core model

- local-first
- repo-targeted
- no auto-commit / auto-push
- generated changes are staged as files + unified diff patch
- current working execution = local only
- committed baseline = `docs/AIprojectcontext/context.lock.json`
- runtime artifacts = `.aictx/**` (local-only, ignored)
- non-dry model providers require explicit `--allow-ai`
- dirty apply allows context-source/generated output paths; unrelated dirty paths require config opt-in or `--allow-dirty`
- provider prompt transfer is guarded by local file safety and budget preflight

## Implemented layers

### CLI

`src/aictx/cli.py`

- `--version`
- `scan`
- `init`
- `run` (`setup-context`, `execution=local`, `scope=full|changed`, `write=patch|apply`)
- `verify --strict [--json]`
- `status [--json]`
- `clean` local run cleanup
- `public-docs update`
- `oci doctor`

### Scanner

`src/aictx/scan/`

- git root detection
- worktree status snapshot
- hard excludes + `.gitignore` + `.aictxignore`
- directory pruning before descent
- file classification
- generated context artifact detection (`docs/AIprojectcontext/**`, generated `AGENTS.md`)
- SHA-256 for eligible files
- high-confidence secret scan
- detector/test-fixture self-protection
- deterministic project classification
- inventory model output to `.aictx/runs/<run-id>/inventory.json`

### Git integration

`src/aictx/git/`

- `repo.py` git root detection
- `status.py` branch/head/dirty/tracked/untracked/modified/deleted/renamed
- `diff.py` unified diff against base ref

### Context pipeline

`src/aictx/context/`

Run order:

1. rescan repo
2. fail on secrets
3. block dirty apply when dirty paths are outside context-source/generated outputs
4. load config if present
5. compute changed files against existing lock
6. build deterministic plan, excluding generated context artifacts from source input
7. enforce model-transfer safety boundary
8. estimate input/output tokens and file budgets
9. create provider through guarded factory (`dry_run` default)
10. write safe provider metadata without prompt content
11. extract deterministic fact packs
12. write staged scaffold under `.aictx/runs/<run-id>/out/`
13. write `aictx.patch`
14. write `run-report.json`
15. if apply mode, copy staged files into repo

Generated targets:

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

Run artifacts:

- `inventory.json`
- `context-plan.json`
- `facts/*_facts.json`
- `coverage-report.json`
- `contradictions.json`
- `out/**`
- `aictx.patch`
- `provider-metadata.json`
- `run-report.json`

### Verification

`src/aictx/verify/`

Current verifier checks:

- lock exists
- schema supported
- source paths exist
- source hashes match
- generated paths exist
- generated hashes match
- strict mode requires expected generated context files
- strict mode verifies section source paths/hash links
- strict mode verifies generated `AGENTS.md` points to `docs/AIprojectcontext/ai-index.md`
- public-doc source changes mapped in lock
- detailed JSON report + next-command hint

Result codes in current architecture:

- `PASS`
- `FAIL_STALE_AI_CONTEXT`
- `FAIL_PUBLIC_DOCS_IMPACT`
- `FAIL_LOCK_MISMATCH`
- `FAIL_MISSING_SOURCE`
- `FAIL_UNSUPPORTED_SCHEMA`

Verifier remains deterministic/hash-based; no semantic freshness.

### Public docs

`src/aictx/public_docs/`

- maps public docs (`README.md`, `docs/**`, `documentation/**`) to source/manifest files
- stores map in `context.lock.json`
- context regeneration refreshes mapped source hashes
- `public-docs update` writes deterministic review artifacts and patches; it does not invent public-doc prose

### OCI readiness

`src/aictx/oci/doctor.py`

- checks local OCI SDK presence
- checks OCI config/profile presence
- checks compartment id from env/config
- no network calls, no remote mutation

## Safety behavior

- scanner never prints secret values
- symlinks skipped
- hard excludes block `.aictx/`, `.git/`, build outputs, credential files from inventory
- pipeline blocks when secrets found
- dirty-worktree apply gate blocks unplanned dirty paths
- model-transfer preflight blocks ignored, binary, generated, `.git`, `.aictx/runs`, cache/build, oversize, and secret-bearing files
- token/file-count/output budgets fail before provider creation
- non-dry providers require `--allow-ai`
- contradiction/coverage gating not enforced yet

## Lockfile behavior

`init` rebuilds source-side hashes from fresh scan.

If existing lockfile already contains generated metadata from prior `run --write apply`, preserve generated metadata while refreshing source verification state.

Generated context artifacts are tracked in `generated_files`, not `source_files`; `context.lock.json` is loaded as the verifier input and is not self-hashed as a generated file.

## Stubs / placeholders

- `context/agents_md.py` = static template generator
- `context/compressor.py` = pass-through stub
- contradiction report = deterministic empty placeholder
- coverage report = deterministic empty placeholder
- `verify/reports.py` = one-line placeholder
- `llm/oci_genai.py` = stub
- OCI object storage / remote job / cleanup = stubs

## Current limits

- `run`: local `setup-context` only; changed scope is targeted but still coarse at shard level
- `verify`: no semantic freshness
- `init`: no context shard generation
- `public-docs update`: deterministic review flow only; manual doc edits required
- `oci doctor`: local readiness only
- no CI workflow generation
- no Object Storage, remote jobs, Terraform, hosted service, or real OCI/AI provider calls
