# One-shot task

Run a function once without creating a permanent schedule.

## Desk

Use **create and run** flow on BTU Task, or run an existing task on demand.

## Code

```python
from btu.btu_core.doctype.btu_task.btu_task import create_and_run_one_shot

create_and_run_one_shot(
    short_description="Manual cleanup",
    function_path="myapp.tasks.cleanup_temp_files",
    arguments={},
    queue_name="short",
)
```

Creates a ephemeral task execution path and enqueues immediately.
