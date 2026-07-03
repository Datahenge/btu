# Public API

Selected entry points for integrators. Not exhaustive — see source for full signatures.

## Task execution

| Path | Purpose |
|------|---------|
| `btu.btu_core.task_runner.run_task_by_id` | RQ worker entry; run task by name |
| `btu.btu_core.doctype.btu_task.btu_task.create_and_run_one_shot` | Create and enqueue one-shot |

## Run Later

| Path | Purpose |
|------|---------|
| `btu.btu_core.run_later.enqueue_for_later` | Redis-based deferral |
| `btu.btu_core.run_later.create_doc_run_later` | DocType-based deferral |
| `btu.btu_core.run_later.poll_for_ready_work` | Poller (schedule via BTU Task) |

## Scheduler control

| Path | Purpose |
|------|---------|
| `btu.btu_api.scheduler.SchedulerAPI` | Redis RPC client |

## Auto Report

| Path | Purpose |
|------|---------|
| `btu.btu_core.auto_report.run_btu_report` | Scheduled report delivery |

## Utilities

| Path | Purpose |
|------|---------|
| `btu.Result` | Success/failure result type |
| `btu.get_system_datetime_now` | Timezone-aware now for site |
