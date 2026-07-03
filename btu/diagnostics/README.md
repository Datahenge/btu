# BTU diagnostics

Python helpers for **manual smoke testing** via `bench execute`. These are not sample BTU Task targets.

| Module | Purpose |
|--------|---------|
| `smoke.py` | Minimal ping/pong callables for workers and run-later |
| `rq_workers.py` | RQ enqueue and pickling checks |
| `task_runner.py` | BTU Task / TaskRunner integration tests |
| `logging_test.py` | BTU logger exercise |

The legacy import path `btu.manual_tests` re-exports these modules for backward compatibility.
