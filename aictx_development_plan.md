# AICtx Corrected Development Roadmap

## Current baseline

This roadmap is based on the current repository.

AICtx is no longer only a scanner scaffold. The repo now has a real local foundation:

    implemented:
      Typer CLI scaffold
      aictx --help
      aictx --version
      aictx scan --project <repo>
      deterministic repository scanner
      Git state detection
      structured Git status in inventory
      ignored-directory pruning
      .aictx runtime artifact exclusion
      file/doc/test/manifest classification
      secret finding reports
      baseline docs/AIprojectcontext/context.lock.json
      aictx init baseline lockfile behavior
      hash-only aictx verify --strict MVP
      dry_run model provider
      local setup-context run pipeline
      context planner
      deterministic fact extraction
      context scaffold writer
      generated AGENTS.md content
      staged patch output
      optional apply mode
      public docs under documentation/
      unit/integration tests for scanner, init, verify, and Phase 1 run behavior

    still stubbed or incomplete:
      real LLM-backed fact extraction
      OCI GenAI provider calls
      semantic verification
      public-docs updater
      changed-scope refresh
      full change impact mapping
      OCI Object Storage exchange
      OCI remote worker
      GitHub Actions verifier generation
      packaging/release hardening

The immediate roadmap should not jump to OCI. The next step is to harden the local dry-run pipeline and then finish the deterministic local verification/refresh loop.

## Product goal

AICtx is a local-first CLI that prepares Git repositories for low-token AI-agent work.

The final workflow should be:

    scan repository
    generate compact source-traced AI context
    write routed context under docs/AIprojectcontext/
    create or update root AGENTS.md
    maintain docs/AIprojectcontext/context.lock.json
    verify context freshness
    identify stale AI context and public-doc impact
    optionally update public human-facing docs
    optionally use OCI for expensive model calls or remote batch execution

AICtx must remain safe by default:

    local-first
    patch/review oriented
    deterministic where possible
    no automatic commits
    no automatic pushes
    no hidden cloud uploads
    no secret transfer to model providers
    no planned features documented as implemented

## Core architecture target

Keep the current modular Python CLI architecture.

    src/aictx/cli.py
      command routing and user-facing CLI behavior

    src/aictx/config.py
      .aictx/config.toml loading and typed configuration

    src/aictx/git/
      direct Git subprocess helpers for repo root, status, and diffs

    src/aictx/scan/
      scanner, ignore rules, classification, secret detection

    src/aictx/models/
      Pydantic data contracts for inventory, lockfile, reports, docs maps

    src/aictx/context/
      planning, fact extraction, compression, scaffold writer, lockfile handling, AGENTS.md generation

    src/aictx/verify/
      hash checks, impact checks, reports, strict verifier

    src/aictx/public_docs/
      later public documentation mapping and update pipeline

    src/aictx/llm/
      provider interface, dry_run provider, later OCI provider

    src/aictx/oci/
      later OCI config, Object Storage, remote jobs, cleanup

    src/aictx/io/
      safe file writes, JSONL helpers, patch/diff helpers

Do not collapse this into a monolithic tool. AICtx’s value depends on clean stage boundaries.

## Repository documentation layout

Keep the current docs layout:

    README.md
    AGENTS.md
    aictx_development_plan.md
    documentation/
      README.md
      CODEMAP.md
      ARCHITECTURE.md
      DOCUMENTATION.md
      CHANGELOG.md
    docs/AIprojectcontext/
      context.lock.json
      future generated AI context shards

Root docs should stay concise. Detailed human-facing docs belong under documentation/.

Runtime output stays uncommitted:

    .aictx/runs/
    .aictx/cache/
    .aictx/tmp/

Versioned generated state should be committed when it is part of verification:

    docs/AIprojectcontext/context.lock.json

## OCI timing decision

Do not start full OCI integration yet.

Correct OCI timing:

    before OCI:
      local dry_run run pipeline works on AICtx itself
      local dry_run run pipeline works on StorageMaster in patch mode
      token-budget checks exist
      secret findings can block model-transfer paths
      config loading is stable
      context scaffold is correct
      verifier handles generated context files correctly
      tests pass without OCI credentials

    first OCI work:
      thin optional oci_genai provider smoke test
      local CLI calls OCI GenAI for one controlled request
      no Object Storage
      no remote jobs
      no Terraform-heavy setup

    real OCI work:
      Phase 4 only
      Object Storage
      sanitized snapshots
      remote workers
      Data Science Jobs or Container Instances
      cleanup
      budgets and runtime guardrails

Roadmap rule:

    Phase 1 through Phase 3 should be fully useful locally.
    Phase 4 is where real OCI-backed execution starts.

## Phase 0: Foundation already completed

Status: implemented.

This phase created the deterministic local base.

Delivered capabilities:

    CLI scaffold
    scanner
    ignore handling
    secret finding
    inventory JSON
    structured Git status
    baseline lockfile
    init command
    hash-only verifier MVP
    dry_run provider
    local setup-context run pipeline
    context scaffold writer
    generated AGENTS.md
    docs structure
    tests

Remaining Phase 0 cleanup that should be handled immediately:

    finalize docs and dogfooding validation for the completed local hardening work

## Phase 1: Local dry-run context pipeline hardening

Status: active immediate phase.

Goal: make local setup-context generation correct, deterministic, and safe enough to dogfood on AICtx itself and StorageMaster before any OCI work.

### Phase 1.1 Tooling and formatting hardening

Fix Ruff configuration so local virtual environments are never linted or formatted.

Completed hardening:

    .venv is excluded from Ruff and related local validation targets

Required pyproject exclusions:

    .git
    .venv
    .pytest-tmp
    .pytest_cache
    .mypy_cache
    .ruff_cache
    .aictx/runs
    .aictx/cache
    .aictx/tmp
    build
    dist
    node_modules

Then run:

    uv run ruff format .
    uv run ruff format --check .
    uv run ruff check .
    uv run mypy src
    uv run pytest

Acceptance:

    ruff does not inspect .venv
    format check passes
    ruff check passes
    mypy passes
    pytest passes

### Phase 1.2 Correct lockfile staging and apply behavior

Completed hardening work:

        run pipeline now stages the generated lockfile under the context directory path
        apply mode no longer creates a root-level `context.lock.json`

Correct behavior:

    staged lockfile:
      .aictx/runs/<run-id>/out/docs/AIprojectcontext/context.lock.json

    applied lockfile:
      docs/AIprojectcontext/context.lock.json

    forbidden:
      context.lock.json at repository root

Patch output must target:

    b/docs/AIprojectcontext/context.lock.json

and must never target:

    b/context.lock.json

Implementation target:

    update src/aictx/context/pipeline.py
    use context_dir relative path when writing the generated lockfile into out/
    include docs/AIprojectcontext/context.lock.json in generated_paths
    remove any special second write that creates duplicate root-level lockfile
    ensure _apply_out_dir copies only staged repo-relative outputs

Acceptance tests:

    test_run_phase1_patch_stages_lockfile_under_context_dir
    test_run_phase1_apply_does_not_create_root_context_lock
    test_run_phase1_patch_does_not_target_root_context_lock

### Phase 1.3 Clarify patch/apply implementation

Current reality:

    make_unified_diff is implemented
    patch file generation is implemented
    apply mode copies staged generated files into the repo
    low-level apply_patch helper remains stubbed

Roadmap rule:

    do not claim true patch application is implemented until io.patches.apply_patch actually applies patches

Docs should describe current behavior as:

    --write patch:
      writes .aictx/runs/<run-id>/aictx.patch and staged outputs

    --write apply:
      writes staged generated outputs into their target repo paths

    io.patches.apply_patch:
      still stubbed until a later safe writing milestone

### Phase 1.4 Secret suppression for intentional detector/test strings

Completed hardening:

    aictx run on AICtx itself now avoids intentional detector-source and test-fixture false positives

Keep default behavior safe:

    unsuppressed high-confidence findings should block model/context-transfer paths
    scanner may still complete and report findings
    secret values must never be printed

Implemented suppression for intentional examples.

Recommended mechanism:

    inline marker:
      aictx-secret-ignore

Behavior:

    if the marker appears on the same line or nearby comment, suppress that finding
    suppressed findings should not block local dry-run context generation
    unsuppressed findings must still be reported

Tests:

    test_secret_scan_supports_inline_suppression
    test_unsuppressed_secret_is_still_reported

Docs must explain:

    suppression is for intentional examples only
    real secrets should be removed, not suppressed

### Phase 1.5 Complete deterministic run artifacts

For every run, write these local artifacts:

    .aictx/runs/<run-id>/inventory.json
    .aictx/runs/<run-id>/context-plan.json
    .aictx/runs/<run-id>/facts/project_identity.json
    .aictx/runs/<run-id>/facts/architecture_facts.json
    .aictx/runs/<run-id>/facts/feature_facts.json
    .aictx/runs/<run-id>/facts/workflow_facts.json
    .aictx/runs/<run-id>/facts/docs_facts.json
    .aictx/runs/<run-id>/facts/risk_facts.json
    .aictx/runs/<run-id>/coverage-report.json
    .aictx/runs/<run-id>/contradictions.json
    .aictx/runs/<run-id>/out/
    .aictx/runs/<run-id>/aictx.patch

These artifacts are now written for the current deterministic Phase 1 pipeline; remaining work is to deepen semantics rather than establish the files.

Rules:

    run artifacts are local-only
    run artifacts are not committed
    run artifacts must not affect future scans
    persisted generated repo files must be under docs/AIprojectcontext/ or explicitly documented target paths

### Phase 1.6 Improve source tracing quality

Current deterministic facts are useful but shallow.

Improve local deterministic extraction before introducing real LLM calls.

Minimum improvements:

    fact IDs should be stable across runs where possible
    facts should reference repo-relative source paths
    critical facts should include source spans if easy
    unsupported facts should be marked needs_source
    facts should distinguish implemented, stubbed, and planned modules

Examples of source-traced fact categories:

    project identity
    CLI command surface
    implemented commands
    stubbed commands
    scanner behavior
    verifier behavior
    run pipeline behavior
    config behavior
    dependency state
    test coverage signals
    known limitations

### Phase 1.7 Phase 1 acceptance gate

Run from repo root:

    uv sync --extra dev
    uv run python -m compileall src tests
    uv run aictx --help
    uv run aictx --version
    uv run ruff format --check .
    uv run ruff check .
    uv run mypy src
    uv run pytest
    Remove-Item -Force context.lock.json -ErrorAction SilentlyContinue
    uv run aictx run --project . --mode setup-context --execution local --scope full --write patch
    uv run aictx run --project . --mode setup-context --execution local --scope full --write apply
    Test-Path context.lock.json
    Test-Path docs/AIprojectcontext/context.lock.json
    uv run aictx verify --project . --strict

Expected:

    compileall passes
    help/version pass
    ruff format check passes
    ruff check passes
    mypy passes
    pytest passes
    patch mode works
    apply mode works
    root context.lock.json does not exist
    docs/AIprojectcontext/context.lock.json exists
    verify passes after apply

Phase 1 is complete only when AICtx can dogfood itself locally in dry-run mode.

## Phase 2: Full deterministic verification and changed-scope refresh

Goal: turn the generated context scaffold into a strict, cheap, deterministic freshness system.

Do this after Phase 1 is stable.

### Phase 2.1 Expand context.lock.json semantics

The lockfile should fully represent:

    schema_version
    tool_version
    repo_head_commit
    generated_at
    model_provider
    model_name
    scanner_config_hash
    generated_files[]
    source_files[]
    sections[]
    public_docs_map[]
    change_impact_map[]
    last_validation

Generated file entries:

    path
    sha256
    generated_from_sections

Source file entries:

    path
    sha256
    kind
    included_in_generation

Section entries:

    section_id
    generated_file
    heading
    source_paths
    source_hashes
    fact_ids
    status

Rules:

    context.lock.json is generated-but-versioned
    .aictx/runs is generated-and-local-only
    lockfile must never include .aictx/runs
    lockfile must never include .git internals
    lockfile must preserve deterministic ordering

### Phase 2.2 Complete strict verifier

Verifier checks:

    context.lock.json exists
    schema version is supported
    required context files exist
    AGENTS.md points to docs/AIprojectcontext/ai-index.md
    generated file hashes match lockfile
    source file paths exist
    source hashes match lockfile
    section source paths exist
    section source hashes match
    critical needs_source markers fail
    build/test commands in workflows.md exist
    generated stale sections fail

Verifier result codes:

    PASS
    FAIL_STALE_AI_CONTEXT
    FAIL_PUBLIC_DOCS_IMPACT
    FAIL_LOCK_MISMATCH
    FAIL_MISSING_SOURCE
    FAIL_UNSUPPORTED_SCHEMA

Exit behavior:

    PASS -> exit 0
    any failure -> nonzero exit

Do not add LLM semantic verification in Phase 2.

### Phase 2.3 Change impact mapping

Generate:

    docs/AIprojectcontext/change-impact-map.md

and machine-readable mappings in context.lock.json.

Mappings should cover:

    source paths -> AI context files
    source paths -> public docs when known
    workflow files -> workflows.md and relevant public docs
    config files -> workflows.md/config docs
    docs files -> public-docs-map.md or docs impact

If no public docs impact exists, record:

    docs:none

Do not block on public-doc impact until the mapping is good enough.

### Phase 2.4 Changed-scope refresh

Command:

    aictx run --project <repo> --mode setup-context --scope changed --write patch

Behavior:

    read Git diff against base
    identify impacted source paths
    read impacted source/context only
    regenerate impacted sections/files
    update context.lock.json
    run verifier

Options:

    --base origin/main
    --base HEAD~1
    --scope full
    --scope changed

Acceptance:

    editing mapped source makes verify fail
    changed-scope refresh updates only impacted generated files
    verify passes after refresh
    patch remains small and targeted

## Phase 3: Public documentation mapping and update mode

Goal: maintain human-facing docs accurately without forcing every normal coding agent to read them.

Do this after Phase 2’s impact mapping is reliable.

### Phase 3.1 Public docs map

Generate:

    docs/AIprojectcontext/public-docs-map.md

Also store machine-readable entries in context.lock.json:

    path
    purpose
    audience
    described_features
    source_paths
    last_verified_source_hashes
    stale_risk

Rules:

    do not duplicate full public docs into AI context
    map what public docs describe
    keep public-docs-map compact
    distinguish root docs from documentation/ docs

### Phase 3.2 Public docs update command

Commands:

    aictx public-docs update --project <repo> --scope changed --write patch
    aictx public-docs update --project <repo> --scope full --write patch

Changed-scope behavior:

    read changed source files
    read impacted AI context sections
    read only mapped public docs
    generate doc patch
    update public-docs-map.md
    update context.lock.json
    run verifier

Full-scope behavior:

    read all scanner-selected public docs
    compare docs against source facts
    remove stale claims
    add missing implemented behavior
    preserve human readability
    update maps and lockfile

Acceptance:

    changed-scope docs update touches only impacted docs
    full-scope can refresh all public docs explicitly
    normal coding-agent flow still avoids huge public docs
    public docs never become source of truth over code

### Phase 3.3 Optional semantic verification

Command:

    aictx verify --project <repo> --strict --llm

Checks:

    generated AI context contradicts current source
    public docs claim features not implemented
    public docs omit major implemented behavior
    AGENTS.md points to missing context
    compression removed critical safety/build info

Rules:

    optional only
    never required for every local commit
    must use token/cost caps
    must not send secrets
    must fail closed

## Phase 4: Optional OCI-backed model provider and remote execution

Goal: add OCI as an optional accelerator without weakening local-first behavior.

Start Phase 4 only after:

    local dry-run run pipeline works
    strict verifier works
    changed-scope refresh works
    secret gating exists for model-transfer paths
    token budget checks exist
    docs accurately describe local behavior

### Phase 4.1 OCI GenAI local provider

Command:

    aictx run --project <repo> --mode setup-context --execution local --provider oci_genai --write patch

Implementation:

    keep oci dependency optional
    read standard OCI config or env vars
    support compartment OCID
    support model ID
    add auth smoke test
    add structured request/response handling
    add retries with strict caps
    estimate token/cost before calls
    log metadata only by default
    fail clearly on auth, region, quota, and model-access errors

Acceptance:

    tests pass without OCI credentials
    provider-specific tests are skipped without credentials
    one controlled OCI chat call works when configured
    secret findings block transfer
    token budget caps block oversized runs

### Phase 4.2 OCI setup doctor

Command:

    aictx oci doctor

Checks:

    OCI config readable
    compartment accessible
    Generative AI endpoint reachable
    Object Storage bucket accessible when configured
    policies likely sufficient
    budget warning documented

No heavy Terraform requirement yet.

### Phase 4.3 Snapshot and Object Storage exchange

Create snapshot format:

    aictx-snapshot.zip
      manifest.json
      repo/
      inventory.json

Rules:

    include only scanner-approved files
    exclude ignored files
    exclude secrets
    store source hashes
    never include .git unless explicitly needed
    preferably encrypt before upload

Create result bundle:

    aictx-result.zip
      run-report.json
      validation-report.md
      aictx.patch
      generated/

Object layout:

    aictx-runs/<run-id>/input/aictx-snapshot.zip
    aictx-runs/<run-id>/output/aictx-result.zip
    aictx-runs/<run-id>/logs/

### Phase 4.4 Remote worker

Preferred first option:

    OCI Data Science Jobs

Alternative:

    OCI Container Instances

Worker behavior:

    read run env vars
    download snapshot
    unpack into temp dir
    run same AICtx pipeline
    upload result bundle
    exit
    never push to GitHub

Commands:

    aictx run --project <repo> --mode setup-context --execution oci-job --write patch
    aictx public-docs update --project <repo> --scope full --execution oci-job --write patch

### Phase 4.5 Cost and runtime guardrails

Required limits:

    max_input_tokens_per_run
    max_output_tokens_per_run
    max_model_calls_per_run
    max_remote_runtime_minutes
    max_snapshot_size_mb
    max_files_per_run
    require_confirm_above_token_estimate

Remote limits:

    job timeout
    object lifecycle cleanup
    bounded retries
    no infinite loops
    fail on repeated model errors

Acceptance:

    too-large repos fail before cloud work
    secret-bearing snapshots fail before upload
    remote worker can process tiny repo
    result patch returns locally
    no persistent compute remains running

## Phase 5: CI, packaging, and release hardening

Goal: make AICtx repeatable across clones, CI, and real repos.

### Phase 5.1 Expanded tests

Minimum coverage:

    scanner ignores generated files
    scanner includes docs/manifests
    dirty worktree blocks unsafe apply
    secret findings block model/cloud transfer
    inventory stable across repeated runs
    dry_run provider works
    context scaffold writes expected files
    lockfile detects changed source hash
    verifier detects missing context file
    verifier detects manual generated-file edit
    impact map reports stale docs
    patch mode does not modify repo
    apply mode modifies only expected files
    public-docs update patches only mapped docs
    OCI tests are optional/skipped without credentials

Fixtures:

    python_cli_repo
    dotnet_desktop_repo
    docs_heavy_repo
    dirty_repo
    secret_repo

### Phase 5.2 Tiny repo end-to-end validation

Create tiny repo:

    README.md
    docs/public/manual.md
    src/app.py
    tests/test_app.py

Run:

    aictx init --project <tiny-repo>
    aictx scan --project <tiny-repo>
    aictx run --project <tiny-repo> --mode setup-context --execution local --write patch
    aictx run --project <tiny-repo> --mode setup-context --execution local --write apply
    aictx verify --project <tiny-repo> --strict

Then modify src/app.py and verify stale detection.

### Phase 5.3 Real repo validation

First real target:

    StorageMaster

Workflow:

    aictx scan --project <StorageMaster>
    aictx run --project <StorageMaster> --mode setup-context --scope full --execution local --write patch
    review generated context density
    review ai-index routing
    review code-map accuracy
    review AGENTS.md rules
    apply only after review
    aictx verify --project <StorageMaster> --strict

Acceptance:

    generated context is smaller than public docs
    future agents can route through ai-index.md
    verifier catches source/context drift
    public docs are not required for normal coding context

### Phase 5.4 GitHub Actions

For AICtx itself:

    lint
    format check
    typecheck
    tests
    build package

For repos processed by AICtx:

    checkout
    install aictx
    run aictx verify --strict
    upload validation-report.md as artifact
    fail PR on stale AI context or docs impact

Basic verifier CI must not require OCI credentials.

### Phase 5.5 Packaging

Commands:

    uv build
    pipx install .

Acceptance:

    fresh clone installs
    aictx --help works after install
    package metadata correct
    README installation docs correct
    no signing or complex release automation yet

## Version roadmap

### v0.1.x: Local foundation and dry-run context generation

Current line.

Includes:

    scanner
    init
    hash-only verify
    dry_run run pipeline
    context scaffold writer
    AGENTS.md generation
    baseline lockfile
    docs structure
    tests

Remaining v0.1.x hardening:

    ruff exclude .venv
    lockfile staging path fix
    root context.lock.json prevention
    secret suppression for intentional examples
    run artifact completeness
    deterministic fact stability

### v0.2.0: Stable local setup-context workflow

Includes:

    robust local dry-run setup-context generation
    complete staged artifacts
    correct patch/apply behavior
    source-traced deterministic facts
    generated context scaffold
    generated AGENTS.md
    verifier passes after apply
    AICtx dogfoods itself

No real OCI required.

### v0.3.0: Strict verification and changed-scope refresh

Includes:

    expanded context.lock.json
    generated file hash verification
    source section verification
    change-impact-map
    changed-scope refresh
    targeted stale reports

No real OCI required.

### v0.4.0: Public docs mapping and update mode

Includes:

    public-docs-map
    public-docs update --scope changed
    public-docs update --scope full
    public-doc impact detection
    optional semantic verification interface

OCI still optional and not required.

### v0.5.0: OCI local provider

Includes:

    optional OCI dependency
    oci_genai provider
    token/cost caps
    auth/config doctor
    no remote worker yet

### v0.6.0: OCI remote execution

Includes:

    sanitized snapshots
    Object Storage exchange
    result bundles
    remote worker
    cleanup
    remote public-docs refresh

### v0.7.0: CI and packaging hardening

Includes:

    GitHub Actions workflow generation
    PR-safe verifier
    package build/install validation
    expanded fixtures
    real repo validation

### v1.0.0: Stable personal workflow

Includes:

    safe defaults
    local-first context generation
    strict verifier
    docs impact mapping
    optional public-doc updates
    optional OCI acceleration
    successful runs on AICtx and StorageMaster
    no automatic commits or pushes
    documented failure modes

## Remaining implementation order

1. Fix Ruff excludes and formatting.
2. Fix run pipeline context.lock.json placement.
3. Add tests preventing root context.lock.json.
4. Add intentional secret suppression.
5. Complete run artifact writing.
6. Improve deterministic source-traced facts.
7. Dogfood AICtx with local dry_run patch/apply.
8. Expand strict verifier over generated context files and sections.
9. Add change-impact-map and changed-scope refresh.
10. Add public-docs-map.
11. Implement public-docs update mode locally.
12. Add optional semantic verification.
13. Add OCI GenAI provider only after local safety gates exist.
14. Add OCI snapshot/Object Storage/remote worker.
15. Add CI workflow generation.
16. Harden packaging and release workflow.

## Definition of done

AICtx is done for v1 when this works reliably:

    aictx run --project <repo> --mode setup-context --scope full --execution local --write apply
    aictx verify --project <repo> --strict

Then, after a source change:

    aictx verify --project <repo> --strict

must identify stale AI context or affected docs.

Then:

    aictx run --project <repo> --mode setup-context --scope changed --write apply
    aictx public-docs update --project <repo> --scope changed --write patch
    aictx verify --project <repo> --strict

must return the repository to a verified state without forcing normal coding agents to read huge public docs.

## Non-goals before v1

Do not build these before the core CLI is proven:

    persistent hosted service
    web dashboard
    multi-user authentication
    automatic GitHub pushes
    automatic merge behavior
    fully autonomous repo editing without patch review
    claims of mathematical 100 percent documentation correctness

The correct promise is:

    source-traced context
    deterministic stale detection
    targeted docs impact reporting
    fail-closed verification
    optional high-token OCI acceleration
