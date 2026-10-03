# Install scheduler

Install [btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py) on the host that can reach your site database, Redis, and Frappe web port.

!!! warning "Not a Frappe app"
    Do **not** clone into `apps/`. Bench will treat it as a Frappe application.

## Steps (development)

```bash
python3 -m venv ~/venvs/btu-scheduler
source ~/venvs/btu-scheduler/bin/activate
git clone https://github.com/Datahenge/btu_scheduler_py.git
cd btu_scheduler_py
pip install -e .
# optional: pip install -e ".[development]"
```

Configure environment — see [Scheduler configuration](scheduler-config.md).

Verify CLI:

```bash
btu config path
btu config show
```

## Production VPS install

For a first-time install on a client VPS (fresh login, nothing installed yet), use
`scripts/install-vps.sh` from the [btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py)
repository. It installs `uv` if missing, installs BTU Scheduler, creates the dedicated
`btu-scheduler` system user, writes the `/etc/btu-scheduler/btu-scheduler.env` file, and installs
+ enables the systemd service described in [Run the scheduler](run-scheduler.md).

```bash
curl -fsSL https://raw.githubusercontent.com/Datahenge/btu_scheduler_py/main/scripts/install-vps.sh \
  -o install-vps.sh
chmod +x install-vps.sh
sudo ./install-vps.sh
```

Run it without arguments for an interactive prompt walking through each setting, or pass
`BTU_SCHEDULER_*` values as environment variables to run non-interactively. See the script's
`--help` for the full list.

## Next

[Run the scheduler](run-scheduler.md)
