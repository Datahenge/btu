# Version policy

## Frappe app

- **Branch `version-15`** — current production line for Frappe v15 benches.
- Version in `btu/__init__.py` (e.g. `15.2.0`) tracks app releases.

## Scheduler

- **Canonical:** [Datahenge/btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py)
- **Retired:** [btu_scheduler_daemon](https://github.com/Datahenge/btu_scheduler_daemon) (Rust) — do not install for new deployments

This documentation describes **compatible pairs**: a `version-15` app branch with a current `btu_scheduler_py` checkout. When in doubt, upgrade both after protocol or schema changes.

## Documentation

- **Canonical URL:** [https://btu.datahenge.com/](https://btu.datahenge.com/)
- Built from the `Datahenge/btu` repository only
- Scheduler user docs are authored here, not on a separate site

## Python versions

| Component | Python |
|-----------|--------|
| BTU app (bench) | Follows bench / Frappe (typically 3.10–3.11) |
| BTU Scheduler | ≥ 3.11 (see scheduler `pyproject.toml`) |

RQ is pinned to Frappe v15's version (`rq~=1.15.1`) in both projects.
