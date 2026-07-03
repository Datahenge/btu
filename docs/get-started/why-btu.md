# Why BTU?

Frappe ships **Scheduled Job Types** and `scheduler_events` in `hooks.py`. That works when schedules are fixed in application code and only developers change them.

BTU exists for a different audience: **operations and power users** who need to configure, inspect, and audit background work from the Desk — without SSH, deploys, or Python edits.

## What BTU adds

| Capability | Frappe built-in | BTU |
|------------|-----------------|-----|
| Schedules editable in UI | Limited | Full cron + timezone per schedule |
| Task output logging | Minimal | Complete stdout/stderr in Task Log |
| Email on failure | Ad hoc | Built into Task / Schedule |
| Deferred execution with visibility | RQ delay (opaque) | Run Later DocType + poller |
| Non-developer ownership | No | Yes |

## One product, two repos

BTU is intentionally split:

| Component | Repo | Why separate |
|-----------|------|--------------|
| Frappe app | [Datahenge/btu](https://github.com/Datahenge/btu) | Only a Frappe app provides Desk, DocTypes, permissions |
| Scheduler daemon | [Datahenge/btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py) | Must run continuously; cannot live in `apps/` or as a Frappe app |

They communicate via **HTTP** (enqueue at fire time), **Redis RQ** (worker execution), and **Redis RPC** (ping, reload, cancel).

The legacy Rust scheduler ([btu_scheduler_daemon](https://github.com/Datahenge/btu_scheduler_daemon)) is **retired**. Use `btu_scheduler_py` only.

## When BTU is not the right tool

- One-off `frappe.enqueue` from custom app code with no UI requirement
- Fixed cron in your app's `hooks.py` that never changes in production
- Work that must run inside Frappe's web request lifecycle

For everything else that looks like **business-configured automation**, BTU is the intended product.
