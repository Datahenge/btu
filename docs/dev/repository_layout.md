# Repository layout

## Frappe app package (`btu/`)

| Path | Role |
|------|------|
| `hooks.py` | Frappe hooks (scheduler events, fixtures, `before_job`) |
| `__init__.py` | Version, `Result`, shared date/cron utilities; re-exports deprecated RQ admin paths |
| `btu_core/` | Product code: DocTypes, task execution, email, reports, housekeeping |
| `btu_api/` | Scheduler daemon integration (Redis RPC, HTTP endpoints) |
| `samples/` | **BTU Task target examples** (`btu.samples.*`) |
| `diagnostics/` | **Developer smoke tests** (`bench execute`; not production tasks) |
| `examples.py`, `manual_tests.py`, `auto_report.py` | Deprecated shims — keep for existing `function_string` values |
| `config/`, `patches/` | Frappe desktop config and migration patches |

## Tests

DocType unit tests live beside controllers (`test_*.py`). Integration tests may be added under `btu/tests/` later.

## User documentation

Published guides live in `docs/` at the repository root (GitHub Pages).

## Boundaries

- Do not move DocTypes outside `btu_core/doctype/` (Frappe sync depends on module paths).
- When relocating callables, keep import shims until a major version bump.
