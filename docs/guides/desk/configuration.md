# BTU Configuration

Singleton settings for BTU and scheduler integration.

## Environment

| Field | Purpose |
|-------|---------|
| Environment Name | Prefix on email subject/body (e.g. `[PROD]`) |
| Force Debug Mode | Elevate BTU logger verbosity |

## Email

| Field | Purpose |
|-------|---------|
| Send Email Via | Provider selection |
| Default Email Account | Frappe Email Account for notifications |
| Email Body is HTML | Format for notification bodies |
| Email Recipients | Default recipients |

SMTP fields were removed in 15.2 — use Frappe Email Account (Mandrill supported).

## Default task settings

| Field | Purpose |
|-------|---------|
| Queue Name | Default RQ queue for new tasks |
| Max Task Duration | Default timeout hint (seconds) |

## Scheduler integration

| Control | Purpose |
|---------|---------|
| Send ping | Test Redis RPC to scheduler |
| Resubmit all schedules | Force daemon reload |

## Documentation link

The form links to [https://btu.datahenge.com/](https://btu.datahenge.com/).
