# Scheduler configuration

All scheduler settings use the `BTU_SCHEDULER_` prefix.

## Configuration file (development)

```bash
mkdir -p ~/.config/btu-scheduler
cp .env.example ~/.config/btu-scheduler/.env
nano ~/.config/btu-scheduler/.env
```

Path: `$XDG_CONFIG_HOME/btu-scheduler/.env` or `~/.config/btu-scheduler/.env`.

## Production (systemd / containers)

Set the same variables in the process environment (systemd `EnvironmentFile=`, Docker/Compose
`environment:`, or Kubernetes env). **Process environment always overrides** the `.env` file —
see [Run the scheduler](run-scheduler.md) for a systemd example and
[docker/](https://github.com/Datahenge/btu_scheduler_py/tree/main/docker) in the repo for a
Compose example.

## Connectivity mode

`BTU_SCHEDULER_CONNECTIVITY_MODE` controls how the scheduler reaches ERPNext, and determines
which of the variables below are actually required:

| Value | Reaches ERPNext via | Needs SQL/RQ variables? |
|-------|---------------------|--------------------------|
| `direct` (default) | Direct SQL + Redis, plus the Frappe web server for enqueueing | Yes |
| `webserver` | Frappe REST API only | No |

## Required variables (`connectivity_mode=direct`)

| Variable | Description |
|----------|-------------|
| `BTU_SCHEDULER_FULL_REFRESH_INTERNAL_SECS` | Seconds between full queue refills |
| `BTU_SCHEDULER_SCHEDULER_POLLING_INTERVAL` | Seconds between RQ eligibility checks (and, in `webserver` mode, the command-poll interval) |
| `BTU_SCHEDULER_SQL_TYPE` | `postgres` or `mariadb` |
| `BTU_SCHEDULER_SQL_HOST` | Database host |
| `BTU_SCHEDULER_SQL_PORT` | Database port |
| `BTU_SCHEDULER_SQL_DATABASE` | Frappe site database name |
| `BTU_SCHEDULER_SQL_USER` | Database user |
| `BTU_SCHEDULER_SQL_PASSWORD` | Database password |
| `BTU_SCHEDULER_RQ_HOST` | Redis host (same as bench) |
| `BTU_SCHEDULER_RQ_PORT` | Redis port |

## Required variables (both modes)

| Variable | Description |
|----------|-------------|
| `BTU_SCHEDULER_WEBSERVER_IP` | Frappe web server host or public DNS name |
| `BTU_SCHEDULER_WEBSERVER_PORT` | Frappe web port (443 for HTTPS) |
| `BTU_SCHEDULER_WEBSERVER_TOKEN` | Frappe API token (`token api_key:api_secret`) |

## Optional variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BTU_SCHEDULER_CONNECTIVITY_MODE` | `direct` | `direct` or `webserver` — see above |
| `BTU_SCHEDULER_RQ_PASSWORD` | unset | Redis password, if required |
| `BTU_SCHEDULER_WEBSERVER_HOST_HEADER` | unset | Host header for multi-tenant sites |
| `BTU_SCHEDULER_LOG_LEVEL` | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `BTU_SCHEDULER_TRACING_LEVEL` | unset | Legacy alias for `LOG_LEVEL` |

Full reference: [Scheduler environment variables](scheduler-env-vars.md).

## Loading precedence

```
Process environment          (highest)
.env in current directory
$XDG_CONFIG_HOME/btu-scheduler/.env, or ~/.config/btu-scheduler/.env
Field defaults                (lowest)
```

See scheduler source `btu_scheduler/lib/config.py`.
