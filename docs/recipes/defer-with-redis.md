# Defer with Redis

Programmatic deferral via `enqueue_for_later()` — no BTU Run Later DocType row until the poller fires.

## Prerequisites

- [Run Later poller](set-up-run-later-poller.md) running

## Example

```python
from datetime import timedelta
from btu import get_system_datetime_now
from btu.btu_core.run_later import enqueue_for_later

enqueue_for_later(
    short_name="sync_contacts",
    not_before_time=get_system_datetime_now() + timedelta(hours=2),
    target_queue="default",
    path_to_function="myapp.tasks.sync_contacts",
    arguments={"full": True},
    unique_identifier="sync-contacts-2026-07-03",
)
```

`unique_identifier` prevents duplicate pending entries.

## Verify

After `hold` time and poller cycle, confirm Task Log for the enqueued one-shot.
