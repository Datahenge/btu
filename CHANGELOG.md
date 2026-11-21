# Changelog

All notable changes to Background Tasks Unleashed (BTU) are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

- **Per-schedule time zones** — Each BTU Task Schedule can specify its own IANA time zone. Cron times are entered in local time; UTC conversion happens at scheduling time. Defaults to the site time zone from System Settings.
- **Scheduler Redis RPC** — Control commands between the Frappe app and the BTU Scheduler daemon (ping, reload, cancel) now use Redis instead of Unix domain sockets. See [docs/reference/redis-rpc.md](docs/reference/redis-rpc.md).
- **Documentation** — Technical design overview, Architecture Decision Records (ADRs), expanded Auto Report guide, and contributor layout docs.
- **Repository layout** — Shared utilities (`btu/utils/`), sample tasks (`btu/samples/`), and diagnostics (`btu/diagnostics/`). Deprecated top-level shims remain for compatibility.
- **Contributor tooling** — `AGENTS.md`, VS Code workspace, and Ruff lint/format configuration.
- **Unit tests** — Coverage for cron, datetime, Result type, form options, and auto report helpers.

### Changed

- **RQ task entry point** — Workers call `run_task_by_id` with primitive arguments instead of pickling bound methods or Frappe Document objects.
- **`TaskComponent` API** — The `function` argument must be a fully-qualified dotted path string (e.g. `myapp.module.my_function`). Function objects are no longer accepted.
- **Logging** — Replaced ad-hoc `print()` and `dprint()` calls with standard Python logging via the `btu` logger.
- **Non-production scripts** — Moved out of the main package to documented Gists (see [docs/internals/gists.md](docs/internals/gists.md)).

### Fixed

- **RQ pickling failures** ([#9](https://github.com/Datahenge/btu/issues/9)) — Scheduler-enqueued tasks no longer fail when RQ cannot pickle bound methods or Frappe Documents.
- **Failed jobs not logged** ([#11](https://github.com/Datahenge/btu/issues/11)) — RQ worker failures (including timeouts and SIGKILL) now update the BTU Task Log with a traceback and trigger failure email notifications.
- **RQ Job ID on Task Logs** — Job ID is recorded reliably at enqueue time and indexed for lookup.
- **Duplicate task runs** — Tasks with an existing In-Progress log are skipped rather than enqueued again.
- **Run Later polling lock** — Advisory locks (MariaDB `GET_LOCK` / PostgreSQL `pg_try_advisory_lock`) survive `frappe.db.commit()`, preventing overlapping poll runs.
- **Cron string generation** — Fixed edge cases in `schedule_to_cron_string()`.
- **Email failures** — A failure to send the result email no longer marks the task itself as failed.
- **Task log stdout formatting** — Fixed an f-string quoting bug when appending captured output ([#7](https://github.com/Datahenge/btu/pull/7)).

### Upgrade notes

1. Run `bench migrate` after upgrading.
2. Update the **BTU Scheduler daemon** (`btu_scheduler_py`) to a version that supports Redis RPC.
3. If you call `TaskComponent` programmatically, pass a dotted function path string instead of a function reference.

---

## [15.1.0]

Prior releases are not documented in this file. See [git tags](https://github.com/Datahenge/btu/tags) for earlier versions.

[15.2.1]: https://github.com/Datahenge/btu/compare/v15.2.0...v15.2.1
[15.2.0]: https://github.com/Datahenge/btu/compare/15.1.1...v15.2.0
[15.1.1]: https://github.com/Datahenge/btu/compare/15.1.0...15.1.1
