# Run the scheduler in Docker (webserver mode)

The simplest way to schedule BTU Tasks on a containerized ERPNext stack: run the scheduler daemon as
its own Docker Compose project, in **webserver** connectivity mode, on the stack's private network.

- **No SQL or Redis access.** The daemon calls only BTU's whitelisted endpoints on the Frappe web server.
- **No public internet.** It joins the ERPNext stack's Docker network and calls the web server by its
  service name over plain HTTP, with the site's `Host` header.
- **Its own lifecycle.** Rebuild or restart it without touching the ERPNext stack.

A complete, working example is in the scheduler repository:
[docker/standalone/](https://github.com/Datahenge/btu_scheduler_py/tree/version-16/docker/standalone).

## 1. Prepare the site

1. Install BTU and migrate. Migration creates the **BTU Scheduler** role (no Desk access).
2. Create a User for the daemon, for example `btu-scheduler@example.com`. Give it **only** the
   BTU Scheduler role, and generate its API key and secret.
3. In **BTU Configuration → Misc**, set **Run Scheduled Tasks As** to the User that scheduled Tasks
   should run as. The default is Administrator. Scheduled Tasks never run as the daemon's own User,
   so that User needs no other role.
4. Switch the site to webserver mode, which BTU Configuration also uses to show the daemon's liveness:

    ```bash
    bench --site <site> set-config btu_scheduler_connectivity_mode webserver
    ```

## 2. Create the Compose project

On the Docker host, in a directory such as `~/btu-scheduler`:

```text
btu-scheduler/
├── compose.yml                # from docker/standalone/
├── scheduler.settings.env     # from scheduler.settings.env.example
├── scheduler.secret.env       # from scheduler.secret.env.example; chmod 600
└── src/                       # btu_scheduler_py source at a known commit (+ src/COMMIT)
```

`compose.yml`:

```yaml
name: btu-scheduler

services:
  btu-scheduler:
    build:
      context: ./src
      args:
        UV_SYNC_EXTRAS: ""    # webserver mode needs no SQL drivers
    image: btu-scheduler:local
    container_name: btu-scheduler
    restart: unless-stopped
    env_file:
      - ./scheduler.settings.env
      - ./scheduler.secret.env
    networks:
      - erpnext
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

networks:
  erpnext:
    external: true
    name: erpnext_default     # the ERPNext stack's network, from `docker network ls`
```

`scheduler.settings.env`:

```ini
BTU_SCHEDULER_CONNECTIVITY_MODE=webserver
BTU_SCHEDULER_WEBSERVER_IP=backend          # the Frappe web server's service name or alias
BTU_SCHEDULER_WEBSERVER_PORT=8000           # its internal port
BTU_SCHEDULER_WEBSERVER_HOST_HEADER=erp.example.com   # the site name
BTU_SCHEDULER_FULL_REFRESH_INTERNAL_SECS=30
BTU_SCHEDULER_SCHEDULER_POLLING_INTERVAL=30
BTU_SCHEDULER_LOG_LEVEL=INFO
```

`scheduler.secret.env` (`chmod 600`; never commit or print it):

```ini
BTU_SCHEDULER_WEBSERVER_TOKEN=token <api_key>:<api_secret>
```

Pin the source so you know what runs:

```bash
mkdir -p src
git -C /path/to/btu_scheduler_py archive --format=tar <commit> | tar -x -C src
echo <commit> > src/COMMIT
```

## 3. Start and check

```bash
docker compose up -d --build
docker compose ps          # "healthy" after about a minute
docker compose logs -f
```

The scheduler is working when **BTU Configuration** shows "BTU Scheduler (webserver mode) last polled
N seconds ago" in green, and a schedule produces BTU Task Logs at its cron times. A quick end-to-end
test: **Create Ping Task (10 s wait)** in BTU Configuration, then give that Task a schedule such as
`*/3 * * * *`.

## Operating notes

- **Restarts.** The daemon's loops retry after a failed call, for example while the web server
  restarts. A fatal error makes the process exit, and `restart: unless-stopped` brings it back.
- **Health.** The image's `HEALTHCHECK` watches a zero-byte heartbeat file that the scheduling loop
  touches every pass. Docker Compose reports `unhealthy` but does not restart on it.
- **Ping.** Nothing can answer a ping in webserver mode, so BTU Configuration disables
  **Send 'ping' to Scheduler** and shows the last poll instead.
- **Commands.** Schedule reloads and cancellations reach the daemon on its next poll, up to one
  polling interval later.
- **Logs.** The daemon logs JSON lines to stdout only. `compose.yml` caps Docker's log at 3 × 10 MB.
  Per-schedule next-run lines are logged at DEBUG.
- **Upgrade.** Replace `src/` with a newer commit (keep the old one for rollback), update `src/COMMIT`,
  and run `docker compose up -d --build`.
