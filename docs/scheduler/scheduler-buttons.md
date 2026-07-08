# Scheduler buttons

**BTU Configuration** and schedule forms expose scheduler control actions over Redis RPC.

| Button | Effect |
|--------|--------|
| Send ping | Verify scheduler process and Redis RPC path |
| Resubmit all task schedules | Reload all schedules in daemon |

Schedule save/cancel also sends reload/cancel RPC when the daemon is reachable. If offline, schedule **saves still succeed** (15.2+) with a warning.

See [Redis control plane](../concepts/redis-control-plane.md).
