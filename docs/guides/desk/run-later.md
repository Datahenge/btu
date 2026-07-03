# BTU Run Later

Desk-visible deferred one-shot execution.

## Key fields

| Field | Purpose |
|-------|---------|
| Function Path | Dotted Python path |
| Function Arguments | JSON kwargs |
| Hold Until | Do not run before this datetime |
| Redis Queue Name | Target RQ queue |
| Execution Status | Pending Future, In-Progress, Success, Failed, Abandoned |
| Last Attempt / Last Result | Retry diagnostics |

## Requires poller

Create [Run Later poller task + schedule](../../recipes/set-up-run-later-poller.md) — typically every 1–5 minutes.

## Programmatic creation

`create_doc_run_later()` in `btu.btu_core.run_later`.
