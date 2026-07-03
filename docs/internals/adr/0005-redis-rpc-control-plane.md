# ADR-0005: Redis RPC as scheduler control plane

**Status:** Accepted  
**Date:** 2026-03-02

## Context

The Frappe app must send control commands to the scheduler daemon (ping, reload schedule, cancel schedule). Early designs used Unix domain sockets, which break across containers without shared filesystems.

Both Frappe and the daemon already depend on Redis for RQ job queues.

## Decision

Use **Redis RPC** (`btu:scheduler:commands` / per-request response keys) as the sole control channel from the Frappe app. Implement via `SchedulerAPI` in `btu/btu_api/scheduler.py`.

Remove Unix socket configuration from BTU Configuration and documentation.

## Consequences

- Daemon and Frappe must share the same Redis instance used for `redis_queue`.
- BLPOP timeouts indicate daemon unreachability, not command failure (receipt ACK model — see [Redis RPC protocol](../../reference/redis-rpc.md)).
- TCP/UDS control paths are out of scope for the Frappe app; daemon-side legacy listeners are a separate project concern.
