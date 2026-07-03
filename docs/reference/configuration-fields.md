# BTU Configuration fields

See [Desk → BTU Configuration](../guides/desk/configuration.md) for usage.

DocType: `BTU Configuration` (single). Key fields:

| Fieldname | Type | Description |
|-----------|------|-------------|
| `environment_name` | Data | Email prefix tag |
| `force_debug_mode` | Check | Verbose BTU logging |
| `send_email_via` | Select | Email provider |
| `default_email_account` | Link | Email Account |
| `email_body_is_html` | Check | HTML notification bodies |
| `queue_name` | Data | Default RQ queue |
| `max_task_duration` | Int | Default max seconds |

Full schema: `btu/btu_core/doctype/btu_configuration/btu_configuration.json`.
