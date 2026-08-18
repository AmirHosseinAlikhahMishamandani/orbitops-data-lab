# Development Workflow

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
make check
```

## Branches

Use focused feature branches such as `feature/04-ingestion-validation`. Start new work from the latest `main`.

## Commits

Use concise Conventional Commit-style subjects where they fit, for example `feat: validate and deduplicate telemetry`. A commit should represent one understandable engineering change.

## Pull Requests

PR descriptions record motivation, implementation, design decisions, validation and limitations. CI must pass before merge.
