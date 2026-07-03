# Notes for AI / automation

**Read this file first** before making changes in this repository.

## Read order

| Order | File | Why |
|-------|------|-----|
| 1 | [AGENTS.md](AGENTS.md) | This file — project map, conventions, boundaries |
| 2 | [README.md](README.md) | Product overview, links to official docs |
| 3 | [docs/index.md](docs/index.md) | Local documentation index |
| 4 | Topic-specific docs under [docs/](docs/) | Installation, configuration, CLI/web guides, FAQ |
| 5 | [btu/btu_api/REFERENCE.md](btu/btu_api/REFERENCE.md) | Scheduler Redis RPC protocol (when touching scheduler integration) |

Official user documentation: <https://datahenge.github.io/btu/>

## What this is

**Background Tasks Unleashed (BTU)** is a [Frappe Framework](https://frappeframework.com) app for scheduling and running Python background tasks. It replaces Frappe's built-in Scheduled Job Types with cron-based schedules, full stdout/stderr logging, email notifications, and an optional external scheduler daemon.

- **Branch:** (see current git branch)
- **Python Version:** (see [pyproject.toml](pyproject.toml))
- **Publisher:** Datahenge LLC — maintainer Brian Pond
- **License:** MIT

## Related projects (separate repos)

Do not confuse this repo with these companions:

| Project | Purpose |
|---------|---------|
| [btu_scheduler_daemon](https://github.com/Datahenge/btu_scheduler_daemon) | Rust scheduler daemon (legacy) |
| [btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py) | Python scheduler daemon (2025+) |

Scheduler ↔ Frappe communication uses a Redis RPC protocol documented in [docs/scheduler_redis_rpc.md](docs/scheduler_redis_rpc.md).

## Repository layout

```
btu/                          # Python package root (Frappe app)
├── hooks.py                  # Frappe hooks (scheduler_events, fixtures, before_job)
├── __init__.py               # Version, Result class, shared utilities
├── examples.py               # Sample BTU Task target functions
├── auto_report.py            # Scheduled report build and delivery
├── btu_core/                 # Core DocTypes and task execution
│   ├── task_runner.py        # RQ entry point; runs BTU Tasks in workers
│   ├── run_later.py          # Deferred execution helpers
│   ├── housekeeping.py       # BTU-specific maintenance (e.g. transient log cleanup)
│   ├── wrapped_function.py   # Function wrapping for logging
│   └── doctype/              # BTU Task, BTU Task Schedule, BTU Task Log, etc.
├── btu_api/                  # Scheduler daemon API (Redis RPC, endpoints)
├── patches/                  # Migration patches
└── config/                   # Desktop module config

docs/                         # Markdown documentation (published to GitHub Pages)
```

Frappe modules (see [btu/modules.txt](btu/modules.txt)): `btu_core`, `btu_api`.

## Architecture (short)

1. **BTU Task** — defines a callable Python function path and arguments.
2. **BTU Task Schedule** — binds a Task to a cron expression (with timezone support).
3. **BTU Task Log** — records execution output, status, and timing.
4. **RQ (Redis Queue)** — Frappe workers execute tasks via `run_task_by_id` in `task_runner.py`.
5. **External scheduler** (optional) — polls schedules and enqueues work; controlled via Redis RPC.

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
- **Tests:** DocType tests live alongside DocTypes (`test_<doctype>.py`). Run via bench, not standalone pytest.
- **Do not** add cross-dependencies on other custom Frappe apps unless explicitly requested.

## Editor setup

Open [btu.code-workspace](btu.code-workspace) in VS Code / Cursor. It assumes this repo lives at `<bench>/apps/btu` with Frappe at `<bench>/apps/frappe`, and uses the bench virtualenv at `<bench>/env/bin/python`.

Ruff lint/format settings extend [../frappe/pyproject.toml](../frappe/pyproject.toml). Optional CLI install: `../../env/bin/pip install -e ".[dev]"` from this directory.

## Bench commands (typical)

This app is installed in a Frappe bench site. Common operations:

```bash
# From the bench directory (not this app directory):
bench --site <site> migrate
bench --site <site> run-tests --app btu
bench --site <site> console   # interactive Python shell with frappe loaded
bench restart                 # after hooks.py or worker-related changes
```

Linux build prerequisites for scheduler daemon: `pkg-config libsystemd-dev`.

## Boundaries — do not change without explicit request

- Version numbers in [btu/__init__.py](btu/__init__.py) and git tags
- Published GitHub Pages docs in `docs/` (unless the task is documentation)
- LICENSE or copyright headers
- Unrelated DocType JSON field changes (schema migrations need care)

## Cursor rules

Project-specific agent rules live in [.cursor/rules/](.cursor/rules/). They supplement this file with always-on or file-scoped guidance.
