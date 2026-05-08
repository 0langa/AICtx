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

## Implemented layers

### CLI

`src/aictx/cli.py`

- `--version`
- `scan`
- `init`
- `run` (`setup-context`, `execution=local`, `scope=full`, `write=patch|apply`)
- `verify --strict`
- `clean` stub
- `public-docs update` stub

### Scanner

`src/aictx/scan/`

- git root detection
- worktree status snapshot
- hard excludes + `.gitignore` + `.aictxignore`
- directory pruning before descent
- file classification
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
3. load config if present
4. build deterministic plan
5. estimate token cost
6. use `DryRunProvider`
7. extract deterministic fact packs
8. write staged scaffold under `.aictx/runs/<run-id>/out/`
9. write `aictx.patch`
10. if apply mode, copy staged files into repo

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

### Verification

`src/aictx/verify/`

Current verifier checks:

- lock exists
- schema supported
- source paths exist
- source hashes match
- generated paths exist
- generated hashes match

Result codes in current architecture:

- `PASS`
- `FAIL_STALE_AI_CONTEXT`
- `FAIL_PUBLIC_DOCS_IMPACT`
- `FAIL_LOCK_MISMATCH`
- `FAIL_MISSING_SOURCE`
- `FAIL_UNSUPPORTED_SCHEMA`

Only hash-based outcomes are actually implemented now.

## Safety behavior

- scanner never prints secret values
- symlinks skipped
- hard excludes block `.aictx/`, `.git/`, build outputs, credential files from inventory
- pipeline blocks when secrets found
- dirty-worktree gating not enforced yet
- contradiction/coverage gating not enforced yet

## Lockfile behavior

`init` rebuilds source-side hashes from fresh scan.

If existing lockfile already contains generated metadata from prior `run --write apply`, preserve generated metadata while refreshing source verification state.

## Stubs / placeholders

- `context/agents_md.py` = static template generator
- `context/compressor.py` = pass-through stub
- contradiction report = deterministic empty placeholder
- coverage report = deterministic empty placeholder
- `verify/impact.py` = empty-list stub
- `verify/reports.py` = one-line placeholder
- `public_docs/*` = stubs
- `llm/oci_genai.py` = stub
- `oci/*` = stubs
- `io/patches.apply_patch` = no-op stub

## Current limits

- `run`: local `setup-context` + `scope=full` only
- `verify`: no semantic freshness, no public-docs impact validation
- `init`: no context shard generation
- `clean`: no cleanup
- `public-docs update`: not implemented
- no CI workflow generation