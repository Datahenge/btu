# Email on failure

Configure tasks to email recipients when execution fails.

## Prerequisites

- **BTU Configuration → Default Email Account** set (Frappe Email Account)
- Valid recipients on the task or schedule

## Steps

1. Open **BTU Task** (or schedule-linked task).
2. Enable email notification on failure and add recipients (BTU Email Recipient child table or task fields as applicable).
3. Run a task that raises an exception intentionally.
4. Confirm email received with environment prefix from **BTU Configuration → Environment Name**.

See [Email integration](../integrations/email.md).
