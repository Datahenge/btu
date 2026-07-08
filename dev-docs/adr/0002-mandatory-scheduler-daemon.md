# ADR-0002: External scheduler daemon is mandatory

**Status:** Accepted  
**Date:** 2026-03-02

## Context

Documentation and casual descriptions sometimes imply the BTU Scheduler is an optional add-on for advanced deployments.

For BTU’s product model — cron-based Task Schedules edited in the Desk — something must run outside Frappe to evaluate cron and fire schedules. Frappe’s own scheduler hooks are developer-centric and do not replace that role.

## Decision

Treat the **scheduler daemon as mandatory** for normal BTU operation with Task Schedules.

The Frappe app alone can enqueue one-shot Tasks and Run Later work, but **recurring scheduled automation** requires the daemon.

## Consequences

- Installation and operations docs must include daemon setup, not bury it as advanced.
- Health checks should cover daemon ↔ Redis ↔ Frappe connectivity (e.g. Configuration “ping” via Redis RPC).
- Feature design must not assume `hooks.py` or Frappe Scheduled Job Types as the primary scheduling path.
