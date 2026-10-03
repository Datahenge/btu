# Run the scheduler

## Foreground (development)

```bash
source ~/venvs/btu-scheduler/bin/activate
btu run-daemon
```

## systemd (production)

Install the unit file and an `EnvironmentFile` — `scripts/install-vps.sh` (see
[Install scheduler](install-scheduler.md)) does this for you, or set it up by hand:

```ini
# /etc/systemd/system/btu-scheduler.service
[Unit]
Description=BTU Scheduler daemon
After=network-online.target mariadb.service redis-server.service
Wants=network-online.target

[Service]
Type=simple
User=btu-scheduler
Group=btu-scheduler
EnvironmentFile=/etc/btu-scheduler/btu-scheduler.env
ExecStart=/opt/btu-scheduler/.venv/bin/btu run-daemon
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true

[Install]
WantedBy=multi-user.target
```

`EnvironmentFile` takes plain `KEY=VALUE` lines — no shell, so no quotes even around values
containing spaces (e.g. `BTU_SCHEDULER_WEBSERVER_TOKEN=token abc:def`). See
[Scheduler environment variables](scheduler-env-vars.md) for the full list, and
[Scheduler configuration](scheduler-config.md) for `BTU_SCHEDULER_CONNECTIVITY_MODE`, which
decides whether `EnvironmentFile` needs the SQL/Redis variables at all.

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now btu-scheduler
sudo journalctl -u btu-scheduler -f
```

## Health check

From Frappe Desk → **BTU Configuration** → **Send 'ping' to Schedule Bot**.

## Logs

- `sudo journalctl -u btu-scheduler -f` (systemd) or stdout (foreground/container)
- CLI: `btu config show` (secrets redacted)
