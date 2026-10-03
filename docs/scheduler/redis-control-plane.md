# Redis control plane

The Frappe app sends **control commands** to the scheduler daemon over Redis RPC — same Redis instance as RQ.

## Commands

| Command | Purpose |
|---------|---------|
| Ping | Verify daemon is alive |
| Reload schedule | Push schedule changes to daemon |
| Cancel schedule | Stop future fires for a schedule |

## User-facing triggers

**BTU Configuration** and **BTU Task Schedule** forms expose buttons that call this API.

## Protocol details

See [Reference → Redis RPC protocol](redis-rpc.md).

!!! note "webserver connectivity mode"
    This Redis RPC channel only runs when the scheduler daemon is in `connectivity_mode=direct`
    (the default). In `connectivity_mode=webserver`, the daemon has no direct Redis access, so it
    polls `get_pending_scheduler_commands` on the Frappe web server instead of listening on
    Redis — the Frappe side still pushes to the same queue, it's just drained by HTTP poll rather
    than `BLPOP`. See [Scheduler configuration](scheduler-config.md).
