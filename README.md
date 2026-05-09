# AICtx

Local-first CLI for low-token AI-agent repo context.

## Status

Production-hardening in progress.

Implemented:

- `scan`
- `init`
- `run --mode setup-context --execution local --scope full --write patch|apply`
- `run --mode setup-context --execution local --scope changed --write patch|apply`
- `verify --strict`
- `verify --strict --json`
- `status --json`
- `public-docs update --scope changed|full --write patch|apply`
- `clean --run-id <id>` / `clean --keep-runs <n> --yes`
- `oci doctor --json`
- `snapshot create` / `snapshot verify`
- `oci capabilities`
- `oci upload-snapshot` / `oci download-result`
- `oci estimate`
- deterministic scanner
- baseline lockfile bootstrap
- deterministic verifier MVP
- strict generated-context structure checks
- structured verification reports + next-command hints
- local Phase 1 context pipeline
- dry-run provider
- provider factory; non-dry providers require `--allow-ai`
- generated context scaffold + `AGENTS.md`
- generated artifact isolation during scan/planning
- patch output + apply-by-copy
- safe patch apply helper with `git apply --check`
- targeted changed-scope refresh for impacted context shards
- deterministic public-doc impact review artifacts
- model-transfer safety boundary before any provider call
- input/output/file-count/file-size budget preflight
- provider metadata + run-report artifacts without prompt content
- dirty-worktree apply gate for unplanned paths; context-source/output paths are allowed
- tests + Ruff + mypy + pytest setup

Still partial/not implemented:

- semantic freshness verification (deferred: post-v1)
- fully proven live OCI execution in automation (deferred: post-v1)
- automated public-doc prose rewriting (deferred: post-v1)

Install matrix validation runs via `.github/workflows/install-matrix.yml`.

## Install

Python 3.12+.

```bash
git clone https://github.com/0langa/AICtx.git
cd AICtx
uv sync --extra dev
# or
pip install -e ".[dev]"
```

## Quick start

```bash
uv run aictx --version
uv run aictx scan --project .
uv run aictx init --project .
uv run aictx verify --project . --strict
uv run aictx status --project . --strict --json
uv run aictx run --project . --mode setup-context --execution local --scope full --write patch
uv run aictx run --project . --mode setup-context --execution local --scope full --write apply
uv run aictx public-docs update --project . --scope changed --write patch
uv run aictx oci doctor --json
uv run aictx snapshot create --project .
uv run aictx oci capabilities --project .
uv run aictx oci estimate --project .
```

## Packaging

```bash
uv build
pipx install .
pip install -e ".[oci]"
```

## Command surface

| Command | State | Notes |
| --- | --- | --- |
| `scan` | implemented | deterministic inventory + secret scan |
| `init` | implemented | writes/refreshes `docs/AIprojectcontext/context.lock.json`; preserves generated metadata when present |
| `run` | implemented | local Phase 1 only; `setup-context`; `scope=full|changed`; patch/apply; budget + transfer preflight |
| `verify` | implemented | hash verification plus strict generated-file/source-link checks; JSON report |
| `status` | implemented | scan + verify summary for automation |
| `clean` | implemented | safe local/OCI cleanup; dry-run until `--yes` |
| `public-docs update` | implemented | deterministic review/patch for mapped doc impacts; manual prose edits still required |
| `snapshot create` / `snapshot verify` | implemented | deterministic snapshot packaging + integrity verification |
| `oci doctor` | implemented | local SDK/config/compartment/model readiness check |
| `oci capabilities` | implemented | validates object storage/job prerequisites |
| `oci upload-snapshot` / `oci download-result` | implemented | OCI artifact exchange + bundle verify/unpack |
| `oci estimate` | implemented | remote runtime/cost estimate with budget gate |

## What `run --write apply` writes

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

Existing unmanaged second-level sections in `AGENTS.md` are preserved during regeneration.
`--write apply` refuses dirty paths outside context-source/generated outputs unless config or `--allow-dirty` opts in.

## Dev commands

```bash
uv run pytest
uv run ruff check .
uv run ruff format .
uv run mypy src
```

## Docs

- `documentation/DOCUMENTATION.md`
- `documentation/CODEMAP.md`
- `documentation/ARCHITECTURE.md`
- `documentation/CHANGELOG.md`
- `aictx_development_plan.md`

## Safety / limits

- scanner never prints secret values
- no auto-commit / auto-push
- no silent overwrite beyond explicit `--write apply`; dirty apply blocks non-context paths unless `--allow-dirty`
- runtime-only: `.aictx/runs/`, `.aictx/cache/`, `.aictx/tmp/`
- committed generated baseline: `docs/AIprojectcontext/context.lock.json`
- generated `docs/AIprojectcontext/**` and generated `AGENTS.md` are not fed back into context selection
- model-transfer preflight excludes ignored, binary, generated, `.git`, `.aictx/runs`, cache/build, oversize, and secret-bearing files
- configured token/file budgets fail before provider creation or calls
- snapshot generation is deterministic and bounded by hard caps
- OCI runtime budgets gate snapshot size/runtime/tokens before submit
- contradiction/coverage outputs are deterministic placeholders only
- default provider: `dry_run`; `oci_genai` requires `--allow-ai`, SDK, config, `llm.compartment_id`, and `llm.model`
- OCI remote execution remains patch-first; no autonomous apply/commit/push behavior

## Verification philosophy

- fail closed on uncertain correctness or safety
- hash/source-trace verification is primary; LLM semantics are supplemental only
- public-doc updates stay review-first
- OCI wraps transport/runtime only; local pipeline remains canonical

## OCI workflow

1. `snapshot create`
2. `oci upload-snapshot`
3. `run --execution oci-job --write patch`
4. `oci download-result`
5. review `aictx.patch`
6. optional local apply

## Cost-control model

- configured token caps
- snapshot size caps before upload
- remote runtime caps before submission
- bounded retry counts
- explicit cleanup confirmation gates

## License

MIT. See `LICENSE`.
