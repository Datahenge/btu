# Set up Run Later poller

Run Later requires a **BTU Task** that calls `poll_for_ready_work` on a short interval. Do not use external cron or `hooks.py` — you lose BTU logging, email, and timeout handling for the poller itself.

## Prerequisites

- BTU app installed, workers running
- At least one Run Later document or Redis `enqueue_for_later` usage planned

## Steps

### 1. Create the poller task

**BTU Task** with:

| Field | Value |
|-------|-------|
| Function | `btu.btu_core.run_later.poll_for_ready_work` |
| Function Arguments | `{}` |
| Queue Name | `short` (or your preferred worker queue) |

### 2. Create a schedule

**BTU Task Schedule** on that task:

| Field | Suggested value |
|-------|-----------------|
| Cron | Every 1–5 minutes (e.g. `*/5 * * * *`) |
| Time zone | Site default |
| Enabled | Yes |

### 3. Verify

1. Create a **BTU Run Later** row with `hold_until` a minute in the future, or call `enqueue_for_later` from code.
2. Wait for the next poller fire.
3. Confirm a **BTU Task Log** appears for the deferred work.

## What the poller does

- Acquires a DB advisory lock (no overlapping polls)
- Scans Redis `btu_scheduler:run_later:*` keys ready to run
- Scans **BTU Run Later** documents with `execution_status = Pending Future`
- Marks timeouts on stuck In-Progress rows

## Why not hooks.py?

Frappe's scheduler hooks are developer-centric, lack Task Logs for the poller, and reintroduce the visibility gap BTU was built to close.
