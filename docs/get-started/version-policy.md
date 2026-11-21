# Version policy

## Frappe app

- **Branch `version-16`**: current production line for Frappe v16 benches.
- **Branch `version-15`**: Frappe v15 benches.
- Version in `btu/__init__.py` (e.g. `16.1.0`) tracks app releases.

## Scheduler

- **Canonical:** [Datahenge/btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py)
- **Retired:** [btu_scheduler_daemon](https://github.com/Datahenge/btu_scheduler_daemon) (Rust) — do not install for new deployments

This documentation describes **compatible pairs**: a `version-16` app branch with the `version-16` branch of `btu_scheduler_py` (or `version-15` with `version-15`). When in doubt, upgrade both after protocol or schema changes.

## Documentation

- **Canonical URL:** [https://btu.datahenge.com/](https://btu.datahenge.com/)
- Built from the `Datahenge/btu` repository only
- Scheduler user docs are authored here, not on a separate site

## Python versions

| Component | Python |
|-----------|--------|
| BTU app (bench) | Follows Frappe: 3.14 for v16 |
| BTU Scheduler | ≥ 3.11 (see scheduler `pyproject.toml`) |

The BTU app does not pin RQ; Frappe owns it. The scheduler's `version-16` branch pins `rq==2.6.1`, matching Frappe v16 (see its `pyproject.toml`).
