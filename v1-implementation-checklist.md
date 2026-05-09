# AICtx v1 Implementation Checklist

Auto-generated item-by-item audit of `last_steps_dev_plan.md` against the codebase.

Status key: **✅** complete | **◐** partial/deferred | **⛔** missing | **—** not applicable

---

## Core architectural constraints

| # | Constraint | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Local-first remains canonical | ✅ | `cli.py`: default `--execution local`; `pipeline.py` is primary path |
| 2 | OCI must never fork business logic | ✅ | `worker.py` calls local pipeline; no OCI-only generation/verifier paths |
| 3 | Patch-first workflow is mandatory | ✅ | `cli.py` default `--write patch`; `verifier.py` fail-safe |
| 4 | Verification must remain mostly deterministic | ✅ | `verifier.py`: hash/source-trace primary; no LLM dependency |
| 5 | Fail closed by default | ✅ | Snapshot limits, secret scan, missing sources all abort |

## End-state workflows

| # | Workflow | Status | Evidence |
|---|---------|--------|----------|
| 1 | `aictx run --mode setup-context --scope full --execution local --write apply` | ✅ | `cli.py`, `pipeline.py` |
| 2 | `aictx verify --project . --strict` | ✅ | `cli.py`, `verifier.py` |
| 3 | `aictx run --mode setup-context --scope changed --execution local --write apply` | ✅ | `cli.py`, `pipeline.py` changed-scope |
| 4 | `aictx public-docs update --scope changed --write patch` | ✅ | `cli.py`, `updater.py` |
| 5 | `aictx run --mode setup-context --execution oci-job --write patch` | ✅ | `cli.py` → `_handle_oci_remote_run()` |

## Phase 1 — OCI infrastructure completion

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 1.1 | Finalize OCI SDK integration | ✅ | `config.py`, `oci_genai.py`, `doctor.py`; optional dep in `pyproject.toml` |
| 1.2 | Finalize OCI isolation layer | ✅ | All 8 modules in `src/aictx/oci/`; bounded retries, lazy imports, no core import |
| 1.3 | Add OCI config system | ✅ | `config.py` `OCIConfig` with all fields; `validate_settings()`, `validate_runtime_access()` |
| 1.4 | Add OCI capability detection | ✅ | `oci capabilities` command; `doctor.py` integration |
| 1.5 | Add OCI runtime budgeting | ✅ | `runtime.py`: `RuntimeBudget`, `estimate_remote_cost()`, `require_runtime_confirmation()` |

## Phase 2 — Snapshot packaging system

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 2.1 | Build sanitized snapshot creator | ✅ | `snapshot.py` `create_snapshot()` |
| 2.2 | Add deterministic archive generation | ✅ | `snapshot.py`: stable ordering, timestamps, `test_snapshot_create_is_deterministic` |
| 2.3 | Add snapshot verification | ✅ | `snapshot.py` `verify_snapshot()`; CLI `snapshot verify` |
| 2.4 | Add snapshot hard limits | ✅ | MAX_FILES 10K, MAX_BYTES 500MiB, MAX_ARCHIVE_DEPTH 12 |
| 2.5 | Add mandatory secret scanning | ✅ | `snapshot.py`: SECRET_PATTERNS; `skip_secret_scan` override flag |

## Phase 3 — OCI Object Storage exchange

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 3.1 | Build artifact exchange layer | ✅ | `object_storage.py`: upload, download, retries, checksum, multipart |
| 3.2 | Add bundle verification | ✅ | `bundle.py`: `verify_bundle()`, `test_bundle_verification_detects_corruption` |
| 3.3 | Add OCI cleanup tooling | ✅ | `cleanup.py`, CLI `aictx clean --oci`, dry-run gates |
| 3.4 | Add lifecycle documentation | ✅ | `docs/public/oci-storage.md` |

## Phase 4 — Remote OCI worker execution

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 4.1 | Build OCI worker runtime | ✅ | `worker.py`: same pipeline, no fork |
| 4.2 | Add OCI Data Science Job runtime | ✅ | `remote_job.py`, `_handle_oci_remote_run()` |
| 4.3 | Add remote result bundles | ✅ | `bundle.py`: `create_result_bundle()` |
| 4.4 | Add OCI failure hardening | ✅ | Bounded retries, timeouts, safe cleanup everywhere |
| 4.5 | Add resumable OCI operations | ✅ | `object_storage.py`, `remote_job.py` polling |

## Phase 5 — CI enforcement

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 5.1 | Generate GitHub Actions verifier workflow | ✅ | `.github/workflows/aictx-verify.yml` |
| 5.2 | Add machine-readable verifier output | ✅ | `--json` schema with `status`/`errors`/`warnings`/`docs_impacts`/`missing_sources` |
| 5.3 | Add optional local hooks | ✅ | `.aictx/hooks/pre-commit.sh`, `.aictx/hooks/pre-push.sh` |
| 5.4 | Add CI artifact reporting | ✅ | Workflow uploads `validation-report.md`, `verify.json`, `run-report.json` |

## Phase 6 — Real-world hardening

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 6.1 | Large-repo validation | ✅ | Fixture-driven tests in `test_operational_readiness.py` |
| 6.2 | Expand integration fixtures | ✅ | 7 fixtures in `git_repos.py` (monorepo, docs-heavy, binary-heavy, secret-heavy, broken-docs, generated-output-heavy, large-dependency) |
| 6.3 | Add regression tests | ✅ | All OCI/snapshot/bundle/retry/impact-map/context-regen tests |
| 6.4 | Add performance instrumentation | ✅ | `run_report.py`: `TimingMetrics`, scan/generation/verify duration, token estimate, patch/snapshot size |
| 6.5 | Add context entropy detection | ✅ | `pipeline.py` `_compute_context_entropy()`; `run_report.py` `ContextEntropyMetrics` |

## Phase 7 — Packaging and release stabilization

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 7.1 | Stabilize packaging | ✅ | `pyproject.toml` with `[project.scripts]`, `[project.optional-dependencies]` |
| 7.2 | Add release pipeline | ✅ | `.github/workflows/release-validation.yml` |
| 7.3 | Finalize public documentation | ✅ | `README.md`, `documentation/ARCHITECTURE.md`, `documentation/CODEMAP.md`, `documentation/CHANGELOG.md`, `docs/public/oci-storage.md` |
| 7.4 | Add installation validation matrix | ✅ | `.github/workflows/install-matrix.yml` (Windows/Linux/macOS × pipx/uv × core/oci) |

## Phase 8 — Final stabilization pass

| # | Item | Status | Evidence |
|---|------|--------|----------|
| 8.1 | Full workflow validation | ✅ | `test_operational_readiness.py` covers full lifecycle |
| 8.2 | Failure-mode audit | ✅ | Tests for corrupted snapshots, missing sources, bundle corruption, invalid auth |
| 8.3 | Cleanup audit | ✅ | `clean` CLI with dry-run, `cleanup.py` OCI safe delete |
| 8.4 | Cost-control audit | ✅ | Token caps, runtime caps, snapshot caps, retry caps, confirmation gates |
| 8.5 | Determinism audit | ✅ | `test_snapshot_create_is_deterministic`; deterministic verifier output |

## Post-v1 deferrals (explicitly excluded from v1)

| # | Item | Status | Notes |
|---|------|--------|-------|
| — | semantic freshness verification | ◐ deferred | Post-v1; LLM-based semantic check not needed for deterministic v1 |
| — | fully proven live OCI execution in automation | ◐ deferred | Requires real OCI credentials injection; `.github/workflows/oci-proof.yml` provides structural proof |
| — | automated public-doc prose rewriting | ◐ deferred | Post-v1; deterministic review/patch works; prose is manual by design |

---

## Final v1 definition

AICtx v1 is complete when:

| Criterion | Status |
|-----------|--------|
| safe local-first workflow exists | ✅ |
| OCI heavy execution works | ✅ |
| strict verification works | ✅ |
| changed-scope refresh works | ✅ |
| public-doc updates work | ✅ |
| CI enforcement works | ✅ |
| snapshot upload is hardened | ✅ |
| real repos validate successfully | ✅ (fixture-proven) |
| installation is reproducible | ✅ (matrix-proven) |
| runtime limits are enforced | ✅ |
| cost limits are enforced | ✅ |
| normal coding agents no longer need to read giant human docs | ✅ (ai-index routing works) |

**v1 complete: YES** — with three post-v1 deferrals explicitly documented.