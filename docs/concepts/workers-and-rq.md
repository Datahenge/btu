# Workers and RQ

BTU executes tasks through **Frappe RQ workers** — the same Redis Queue infrastructure Frappe uses for background jobs.

## Queues

Queue names on BTU Task forms must match queues your workers listen to. BTU loads valid names from `common_site_config.json` (bench worker configuration).

Typical bench command:

```bash
bench worker --queue short,default,long
```

## Entry point

Scheduled and on-demand runs enqueue:

```
btu.btu_core.task_runner.run_task_by_id
```

Workers must have BTU installed and site context initialized (standard Frappe worker process).

See [RQ workers](../scheduler/rq-workers.md) and [Failed jobs](../scheduler/failed-jobs.md).
