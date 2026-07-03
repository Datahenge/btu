# Scheduler

The **BTU Scheduler** ([btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py)) is a standalone Python daemon — mandatory for cron-based Task Schedules.

## Responsibilities

- Read enabled BTU Task Schedules from the site database
- Evaluate cron expressions with per-schedule time zones
- At fire time, HTTP-call Frappe to enqueue the linked BTU Task
- Listen on Redis RPC for ping, reload, and cancel commands

## Not responsible for

- Running Python task code (RQ workers do that)
- Storing Task Logs (Frappe app does that)
- Desk UI

## Legacy

The Rust [btu_scheduler_daemon](https://github.com/Datahenge/btu_scheduler_daemon) is **retired**. See [Legacy Rust scheduler](../internals/legacy-rust-scheduler.md).

## Operations

- [Install scheduler](../operations/install-scheduler.md)
- [Scheduler configuration](../operations/scheduler-config.md)
- [Run the scheduler](../operations/run-scheduler.md)
