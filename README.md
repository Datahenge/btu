## Background Tasks Unleashed
Background Tasks Unleashed (BTU) is a [Frappe Framework](https://github.com/frappe) application for Task Scheduling and automation for Python code.  It is effectively a replacement for the 'out-of-the-box' **`Scheduled Job Types`** feature in Frappe v13.

What can BTU do?

* Enables users to configure any Python function (*with associated arguments*) to either run On-Demand, or on a repeating Schedule.
* Write to a Log, indicating not only the success/fail of the Task, but also execution time, Standard Output and Errors.
* View Logs on the web page, or automatically email Logs to multiple users.

**See Also**: You must also install the companion application: [BTU Scheduler Daemon](https://github.com/Datahenge/btu_scheduler_daemon)

----
### Features
#### Web-Centric
Background Tasks are created, edited, and scheduled entirely from the web browser.  Users never need to login to the web server, touch `hooks.py`, or examine log files on disk.

#### Flexible
Tasks can be executed in 4 different ways:
1. Immediately, on the web server, by clicking a button in the browser.
3. Immediately, via Redis Queue and job workers, by clicking a button in the browser.
5. Scheduled for future execution using a `BTU Task Schedule` DocType.
6. By writing your own Python code, and interacting with the TaskRunner() class.

#### Improved Logging
* Task activity is stored in a Document on the MySQL database.
  * You can review a Task's Log in the web browser by opening the `BTU Task Log` DocType.
  * This removes the need to SSH into the Frappe web server (*or install a 3rd party log collector*) just to review job logs.
* Task Logs automatically capture any `return` statement from their Task's Python function.
* Task Logs **automatically capture all standard output (stdout)** during function execution! 🥳
* Task Logs automatically record the Start Time and Duration of their Task.

#### Improved Scheduling
* Tasks can be scheduled via a Unix cron string.
* Without writing cron, Tasks can also be scheduled Hourly, Daily, Weekly, Monthly, or Annualy.
* No matter how you schedule, a **human-readable schedule** is shown, so you can be confident about your schedule.

#### Miscellaneous
* You can pass keyword arguments (kwargs) to your Task's function, by editing the Task document.

----
### Installation

To Install BTU as a Frappe App:

```
bench get-app --branch version-13 https://github.com/Datahenge/btu
bench --site your_site_name install-app btu
```

### Task Scheduler Daemon.
BTU is currently using [rq-scheduler](https://pypi.org/project/rq-scheduler/) for task scheduling and integration with Redis Queue RQ. 
Work is underway to replace rq-scheduler with [btu-scheduler](https://github.com/Datahenge/btu_scheduler_daemon).

### Legacy RQ Scheduler instructions.
An instance of `rqscheduler` must be running at all times, to perform the scheduling.

#### Option 1: Run rqscheduler manually, in a terminal

Here is how you would launch `rqscheduler` from a terminal:
```bash
cd frappe-bench
source env/bin/activate
rqscheduler -H 127.0.0.1 --port 11000
```

#### Option 2: Add rqscheduler to your Procfile
(documentation To Be Continued)

#### Option 3: Create a systemd Unit File, for automatic execution on boot.

Create a file here:  `/etc/systemd/system/erpnext_rqscheduler.service`

And write the following contents.  Make sure you edit and enter the proper path to your Frappe environment.
```
[Unit]
Description=Background Tasks Unleashed: RQ Scheduler

Wants=network.target
After=syslog.target network-online.target

[Service]
Type=simple
WorkingDirectory=/erpnext/v13bench
#
# It's very important that we run rqscheduler in the context of the ERPNext Python Virtual Environment.
#
ExecStart=/erpnext/v13bench/env/bin/python \
    /erpnext/v13bench/env/lib/python3.7/site-packages/rq_scheduler/scripts/rqscheduler.py -H 127.0.0.1 --port 11000
StandardOutput=/erpnext/v13bench/logs/rqscheduler.log
StandardError=/erpnext/v13bench/logs/rqscheduler_error.log
Restart=on-failure
RestartSec=10
KillMode=process

[Install]
WantedBy=multi-user.target
```

### Usage
Your website should have a new Workspace named `BTU Workspace`, with 3 new DocTypes:

  * Tasks
  * Task Schedules
  * Task Logs

(to be continued)

### BTU Project Roadmap
These are some of project tasks I intend want to finish:

* Create a *User Guide* here on GitHub.
* Create some HTML that displays what is happening on RQ.
    * It's rather difficult to **know** what is happening in Redis Queue.
    * Administrator can install GUI tools like [Another Redis Desktop Manager](https://www.electronjs.org/apps/anotherredisdesktopmanager) or [RQ Monitor](https://pypi.org/project/rqmonitor/).
    * However, these tools don't help non-Admins to understand whether everything is running okay, or not.

#### Copyright and License
BTU is licensed MIT.  See LICENSE.md file.

Copyright 2021, Datahenge LLC
Maintainer: brian@datahenge.com
