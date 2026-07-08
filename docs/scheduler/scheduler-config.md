# Scheduler configuration

All scheduler settings use the `BTU_SCHEDULER_` prefix.

## Configuration file (development)

```bash
mkdir -p ~/.config/btu_scheduler
cp .env.example ~/.config/btu_scheduler/.env
nano ~/.config/btu_scheduler/.env
```

Path: `$XDG_CONFIG_HOME/btu_scheduler/.env` or `~/.config/btu_scheduler/.env`.

## Production (systemd / containers)

Set the same variables in the process environment. **Environment always overrides** the `.env` file.

## Required variables

| Variable | Description |
|----------|-------------|
| `BTU_SCHEDULER_FULL_REFRESH_INTERNAL_SECS` | Seconds between full queue refills |
| `BTU_SCHEDULER_SCHEDULER_POLLING_INTERVAL` | Seconds between RQ eligibility checks |
| `BTU_SCHEDULER_TIME_ZONE_STRING` | Default IANA timezone |
| `BTU_SCHEDULER_TRACING_LEVEL` | Log level (`INFO`, `DEBUG`, …) |
| `BTU_SCHEDULER_SQL_TYPE` | `postgres` or `mariadb` |
| `BTU_SCHEDULER_SQL_HOST` | Database host |
| `BTU_SCHEDULER_SQL_PORT` | Database port |
| `BTU_SCHEDULER_SQL_DATABASE` | Frappe site database name |
| `BTU_SCHEDULER_SQL_USER` | Database user |
| `BTU_SCHEDULER_SQL_PASSWORD` | Database password |
| `BTU_SCHEDULER_RQ_HOST` | Redis host (same as bench) |
| `BTU_SCHEDULER_RQ_PORT` | Redis port |
| `BTU_SCHEDULER_TCP_SOCKET_PORT` | TCP listener port |
| `BTU_SCHEDULER_SOCKET_PATH` | Unix domain socket path |
| `BTU_SCHEDULER_WEBSERVER_IP` | Frappe web server IP |
| `BTU_SCHEDULER_WEBSERVER_PORT` | Frappe web port |
| `BTU_SCHEDULER_WEBSERVER_TOKEN` | Frappe API token (`token api_key:api_secret`) |
| `BTU_SCHEDULER_JOBS_SITE_PREFIX` | Prefix for RQ job identifiers |

## Optional variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BTU_SCHEDULER_DISABLE_REDIS_RPC` | `false` | Disable Redis RPC listener |
| `BTU_SCHEDULER_DISABLE_UNIX_SOCKET` | `false` | Disable Unix socket listener |
| `BTU_SCHEDULER_DISABLE_TCP_SOCKET` | `false` | Disable TCP socket listener |
| `BTU_SCHEDULER_WEBSERVER_HOST_HEADER` | unset | Host header for multi-tenant sites |
| `BTU_SCHEDULER_SLACK_WEBHOOK_URL` | unset | Slack notifications |
| `BTU_SCHEDULER_LOGGER_PATH` | `$XDG_STATE_HOME/btu_scheduler/logger.log` | Log file |

Full reference: [Scheduler environment variables](../reference/scheduler-env-vars.md).

## Loading precedence

```
Process environment  (highest)
.env file            (fills unset keys only)
```

See scheduler source `btu_py/lib/config.py`.
