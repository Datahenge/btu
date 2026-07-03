# Mental model

BTU is one product with four runtime pieces:

```mermaid
flowchart TB
  subgraph desk [Frappe Desk - BTU app]
    Task[BTU Task]
    Schedule[BTU Task Schedule]
    RunLater[BTU Run Later]
    Config[BTU Configuration]
    Log[BTU Task Log]
  end
  subgraph daemon [btu_scheduler_py]
    Cron[Cron evaluator]
  end
  subgraph redis [Redis]
    RQ[RQ queues]
    RPC[Scheduler RPC]
    RLKeys[run_later keys]
  end
  subgraph workers [RQ Workers]
    Runner[run_task_by_id]
  end
  Schedule --> Cron
  Cron -->|HTTP enqueue| Task
  Task --> RQ
  RQ --> Runner
  Runner --> Log
  RunLater -->|poll_for_ready_work| Task
  RLKeys -->|poll_for_ready_work| Task
  Config --> RPC
  RPC --> daemon
```

## Data flow for a scheduled task

1. User creates a **BTU Task** (function path + arguments) and **BTU Task Schedule** (cron, timezone).
2. **Scheduler daemon** reads enabled schedules from the database, computes next run times.
3. At fire time, scheduler calls Frappe to enqueue the task on RQ.
4. **RQ worker** runs `btu.btu_core.task_runner.run_task_by_id`, which executes the Python function and writes a **BTU Task Log**.

## Control vs execution

| Plane | Component | Responsibility |
|-------|-----------|----------------|
| System of record | Frappe app | Tasks, Schedules, Logs, permissions, Desk |
| Time engine | Scheduler daemon | Cron evaluation, fire-at-time enqueue |
| Execution | RQ workers | Run Python callables |
| Transport | Redis | Job queues + scheduler RPC |

## Why two GitHub repos?

See [Why BTU](../get-started/why-btu.md) and [Technical design](../internals/technical-design.md).
