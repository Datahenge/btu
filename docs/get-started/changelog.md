# Changelog

All notable changes to Background Tasks Unleashed (BTU) are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Source file for releases: [CHANGELOG.md on GitHub](https://github.com/Datahenge/btu/blob/version-16/CHANGELOG.md).

## [Unreleased]

Work on `version-16` since 16.0.0, running in production in webserver mode.

### Added

- **Webserver connectivity mode:** the BTU Scheduler daemon can run with no direct SQL or Redis access, reaching the site only through BTU's REST endpoints (`get_enabled_task_schedules`, `get_task_schedule_details`, `get_pending_scheduler_commands`). Opt in by setting `btu_scheduler_connectivity_mode: "webserver"` in site config to match the daemon's `BTU_SCHEDULER_CONNECTIVITY_MODE=webserver`. The default (`direct`) is unchanged. Suited to Docker: the daemon can run as its own Compose project on the ERPNext stack's private network. See [Run the scheduler in Docker](https://btu.datahenge.com/scheduler/run-in-docker/).
- **BTU Scheduler role:** an API-only role (no Desk access) for the scheduler daemon's user. Created on install and by a patch on migrate.
- **Run Scheduled Tasks As:** a new field in BTU Configuration choosing the User that scheduled Tasks run as (default Administrator). Tasks a person queues by hand still run as that person.
- **Scheduler liveness in webserver mode:** BTU Configuration shows when the daemon last polled, in green or red.
- **"Create Ping Task" button** in BTU Configuration, for a quick end-to-end check.

### Changed

- **Scheduler endpoints require the BTU Scheduler or System Manager role.** Previously any signed-in user could call them. Give the daemon's API user only the BTU Scheduler role.
- **Scheduled Tasks no longer run as the daemon's API user**, so that user no longer needs broad roles such as System Manager.
- **BTU Task Schedule** no longer grants read access to "All".
- **Default Email Account is optional.** Saving without one shows a warning, and failure emails are skipped instead of raising an error.
- Clearer scheduler command responses in schedule logs.
- Workspace fixture refreshed for Frappe v16.

### Fixed

- **Deleting a BTU Task failed on MariaDB** (error 1064).
- Explicit task Result failures are now honored.
- Three incorrect error messages.

### Upgrade notes

1. Run `bench migrate` after upgrading.
2. Give the scheduler daemon's API user the **BTU Scheduler** role, and remove any broader roles it no longer needs.
3. Check **BTU Configuration → Run Scheduled Tasks As**.
4. To use webserver mode, set `btu_scheduler_connectivity_mode` on the site and the matching variable on the daemon.

---

## [16.0.0] — 2026-07-10

BTU for Frappe v16. Includes everything in 15.2.0 below.

### Added

- **Frappe v16 and Python 3.14 support.**
- **Desk workspace tile and icon** ("Automated Tasks"), created on install.
- **New documentation** for v16.

### Changed

- **BTU Scheduled Task Summary and BTU Task Log Summary** are now Script Reports, compatible with MariaDB and PostgreSQL.

### Removed

- **Mandrill / Mailchimp Transactional email support.** Use a Frappe Email Account.
- Legacy `rq.compat` code and obsolete environment variables. BTU no longer pins `rq` itself; Frappe owns it.

### Fixed

- SQL bugs in the summary reports (minutes shown as months, hard-coded time zone).

### Upgrade notes

1. Run `bench migrate` after upgrading.
2. If you sent email through Mandrill, configure a Frappe Email Account.

---

## [15.2.0] — 2026-07-06

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
- **Scheduler Redis RPC** — See [Redis RPC protocol](../scheduler/redis-rpc.md).
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
