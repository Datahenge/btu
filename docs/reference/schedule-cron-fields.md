# Schedule cron fields

BTU Task Schedule uses **five-field cron**:

```
minute hour day-of-month month day-of-week
```

## Examples

| Expression | Meaning (local time in schedule TZ) |
|------------|-------------------------------------|
| `*/5 * * * *` | Every 5 minutes |
| `0 9 * * 1-5` | Weekdays at 09:00 |
| `0 0 1 * *` | First day of month at midnight |

## Time zone

Set **Time Zone** on the schedule. Cron is evaluated in that zone, not UTC.

## Validation

BTU uses cron parsing utilities in `btu/utils/cron.py` for Desk validation and display.
