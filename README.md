## Background Tasks Unleashed (BTU) v15

**[Official documentation](https://btu.datahenge.com/)** — Frappe app + Python scheduler, one product.

Companion scheduler: **[btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py)** (required for recurring schedules). The legacy Rust scheduler is [retired](https://btu.datahenge.com/internals/legacy-rust-scheduler/).

### What is this?

Background Tasks Unleashed is:

* a [Frappe Framework](https://frappeframework.com) application for task scheduling and automation
* a tool for running Python processes automatically on a repeating schedule in the background
* a robust alternative to Frappe's built-in **Scheduled Job Types** for business-configured work

### Capabilities

Using the Desk (no SSH, no `hooks.py` edits):

* **Tasks** — run any Python function with your own arguments
* **Schedules** — cron with per-schedule time zones
* **Logs** — complete stdout/stderr history
* **Run Later** — deferred one-shot work with visibility

### Installation

See the unified guide: **[Installation](https://btu.datahenge.com/get-started/installation/)**

```bash
bench get-app --branch version-15 https://github.com/Datahenge/btu
bench --site YOUR_SITE install-app btu
```

Plus [BTU Scheduler](https://github.com/Datahenge/btu_scheduler_py) and RQ workers — details on the docs site.

### Quick links

| Topic | Link |
|-------|------|
| Why two components? | [Why BTU](https://btu.datahenge.com/get-started/why-btu/) |
| Run Later poller | [Recipe](https://btu.datahenge.com/recipes/set-up-run-later-poller/) |
| Scheduler config | [BTU Scheduler](https://btu.datahenge.com/scheduler/scheduler-config/) |
| Changelog | [Changelog](https://btu.datahenge.com/get-started/changelog/) |

### License

MIT — Datahenge LLC
