# Schedules

A **BTU Task Schedule** binds a BTU Task to a **cron expression** and optional **IANA time zone**.

## Cron in local time

Enter cron fields in the schedule's time zone (e.g. `America/New_York`). BTU converts to UTC for the scheduler daemon.

Default time zone comes from **System Settings** if not set on the schedule.

## Enable / disable

Disabled schedules remain in the database but the scheduler ignores them. Saving a schedule notifies the daemon via Redis RPC (reload).

## Scheduler dependency

Recurring schedules require **btu_scheduler_py** running. Without it, tasks can still run on-demand or via Run Later, but nothing fires on cron.

See [Desk → BTU Task Schedule](../guides/desk/task-schedule.md) and [Reference → Cron fields](../reference/schedule-cron-fields.md).
