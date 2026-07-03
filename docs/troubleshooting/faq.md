# FAQ

## Do I need ERPNext?

No. BTU depends only on Frappe Framework.

## Why not Frappe Scheduled Job Types?

Scheduled Job Types and `scheduler_events` are developer hooks — schedules live in code, require deploys, and are opaque to non-developers. BTU targets **business-configured** automation with Desk visibility and full logs.

## Why two repos but one product?

The Frappe app provides UI, DocTypes, and RQ enqueue. The scheduler daemon must run continuously outside Frappe to evaluate cron — it cannot be a Frappe app or live in `apps/`. Both are **required** for recurring schedules. Documentation is unified here; code stays in two GitHub repos by necessity.

See [Why BTU](../get-started/why-btu.md).

## Which scheduler should I install?

**Only** [btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py). The Rust [btu_scheduler_daemon](https://github.com/Datahenge/btu_scheduler_daemon) is retired.

## Schedules never fire

1. Is `btu-py run-daemon` running?
2. Does ping from BTU Configuration succeed?
3. Is the schedule **Enabled**?
4. Are SQL credentials in scheduler env correct (same DB as site)?

## Tasks stuck In-Progress

Check worker is running, queue name matches, and review worker logs. BTU housekeeping marks long In-Progress logs timed out.

## Run Later never executes

Configure [Run Later poller](../recipes/set-up-run-later-poller.md) (BTU Task + Schedule every 1–5 min).
