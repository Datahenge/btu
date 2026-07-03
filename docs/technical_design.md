# BTU Technical Design

This document explains **why** Background Tasks Unleashed (BTU) exists, how it is split across two projects, and the product constraints that shaped those decisions. It is written for maintainers and contributors who need context beyond “what the code does.”

For protocol details between the Frappe app and the scheduler daemon, see [Scheduler Redis RPC](scheduler_redis_rpc.md).

---

## Purpose

BTU turns background Python work into **managed, schedulable, observable infrastructure** inside Frappe/ERPNext:

- **Tasks** — callable functions and arguments stored as configuration, not buried in `hooks.py` or ad-hoc `frappe.enqueue` calls.
- **Schedules** — cron expressions and time zones as Desk-editable data.
- **Logs** — stdout/stderr, status, timing, and optional email notifications.
- **Workers** — execution via Python RQ (Redis Queue), Frappe’s standard background job mechanism.

The audience is not only developers. Operations and power users who do not edit Python must still be able to **create, inspect, and reason about** automated work from the ERPNext UI.

---

## Problem with Frappe’s built-in scheduler

Frappe provides Scheduled Job Types and `scheduler_events` in `hooks.py`. That mechanism is a **developer integration point**:

- Schedules live in application code.
- Changes require deploys and code ownership.
- Non-developers cannot see or edit what will run, when, or what happened last time.

For ERPNext sites where automation is **business configuration** (reports, integrations, housekeeping), Frappe’s built-in scheduler may as well not exist for end users. BTU exists because that gap is real and Frappe’s scheduler is not something site owners can extend on their own terms.

---

## Why BTU is two tools (necessity, not preference)

BTU was split into two cooperating projects because no single Frappe App could satisfy all requirements.

### 1. Frappe app (`btu` on GitHub)

Only a Frappe application can provide:

- Web UI (Desk) for Tasks, Schedules, Logs, and Configuration.
- DocTypes that are **both** user interface and persistent data model.
- Permissions, auditing, and the rest of the Frappe document lifecycle.

Whether or not that was the preferred shape, **schedule and task data belong in Frappe’s database** if non-developers are first-class users.

The app also owns:

- Enqueueing work to RQ when the scheduler fires (`task_runner.run_task_by_id`).
- Task Log creation and email notifications.
- Redis RPC client calls to the scheduler daemon (reload/cancel/ping schedules).

### 2. Scheduler daemon ([`btu_scheduler_py`](https://github.com/Datahenge/btu_scheduler_py) / legacy [`btu_scheduler_daemon`](https://github.com/Datahenge/btu_scheduler_daemon))

The missing piece was a **background process** that:

- Reads enabled Task Schedules from the site database.
- Calculates next execution datetimes from cron expressions (with timezone support).
- At fire time, tells Frappe to enqueue the corresponding Task as an RQ job.

That process **cannot** be a Frappe App:

- Wrong lifecycle (must run continuously as a daemon, not as web/worker requests).
- Too heavy (full Frappe stack and dependencies for what is essentially a clock + cron evaluator + thin client).
- Poor fit for ops (one lean process per bench/site vs coupling to `bench serve` / worker restarts).

**The external scheduler daemon is mandatory** for the BTU product model. It is not an optional integration for advanced deployments.

### Control-plane vs execution-plane

| Component | Role |
|-----------|------|
| **Frappe app** | System of record: Tasks, Schedules, Logs, Run Later, Configuration. Human visibility and permissions. |
| **Scheduler daemon** | Time engine: poll/sync schedules, compute next runs, trigger enqueue at fire time. |
| **RQ workers** | Execution engine: run Python callables, report results back into Task Logs. |
| **Redis** | Job queues (RQ) and scheduler control channel (RPC). |

---

## End-to-end mental model

Teach users (and developers) one chain:

1. **Configure** a Task and Schedule in the Desk.
2. **Daemon** evaluates cron and decides when the schedule is due.
3. **Frappe** enqueues an RQ job (via HTTP endpoint or equivalent integration).
4. **Worker** runs the task; BTU writes a **Task Log**.
5. **User** inspects the log (and optional emails) to confirm success or failure.

Everything else — Run Later, RQ admin buttons, auto-report delivery, Mandrill/SMTP — extends this chain; it should not replace it.

---

## Inter-app communication

Scheduler control commands (ping, reload schedule, cancel schedule) use **Redis RPC** on the same Redis instance as Frappe’s RQ queues. See [scheduler_redis_rpc.md](scheduler_redis_rpc.md).

Historical Unix-domain-socket and TCP control paths have been removed from the Frappe app; Redis is the supported control plane for container-friendly deployments.

When a schedule fires, the daemon calls Frappe (HTTP) to enqueue work. Frappe remains authoritative for building the RQ job and applying site context.

---

## BTU Run Later: visibility over convenience

`run_later` (Redis keys and/or **BTU Run Later** documents) defers one-shot execution until a future datetime.

Python RQ supports delayed enqueue natively. BTU did not rely on that alone because **once a job exists only inside RQ, it is invisible to ERPNext users**:

- There is nothing to see in the Desk.
- Users cannot tell whether something will still run later.
- Operators cannot inspect pending deferred work without Redis/RQ expertise.

By modeling deferred work as BTU data (especially **BTU Run Later** documents), users can see that work **exists** and **remains scheduled** until it goes in-flight — consistent with Task Logs and In-Progress status for observability.

Trade-offs (accepted):

- Extra code paths (Redis polling, SQL documents, `poll_for_ready_work`).
- Some overlap with RQ’s built-in delay.

**Refactoring bar:** Replacing Run Later with RQ-only delay would require an equally visible Frappe-side queue of pending work, not merely fewer lines of code.

---

## What BTU is not

- **Not a replacement for Frappe workers** — BTU schedules and logs work; RQ workers still execute it.
- **Not a generic distributed workflow engine** — no DAG UI, retries policy engine, or cross-site orchestration as a core promise.
- **Not decoupled from Frappe** — Tasks are DocTypes; execution assumes `frappe.init` / site context in workers.

---

## Related documentation

| Document | Topic |
|----------|--------|
| [Architecture Decision Records](dev/adr/README.md) | Numbered decisions (ADR format) |
| [Repository layout](dev/repository_layout.md) | Python package structure |
| [Scheduler Redis RPC](scheduler_redis_rpc.md) | Daemon ↔ Frappe protocol |
| [Web UI guide](guide_web.md) | DocTypes and Configuration |
| [AGENTS.md](../AGENTS.md) | Contributor entry point |
