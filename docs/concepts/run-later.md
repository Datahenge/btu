# Run Later

**Run Later** defers one-shot work to a future time while keeping it **visible** in the Desk.

## Two mechanisms

| Path | Storage | Desk visibility |
|------|---------|-----------------|
| `enqueue_for_later()` | Redis hash keys | No DocType row until poller fires |
| **BTU Run Later** DocType | SQL | Full DocType lifecycle |

Both are processed by `poll_for_ready_work()` — not by Frappe's built-in scheduler or raw RQ delay.

## Why not RQ `enqueue_at`?

RQ delayed jobs are invisible in the Desk, lack BTU logging/email guarantees, and bypass Task Log conventions. BTU Run Later trades a few minutes of latency (poller interval) for observability.

See [Desk → BTU Run Later](../guides/desk/run-later.md) and the [Set up Run Later poller](../recipes/set-up-run-later-poller.md) recipe.

Maintainer rationale: [ADR-0004](../internals/adr/0004-run-later-visibility-over-rq-delay.md).
