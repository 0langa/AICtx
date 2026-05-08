# AICtx Documentation

## Install

Python 3.12+.

```bash
git clone https://github.com/0langa/AICtx.git
cd AICtx
uv sync --extra dev
# or
pip install -e ".[dev]"
```

## CLI quick refs

```bash
uv run aictx --version
uv run aictx --help
uv run aictx scan --project <path>
uv run aictx init --project <path>
uv run aictx verify --project <path> --strict
uv run aictx run --project <path> --mode setup-context --execution local --scope full --write patch
uv run aictx run --project <path> --mode setup-context --execution local --scope full --write apply
```

## `scan`

Behavior:

1. detect git root
2. walk repo with ignore pruning
3. classify source/test/doc/manifest/binary/ignored
4. mark generated context artifacts separately
5. detect languages + project type
6. run high-confidence secret scan on non-binary files
7. print summary
8. write `.aictx/runs/<timestamp>-scan/inventory.json`

Inventory includes deterministic `dirty_state` + `git_status` lists.

## `init`

Behavior:

1. validate target inside git repo
2. run scanner
3. create `docs/AIprojectcontext/` if missing
4. write `docs/AIprojectcontext/context.lock.json`
5. create `.aictxignore` if missing

If existing lockfile contains generated metadata from prior apply run, preserve generated metadata and refresh source-side hashes.

Does not call model provider. Does not generate AI context shards. Does not auto-commit.

## `run`

Supported now:

- `--mode setup-context`
- `--execution local`
- `--scope full`
- `--write patch|apply`

Behavior:

1. validate args
2. load `.aictx/config.toml` if present
3. scan repo; fail on detected secrets
4. build deterministic selection plan
5. extract deterministic fact packs via `dry_run`
6. generate staged context files + `AGENTS.md` under `.aictx/runs/<timestamp>-run/out/`
7. write `.aictx/runs/<timestamp>-run/aictx.patch`
8. if `--write apply`, copy staged outputs into repo

Applied outputs:

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

Notes:

- `--write patch` = staged files + patch only
- `--write apply` = copy staged outputs into repo
- generated context artifacts are excluded from future source selection
- unmanaged second-level sections in existing generated `AGENTS.md` are preserved
- `src/aictx/io/patches.py:apply_patch` not used; still stubbed
- `--scope changed` accepted by CLI, rejected by pipeline

## `verify --strict`

Current checks:

- lockfile exists
- schema version supported
- locked source files exist
- locked source hashes match
- generated files exist if listed in lockfile
- generated file hashes match
- strict mode requires the expected generated context files
- strict mode verifies section source paths and source hashes
- strict mode verifies generated `AGENTS.md` links to `docs/AIprojectcontext/ai-index.md`

Current scope = hash-only. No semantic freshness. No public-docs impact validation.

## Stub commands

- `aictx clean --oci --run-id <id>` → stub message
- `aictx public-docs update --project <path> --scope <scope> --write <mode>` → prints `not yet implemented`, exits 1

## Typical workflows

Baseline-only:

1. change code/docs
2. `uv run aictx verify --project . --strict`
3. if source hash mismatch: `uv run aictx init --project .`
4. commit changes + updated `docs/AIprojectcontext/context.lock.json`

Generated-context:

1. change code/docs affecting context
2. `uv run aictx run --project . --mode setup-context --execution local --scope full --write apply`
3. `uv run aictx verify --project . --strict`
4. commit changes + regenerated context files + lockfile

## Scanner output shape

Example summary fields:

- repo
- branch
- head
- dirty
- files included
- files ignored
- docs
- source
- tests
- manifests
- secrets
- inventory path

Secrets printed as path + detector + severity only; never value.

## Test / lint / typecheck

```bash
uv run pytest
uv run ruff format --check .
uv run ruff format .
uv run ruff check .
uv run mypy src
```

## Troubleshooting

- not a git repo → target must be inside repo with at least one commit
- real secret findings → remove real secret; do not suppress
- `.pytest-tmp` ignored intentionally to avoid transient scan/test/lint drift
- unsupported `run` mode/execution → only local `setup-context` + `scope=full` implemented
- fresh clone verify fail → create/commit `docs/AIprojectcontext/context.lock.json` first via `init`

## Related docs

- [`CODEMAP.md`](./CODEMAP.md)
- [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- [`CHANGELOG.md`](./CHANGELOG.md)
- [`../aictx_development_plan.md`](../aictx_development_plan.md)
