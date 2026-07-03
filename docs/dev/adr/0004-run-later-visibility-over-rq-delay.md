# ADR-0004: Run Later prioritizes Desk visibility over RQ delay

**Status:** Accepted  
**Date:** 2026-03-02

## Context

Deferred one-shot execution could use Python RQ’s built-in job delay: enqueue now, run later, with less BTU-specific code.

RQ delayed jobs are not visible in ERPNext. Users cannot answer: “Will this still run?” or “What is waiting?” without Redis/RQ access.

## Decision

Implement **BTU Run Later** (BTU Run Later documents and/or Redis keys polled by Frappe) so deferred work is **observable in the Desk** until it goes in-flight.

Accept additional complexity (dual storage paths, `poll_for_ready_work`) in exchange for operator visibility — the same philosophy as Task Logs and In-Progress status.

## Consequences

- Replacing Run Later with RQ-only delay requires a new Frappe-visible pending-work model; convenience alone is not sufficient reason to remove it.
- `btu/btu_core/run_later.py` remains a core module until a superseding ADR.
- Tests and docs should treat “pending Run Later” as a user-facing state, not an implementation detail.
