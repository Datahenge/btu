# Run a task on demand

Execute a BTU Task immediately without waiting for cron.

## From the Desk

Open the **BTU Task** and use the run-now action (or create a one-shot from the task form).

## From bench

```bash
bench --site YOUR_SITE execute btu.btu_core.task_runner.run_task_by_id \
  --kwargs "{'task_id': 'TASK-00001'}"
```

Replace `TASK-00001` with your task name.

## Verify

Check **BTU Task Log** for a new row with status Success or Failed.
