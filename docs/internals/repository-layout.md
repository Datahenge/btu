# Repository layout

## Frappe app package (`btu/`)

| Path | Role |
|------|------|
| `hooks.py` | Frappe hooks (scheduler events, fixtures, `before_job`) |
| `__init__.py` | Version; re-exports `btu.utils` and deprecated RQ admin paths |
| `utils/` | `Result`, date/time helpers, cron validation, `print_both` |
| `tests/` | Cross-module unit tests (`test_utils_*`, `test_auto_report`, …) |
| `btu_core/` | Product code: DocTypes, task execution, email, reports, housekeeping |
| `btu_api/` | Scheduler daemon integration (Redis RPC, HTTP endpoints) |
| `samples/` | **BTU Task target examples** (`btu.samples.*`) |
| `diagnostics/` | **Developer smoke tests** (`bench execute`; not production tasks) |
| `examples.py`, `manual_tests.py`, `auto_report.py` | Deprecated shims — keep for existing `function_string` values |
| `config/`, `patches/` | Frappe desktop config and migration patches |

## Tests

DocType unit tests live beside controllers (`test_*.py`). Cross-module tests live in `btu/tests/`.

## User documentation

Published at [https://btu.datahenge.com/](https://btu.datahenge.com/) — MkDocs source in `docs/`, config in `mkdocs.yml`. Scheduler user docs are authored here (not a separate site).

## Boundaries

- Do not move DocTypes outside `btu_core/doctype/` (Frappe sync depends on module paths).
- When relocating callables, keep import shims until a major version bump.
