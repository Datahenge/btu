# BTU Task Schedule

Links a BTU Task to cron timing.

## Fields

| Field | Notes |
|-------|-------|
| Task | Link to BTU Task |
| Cron | Standard five-field cron |
| Time Zone | IANA name; cron interpreted locally |
| Enabled | When off, scheduler skips |

## Save behaviour

Saving notifies the scheduler via Redis RPC when reachable. If the daemon is offline, save succeeds with a warning (15.2+).

## Requires scheduler

Cron firing needs `btu-py run-daemon` running continuously.

See [Recurring schedule recipe](../../recipes/recurring-schedule-with-timezone.md).
