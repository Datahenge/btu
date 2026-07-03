# Failed jobs

## BTU Task Log

Failed executions appear in **BTU Task Log** with stderr/traceback. Email notifications fire if configured.

## RQ failed job registry

**BTU Configuration** exposes tools to inspect/requeue failed RQ jobs (via `btu.btu_core.rq_admin`).

Common causes:

- Import error (function path wrong or app not on worker)
- Timeout / SIGKILL (increase worker timeout or reduce work)
- Pickling issues (BTU 15.1+ uses primitive args — avoid passing Document objects)

## Worker logs

Check bench worker stdout/stderr alongside Task Log for low-level RQ errors.
