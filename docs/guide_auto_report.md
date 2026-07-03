## Automatic Report Delivery

BTU can run a standard Frappe **Report**, build the result, and deliver it on a schedule (or on demand) to one or more targets: Email, a file on disk, or Slack.

The entry point is the Python function `btu.auto_report.run_btu_report`. You normally invoke it from a **BTU Task** by setting the task's function path and passing a dictionary of arguments.

This guide uses Frappe's built-in **ToDo** report (`Report` name: `ToDo`). That report ships with Frappe Framework and requires no ERPNext apps. It lists open ToDo items for the current user and accepts no filters, which keeps the example short.

### Prerequisites

1. BTU is installed and workers are running.
2. For **email** delivery, configure outbound mail under **BTU Configuration** (or ensure Frappe's email settings are working if you rely on `frappe.sendmail` for your site).
3. Confirm the report exists: open **Report** list and verify **ToDo** is present.

### Arguments

`run_btu_report` expects three keyword arguments:

| Argument | Type | Description |
|----------|------|-------------|
| `report_key` | string | Name of the Frappe `Report` document (e.g. `"ToDo"`). |
| `report_parameters` | dict | Report filters. Use `{}` when the report has no filters. |
| `delivery_targets` | list | One or more delivery specifications (see below). |

Each delivery target is a dictionary:

| Field | Values | Description |
|-------|--------|-------------|
| `target_type` | `Email`, `File`, `Slack` | Where to send the output. |
| `target_details` | string | Comma-separated emails, file path, or Slack channel/webhook details (depends on type). |
| `report_format` | `HTML`, `XLSX`, `CSV` | Output format for that target. |

### Example: BTU Task (scheduled email)

1. Create a **BTU Task**.
2. Set **Function** to:

   ```
   btu.auto_report.run_btu_report
   ```

3. Set **Function Arguments** to (JSON or Python dict):

   ```json
   {
     "report_key": "ToDo",
     "report_parameters": {},
     "delivery_targets": [
       {
         "target_type": "Email",
         "target_details": "reports@example.com",
         "report_format": "HTML"
       }
     ]
   }
   ```

   Replace `reports@example.com` with a valid address on your site.

4. Save and submit the task.
5. Create a **BTU Task Schedule** with a cron expression (for example, weekday mornings).
6. Check **BTU Task Log** after the schedule fires.

### Example: one-off run from Bench

Useful for testing before scheduling:

```bash
bench --site YOUR_SITE execute btu.auto_report.run_btu_report --kwargs '{
  "report_key": "ToDo",
  "report_parameters": {},
  "delivery_targets": [
    {
      "target_type": "Email",
      "target_details": "reports@example.com",
      "report_format": "CSV"
    }
  ]
}'
```

If the report has no rows, BTU logs that nothing was transmitted and does not send empty email.

### Multiple targets

You can deliver the same report in different formats to different places in one run:

```json
{
  "report_key": "ToDo",
  "report_parameters": {},
  "delivery_targets": [
    {
      "target_type": "Email",
      "target_details": "team@example.com",
      "report_format": "HTML"
    },
    {
      "target_type": "File",
      "target_details": "/tmp/todo-report.csv",
      "report_format": "CSV"
    }
  ]
}
```

Ensure the worker process can write to any file path you use.

### Reports with filters

For script or query reports that accept filters, put them in `report_parameters` using the report's filter field names. Open the report in the Frappe UI, note the filter fields, then mirror them in the dict. Example shape (field names vary by report):

```json
{
  "report_key": "Some Report",
  "report_parameters": {
    "from_date": "2026-01-01",
    "to_date": "2026-01-31"
  },
  "delivery_targets": [ ... ]
}
```

### Related code

- Implementation: `btu/auto_report.py` (`BTUReport`, `DeliveryTarget`, `run_btu_report`).
- Task execution: BTU passes **Function Arguments** as keyword arguments to the callable (see **BTU Task** DocType).
