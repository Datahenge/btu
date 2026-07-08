# Configuration overview

BTU configuration is split across two sides of the product.

## Frappe app — BTU Configuration

Single DocType: **BTU Configuration** (singleton).

| Area | Purpose |
|------|---------|
| Environment name | Prefix for email subjects/bodies (e.g. `PROD`, `STAGING`) |
| Default email account | Frappe Email Account used for notifications |
| Default task settings | Default queue name, max task duration |
| Scheduler buttons | Ping scheduler, resubmit all schedules |

See [BTU Configuration guide](../guides/desk/configuration.md) and [Reference → Configuration fields](../reference/configuration-fields.md).

## Scheduler — environment variables

The Python scheduler reads `BTU_SCHEDULER_*` variables from:

- Process environment (systemd, Docker, Kubernetes), and/or
- `~/.config/btu_scheduler/.env` (optional developer convenience)

Process environment **always wins** over the `.env` file.

See [Scheduler configuration](../scheduler/scheduler-config.md) and [Reference → Scheduler environment variables](../scheduler/scheduler-env-vars.md).

## Shared infrastructure

Both components use the **same**:

- Site database (scheduler reads Task Schedules directly)
- Redis instance (RQ job queues + `btu:scheduler:commands` RPC channel)

Ensure `redis_queue` in `site_config.json` / `common_site_config.json` matches `BTU_SCHEDULER_RQ_HOST` and `BTU_SCHEDULER_RQ_PORT`.

## Checklist after install

- [ ] BTU app installed and migrated
- [ ] Scheduler `.env` or env vars set with correct DB + Redis + Frappe token
- [ ] `btu-py run-daemon` running
- [ ] `bench worker` running with expected queues
- [ ] Ping from BTU Configuration succeeds
