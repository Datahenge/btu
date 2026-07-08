# Changelog

All notable changes to Background Tasks Unleashed (BTU) are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Source file for releases: [CHANGELOG.md on GitHub](https://github.com/Datahenge/btu/blob/version-15/CHANGELOG.md).

## [15.2.0] — Unreleased

### Added

- **Autocomplete for queue names** — BTU Task and BTU Run Later forms load queue names from bench worker configuration (`common_site_config.json`) with validation.
- **Autocomplete for schedule time zones** — BTU Task Schedule uses IANA time zone names with validation.
- **Migration patches** — Automatic upgrade helpers for SMTP → Email Account and removal of deprecated BTU Queue records.

### Changed

- **Email configuration** — BTU Configuration no longer stores its own SMTP server settings. Notifications use a standard Frappe **Email Account**. Existing SMTP settings are migrated on `bench migrate`.
- **Saving schedules when the scheduler is offline** — BTU Task Schedule documents save successfully even when the scheduler daemon is unreachable; a warning is shown instead of blocking the save.

### Removed

- **BTU Queue DocType** — Queue names come from bench worker configuration, not a separate DocType. Migration removes existing BTU Queue records on upgrade.

### Upgrade notes

1. Run `bench migrate` after upgrading.
2. Confirm **BTU Configuration → Default Email Account** after migrate.
3. Verify queue names on BTU Task and BTU Run Later forms match your bench workers.

---

## [15.1.1] — 2026-07-02

### Added

- **Per-schedule time zones** — Each BTU Task Schedule can specify its own IANA time zone.
- **Scheduler Redis RPC** — See [Redis RPC protocol](../reference/redis-rpc.md).
- **Documentation** — MkDocs site at [btu.datahenge.com](https://btu.datahenge.com/), technical design, ADRs.
- **Repository layout** — Shared utilities, samples, diagnostics.
- **Contributor tooling** — `AGENTS.md`, VS Code workspace, Ruff.
- **Unit tests** — Cron, datetime, Result, form options, auto report.

### Changed

- **RQ task entry point** — Workers call `run_task_by_id` with primitive arguments.
- **`TaskComponent` API** — Function must be a dotted path string.
- **Logging** — Standard Python logging via the `btu` logger.
- **Non-production scripts** — See [Archived scripts](../internals/gists.md).

### Fixed

- RQ pickling failures, failed jobs not logged, duplicate task runs, Run Later polling lock, cron edge cases, email failures, stdout formatting.

### Upgrade notes

1. Run `bench migrate` after upgrading.
2. Update **btu_scheduler_py** to a Redis-RPC-capable build.
3. Pass dotted function path strings to `TaskComponent`.

---

## [15.1.0]

Prior releases: [git tags](https://github.com/Datahenge/btu/tags).
