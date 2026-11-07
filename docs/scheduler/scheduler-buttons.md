# Scheduler buttons

**BTU Configuration** and schedule forms expose scheduler control actions over Redis RPC.

| Button | Effect |
|--------|--------|
| Send ping | Verify scheduler process and Redis RPC path (direct mode only; disabled in webserver mode) |
| Resubmit all task schedules | Reload all schedules in daemon |

Schedule save/cancel also sends reload/cancel RPC when the daemon is reachable. If offline, schedule **saves still succeed** (15.2+) with a warning.

In **webserver** connectivity mode nothing can answer a ping, so the form disables **Send ping** and shows
"BTU Scheduler (webserver mode) last polled N seconds ago" instead: green within 120 seconds, red if
older or if no poll has been recorded.

**Create Ping Task (10 s wait)** creates and submits a BTU Task that runs
`btu.diagnostics.smoke.ping_with_wait` with a 10-second wait, for testing workers and schedules.

See [Redis control plane](redis-control-plane.md).
