# Tasks

A **BTU Task** defines *what* to run: a fully-qualified Python function path and optional arguments.

## Key fields

| Field | Description |
|-------|-------------|
| Function | Dotted path, e.g. `myapp.module.my_function` |
| Function Arguments | JSON/dict passed as kwargs |
| Queue Name | RQ queue (from bench worker config) |
| Max Duration | Timeout hint for logging/housekeeping |

## Lifecycle

- Tasks are **reusable** — many schedules can reference one task.
- **On-demand** execution creates a one-shot run without a schedule.
- Each execution produces a **BTU Task Log**.

## Function requirements

- Must be importable on workers (installed apps on the bench).
- Should return normally or raise; output is captured to the log.
- Use `btu.Result` in custom code when you want structured success/failure messages.

See [Writing task functions](../guides/writing-task-functions.md) and [Desk → BTU Task](../guides/desk/task.md).
