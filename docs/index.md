# Background Tasks Unleashed

**BTU** is a pair of open-source tools for scheduling and running Python background work in [Frappe Framework](https://frappeframework.com) sites:

1. **BTU Frappe app** ([Datahenge/btu](https://github.com/Datahenge/btu)) — Desk UI, Tasks, Schedules, Logs, Run Later, Configuration.
2. **BTU Scheduler** ([Datahenge/btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py)) — cron engine that reads schedules and fires tasks at run time.

Neither component works alone. Both are required for recurring schedules.

## Why use BTU?

- **Desk-first** — create and manage schedules without editing `hooks.py` or redeploying code.
- **Cron with time zones** — per-schedule IANA time zones; enter local times, BTU handles UTC.
- **Full logging** — stdout and stderr captured in BTU Task Log, not just success/fail.
- **Email notifications** — optional alerts on completion or failure via Frappe Email Account.
- **Run Later** — defer one-shot work with Desk visibility (not invisible RQ `enqueue_at`).

## Quick links

| I want to… | Start here |
|------------|------------|
| Install BTU end-to-end | [Installation](get-started/installation.md) |
| Understand the architecture | [Mental model](concepts/mental-model.md) |
| Set up deferred work | [Run Later](concepts/run-later.md) → [Poller recipe](recipes/set-up-run-later-poller.md) |
| Configure the scheduler daemon | [Scheduler configuration](operations/scheduler-config.md) |
| Configure email | [Email integration](integrations/email.md) |

## Requirements

- Frappe v15 bench with Redis and RQ workers
- PostgreSQL or MariaDB (scheduler reads the same site database)
- BTU Scheduler daemon running continuously (`btu-py run-daemon`)

ERPNext is **not** required.
