# AI Context Agent Development Plan

> **Current status:** The scanner milestone is implemented, and a baseline `context.lock.json` plus hash-only verifier MVP are now implemented. Context generation, semantic verification, public-docs update, and OCI integration remain planned.

## Overall goal

Build a local-first CLI tool named `aictx` that prepares Git repositories for low-token AI-agent work. The tool scans a selected local project, builds a source-traced understanding of its code and documentation, generates a compact AI-facing context system under `docs/AIprojectcontext/`, creates or updates a strict root `AGENTS.md`, verifies that generated context is not stale, and optionally updates human-facing public docs through a high-token mode.

The first working product should not be a cloud-hosted app. It should be a safe local CLI that can call OCI Generative AI as the model provider and later offload heavy jobs to ephemeral OCI compute. The repository remains local, generated changes are written as reviewable Git diffs, and OCI resources are used only when a command explicitly needs them.

## Product principles

1. Local repository state is the source of truth.
2. Generated context must be compact, source-traced, and easy for future agents to route through.
3. Normal coding agents should read `AGENTS.md` and `docs/AIprojectcontext/ai-index.md`, not huge human-facing docs.
4. Human docs may be read and rewritten only in the dedicated public-docs mode or when the verifier reports a targeted docs impact.
5. The tool must fail closed: if it cannot prove context freshness, it reports stale or uncertain sections instead of claiming success.
6. No generated files are auto-committed, auto-pushed, or silently written over unrelated user changes.
7. OCI usage is optional per command and guarded by cost, runtime, and upload limits.

## Recommended implementation stack

Use Python for the first version.

Core stack:

- Python 3.12+
- `uv` for environment and packaging
- Typer for CLI commands
- Rich for terminal output
- Pydantic for config and lockfile schemas
- Direct `git` subprocess calls for repository state
- `pathspec` for `.gitignore`/custom ignore matching
- `tree-sitter` later for symbol extraction
- OCI Python SDK for OCI Generative AI, Object Storage, and later remote jobs
- pytest for tests
- ruff for linting/formatting
- mypy or pyright for type checking

Prefer direct `git` subprocess calls for important Git operations because they match user expectations and avoid hidden abstractions.

## Target repository layout for `aictx`

```text
aictx/
  pyproject.toml
  README.md
  AGENTS.md
  src/aictx/
    __init__.py
    cli.py
    config.py
    errors.py
    logging.py
    models/
      inventory.py
      context_lock.py
      run_report.py
      docs_map.py
    git/
      repo.py
      diff.py
      status.py
    scan/
      scanner.py
      ignore.py
      classify.py
      docs.py
      symbols.py
      secrets.py
    llm/
      base.py
      oci_genai.py
      dry_run.py
      prompts.py
      token_budget.py
    context/
      planner.py
      fact_extractor.py
      compressor.py
      writer.py
      lockfile.py
      agents_md.py
    verify/
      verifier.py
      hashes.py
      impact.py
      reports.py
    public_docs/
      mapper.py
      updater.py
      patcher.py
    oci/
      config.py
      object_storage.py
      remote_job.py
      cleanup.py
    io/
      files.py
      patches.py
      jsonl.py
  tests/
    fixtures/
    unit/
    integration/
```

## Target generated scaffold inside each processed project

```text
AGENTS.md
docs/AIprojectcontext/
  ai-index.md
  project-state.md
  code-map.md
  architecture.md
  workflows.md
  public-docs-map.md
  change-impact-map.md
  context.lock.json
  validation-report.md
  schema.md
```

Use this multi-file scaffold instead of one giant context file. A single giant file saves file count but wastes tokens because every future agent has to load irrelevant sections. A routed scaffold lets agents read only the context shard needed for the current task.

## Step 1: Create the CLI skeleton

Goal: establish the project foundation, command structure, config loading, and safe execution conventions.

Implement commands:

```text
aictx init
aictx scan --project <path>
aictx run --project <path> --mode setup-context --execution local
aictx verify --project <path> --strict
aictx public-docs update --project <path> --scope changed
aictx clean --oci
```

Initial behavior:

- `aictx init` currently creates `docs/AIprojectcontext/context.lock.json` and `.aictxignore` if missing. Config initialization is deferred.
- `aictx scan` prints and writes a repository inventory.
- `aictx run` initially calls the dry-run model provider and writes placeholder context only behind `--apply`.
- `aictx verify` currently performs deterministic hash-only validation against the baseline lockfile.
- `aictx public-docs update` can exist as a stub that exits with a clear "not implemented yet" status.
- `aictx clean --oci` can exist as a stub until OCI remote mode exists.

Create config files:

```text
.aictx/config.toml
.aictxignore
```

Example `.aictx/config.toml`:

```toml
[project]
context_dir = "docs/AIprojectcontext"
agents_file = "AGENTS.md"
public_docs_dirs = ["docs", "."]

[execution]
default_execution = "local"
write_mode = "patch"
allow_dirty = false

[limits]
max_input_tokens_per_run = 500000
max_output_tokens_per_run = 100000
max_files_per_run = 5000
max_file_bytes = 250000
max_remote_runtime_minutes = 45

[llm]
provider = "oci_genai"
model = "default"
temperature = 0
```

Acceptance criteria:

```text
aictx --help
aictx init --project <repo>
aictx scan --project <repo>
```

all run successfully on a small test repository.

## Step 2: Implement repository safety checks

Goal: prevent the tool from damaging work or leaking sensitive files.

Implement:

- Git root detection.
- Dirty worktree detection.
- Current branch and commit SHA detection.
- Tracked, untracked, modified, deleted, renamed file detection.
- `.gitignore` parsing.
- `.aictxignore` parsing.
- Default hard excludes.
- Binary file detection.
- Large file exclusion.
- Secret scan before any model call or cloud upload.

Default hard excludes:

```text
.git/**
.aictx/cache/**
.aictx/runs/**
bin/**
obj/**
node_modules/**
dist/**
build/**
.vs/**
.idea/**
*.pfx
*.snk
*.key
*.pem
.env
.env.*
*.sqlite
*.db
```

Dirty-state rule:

- Refuse to apply generated changes if unrelated dirty files exist.
- Allow scanning dirty trees.
- Allow writing only with `--allow-dirty`, but still show a strong warning and write a patch first.

Secret-scan rule:

- If high-confidence secrets are found, do not upload or send affected content to any model.
- Report file paths and secret type, not the secret value.

Acceptance criteria:

- Running on a dirty repo reports the dirty files.
- Files ignored by `.gitignore` and `.aictxignore` are absent from the inventory.
- A fixture containing a fake API key is blocked from model/cloud transfer.

## Step 3: Build the repository inventory model

Goal: produce a deterministic, machine-readable project inventory that later steps can use without rescanning everything.

Create `RepositoryInventory` with:

```text
repo_root
branch
head_commit
dirty_state
files[]
docs[]
manifests[]
build_systems[]
detected_languages[]
entrypoints[]
test_projects[]
generated_at
scanner_version
```

For each file:

```text
path
kind
language
size_bytes
sha256
is_doc
is_source
is_test
is_generated
is_binary
is_ignored
include_reason
exclude_reason
```

Detect at least:

- `.sln`, `.csproj`, `.fsproj`
- `package.json`
- `pyproject.toml`
- `Cargo.toml`
- `go.mod`
- `README.md`
- `CHANGELOG.md`
- `ROADMAP.md`
- `docs/**/*.md`
- `.github/workflows/*.yml`

Write inventory to:

```text
.aictx/runs/<run-id>/inventory.json
```

Acceptance criteria:

- The inventory is stable across repeated scans when files do not change.
- The inventory clearly separates source docs, public docs, generated AI context, tests, build files, and ignored files.

## Step 4: Add project classification

Goal: let the setup agent understand what kind of repository it is before any expensive model call.

Implement deterministic classification first.

For each repo, infer:

```text
primary_language
project_type
build_system
test_system
package_system
app_type
docs_layout
ci_layout
```

Examples:

```text
C# WinUI desktop app
Python CLI tool
Node web app
.NET library
mixed repository
unknown
```

For StorageMaster-style projects, detect:

```text
solution_file
main_app_project
test_projects
XAML/UI files
services
models
viewmodels
packaging/release workflows
```

Acceptance criteria:

- A C#/.NET desktop repo is classified without LLM calls.
- A Python CLI repo is classified without LLM calls.
- Unknown repos still produce a useful inventory instead of failing.

## Step 5: Implement the model provider interface

Goal: isolate the rest of the app from OCI-specific details.

Define:

```python
class ModelProvider:
    def chat(self, request: ChatRequest) -> ChatResponse: ...
    def count_tokens(self, text: str) -> int | None: ...
```

Implement providers:

```text
dry_run
oci_genai
```

The dry-run provider must be good enough for tests and local pipeline development.

Model request fields:

```text
system_prompt
messages
temperature
max_output_tokens
json_schema optional
run_id
purpose
```

Provider requirements:

- Temperature defaults to `0`.
- Every request is logged as metadata only.
- Prompt content is stored only in local run logs when `debug_content_logs = true`.
- Token/cost counters are estimated before sending.
- Requests fail if they exceed configured caps.

Acceptance criteria:

- The scanner and verifier can run without OCI credentials.
- A simple OCI model smoke test can be run with one command.
- Exceeding token limits blocks the request before sending.

## Step 6: Build the context planning stage

Goal: decide what the agent needs to read deeply instead of dumping the whole repository into the model.

Input:

```text
inventory.json
project classification
existing docs/AIprojectcontext if present
existing AGENTS.md if present
```

Output:

```text
context-plan.json
```

The plan should include:

```text
critical_source_files
critical_doc_files
manifest_files
build_files
test_files
files_excluded_from_llm
reason_per_selected_file
estimated_token_cost
```

Selection strategy:

1. Always include manifests and build files.
2. Always include existing AI context files if present.
3. Include root README/ROADMAP/CHANGELOG only for initial setup or public-docs mode.
4. Include source entrypoints and core services.
5. Include tests that reveal behavior.
6. Exclude generated files, binary files, build outputs, and oversized docs unless specifically requested.
7. Prefer changed files and impacted files on refresh runs.

Acceptance criteria:

- The plan chooses a useful subset on a medium repository.
- The plan explains why each selected file is selected.
- The plan stays below configured token limits or fails with a clear "scope too large" report.

## Step 7: Implement fact extraction

Goal: convert selected files into source-traced structured facts before generating final context docs.

Create fact packs such as:

```text
project_identity.json
architecture_facts.json
feature_facts.json
workflow_facts.json
docs_facts.json
risk_facts.json
```

Each fact must have:

```text
id
claim
confidence
source_paths
source_spans optional
derived_from
needs_source boolean
```

Do not generate final markdown directly from raw repo chunks. First generate structured facts. This makes validation, deduplication, and regeneration much easier.

Fact extraction passes:

1. Project identity pass.
2. Architecture pass.
3. Feature/system pass.
4. Build/test/release workflow pass.
5. Public docs map pass.
6. Known risks/limitations pass.

Acceptance criteria:

- Generated facts include source paths.
- Facts without source support are marked `needs_source`.
- Duplicate or conflicting facts are detectable before writing context files.

## Step 8: Implement contradiction and coverage checks

Goal: catch wrong or incomplete model output before writing generated docs.

Checks:

- Same feature described with conflicting status.
- Referenced files do not exist.
- Claimed commands are missing from manifests/workflows.
- Claimed docs do not exist.
- Facts have no source path.
- Important detected files are not represented in any fact pack.
- Existing context claims changed since previous lockfile.

Output:

```text
.aictx/runs/<run-id>/coverage-report.json
.aictx/runs/<run-id>/contradictions.json
```

Fail the run if:

- Critical facts are source-less.
- Contradictions affect project identity, build/test commands, release process, storage model, or public docs mapping.
- Referenced files are missing.

Acceptance criteria:

- A deliberately conflicting fixture causes the run to fail.
- Missing source references are reported with exact fact IDs.
- Non-critical uncertainty is preserved as `unknown` instead of invented.

## Step 9: Generate the AI context scaffold

Goal: write compact AI-facing context files optimized for future coding agents.

Generated files:

```text
docs/AIprojectcontext/ai-index.md
docs/AIprojectcontext/project-state.md
docs/AIprojectcontext/code-map.md
docs/AIprojectcontext/architecture.md
docs/AIprojectcontext/workflows.md
docs/AIprojectcontext/public-docs-map.md
docs/AIprojectcontext/change-impact-map.md
docs/AIprojectcontext/schema.md
docs/AIprojectcontext/validation-report.md
docs/AIprojectcontext/context.lock.json
```

Format rules:

- Short lines.
- Dense key-value style.
- No tutorial prose.
- No marketing language.
- No duplicated explanations across files.
- Source references for important claims.
- Explicit `unknown` or `needs-source` markers where needed.
- Stable headings so diffs are clean.

Recommended file budgets:

```text
ai-index.md <= 500 tokens
project-state.md <= 2000 tokens
code-map.md <= 3000 tokens
architecture.md <= 2000 tokens
workflows.md <= 1200 tokens
public-docs-map.md <= 1500 tokens
change-impact-map.md <= 1500 tokens
```

Acceptance criteria:

- Future agents can understand which file to read from `ai-index.md`.
- The context docs are much smaller than the original public docs.
- Context files reference source paths and avoid unsupported claims.

## Step 10: Generate or update `AGENTS.md`

Goal: direct all future agents to the compact context system and enforce freshness expectations.

`AGENTS.md` must include:

```text
required first read: docs/AIprojectcontext/ai-index.md
primary context source: docs/AIprojectcontext/
avoid huge public docs for general context
when public docs may be read
required pre-commit verification
what to do when AI context is stale
what to do when public docs are impacted
accuracy rules
source-tracing rules
no-fabrication rule
```

Important rule:

Normal agents should not read human docs for general project context. They may read public docs only if the task is documentation-related or `aictx verify --strict` reports a public-docs impact.

Acceptance criteria:

- `AGENTS.md` exists at repo root.
- It points to `docs/AIprojectcontext/ai-index.md`.
- It tells future agents to run `aictx verify --strict` before public commits.
- It tells future agents how to update impacted docs without reading everything.

## Step 11: Implement safe writing and patch mode

Goal: prevent silent destructive edits.

Write flow:

1. Generate all files under `.aictx/runs/<run-id>/out/`.
2. Compare generated output with current repository files.
3. Create a unified diff.
4. Write patch to `.aictx/runs/<run-id>/aictx.patch`.
5. Print summary of files to create/update/delete.
6. Apply only if `--apply` is passed.

Write modes:

```text
--write patch
--write apply
```

Default must be patch.

Never auto-delete user-authored docs unless the generated scaffold explicitly owns the file. For the MVP, avoid deletion entirely.

Acceptance criteria:

- Running without `--apply` does not modify the repo.
- Running with `--apply` modifies only expected files.
- Dirty unrelated files block apply unless explicitly allowed.

## Step 12: Implement `context.lock.json`

Goal: make freshness verification possible without asking an LLM every time.

The lockfile should contain:

```text
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
```

For each generated file:

```text
path
sha256
generated_from_sections
```

For each source file:

```text
path
sha256
kind
included_in_generation
```

For each section:

```text
section_id
generated_file
heading
source_paths
source_hashes
fact_ids
status
```

Acceptance criteria:

- Changing a source file causes the relevant sections to be reported stale.
- Changing a generated context file manually causes hash mismatch detection.
- The verifier can run without LLM calls.

## Step 13: Implement strict verifier

Goal: make `aictx verify --strict` the main freshness gate for humans, agents, and CI.

Checks:

1. Required context files exist.
2. `AGENTS.md` exists and points to `ai-index.md`.
3. `context.lock.json` exists and has a supported schema version.
4. Generated file hashes match the lockfile.
5. Referenced source files exist.
6. Source hashes match the lockfile.
7. Changed source paths map to AI context sections.
8. Changed source paths map to public docs or explicitly declare no public-doc impact.
9. Build/test commands in `workflows.md` still exist.
10. No `needs-source` markers remain in critical sections.
11. No stale generated sections are hidden.

Verifier output:

```text
PASS
FAIL_STALE_AI_CONTEXT
FAIL_PUBLIC_DOCS_IMPACT
FAIL_LOCK_MISMATCH
FAIL_MISSING_SOURCE
FAIL_UNSUPPORTED_SCHEMA
```

Acceptance criteria:

- The verifier succeeds after generation.
- Editing a mapped source file makes verification fail.
- Updating the mapped context makes verification pass again.
- CI can consume the exit code.

## Step 14: Implement change impact mapping

Goal: avoid forcing agents to read or update every doc after every code change.

Generate both markdown and machine-readable mappings.

Example:

```text
src/Services/Duplicate* -> ai:project-state, ai:architecture, docs:docs/public/duplicates.md
src/UI/Settings* -> ai:code-map, ai:project-state, docs:docs/public/settings.md
.github/workflows/* -> ai:workflows, docs:docs/public/release.md
```

Rules:

- Map source areas to AI context files.
- Map source areas to human docs when human docs exist.
- If no public docs exist for a feature, record `docs:none`.
- If a change truly has no public docs impact, require a reason marker.

Add optional local marker file later:

```text
.aictx/no-doc-impact.toml
```

Acceptance criteria:

- A source change produces targeted stale reports.
- Public docs impact is specific, not generic.
- The verifier does not require reading all public docs.

## Step 15: Implement changed-scope context refresh

Goal: make normal refreshes cheap.

Command:

```text
aictx run --project <repo> --mode setup-context --scope changed --write patch
```

Behavior:

1. Read Git diff against a base ref.
2. Identify impacted source files.
3. Use `change-impact-map.md` and `context.lock.json`.
4. Re-read only impacted source and context files.
5. Regenerate only impacted context sections/files.
6. Update lockfile.
7. Run verifier.

Options:

```text
--base origin/main
--base HEAD~1
--scope full
--scope changed
```

Acceptance criteria:

- Small code changes produce small context diffs.
- Full regeneration is still available.
- Changed-scope mode refuses to run if no valid lockfile exists.

## Step 16: Implement public docs map

Goal: know which human-facing docs describe which code areas.

Generate:

```text
docs/AIprojectcontext/public-docs-map.md
```

Also store machine-readable mapping in `context.lock.json`.

For each public doc:

```text
path
purpose
audience
described_features
source_paths
last_verified_source_hashes
stale_risk
```

Do not duplicate full human docs into AI context. Only map them.

Acceptance criteria:

- The tool can say which public docs are impacted by a source change.
- The map is compact.
- Large public docs are not used as default agent context.

## Step 17: Implement public docs update mode

Goal: offload high-token documentation maintenance to a dedicated command instead of making every coding agent do it.

Commands:

```text
aictx public-docs update --project <repo> --scope changed --write patch
aictx public-docs update --project <repo> --scope full --write patch
```

Changed-scope behavior:

1. Read changed files.
2. Read impacted AI context sections.
3. Read only mapped public docs.
4. Generate patches for those docs.
5. Update `public-docs-map.md`.
6. Update `context.lock.json`.
7. Run verifier.

Full-scope behavior:

1. Read all public docs selected by the scanner.
2. Compare docs against source facts.
3. Remove stale claims.
4. Add missing implemented behavior.
5. Preserve user-facing clarity.
6. Update maps and lockfile.

Acceptance criteria:

- Changed-scope updates only impacted docs.
- Full-scope can refresh all public docs when explicitly requested.
- Normal coding-agent context flow still avoids public docs.

## Step 18: Add optional LLM-based semantic verification

Goal: catch stale claims that hash checks cannot catch.

Command:

```text
aictx verify --project <repo> --strict --llm
```

Semantic checks:

- Generated context contradicts current source.
- Public docs claim features that do not exist.
- Public docs omit major implemented behavior.
- `AGENTS.md` points to missing or outdated context rules.
- Context compression removed critical safety or build information.

This mode may cost more and should not be required for every local commit.

Acceptance criteria:

- Hash-only verifier remains fast.
- LLM verifier gives targeted findings with source references.
- LLM verifier never silently edits files.

## Step 19: Add GitHub Actions integration

Goal: enforce freshness before public merges.

Generate workflow:

```text
.github/workflows/aictx-verify.yml
```

Workflow:

```text
checkout
install aictx
run aictx verify --strict --base origin/main
upload validation-report.md as artifact
fail PR on stale AI context or public docs impact
```

Optional PR output:

- `ai-context-impact`
- `public-docs-impact`
- `no-doc-impact-required`
- `aictx-verification-failed`

Do not require OCI credentials for the basic verifier. CI should run hash and impact checks without model calls.

Acceptance criteria:

- A PR that changes source but not impacted context fails.
- A PR that updates source and mapped context passes.
- No OCI model call is needed in basic CI.

## Step 20: Add OCI local model provider

Goal: use OCI Generative AI for local setup and refresh runs.

Implementation:

- Read OCI config from standard OCI config file or environment variables.
- Support compartment OCID.
- Support selected model ID.
- Add request retries with strict caps.
- Add token and approximate cost counters.
- Add structured-output mode where possible.
- Add clear error messages for auth, region, quota, and model access failures.

Command:

```text
aictx run --project <repo> --mode setup-context --execution local --provider oci_genai --write patch
```

Acceptance criteria:

- The CLI can call OCI Generative AI from local mode.
- Failure to authenticate does not corrupt local output.
- Token caps are enforced before calls are sent.

## Step 21: Add OCI resource bootstrap

Goal: make OCI setup repeatable.

Add:

```text
infra/oci/terraform/
```

Provision:

```text
compartment variable
object storage bucket for temporary run artifacts
log group
budget recommendation docs
IAM policy templates
optional dynamic group for remote jobs
```

CLI helper:

```text
aictx oci doctor
```

Checks:

- OCI config readable.
- Compartment accessible.
- Object Storage bucket accessible.
- Generative AI endpoint accessible.
- Required policies appear sufficient.
- Budget warning is configured manually or documented.

Acceptance criteria:

- A new OCI trial account can be prepared from documented steps.
- `aictx oci doctor` reports missing setup clearly.

## Step 22: Add remote execution package format

Goal: prepare for high-token offloading without changing the local pipeline.

Create snapshot format:

```text
aictx-snapshot.zip
  manifest.json
  repo/
  inventory.json
```

Rules:

- Include only scanner-approved files.
- Exclude secrets and ignored files.
- Store source hashes.
- Encrypt snapshot before upload if implemented.
- Never include `.git` unless needed later for diff metadata.

Create result bundle:

```text
aictx-result.zip
  run-report.json
  validation-report.md
  aictx.patch
  generated/
```

Acceptance criteria:

- Local pack/unpack roundtrip works.
- Result bundle can be applied locally as a patch.
- Snapshot refuses to build when secret scan fails.

## Step 23: Add OCI Object Storage exchange

Goal: upload sanitized snapshots and download result bundles for remote workers.

Implement:

```text
aictx oci upload-snapshot
aictx oci download-result
aictx clean --oci --run-id <id>
```

Object layout:

```text
aictx-runs/<run-id>/input/aictx-snapshot.zip
aictx-runs/<run-id>/output/aictx-result.zip
aictx-runs/<run-id>/logs/
```

Retention rule:

- Delete snapshots quickly.
- Keep result bundles only briefly.
- Keep minimal logs.

Acceptance criteria:

- Upload and download work against the configured bucket.
- Cleanup removes all objects for a run.
- Failed runs are still cleanable.

## Step 24: Add OCI remote worker

Goal: run heavy context generation or public-docs refresh in OCI without maintaining a server.

Prefer OCI Data Science Jobs first. Use Container Instances if packaging as a simple container is easier.

Remote worker behavior:

1. Read run environment variables.
2. Download snapshot from Object Storage.
3. Unpack into temp directory.
4. Run same `aictx` pipeline.
5. Write patch/result bundle.
6. Upload result bundle.
7. Exit.
8. Never push to GitHub directly in MVP.

Command:

```text
aictx run --project <repo> --mode setup-context --execution oci-job --write patch
aictx public-docs update --project <repo> --scope full --execution oci-job --write patch
```

Acceptance criteria:

- Remote worker starts, processes a tiny repo, uploads result, and exits.
- Local CLI can download and apply the patch.
- No persistent compute remains running after the job.

## Step 25: Add cost and runtime guardrails

Goal: keep the 30-day OCI trial safe.

Implement local limits:

```text
max_input_tokens_per_run
max_output_tokens_per_run
max_model_calls_per_run
max_remote_runtime_minutes
max_snapshot_size_mb
max_files_per_run
require_confirm_above_token_estimate
```

Implement remote limits:

```text
job timeout
object lifecycle deletion
bounded retries
fail on repeated model errors
no infinite loops
```

Acceptance criteria:

- A too-large repo fails before making expensive calls.
- Retry storms are impossible.
- Remote jobs have a hard timeout.

## Step 26: Add tests

Goal: make the tool safe enough to run on real repositories repeatedly.

Minimum tests:

```text
scanner ignores generated files
scanner includes docs and manifests
dirty worktree blocks apply
secret scan blocks model/cloud transfer
inventory stable across repeated runs
dry-run provider works
context scaffold writes expected files
lockfile detects changed source hash
verifier detects missing context file
verifier detects manual context edit
impact map reports stale docs
patch mode does not modify repo
apply mode modifies only expected files
```

Add integration fixtures:

```text
fixtures/python_cli_repo
fixtures/dotnet_desktop_repo
fixtures/docs_heavy_repo
fixtures/dirty_repo
fixtures/secret_repo
```

Acceptance criteria:

```text
uv run pytest
uv run ruff check .
uv run mypy src
```

pass locally.

## Step 27: Test on a tiny repo first

Goal: validate the end-to-end lifecycle before using a real project.

Create a tiny test repository:

```text
README.md
docs/public/manual.md
src/app.py
tests/test_app.py
```

Run:

```text
aictx init --project <tiny-repo>
aictx scan --project <tiny-repo>
aictx run --project <tiny-repo> --mode setup-context --execution local --write patch
aictx run --project <tiny-repo> --mode setup-context --execution local --write apply
aictx verify --project <tiny-repo> --strict
```

Then modify `src/app.py` and verify stale detection.

Acceptance criteria:

- Initial generation passes.
- Source change causes stale-context failure.
- Refresh fixes the failure.

## Step 28: Test on StorageMaster or another real repo

Goal: prove usefulness on a docs-heavy real codebase.

Run first in patch mode only:

```text
aictx scan --project <StorageMaster>
aictx run --project <StorageMaster> --mode setup-context --scope full --execution local --write patch
```

Review:

- Selected files.
- Generated context density.
- Whether `ai-index.md` routes well.
- Whether `code-map.md` points to the actual important files.
- Whether `AGENTS.md` gives correct future-agent rules.
- Whether verifier passes.

Then apply if the patch is good:

```text
aictx run --project <StorageMaster> --mode setup-context --scope full --execution local --write apply
aictx verify --project <StorageMaster> --strict
```

Acceptance criteria:

- Generated context is meaningfully smaller than existing docs.
- Future agents can use the generated context without reading all human docs.
- The verifier catches stale state after source changes.

## Step 29: Build the first public release workflow for `aictx`

Goal: make the tool installable and reproducible.

Implement:

```text
uv build
pipx install .
```

Add GitHub Actions for `aictx` itself:

```text
lint
typecheck
test
build package
```

Do not add signing or complex release automation yet.

Acceptance criteria:

- Fresh clone can install the CLI.
- CI passes.
- Basic usage is documented.

## Step 30: Version roadmap

Progress as of the current codebase:

### v0.1.0: Local scanner — COMPLETED

Includes CLI skeleton, config models, ignore handling, Git state, inventory, docs detection, project classification, secret scanning, and safe scan reports. All acceptance criteria are met and tests pass.

### v0.2.0: Local context generation — PLANNED

Includes context planning, fact extraction, context scaffold writer, and `AGENTS.md` generation. The dry-run model provider exists. The OCI model provider is stubbed. Context generation modules are stubbed.

### v0.3.0: Verification and lockfile — PLANNED

Includes `context.lock.json`, strict verifier, generated file hash checks, source hash checks, and stale section reports. The lockfile model and I/O helpers exist. The verifier always returns `PASS`.

### v0.4.0: Change impact and cheap refresh — PLANNED

Includes `change-impact-map.md`, changed-scope regeneration, public docs impact detection, and targeted stale reports. Impact mapping is stubbed.

### v0.5.0: Public docs updater — PLANNED

Includes changed-scope and full-scope public-docs update mode, patch output, public docs map refresh, and verifier integration. All public-docs modules are stubbed.

### v0.6.0: GitHub Actions verifier — PLANNED

Includes CI workflow generation, PR-safe verifier, and no-model validation in CI.

### v0.7.0: OCI remote heavy mode — PLANNED

Includes sanitized snapshots, Object Storage exchange, remote worker, result bundles, cleanup, and remote public-docs refresh. All OCI modules are stubbed.

### v1.0.0: Stable personal workflow — PLANNED

Includes safe defaults, tests, documentation, cost caps, OCI setup docs, stable generated scaffold, and successful runs on at least two real repositories.

## Initial MVP cut

Build only this first:

```text
aictx init
aictx scan
aictx run --mode setup-context --execution local --write patch/apply
aictx verify --strict
```

The MVP must generate:

```text
AGENTS.md
docs/AIprojectcontext/ai-index.md
docs/AIprojectcontext/project-state.md
docs/AIprojectcontext/code-map.md
docs/AIprojectcontext/architecture.md
docs/AIprojectcontext/workflows.md
docs/AIprojectcontext/context.lock.json
docs/AIprojectcontext/validation-report.md
```

Delay these until after the MVP works:

```text
remote OCI jobs
public docs full rewrite
GitHub PR automation
web UI
multi-user support
automatic commits
```

## Implementation order summary

Completed:

1. CLI skeleton.
2. Config models (TOML loading not yet implemented).
3. Repository scanner.
4. Inventory model.
5. Project classifier.
6. Dry-run model provider.
7. Secret scanning.
8. File I/O helpers and JSONL utilities.
9. `AGENTS.md` template generator.
10. Context lockfile model and I/O helpers.
11. Basic test suite (scanner, CLI, integration).

Planned / stubbed:

12. OCI model provider.
13. Context planning.
14. Fact extraction.
15. Coverage and contradiction checks.
16. Context scaffold writer.
17. Patch/apply writer.
18. Strict verifier.
19. Change impact map.
20. Changed-scope refresh.
21. Public docs map.
22. Public docs updater.
23. GitHub Actions verifier.
24. OCI setup doctor.
25. Snapshot/result bundle format.
26. Object Storage exchange.
27. Remote worker.
28. Cost/runtime guardrails.
29. Real-repo validation.
30. Package/release workflow.

## Definition of done for the whole system

The project is not yet at the definition of done. The target end state is:

```text
aictx run --project <repo> --mode setup-context --scope full --execution local --write apply
aictx verify --project <repo> --strict
```

Then, after a code change:

```text
aictx verify --project <repo> --strict
```

must identify exactly which AI context and public docs are stale.

Then:

```text
aictx run --project <repo> --mode setup-context --scope changed --write apply
aictx public-docs update --project <repo> --scope changed --write patch
aictx verify --project <repo> --strict
```

must return the repository to a verified state without forcing the coding agent to read huge human-facing docs.

Currently, `aictx run` and `aictx verify` are stubbed, so this workflow is not yet achievable.

## Non-goals for v1

Do not build these before the core CLI is proven:

1. Persistent hosted service.
2. Web dashboard.
3. Multi-user authentication.
4. Automatic GitHub pushes.
5. Automatic merge/commit behavior.
6. Fully autonomous repo editing without patch review.
7. Claiming mathematical certainty that docs are "100% correct".

The correct promise is stricter and more honest: source-traced context, deterministic stale detection, targeted docs impact reporting, and fail-closed verification.
