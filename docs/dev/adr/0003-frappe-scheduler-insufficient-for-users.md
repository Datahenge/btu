# ADR-0003: Frappe built-in scheduler is not a user product

**Status:** Accepted  
**Date:** 2026-03-02

## Context

Frappe provides Scheduled Job Types and `scheduler_events` in `hooks.py`. That works for app developers shipping fixed schedules with their code.

ERPNext customers often need operations staff to create and change automation without Python access, code review, or redeploys. Frappe’s mechanism is effectively invisible to them.

## Decision

BTU targets **business-configurable scheduling** via DocTypes (BTU Task, BTU Task Schedule, BTU Task Log), not extension of Frappe’s hook-based scheduler.

BTU does not attempt to patch or replace Frappe’s internal scheduler implementation. It provides an alternative **product surface** and data model.

## Consequences

- Some overlap with Frappe Scheduled Job Types is acceptable; migration is a site concern, not a BTU core goal.
- UX and permissions investment go into BTU DocTypes, not `hooks.py` examples.
- Documentation should state clearly who the audience is (Desk users vs developers).
