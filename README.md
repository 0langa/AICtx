# AICtx

Local-first CLI for low-token AI-agent repo context.

## Status

Early alpha.

Implemented:

- `scan`
- `init`
- `run --mode setup-context --execution local --scope full --write patch|apply`
- `verify --strict`
- deterministic scanner
- baseline lockfile bootstrap
- hash-only verifier MVP
- strict generated-context structure checks
- local Phase 1 context pipeline
- dry-run provider
- generated context scaffold + `AGENTS.md`
- generated artifact isolation during scan/planning
- patch output + apply-by-copy
- tests + Ruff + mypy + pytest setup

Stubbed/not implemented:

- `clean`
- `public-docs update`
- `run --scope changed`
- real patch replay in `io.patches.apply_patch`
- `oci_genai` provider runtime
- semantic freshness verification
- change-impact mapping
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
uv run aictx run --project . --mode setup-context --execution local --scope full --write patch
uv run aictx run --project . --mode setup-context --execution local --scope full --write apply
```

## Command surface

| Command | State | Notes |
| --- | --- | --- |
| `scan` | implemented | deterministic inventory + secret scan |
| `init` | implemented | writes/refreshes `docs/AIprojectcontext/context.lock.json`; preserves generated metadata when present |
| `run` | implemented | local Phase 1 only; `setup-context`; `scope=full` only |
| `verify` | implemented | hash verification plus strict generated-file/source-link checks |
| `clean` | stub | no cleanup |
| `public-docs update` | stub | exits 1 |

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
- no silent overwrite beyond explicit `--write apply`
- runtime-only: `.aictx/runs/`, `.aictx/cache/`, `.aictx/tmp/`
- committed generated baseline: `docs/AIprojectcontext/context.lock.json`
- generated `docs/AIprojectcontext/**` and generated `AGENTS.md` are not fed back into context selection
- contradiction/coverage outputs are deterministic placeholders only
- only working provider: `dry_run`

## License

MIT. See `LICENSE`.
