# Run the scheduler

## Foreground (development)

```bash
source ~/venvs/btu-scheduler/bin/activate
btu-py run-daemon
```

## systemd example

```ini
[Unit]
Description=BTU Scheduler
After=network.target redis.service mariadb.service

[Service]
Type=simple
User=frappe
EnvironmentFile=/etc/btu_scheduler/env
ExecStart=/home/frappe/venvs/btu-scheduler/bin/btu-py run-daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Use `EnvironmentFile` or inline `Environment=` for all `BTU_SCHEDULER_*` variables in production instead of `~/.config/.../.env`.

## Health check

From Frappe Desk → **BTU Configuration** → **Send 'ping' to Schedule Bot**.

## Logs

- Scheduler file log: `BTU_SCHEDULER_LOGGER_PATH`
- CLI: `btu-py config show` (secrets redacted)
