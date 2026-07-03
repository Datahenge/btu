# Command line

BTU is primarily Desk-driven. Useful bench commands:

## Run a task by ID

```bash
bench --site SITE execute btu.btu_core.task_runner.run_task_by_id \
  --kwargs "{'task_id': 'TASK-00001'}"
```

## Run Later test enqueue

```bash
bench --site SITE execute btu.btu_core.run_later.test_one
```

## Diagnostics

```bash
bench --site SITE execute btu.diagnostics.smoke.ping_with_wait \
  --kwargs "{'seconds_to_wait': 2}"
bench --site SITE execute btu.diagnostics.rq_workers.check_workers
```

## Scheduler CLI

On the scheduler host (not bench):

```bash
btu-py config show
btu-py config path
btu-py run-daemon
```

Legacy Rust `btu_scheduler` binary is retired.
