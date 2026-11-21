# Changelog

All notable changes to Background Tasks Unleashed (BTU) are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

Source file for releases: [CHANGELOG.md on GitHub](https://github.com/Datahenge/btu/blob/version-15/CHANGELOG.md).

## [15.2.1] — 2026-11-21

Security release. Upgrade promptly.

### Security

- **Scheduler endpoints require the BTU Scheduler or System Manager role.** Previously any signed-in user could call `get_pickled_task`, `test_function_ping_now_bytes`, and `enqueue_for_next_available_worker`: fetching pickled job data or enqueuing scheduled Tasks.
- **Failed-job tools require System Manager.** `list_failed_jobs`, `print_job_details`, and `remove_failed_jobs` were callable by any signed-in user.
- **`delete_logs_by_dates` requires delete permission on BTU Task Log.** Previously any signed-in user could delete Task Logs by date range.
- **Ten functions are no longer callable over HTTP:** `poll_for_ready_work`, `resubmit_all_task_schedules`, `run_btu_report`, `check_in_progress_logs_for_timeout`, `reload_timezone_cache`, `send_hello_email_to_current_user`, `ping_with_wait`, `wait_then_throw_error`, `test_rq_workers2`, `test_hello_world_bytes`. They still work when called from Python, from `hooks.py`, from BTU Configuration's buttons, or as BTU Tasks.
- **BTU Task Schedule no longer grants read access to "All".**

### Added

- **BTU Scheduler role:** an API-only role (no Desk access) for the scheduler daemon's user, with read access to BTU Task and BTU Task Schedule. Created on install and by a patch on migrate.

### Upgrade notes

1. Run `bench migrate` after upgrading.
2. **Before restarting the scheduler daemon,** give its API user the **BTU Scheduler** role, unless it already has System Manager. Otherwise the daemon can no longer fetch or enqueue Tasks.
3. On 15.x, scheduled Tasks still run as the daemon's API user, so keep whatever roles your Tasks need. (BTU 16.1.0 adds "Run Scheduled Tasks As", which removes that requirement.)

---

## [15.2.0] — 2026-07-06

### Added

- **Autocomplete for queue names** — BTU Task and BTU Run Later forms load queue names from bench worker configuration (`common_site_config.json`) with validation.
- **Autocomplete for schedule time zones** — BTU Task Schedule uses IANA time zone names with validation.
- **Migration patches** — Automatic upgrade helpers for SMTP → Email Account and removal of deprecated BTU Queue records.

### Changed

- **Email configuration** — BTU Configuration no longer stores its own SMTP server settings. Notifications use a standard Frappe **Email Account** (Mandrill remains supported). Existing SMTP settings are migrated on `bench migrate`.
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
