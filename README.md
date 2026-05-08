# AICtx

Local-first CLI for low-token AI-agent repo context.

## Status

Early alpha.

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
- changed-scope detection recorded in run plan
- deterministic public-doc impact review artifact
- public-doc verification hashes preserved until mapped doc changes
- dirty-worktree apply gate with `--allow-dirty`
- tests + Ruff + mypy + pytest setup

Still stubbed/not implemented:

- `oci_genai` provider runtime
- semantic freshness verification
- remote OCI execution
- CI workflow generation

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
```

## Command surface

| Command | State | Notes |
| --- | --- | --- |
| `scan` | implemented | deterministic inventory + secret scan |
| `init` | implemented | writes/refreshes `docs/AIprojectcontext/context.lock.json`; preserves generated metadata when present |
| `run` | implemented | local Phase 1 only; `setup-context`; `scope=full|changed`; patch/apply; apply blocks dirty unless allowed |
| `verify` | implemented | hash verification plus strict generated-file/source-link checks; JSON report |
| `status` | implemented | scan + verify summary for automation |
| `clean` | implemented | safe local run cleanup; dry-run until `--yes`; OCI cleanup still unsupported |
| `public-docs update` | implemented | deterministic review/patch for mapped doc impacts; manual prose edits still required |
| `oci doctor` | implemented | local SDK/config/compartment readiness check; no network calls |

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
`--write apply` refuses dirty worktrees unless config or `--allow-dirty` opts in.

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
- no silent overwrite beyond explicit `--write apply`; dirty apply requires `--allow-dirty`
- runtime-only: `.aictx/runs/`, `.aictx/cache/`, `.aictx/tmp/`
- committed generated baseline: `docs/AIprojectcontext/context.lock.json`
- generated `docs/AIprojectcontext/**` and generated `AGENTS.md` are not fed back into context selection
- contradiction/coverage outputs are deterministic placeholders only
- default provider: `dry_run`; `oci_genai` factory path requires `--allow-ai` but runtime remains stubbed

## License

MIT. See `LICENSE`.
