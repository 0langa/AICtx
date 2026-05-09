# AICtx Completion Plan (Production v1 Finalization Roadmap)

> Goal
>
> Bring AICtx from its current advanced local-first state to a stable, operationally hardened, production-ready v1 workflow where all original day-1 goals are fully implemented, validated, documented, reproducible, and safely enforceable.
>
> Assumed current state:
>
> - Local-first execution pipeline works
> - Repository scanner works
> - Context generation pipeline works
> - Changed-scope regeneration works
> - Verifier core works
> - Public-docs update pipeline works
> - Patch/apply workflow works
> - OCI provider foundation exists
> - Dummy repo validation exists
> - Initial real-repo validation exists
>
> This roadmap therefore focuses ONLY on:
>
> - OCI completion
> - operational hardening
> - deterministic execution
> - packaging/release stabilization
> - safety enforcement
> - large-scale validation
> - final productionization

---

# Core architectural constraints

These rules are mandatory and must never regress.

---

## 1. Local-first remains canonical

Primary execution model:

    local repo
    -> local scanner
    -> local planner
    -> local generation
    -> local verifier
    -> local patch/review/apply

OCI exists ONLY for:

    large generation runs
    large public-doc refreshes
    high-token workloads
    cross-repo audits
    heavy validation

Never invert this architecture.

---

## 2. OCI must never fork business logic

OCI runtime must execute the SAME pipeline as local mode.

Forbidden:

    OCI-only generation logic
    OCI-only verifier behavior
    OCI-only context formats
    OCI-only stale-doc rules

Allowed:

    OCI transport
    OCI orchestration
    OCI runtime wrappers
    OCI storage exchange
    OCI lifecycle handling

---

## 3. Patch-first workflow is mandatory

AICtx must never silently mutate repositories.

Required workflow:

    generate
    -> diff
    -> patch
    -> review
    -> optional apply

Default behavior:

    write patch
    NOT auto-apply
    NOT auto-commit
    NOT auto-push

---

## 4. Verification must remain mostly deterministic

Verifier correctness must NOT primarily depend on LLM behavior.

Primary mechanisms:

    hashes
    source tracing
    impact maps
    schema validation
    manifest validation
    dependency mapping
    deterministic comparison

LLM validation remains supplemental only.

---

## 5. Fail closed by default

If safety or correctness cannot be determined:

    abort
    report clearly
    require explicit override

Never silently continue.

---

# End-state definition

At roadmap completion the following workflows must function reliably.

---

## Local full generation

    aictx run \
      --project <repo> \
      --mode setup-context \
      --scope full \
      --execution local \
      --write apply

---

## Strict verification

    aictx verify \
      --project <repo> \
      --strict

---

## Changed-scope regeneration

    aictx run \
      --project <repo> \
      --mode setup-context \
      --scope changed \
      --execution local \
      --write apply

---

## Public docs refresh

    aictx public-docs update \
      --project <repo> \
      --scope changed \
      --write patch

---

## OCI remote execution

    aictx run \
      --project <repo> \
      --mode setup-context \
      --execution oci-job \
      --write patch

---

## Operational guarantees

All of the following must be true:

    OCI remote execution works reliably
    snapshot upload/download is hardened
    CI verification is enforceable
    stale-doc detection is trustworthy
    installation is reproducible
    runtime limits are enforced
    cost limits are enforced
    large repos validate successfully
    generated context remains compact
    context regeneration remains stable
    failure modes are handled safely

---

# Phase 1 — OCI infrastructure completion

## Goal

Convert OCI integration from partial/stubbed state into production-capable infrastructure.

---

## 1.1 Finalize OCI SDK integration

Current known state:

    OCI CLI works
    OCI auth works
    compartment works
    OCI doctor mostly works
    Python OCI SDK integration incomplete

Tasks:

    add optional OCI dependency group
    install OCI SDK inside uv environment
    validate SDK imports
    validate auth from Python runtime
    validate compartment access
    validate bucket access
    validate region compatibility

Required command:

    uv run aictx oci doctor

Required output:

    ready: True

---

## 1.2 Finalize OCI isolation layer

Complete:

    src/aictx/oci/

Required modules:

    config.py
    object_storage.py
    remote_job.py
    cleanup.py
    snapshot.py
    bundle.py
    worker.py
    runtime.py
    errors.py
    logging.py

Requirements:

    bounded retries
    typed OCI exceptions
    structured logging
    timeout enforcement
    safe cleanup guarantees
    lazy imports
    isolated OCI dependencies
    deterministic log structure

Rules:

    core pipeline must NOT import OCI internals
    OCI must remain replaceable
    OCI failures must never corrupt local state

---

## 1.3 Add OCI config system

Support:

    [oci]
    enabled = true
    region = "eu-frankfurt-1"
    compartment_id = "..."
    bucket = "aictx-run-artifacts"
    profile = "DEFAULT"
    max_snapshot_size_mb = 250
    max_remote_runtime_minutes = 45
    max_upload_retries = 3
    max_download_retries = 3

Validation requirements:

    missing auth
    missing compartment
    missing bucket
    invalid profile
    unsupported region
    invalid retry counts
    runtime caps out of bounds
    missing permissions

---

## 1.4 Add OCI capability detection

Implement:

    aictx oci capabilities

Must validate:

    object storage
    job execution
    bucket permissions
    log retrieval
    cleanup permissions
    artifact exchange

---

## 1.5 Add OCI runtime budgeting

Implement estimation for:

    snapshot upload size
    estimated runtime
    estimated token usage
    estimated OCI cost

Require confirmation above configured thresholds.

---

# Phase 2 — Snapshot packaging system

## Goal

Create deterministic, reproducible, fail-closed snapshot packaging.

---

## 2.1 Build sanitized snapshot creator

Command:

    aictx snapshot create

Output:

    aictx-snapshot.zip

Structure:

    manifest.json
    inventory.json
    repo/

Requirements:

    exclude ignored files
    exclude generated artifacts
    exclude caches
    exclude secrets
    exclude .git
    store hashes
    store metadata
    store scanner config hash
    store generation metadata

Must fail closed.

---

## 2.2 Add deterministic archive generation

Snapshot generation must be reproducible.

Requirements:

    stable file ordering
    stable timestamps
    stable manifest ordering
    stable compression behavior
    deterministic hashing

Same repo state must produce identical snapshot hashes.

---

## 2.3 Add snapshot verification

Implement:

    manifest validation
    hash validation
    archive integrity validation
    forbidden path validation

Reject by default:

    .env
    .pem
    .key
    .pfx
    .db
    sqlite
    logs
    bin
    obj
    dist
    build

unless explicitly overridden.

---

## 2.4 Add snapshot hard limits

Limits must trigger BEFORE upload.

Required limits:

    max files
    max bytes
    max upload size
    max token estimate
    max archive depth
    max generated output size

---

## 2.5 Add mandatory secret scanning

Detect:

    API keys
    private keys
    certificates
    tokens
    connection strings
    embedded credentials

Failure behavior:

    abort snapshot creation
    show offending paths
    require explicit override

---

# Phase 3 — OCI Object Storage exchange

## Goal

Enable hardened OCI artifact lifecycle.

---

## 3.1 Build artifact exchange layer

Commands:

    aictx oci upload-snapshot
    aictx oci download-result

Object structure:

    aictx-runs/<run-id>/input/
    aictx-runs/<run-id>/output/
    aictx-runs/<run-id>/logs/

Requirements:

    upload retries
    download retries
    collision prevention
    checksum validation
    partial failure recovery
    safe overwrite rules
    multipart upload support

---

## 3.2 Add bundle verification

Downloaded bundles must verify:

    bundle integrity
    manifest correctness
    patch integrity
    schema compatibility
    hash correctness

Reject corrupted bundles automatically.

---

## 3.3 Add OCI cleanup tooling

Command:

    aictx clean --oci

Requirements:

    delete stale snapshots
    delete stale bundles
    delete stale logs
    dry-run mode
    confirm mode
    age filters
    run-id filters

Never silently mass-delete.

---

## 3.4 Add lifecycle documentation

Create:

    docs/public/oci-storage.md

Document:

    retention strategy
    artifact lifecycle
    cost expectations
    cleanup behavior
    snapshot safety model
    failure recovery behavior

---

# Phase 4 — Remote OCI worker execution

## Goal

Run the existing local pipeline remotely without architectural divergence.

---

## 4.1 Build OCI worker runtime

Implement:

    src/aictx/oci/worker.py

Worker flow:

    download snapshot
    verify snapshot
    unpack snapshot
    run local pipeline
    generate patch
    generate reports
    upload bundle
    exit cleanly

Critical rule:

    same pipeline as local mode

No duplicated generation logic.

---

## 4.2 Add OCI Data Science Job runtime

Primary target:

    OCI Data Science Jobs

Command:

    aictx run --execution oci-job

Required:

    job launch
    status polling
    runtime timeout
    cancellation support
    structured logs
    stdout/stderr retrieval
    result retrieval

---

## 4.3 Add remote result bundles

Output:

    aictx-result.zip

Contents:

    aictx.patch
    validation-report.md
    run-report.json
    generated/
    logs/

Local user still manually reviews/apply.

---

## 4.4 Add OCI failure hardening

Handle safely:

    job timeout
    upload failure
    download failure
    OCI throttling
    expired auth
    missing bucket
    bundle corruption
    network interruption
    partial uploads
    partial downloads

All failures must:

    fail safely
    clean safely
    report clearly
    preserve diagnostics

---

## 4.5 Add resumable OCI operations

Allow safe resumption for:

    download resume
    polling resume
    artifact retrieval resume
    cleanup resume

Never resume partial generation blindly.

---

# Phase 5 — CI enforcement

## Goal

Turn verifier into enforceable repository policy.

---

## 5.1 Generate GitHub Actions verifier workflow

Create:

    .github/workflows/aictx-verify.yml

Workflow:

    checkout
    install uv
    install aictx
    run strict verify
    upload reports
    fail on stale context/docs

No OCI dependency required.

---

## 5.2 Add machine-readable verifier output

Add:

    --json

Output schema:

    {
      "status": "...",
      "stale_sections": [],
      "docs_impacts": [],
      "missing_sources": [],
      "warnings": [],
      "errors": []
    }

---

## 5.3 Add optional local hooks

Provide optional:

    pre-commit
    pre-push

Location:

    .aictx/hooks/

Hooks must remain opt-in.

---

## 5.4 Add CI artifact reporting

Upload:

    validation-report.md
    verify.json
    run-report.json

as workflow artifacts.

---

# Phase 6 — Real-world hardening

## Goal

Stress-test AICtx against large repositories and hostile edge cases.

---

## 6.1 Large-repo validation

Repeatedly validate against:

    StorageMaster
    AICtx
    mixed-language repos
    docs-heavy repos
    large monorepos
    binary-heavy repos

Validate:

    selection quality
    token efficiency
    patch cleanliness
    runtime stability
    stale detection accuracy

---

## 6.2 Expand integration fixtures

Add fixtures for:

    monorepo
    docs-heavy repo
    binary-heavy repo
    secret-heavy repo
    broken-docs repo
    generated-output-heavy repo
    large dependency repo

---

## 6.3 Add regression tests

Explicitly test:

    OCI upload exclusions
    snapshot integrity
    bundle corruption
    retry logic
    impact-map precision
    public-doc refresh accuracy
    context regeneration stability

---

## 6.4 Add performance instrumentation

Track:

    scan duration
    generation duration
    verify duration
    token estimate
    selected file count
    patch size
    snapshot size
    remote runtime

Store inside:

    run-report.json

---

## 6.5 Add context entropy detection

Prevent gradual degradation of compact AI docs.

Detect:

    duplicate facts
    redundant sections
    bloated shards
    stale routing
    unused shards

Warn on excessive growth.

---

# Phase 7 — Packaging and release stabilization

## Goal

Make AICtx installable, reproducible, and distributable.

---

## 7.1 Stabilize packaging

Required workflows:

    uv build
    pipx install .

Must support:

    core install
    OCI extras install
    dependency isolation
    reproducible builds

---

## 7.2 Add release pipeline

GitHub Actions pipeline:

    lint
    format check
    typecheck
    tests
    integration tests
    build
    artifact upload

Excluded for v1:

    signing
    auto-release publishing

---

## 7.3 Finalize public documentation

Finalize:

    README.md
    docs/public/*
    AGENTS.md

Document:

    architecture
    verification philosophy
    snapshot safety
    OCI workflow
    patch-first workflow
    cost-control model

---

## 7.4 Add installation validation matrix

Validate installation on:

    Windows
    Linux
    WSL
    fresh virtualenv
    pipx
    uv

---

# Phase 8 — Final stabilization pass

## Goal

Declare v1 operationally complete and trustworthy.

---

## 8.1 Full workflow validation

Validate complete lifecycle:

    fresh install
    scan repo
    generate context
    verify
    modify source
    changed-scope refresh
    public-doc refresh
    remote OCI execution
    patch retrieval
    verify again

---

## 8.2 Failure-mode audit

Explicitly test:

    interrupted runs
    corrupted snapshots
    OCI outages
    invalid auth
    invalid schemas
    stale docs
    missing sources
    bundle corruption
    missing lockfiles

---

## 8.3 Cleanup audit

Ensure:

    temporary OCI artifacts removed
    local temp dirs cleaned
    snapshot retention enforced
    bundle cleanup enforced

---

## 8.4 Cost-control audit

Validate:

    token caps
    runtime caps
    snapshot caps
    retry caps
    confirmation gates
    OCI cleanup guarantees

No unbounded OCI usage allowed.

---

## 8.5 Determinism audit

Validate reproducibility of:

    snapshot generation
    verify output
    context regeneration
    patch generation

Repeated identical runs should produce minimal drift.

---

# Final v1 definition

AICtx v1 is complete when:

    safe local-first workflow exists
    OCI heavy execution works
    strict verification works
    changed-scope refresh works
    public-doc updates work
    CI enforcement works
    snapshot upload is hardened
    real repos validate successfully
    installation is reproducible
    runtime limits are enforced
    cost limits are enforced

And critically:

    normal coding agents no longer need to read giant human docs for general repo context

because:

    AGENTS.md
    -> ai-index.md
    -> routed compact context shards

already provide reliable project routing.

---

# Explicit non-goals (remain excluded)

Do NOT build before post-v1:

    web dashboard
    persistent backend
    multi-user auth
    automatic pushes
    automatic merges
    autonomous repo editing
    always-on OCI infrastructure
    multi-tenant SaaS architecture

AICtx is infrastructure for reliable AI-assisted repository workflows.

It is NOT intended to become an autonomous coding platform.

# Post-v1 deferrals (partial items explicitly excluded from v1 scope)

The following items are intentionally deferred — they are recognized as incomplete
but are NOT required for v1 completion. They will be revisited post-v1 when
semantic reasoning, live OCI automation, or prose generation needs arise.

    1. semantic freshness verification
    2. fully proven live OCI execution in automation
    3. automated public-doc prose rewriting

Each is tracked in the repo's changelog / issue tracker for visibility.