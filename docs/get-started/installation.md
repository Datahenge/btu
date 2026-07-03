# Installation

Install **both** components and verify they work together. ERPNext is not required — any Frappe v15 site with RQ workers is sufficient.

## Part 1 — BTU Frappe app

From your bench directory:

```bash
bench get-app --branch version-15 https://github.com/Datahenge/btu
bench --site YOUR_SITE install-app btu
bench --site YOUR_SITE migrate
bench restart
```

Confirm **BTU_Core** module appears in the Desk.

## Part 2 — BTU Scheduler (Python)

The scheduler is **not** a Frappe app. Do not clone it into `apps/`.

```bash
python3 -m venv ~/venvs/btu-scheduler
source ~/venvs/btu-scheduler/bin/activate
git clone https://github.com/Datahenge/btu_scheduler_py.git
cd btu_scheduler_py
pip install -e .
```

Create configuration (see [Scheduler configuration](../operations/scheduler-config.md)):

```bash
mkdir -p ~/.config/btu_scheduler
cp .env.example ~/.config/btu_scheduler/.env
# edit BTU_SCHEDULER_* variables for your site
nano ~/.config/btu_scheduler/.env
```

Required settings include database credentials (same DB as your Frappe site), Redis/RQ host, and Frappe API token for enqueue.

Start the daemon:

```bash
btu-py run-daemon
```

For production, run under systemd or your process supervisor. See [Run the scheduler](../operations/run-scheduler.md).

## Part 3 — RQ workers

BTU tasks execute via Frappe RQ workers:

```bash
bench worker --queue short,default,long
```

Queue names must match values on BTU Task forms (loaded from `common_site_config.json`).

## Part 4 — Verify together

1. Open **BTU Configuration** in the Desk.
2. Click **Send 'ping' to Schedule Bot** — you should see an acknowledgement if the scheduler is running and Redis RPC is reachable.
3. Create a test **BTU Task** pointing at `btu.diagnostics.smoke.ping_with_wait` with arguments `{"seconds_to_wait": 1}`.
4. Create a **BTU Task Schedule** on that task (e.g. every 5 minutes) and confirm a **BTU Task Log** appears after the next fire.

## Linux build note

If you build scheduler dependencies from source on Debian/Ubuntu:

```bash
apt install pkg-config libsystemd-dev
```

## Next steps

- [Configuration overview](configuration-overview.md)
- [Mental model](../concepts/mental-model.md)
- [Set up Run Later poller](../recipes/set-up-run-later-poller.md)
