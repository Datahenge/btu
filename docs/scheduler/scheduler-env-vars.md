# Scheduler environment variables

All variables use prefix `BTU_SCHEDULER_`. See [Scheduler configuration](scheduler-config.md) for narrative setup, including which variables `connectivity_mode` makes optional.

## Always required

| Variable | Description |
|----------|-------------|
| `FULL_REFRESH_INTERNAL_SECS` | Full queue refill interval, in seconds |
| `SCHEDULER_POLLING_INTERVAL` | RQ eligibility poll interval, in seconds (also the command-poll interval in `webserver` mode) |
| `WEBSERVER_IP` | Frappe web server host or public DNS name |
| `WEBSERVER_PORT` | Frappe web port |
| `WEBSERVER_TOKEN` | Frappe API token (`token api_key:api_secret`) |

## Required only when `CONNECTIVITY_MODE=direct` (the default)

| Variable | Description |
|----------|-------------|
| `SQL_TYPE` | `postgres` or `mariadb` |
| `SQL_HOST` | DB host |
| `SQL_PORT` | DB port |
| `SQL_DATABASE` | Site database name |
| `SQL_USER` | DB user |
| `SQL_PASSWORD` | DB password |
| `RQ_HOST` | Redis host |
| `RQ_PORT` | Redis port |

## Optional (defaults)

| Variable | Default |
|----------|---------|
| `CONNECTIVITY_MODE` | `direct` (or `webserver` — no SQL/RQ variables needed; see [Scheduler configuration](scheduler-config.md)) |
| `RQ_PASSWORD` | unset |
| `WEBSERVER_HOST_HEADER` | unset |
| `LOG_LEVEL` | `INFO` |
| `TRACING_LEVEL` | unset — legacy alias for `LOG_LEVEL` |

Source of truth: `btu_scheduler/lib/config.py` in [btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py).
