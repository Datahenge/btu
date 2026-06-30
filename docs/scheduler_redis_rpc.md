# BTU Scheduler — Redis RPC Control Protocol

## Why this exists

The original BTU Scheduler communicated with the Frappe web application via a Unix Domain Socket (UDS). UDS works well on a single machine but breaks entirely in containerised deployments, because two processes in separate containers cannot share a socket file path without a shared filesystem volume — which is fragile, non-standard, and unavailable in most container orchestration environments (Docker, Kubernetes, etc.).

The replacement is a Redis-based request/reply protocol. Redis is already required by both Frappe (for Python RQ job queues) and the BTU Scheduler itself, so this adds no new infrastructure dependency and works across containers out of the box.

---

## How it works

### The rendezvous model

Redis Lists have a blocking pop command: `BLPOP key timeout`. This command removes and returns an element from the list, blocking the caller for up to `timeout` seconds if the list is currently empty. When another process pushes an element to the same key, the blocked caller wakes up immediately.

BTU uses two lists per command:

1. **Command queue** — a single, well-known key (`btu:scheduler:commands`) where the Frappe web server pushes incoming commands.
2. **Response key** — a unique, per-request key (`btu:scheduler:rpc:{uuid}`) where the scheduler pushes its acknowledgement.

### Step-by-step sequence

```
Frappe Web Worker                    Redis                    BTU Scheduler Daemon

1. Generate unique response_key:
   "btu:scheduler:rpc:abc123"

2. Build command JSON:
   {
     "request_type": "cancel_task_schedule",
     "request_content": "TS-000003",
     "response_key": "btu:scheduler:rpc:abc123"
   }

3. LPUSH "btu:scheduler:commands"
   <command JSON>                ──────────────────────►

4. BLPOP "btu:scheduler:rpc:abc123"
   timeout=5                    ◄── (blocking; waits up to 5 seconds)

                                                         5. BRPOP "btu:scheduler:commands"
                                                            (was already waiting here)
                                                            ← receives the command

                                                         6. IMMEDIATELY:
                                                            LPUSH "btu:scheduler:rpc:abc123"
                                                            { "status": "ok",
                                                              "request_type": "cancel_task_schedule",
                                                              "message": "Command received by BTU Scheduler." }

7. BLPOP unblocks; reads ACK  ◄────────────────────────
8. Returns response to browser UI

                                                         9. (After ACK) Executes the cancellation.
```

### Receipt ACK, not completion ACK

The scheduler pushes its acknowledgement **before** executing the command (step 6 precedes step 9). This is intentional.

If the scheduler ACKed after execution, multiple rapid commands from the browser (e.g. cancelling five schedules quickly) could queue up and time out — not because the scheduler is broken, but simply because it can only execute one command at a time. The caller's 5-second timeout would expire while the scheduler was still working through an earlier command.

By ACKing receipt immediately, the web worker unblocks in milliseconds regardless of queue depth. What the ACK actually confirms is meaningful and sufficient:

- The BTU Scheduler process is alive.
- Its Redis connection is healthy.
- Its command-dispatch loop is spinning.

Execution errors, if any, are captured in the scheduler's own logs.

---

## Key names

| Key | Owner | Purpose |
|-----|-------|---------|
| `btu:scheduler:commands` | Frappe writes, Scheduler reads | Incoming command queue |
| `btu:scheduler:rpc:{uuid}` | Scheduler writes, Frappe reads | Per-request response inbox |

The response key has a 60-second TTL set by the scheduler (`EXPIRE`). This auto-cleans orphaned keys if the web worker dies before reading its response.

---

## Command message format

```json
{
  "request_type": "cancel_task_schedule",
  "request_content": "TS-000003",
  "response_key": "btu:scheduler:rpc:abc123def456"
}
```

| Field | Type | Values |
|-------|------|--------|
| `request_type` | string | `ping`, `create_task_schedule`, `cancel_task_schedule` |
| `request_content` | string or null | Task Schedule ID for create/cancel; null for ping |
| `response_key` | string | Unique Redis key the scheduler writes its ACK to |

## ACK response format

```json
{
  "status": "ok",
  "request_type": "cancel_task_schedule",
  "message": "Command received by BTU Scheduler."
}
```

A `null` response (BLPOP timeout) means the scheduler did not respond within 5 seconds. It does not mean the command failed — it means the scheduler is unreachable. Check that the scheduler process is running and that both processes share the same Redis instance.

---

## Disabling the Redis RPC listener

Set `disable_redis_rpc = true` in `/etc/btu_scheduler/btu_scheduler.toml` to prevent the scheduler from starting the listener. This should only be needed for debugging.

---

## Relationship to TCP and Unix Domain Sockets

The Redis RPC listener is the **primary** control channel as of 2025. The TCP and UDS listeners remain available for backward compatibility and local debugging but are no longer required for normal operation. The Frappe `SchedulerAPI` class now uses Redis RPC exclusively.
