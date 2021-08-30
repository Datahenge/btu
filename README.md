## Background Tasks Unleashed

Background Tasks Unleashed
Copyright 2021, Datahenge LLC

Maintainer: brian@datahenge.com

#### License

MIT

#### Usage

1. Install BTU as a Frappe App
```
bench get-app --branch v1.0.0 https://github.com/frappe/erpnext
```
2. You need to run `rqscheduler` (which runs continously) in a terminal, or as a daemon.

Here is how you would launch `rqscheduler` from a terminal:
```bash
cd frappe-bench
source env/bin/activate
rqscheduler -H 127.0.0.1 --port 11000
```

Once in Production, this should be a systemd job and daemon.

#### Roadmap

* Ensure the schedules are populated on startup.
* Create some HTML that displays what is happening on RQ.