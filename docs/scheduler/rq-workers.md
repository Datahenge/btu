# RQ workers

BTU tasks run on standard Frappe RQ workers.

```bash
bench worker --queue short,default,long
```

Queue names on BTU forms must match `worker` queue configuration in `common_site_config.json`.

## After code changes

```bash
bench restart
```

Restart workers when BTU app code or task functions change.

## Diagnostics

```bash
bench --site YOUR_SITE execute btu.diagnostics.rq_workers.check_workers
bench --site YOUR_SITE execute btu.diagnostics.smoke.ping_with_wait --kwargs "{'seconds_to_wait': 1}"
```

See [Failed jobs](failed-jobs.md).
