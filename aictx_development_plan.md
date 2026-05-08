# AICtx Roadmap AI-Only

## Ground truth

Trust code over docs. Read `docs/AIprojectcontext/ai-index.md` first. Do not expand scope from roadmap text alone.

## Current implemented surface

- CLI commands working:
  - `aictx --version`
  - `aictx scan --project <repo>`
  - `aictx init --project <repo>`
  - `aictx run --project <repo> --mode setup-context --execution local --scope full|changed --write patch|apply`
  - `aictx verify --project <repo> --strict [--json]`
  - `aictx status --project <repo> --strict [--json]`
  - `aictx public-docs update --project <repo> --scope changed|full --write patch|apply`
  - `aictx clean --project <repo> --run-id <id>|--keep-runs <n> [--yes]`
  - `aictx oci doctor [--json]`

## Current pipeline facts

- scan: deterministic inventory + git status + ignore handling + generated-artifact detection + secret scan.
- init: writes `docs/AIprojectcontext/context.lock.json`; preserves existing generated metadata if lock already has it.
- run local:
  - blocks on detected secrets
  - blocks dirty `--write apply` unless allowed
  - records changed files against existing lock for `--scope changed`
  - builds deterministic plan
  - uses provider factory; `dry_run` default; non-dry requires `--allow-ai`
  - writes run artifacts under `.aictx/runs/<run-id>/`
  - writes scaffold to `.aictx/runs/<run-id>/out/`
  - writes patch file `aictx.patch`
  - `--write apply` copies staged files into repo
  - generated context artifacts are excluded from future source selection
  - unmanaged second-level sections in generated `AGENTS.md` are preserved
  - public-doc source verification hashes preserve review impact until mapped doc changes
  - applied lockfile path = `docs/AIprojectcontext/context.lock.json`
  - root `context.lock.json` must not exist
- verify: checks lock exists, schema supported, source files exist/hash-match, generated files exist/hash-match, expected generated files, section source/hash links, generated `AGENTS.md` index link, and public-doc source impacts.

## Generated outputs expected from run/apply

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

## Run artifact minimum

- `.aictx/runs/<run-id>/inventory.json`
- `.aictx/runs/<run-id>/context-plan.json`
- `.aictx/runs/<run-id>/facts/*_facts.json`
- `.aictx/runs/<run-id>/coverage-report.json`
- `.aictx/runs/<run-id>/contradictions.json`
- `.aictx/runs/<run-id>/out/**`
- `.aictx/runs/<run-id>/aictx.patch`

## Verified done already

- lockfile staged/applied under context dir, not repo root.
- patch targets `b/docs/AIprojectcontext/context.lock.json`, not `b/context.lock.json`.
- secret self-protection exists for detector/examples + test/fixture paths.
- `.venv` / `.pytest-tmp` exclusions exist.
- tests cover phase1 patch/apply lockfile behavior.

## Active priorities

1. Dogfood local flow on AICtx end-to-end until stable.
2. Improve deterministic fact quality/source tracing.
3. Make changed-scope regeneration partial instead of full-safe.
4. Convert public-doc review into source-grounded doc patching.
5. Implement OCI provider/runtime behind current opt-in seam.
6. Add CI/release hardening after local contracts stay stable.

## Immediate tasks

### P1 dogfood gate

Must pass:

    uv sync --extra dev
    uv run python -m compileall src tests
    uv run aictx --help
    uv run aictx --version
    uv run ruff format --check .
    uv run ruff check .
    uv run mypy src
    uv run pytest
    uv run aictx run --project . --mode setup-context --execution local --scope full --write patch
    uv run aictx run --project . --mode setup-context --execution local --scope full --write apply
    uv run aictx verify --project . --strict

Required result:

- no root `context.lock.json`
- context files generated under `docs/AIprojectcontext/`
- generated context files are not selected as source on repeated runs
- section source links use repo-relative paths with known source hashes
- verify returns PASS after apply

### P1 fact quality

Need next:

- stable fact ids where possible
- repo-relative source references everywhere possible
- source spans for critical claims when cheap
- clear implemented/stubbed/planned labeling
- no invented semantics

### P2 verifier expansion

Add deterministic checks for:

- required generated files exist
- `AGENTS.md` points to `docs/AIprojectcontext/ai-index.md`
- section/source linkage integrity in lockfile
- stale generated sections / unsupported `needs-source` critical markers
- workflow command presence where documented

### P2 changed-scope

Upgrade changed refresh:

- diff base
- map impacted source paths
- regenerate only impacted context files/sections
- update lockfile
- keep patch targeted

### P3 public docs

Current state: deterministic map + review patch exists; no prose generation.

Need:

- source-grounded doc patching
- stronger feature/doc mapping than conservative all-source map
- apply-review workflow that keeps manual edits auditable

## Deferred until local flow solid

- OCI GenAI provider runtime
- OCI snapshot/object storage
- OCI remote jobs/workers
- CI workflow generation
- packaging/release hardening
- optional semantic/LLM verification

## Non-negotiables

- local-first
- no auto-commit/push
- no silent overwrite beyond explicit apply; dirty apply must be opt-in
- no claiming planned work as implemented
- no sending secrets to model providers
- no monolithic rewrite

## True current architecture map

- `src/aictx/cli.py` = command surface
- `src/aictx/scan/` = implemented scanner path
- `src/aictx/context/pipeline.py` = implemented local Phase 1 orchestration
- `src/aictx/context/compressor.py` = stub/pass-through
- `src/aictx/verify/verifier.py` = implemented deterministic verifier + detailed reports
- `src/aictx/public_docs/` = deterministic mapping/review flow
- `src/aictx/llm/dry_run.py` = only working provider
- `src/aictx/llm/providers.py` = guarded provider factory
- `src/aictx/llm/oci_genai.py` = stub
- `src/aictx/oci/doctor.py` = local readiness check
- OCI remote modules = stubs

## Definition of actually done v1

Required stable loop:

    aictx run --project <repo> --mode setup-context --execution local --scope full --write apply
    aictx verify --project <repo> --strict

After source change:

    aictx verify --project <repo> --strict

must fail correctly, then:

    aictx run --project <repo> --mode setup-context --scope changed --write apply --allow-dirty
    aictx public-docs update --project <repo> --scope changed --write patch
    aictx verify --project <repo> --strict

must restore verified state.
