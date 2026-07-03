# Install scheduler

Install [btu_scheduler_py](https://github.com/Datahenge/btu_scheduler_py) on the host that can reach your site database, Redis, and Frappe web port.

!!! warning "Not a Frappe app"
    Do **not** clone into `apps/`. Bench will treat it as a Frappe application.

## Steps

```bash
python3 -m venv ~/venvs/btu-scheduler
source ~/venvs/btu-scheduler/bin/activate
git clone https://github.com/Datahenge/btu_scheduler_py.git
cd btu_scheduler_py
pip install -e .
# optional: pip install -e ".[development]"
```

Configure environment — see [Scheduler configuration](scheduler-config.md).

Verify CLI:

```bash
btu-py config path
btu-py config show
```

## Next

[Run the scheduler](run-scheduler.md)
