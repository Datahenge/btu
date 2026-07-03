# Defer with document

Use the **BTU Run Later** DocType for Desk-visible deferred execution.

## Steps

1. Ensure [Run Later poller](set-up-run-later-poller.md) is configured.
2. Create **BTU Run Later**:
   - Function path and arguments
   - **Hold Until** datetime
   - Queue name
   - Execution status: Pending Future
3. Poller picks it up when `hold_until <= now`.

## Public API

`create_doc_run_later()` in `btu.btu_core.run_later` creates documents programmatically with the same fields.

## Verify

Row transitions Pending Future → In-Progress → Success/Failed; linked Task Log when complete.

See [Desk → BTU Run Later](../guides/desk/run-later.md).
