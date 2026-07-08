# Notes for AI / automation

**Read this file first** before making changes in this repository.

## Read order

| Order | File | Why |
|-------|------|-----|
| 1 | [AGENTS.md](AGENTS.md) | This file — project map, conventions, boundaries |
| 2 | [README.md](README.md) | Product overview, links to official docs |
| 3 | [docs/index.md](docs/index.md) | Documentation home (MkDocs source) |
| 4 | [mkdocs.yml](mkdocs.yml) | Site nav and build config |
| 5 | Topic docs under [docs/](docs/) | get-started, concepts, guides, scheduler, … |
| 6 | [docs/scheduler/redis-rpc.md](docs/scheduler/redis-rpc.md) | Scheduler Redis RPC (when touching scheduler integration) |
| 7 | [docs/internals/](docs/internals/) | Technical design, contributor docs |
| 8 | [dev-docs/](dev-docs/) | Internal, unpublished maintainer notes (ADRs, repository layout) |

Official user documentation: <https://btu.datahenge.com/>

## What this is

**Background Tasks Unleashed (BTU)** is a [Frappe Framework](https://frappeframework.com) app for scheduling and running Python background tasks. It replaces Frappe's built-in Scheduled Job Types with cron-based schedules, full stdout/stderr logging, email notifications, and an external scheduler daemon.

- **Branch:** (see current git branch)
- **Python Version:** (see [pyproject.toml](pyproject.toml))
- **Publisher:** Datahenge LLC — maintainer Brian Pond
- **License:** MIT

## Related projects (separate repos)

BTU is **one product, two required components**. User docs are unified at btu.datahenge.com; code stays in separate repos.

| Project | Purpose |
|---------|---------|
| [btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py) | **Canonical** Python scheduler daemon |
| [btu_scheduler_daemon](https://github.com/Datahenge/btu_scheduler_daemon) | Rust scheduler — **retired** |

Scheduler ↔ Frappe communication uses Redis RPC documented in [docs/scheduler/redis-rpc.md](docs/scheduler/redis-rpc.md).

## Repository layout

```
btu/                          # Python package root (Frappe app)
├── hooks.py                  # Frappe hooks (scheduler_events, fixtures, before_job)
├── __init__.py               # Version; re-exports btu.utils and rq_admin shims
├── logging.py                # BTU logger configuration
├── utils/                    # Shared helpers (Result, dates, cron, messaging)
├── samples/                  # Example BTU Task target functions
├── diagnostics/              # bench execute smoke tests (not production tasks)
├── tests/                    # Cross-module unit tests
├── btu_core/                 # Core DocTypes and task execution
├── btu_api/                  # Scheduler daemon API (Redis RPC, endpoints)
├── patches/                  # Migration patches
├── fixtures/                 # Exported Workspaces
└── config/                   # Desktop module config

docs/                         # MkDocs source → https://btu.datahenge.com/
mkdocs.yml                    # Documentation site configuration
```

Frappe modules (see [btu/modules.txt](btu/modules.txt)): `btu_core`, `btu_api`.

## Architecture (short)

1. **BTU Task** — defines a callable Python function path and arguments.
2. **BTU Task Schedule** — binds a Task to a cron expression (with timezone support).
3. **BTU Task Log** — records execution output, status, and timing.
4. **RQ (Redis Queue)** — Frappe workers execute tasks via `run_task_by_id` in `task_runner.py`.
5. **Scheduler daemon** (required for recurring schedules) — [btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py); controlled via Redis RPC. See [docs/internals/technical-design.md](docs/internals/technical-design.md).

Key hook in [btu/hooks.py](btu/hooks.py):

- `scheduler_events` — cron job every 5 minutes to detect timed-out in-progress logs
- `before_job` — suppresses deprecation warnings in workers
- `fixtures` — exports BTU_Core Workspaces

## Development conventions

- **Match existing style** in each file (this codebase uses tabs in many Python files).
- **Frappe patterns:** DocTypes live in `doctype/<name>/` with `.json`, `.py`, and optional `.js` files.
- **Minimize scope:** BTU is a focused scheduling app — avoid unrelated refactors or new abstractions.
- **Result type:** Use `btu.Result` for functions that return success/failure with a message.
- **Logging:** BTU tasks use the `btu` logger; level is controlled by `BTU_LOG_LEVEL` env var and `BTU Configuration.force_debug_mode`.
- **Patches:** Add data migrations in [btu/patches.txt](btu/patches.txt) under `btu/patches/`.
- **Tests:** DocType tests live alongside DocTypes (`test_<doctype>.py`). Cross-module tests live in `btu/tests/`. Run via bench, not standalone pytest.
- **Do not** add cross-dependencies on other custom Frappe apps unless explicitly requested.

## Editor setup

Open [btu.code-workspace](btu.code-workspace) in VS Code / Cursor — **BTU + Frappe** (bench layout: `apps/btu`, `apps/frappe`, `env/bin/python`).

Optional cross-repo workspace: copy [btu-full.code-workspace.example](btu-full.code-workspace.example) to gitignored `btu-full.code-workspace` and set the scheduler folder path.

Docs: `pip install -e ".[docs]"` then `mkdocs serve`. See [docs/internals/contributing-docs.md](docs/internals/contributing-docs.md).

Ruff lint/format settings extend [../frappe/pyproject.toml](../frappe/pyproject.toml).

## Bench commands (typical)

```bash
bench --site <site> migrate
bench --site <site> run-tests --app btu
bench --site <site> console
bench restart
```

## Boundaries — do not change without explicit request

- Version numbers in [btu/__init__.py](btu/__init__.py) and git tags
- LICENSE or copyright headers
- Unrelated DocType JSON field changes (schema migrations need care)

## Cursor rules

Project-specific agent rules live in [.cursor/rules/](.cursor/rules/). They supplement this file with always-on or file-scoped guidance.
