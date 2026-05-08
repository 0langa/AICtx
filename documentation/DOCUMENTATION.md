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
uv run aictx verify --project <path> --strict --json
uv run aictx status --project <path> --strict --json
uv run aictx run --project <path> --mode setup-context --execution local --scope full --write patch
uv run aictx run --project <path> --mode setup-context --execution local --scope full --write apply
uv run aictx run --project <path> --mode setup-context --execution local --scope changed --write patch
uv run aictx public-docs update --project <path> --scope changed --write patch
uv run aictx oci doctor --json
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
2. create `.aictxignore` if missing
3. run scanner
4. create `docs/AIprojectcontext/` if missing
5. write `docs/AIprojectcontext/context.lock.json`

If existing lockfile contains generated metadata from prior apply run, preserve generated metadata and refresh source-side hashes.

Does not call model provider. Does not generate AI context shards. Does not auto-commit.

## `run`

Supported now:

- `--mode setup-context`
- `--execution local`
- `--scope full|changed`
- `--write patch|apply`
- `--provider dry_run|oci_genai`
- `--allow-ai`
- `--allow-dirty`

Behavior:

1. validate args
2. load `.aictx/config.toml` if present
3. scan repo; fail on detected secrets
4. fail `--write apply` when dirty paths are outside context-source/generated outputs unless `--allow-dirty` or config allows it
5. compute changed files against existing lock
6. build deterministic selection plan
7. enforce model-transfer file safety
8. enforce input/output/file-count/file-size budgets
9. write safe provider metadata, excluding prompt content
10. extract deterministic fact packs via configured provider (`dry_run` default)
11. generate staged context files + `AGENTS.md` under `.aictx/runs/<timestamp>-run/out/`
12. write `.aictx/runs/<timestamp>-run/aictx.patch`
13. write `.aictx/runs/<timestamp>-run/run-report.json`
14. if `--write apply`, copy staged outputs into repo

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
- `--scope changed` selects impacted files and preserves unaffected generated shards when possible
- generated context artifacts are excluded from future source selection
- unmanaged second-level sections in existing generated `AGENTS.md` are preserved
- public-doc source verification hashes refresh during context regeneration
- non-dry provider use requires explicit `--allow-ai`; `oci_genai` also requires `llm.compartment_id` and runtime still raises `NotImplementedError`
- ignored, binary, generated, `.git`, `.aictx/runs`, cache/build, oversize, or secret-bearing files cannot enter model-transfer selection
- prompt content is not written to provider metadata by default

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
- public docs impacts are reported from lockfile doc/source maps before context refresh
- `--json` emits structured verification details and next-command hints

Current scope = deterministic hash/linkage only. No semantic freshness.

## Operational commands

- `aictx status --project <path> --strict --json` → scan + verify status for automation
- `aictx clean --project <path> --run-id <id> --yes` → delete one local run
- `aictx clean --project <path> --keep-runs <n> --yes` → keep newest N local runs
- `aictx public-docs update --project <path> --scope changed --write patch` → write deterministic review patch
- `aictx public-docs update --project <path> --scope full --write patch` → review all mapped public docs
- `aictx public-docs update --project <path> --write apply` → write `docs/AIprojectcontext/public-docs-review.md`; does not rewrite public docs prose
- `aictx oci doctor --json` → local SDK/config/compartment readiness; no network mutation

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

Public-doc review:

1. change source
2. `uv run aictx public-docs update --project . --scope changed --write patch`
3. manually update impacted public docs from source facts
4. `uv run aictx run --project . --mode setup-context --execution local --scope changed --write apply`
5. `uv run aictx verify --project . --strict`

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
- dirty apply rejected → rerun with `--allow-dirty` only when dirty files are intentional
- budget exceeded → reduce selected files or raise `.aictx/config.toml` limits intentionally
- unsupported `run` mode/execution → only local `setup-context` implemented
- fresh clone verify fail → create/commit `docs/AIprojectcontext/context.lock.json` first via `init`

## Related docs

- [`CODEMAP.md`](./CODEMAP.md)
- [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- [`CHANGELOG.md`](./CHANGELOG.md)
- [`../aictx_development_plan.md`](../aictx_development_plan.md)
