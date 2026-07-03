# Recurring schedule with timezone

Run a task every weekday at 9:00 AM Eastern.

## Steps

1. Create **BTU Task** with your function path and arguments.
2. Create **BTU Task Schedule**:
   - Link the task
   - Cron: `0 9 * * 1-5` (minute hour dom month dow)
   - Time zone: `America/New_York`
   - Enabled: Yes
3. Ensure `btu-py run-daemon` is running.
4. After the next fire, check **BTU Task Log**.

## Notes

- Cron fields are interpreted in the **schedule's** time zone, not UTC.
- Daylight saving transitions follow the IANA zone rules.
