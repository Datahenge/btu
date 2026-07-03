# Timeouts and housekeeping

## In-progress log timeout

BTU runs a hook every 5 minutes (`identify_timeouts` in housekeeping) to detect Task Logs stuck **In-Progress** beyond configured max duration.

## Run Later timeouts

`poll_for_ready_work` marks **BTU Run Later** rows In-Progress for more than one hour as failed/retry per retry rules.

## Scheduler polling

Tune `BTU_SCHEDULER_SCHEDULER_POLLING_INTERVAL` and `BTU_SCHEDULER_FULL_REFRESH_INTERNAL_SECS` for load vs responsiveness tradeoffs.
