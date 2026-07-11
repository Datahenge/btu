# Scheduler environment variables

All variables use prefix `BTU_SCHEDULER_`. See [Scheduler configuration](scheduler-config.md) for narrative setup.

## Required

| Variable | Description |
|----------|-------------|
| `FULL_REFRESH_INTERNAL_SECS` | Full queue refill interval |
| `SCHEDULER_POLLING_INTERVAL` | RQ eligibility poll interval |
| `TIME_ZONE_STRING` | Default IANA timezone |
| `TRACING_LEVEL` | Log level |
| `SQL_TYPE` | `postgres` or `mariadb` |
| `SQL_HOST` | DB host |
| `SQL_PORT` | DB port |
| `SQL_DATABASE` | Site database name |
| `SQL_USER` | DB user |
| `SQL_PASSWORD` | DB password |
| `RQ_HOST` | Redis host |
| `RQ_PORT` | Redis port |
| `WEBSERVER_IP` | Frappe host |
| `WEBSERVER_PORT` | Frappe port |
| `WEBSERVER_TOKEN` | API token |
| `JOBS_SITE_PREFIX` | RQ job ID prefix |

## Optional (defaults)

| Variable | Default |
|----------|---------|
| `DISABLE_REDIS_RPC` | `false` |
| `WEBSERVER_HOST_HEADER` | unset |
| `SLACK_WEBHOOK_URL` | unset |
| `LOGGER_PATH` | `$XDG_STATE_HOME/btu_scheduler/logger.log` |

Source of truth: `btu_py/lib/config.py` in [btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py).
