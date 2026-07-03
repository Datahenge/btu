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

See [Reference → Redis RPC protocol](../reference/redis-rpc.md).

Set `BTU_SCHEDULER_DISABLE_REDIS_RPC=true` only for debugging — the Frappe app will not reach the daemon.
