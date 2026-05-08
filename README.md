# AICtx

A local-first CLI tool that prepares Git repositories for low-token AI-agent work.

## Overview

AICtx scans a selected local project, builds a source-traced understanding of its code and documentation, generates a compact AI-facing context system under `docs/AIprojectcontext/`, creates or updates a strict root `AGENTS.md`, verifies that generated context is not stale, and optionally updates human-facing public docs through a high-token mode.

## Installation

```bash
pip install aictx
# or
uv pip install aictx
```

## Quick Start

```bash
aictx init --project <repo>
aictx scan --project <repo>
aictx run --project <repo> --mode setup-context --execution local --write patch
aictx verify --project <repo> --strict
```

## Documentation

See [aictx_development_plan.md](aictx_development_plan.md) for the full project roadmap.
