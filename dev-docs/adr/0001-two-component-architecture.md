# ADR-0001: Two-component architecture (Frappe app + daemon)

**Status:** Accepted  
**Date:** 2026-03-02

## Context

BTU must let non-developers configure recurring background work from the ERPNext Desk, while a separate process evaluates cron schedules and triggers execution at the right time.

A single Python package cannot satisfy both:

- User-facing UI and persistent schedule data require Frappe DocTypes.
- Continuous schedule evaluation requires a lightweight daemon, not a Frappe web or worker process.

## Decision

Split BTU into:

1. **Frappe app** (`btu`) — Tasks, Schedules, Logs, Configuration, Run Later, enqueue integration, observability.
2. **Scheduler daemon** (`btu_scheduler_py` / legacy Rust daemon) — reads schedules, computes next run times, triggers Frappe/RQ at fire time.

Schedule and task **data** live in Frappe. Schedule **timing** lives in the daemon.

## Consequences

- Two repositories to install, configure, and operate.
- Redis (RQ + RPC) and HTTP are required integration surfaces.
- DocTypes remain the system of record; the daemon is a client, not a second database of truth.
- Contributors must understand which code belongs in which component (see [Technical Design](../../docs/internals/technical-design.md)).
