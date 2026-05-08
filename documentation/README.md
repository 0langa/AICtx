# AICtx Documentation

Docs index.

Current repo state:

- `scan` implemented
- `init` implemented
- `verify --strict [--json]` implemented, deterministic hash/linkage
- `status --json` implemented
- `run --mode setup-context --execution local --scope full|changed` implemented
- `run` model-transfer and token/file budget preflight implemented
- changed-scope targeted context refresh implemented
- `public-docs update` deterministic review/patch flow implemented; no prose rewrite
- local `clean` implemented
- `oci doctor` implemented; remote OCI work still stubbed

Files:

- [`README.md`](../README.md) — project overview / quick start
- [`DOCUMENTATION.md`](DOCUMENTATION.md) — usage / workflow / troubleshoot
- [`CODEMAP.md`](CODEMAP.md) — file map
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — architecture / implemented seams / limits
- [`CHANGELOG.md`](CHANGELOG.md) — unreleased changes / known limitations
- [`aictx_development_plan.md`](../aictx_development_plan.md) — AI-only roadmap
- [`AGENTS.md`](../AGENTS.md) — repo agent instructions
