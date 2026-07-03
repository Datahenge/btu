# Logs

Every BTU task execution creates a **BTU Task Log** with status, timing, stdout, stderr, and optional email delivery.

## Status values

| Status | Meaning |
|--------|---------|
| In-Progress | Worker is running or just started |
| Success | Completed without unhandled exception |
| Failed | Exception or RQ failure |
| Timed Out | Detected by BTU housekeeping when log stays in-progress too long |

## Visibility

Logs are first-class Desk documents — searchable, linkable, and auditable. This is a core reason to prefer BTU over opaque `frappe.enqueue` or external cron.

See [Desk → BTU Task Log](../guides/desk/task-log.md) and [Timeouts and housekeeping](../operations/timeouts-and-housekeeping.md).
