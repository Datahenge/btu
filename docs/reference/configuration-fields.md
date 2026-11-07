# BTU Configuration fields

See [Desk → BTU Configuration](../guides/desk/configuration.md) for usage.

DocType: `BTU Configuration` (single). Key fields:

| Fieldname | Type | Description |
|-----------|------|-------------|
| `environment_name` | Data | Email prefix tag |
| `force_debug_mode` | Check | Verbose BTU logging |
| `default_email_account` | Link | Email Account for notifications. Optional: without it BTU skips its emails and logs a warning |
| `email_body_is_html` | Check | HTML notification bodies |
| `queue_name` | Data | Default RQ queue |
| `max_task_duration` | Int | Default max seconds |
| `scheduled_task_user` | Link | **Run Scheduled Tasks As**: the User scheduled Tasks run as (default Administrator), never the scheduler daemon's API user |

Full schema: `btu/btu_core/doctype/btu_configuration/btu_configuration.json`.
