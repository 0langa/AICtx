# AICtx Documentation

This directory is for human-facing public and developer documentation.

Current implemented status:

- `aictx scan` is fully implemented and tested.
- `aictx init` creates or refreshes `docs/AIprojectcontext/context.lock.json` as a baseline lockfile, preserving generated metadata when present.
- `aictx verify --strict` performs deterministic hash-only verification against that lockfile.
- `aictx run --mode setup-context --execution local --scope full` generates deterministic AI context scaffolding and can stage or apply it. `--scope changed` is not implemented yet.
- `aictx public-docs update` is stubbed.
- `aictx clean` is stubbed.

The main documentation lives in the repository root and this directory:

- [`README.md`](../README.md) — Project overview and quick start.
- [`DOCUMENTATION.md`](DOCUMENTATION.md) — Install, CLI usage, tests, and troubleshooting.
- [`CODEMAP.md`](CODEMAP.md) — File-by-file code map.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — System architecture and current limitations.
- [`aictx_development_plan.md`](../aictx_development_plan.md) — Full development roadmap.
- [`CHANGELOG.md`](CHANGELOG.md) — Unreleased changes and known limitations.
- [`AGENTS.md`](../AGENTS.md) — Guidance for future AI agents working in this repository.
