# Common errors

## Ping fails / scheduler unreachable

- Scheduler not running
- `BTU_SCHEDULER_DISABLE_REDIS_RPC=true`
- Redis host/port mismatch between bench and scheduler
- Firewall between scheduler and Redis

## Task Log: ImportError on function path

Function not importable on worker — app not installed, typo in path, or worker not restarted after deploy.

## RQ job failed / pickling error

Upgrade to BTU 15.1+. Pass dotted function path strings, not function objects or Documents.

## Schedule saves but never runs

Cron wrong for intended timezone, schedule disabled, or daemon not reading DB (check SQL config).

## Email not sent

Verify **Default Email Account**, Frappe email queue, and that task failure actually occurred (email send failure does not fail the task).
