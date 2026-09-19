# AICtx — Status & Roadmap
_Portfolio audit: 2026-07-11_

## What this is
A local-first CLI that prepares Git repositories for low-token AI-agent work: deterministic scan,
lockfile-anchored context generation into `docs/AIprojectcontext/`, strict hash/source-link
verification, patch-first apply, changed-scope refresh, public-docs impact review, and optional
heavy execution on OCI (snapshot upload, Data Science Jobs, result bundles). Stack: Python 3.12+,
Typer + Rich + Pydantic + pathspec, optional `oci` SDK; pytest/ruff/mypy; four GitHub workflows
(`aictx-verify`, `install-matrix`, `oci-proof`, `release-validation`).

## Current state
Functionally this is the portfolio's most feature-complete CLI, but administratively it stopped one
step before the finish line and has been idle since 2026-05-09.

What works:
- The whole documented command surface is implemented: `scan`, `init`, `run` (full/changed scope,
  patch/apply), `verify --strict [--json]`, `status --json`, `clean`, `public-docs update`,
  `snapshot create/verify`, and the `oci` subcommands (`doctor`, `capabilities`, `estimate`,
  `upload-snapshot`, `download-result`).
- `v1-implementation-checklist.md` audits every item of `last_steps_dev_plan.md` against the code
  and concludes "v1 complete: YES", with exactly three explicit post-v1 deferrals (semantic
  freshness verification, live OCI execution in automation, automated prose rewriting).
- Fail-closed safety posture throughout: secret scanning, snapshot hard limits, budget preflight,
  dirty-worktree apply gate.

Gaps and loose ends:
- The release was never cut: `pyproject.toml` still says `0.1.0` with classifier
  `Development Status :: 3 - Alpha`, there are **zero git tags**, and
  `documentation/CHANGELOG.md` is one giant "Unreleased" section. The repo claims v1 but ships 0.1.
- `tests/integration/` is an empty scaffold (only `__init__.py`); all six test modules live under
  `tests/unit/`, despite the fixture project sitting ready in `..\AICtxTestRepos\AICtxDummyProject`.
- Untracked `.kimi/AGENTS.MD` sits in the working tree (`git status` noise) — commit or ignore it.
- Portfolio overlap: context-crafter-mcp generates repo context too. AICtx's differentiators are
  the maintained-in-repo lockfile + verification loop and OCI offload; that positioning is written
  nowhere.

## Definition of "finished"
The version the checklist already claims actually exists: `pyproject.toml` at 1.0.0 with a Beta or
Production classifier, a dated changelog, a `v1.0.0` git tag and GitHub release, all four workflows
green on that tag, at least one real end-to-end integration test against `AICtxDummyProject`, a
clean working tree, and a README paragraph stating how AICtx relates to context-crafter-mcp.

## Roadmap

### Phase 1 — Now (next 1–2 weeks)
- Resolve the `.kimi/` untracked directory (commit the agent guide or add it to `.gitignore`).
- Reconcile versioning: bump `pyproject.toml` to `1.0.0rc1`, update the alpha classifier, and cut
  `documentation/CHANGELOG.md`'s "Unreleased" into a dated pre-release section.
- Re-run the local quality bar after two idle months: `uv sync --extra dev`, pytest, ruff, mypy,
  and the `release-validation.yml` steps locally; fix drift.

### Phase 2 — Next (2–6 weeks)
- Populate `tests/integration/`: drive `init → run --scope full --write apply → verify --strict →
  run --scope changed` end-to-end against a copy of `..\AICtxTestRepos\AICtxDummyProject` and
  assert on the JSON reports.
- Tag `v1.0.0`, publish a GitHub release with wheel/sdist (`uv build`), and make
  `install-matrix.yml` run against the built artifact.
- Add a "How this differs from context-crafter-mcp" section to `README.md` (maintained in-repo
  context + deterministic verification + OCI offload vs. on-demand MCP context bundles).

### Phase 3 — Later (optional/stretch)
- The three documented post-v1 deferrals, in value order: prove live OCI execution once real
  credentials can be injected into `oci-proof.yml`; semantic freshness verification; automated
  public-doc prose rewriting.
- Decide the consolidation question: keep AICtx independent, or fold its changed-scope refresh and
  verifier ideas into context-crafter-mcp and put this repo into maintenance.

## Effort to "finished"
**M (1–4 weeks part-time).** No new features are needed, but release mechanics, two idle months of
dependency drift, and the missing integration tests add up to more than a weekend.
