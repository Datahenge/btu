# BTU Task Log

Immutable-ish record of one task execution.

## Contents

- Linked BTU Task
- Status (In-Progress, Success, Failed, …)
- Start/end timestamps
- Captured stdout and stderr
- RQ Job ID (when available)

## Usage

- Audit what ran and what it printed
- Debug failures without SSH
- Filter/list views for operations

Logs are created by `task_runner.run_task_by_id` for scheduled, on-demand, and Run Later executions.
