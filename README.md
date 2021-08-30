## Background Tasks Unleashed
Copyright 2021, Datahenge LLC\
Maintainer: brian@datahenge.com

#### License

MIT

### Overview
Background Tasks Unleashed (BTU) is an application for the [Frappe Framework](https://frappeframework.com/) (See GitHub repo [here](https://github.com/frappe)).\
It is effectively a replacement for the 'out-of-the-box' **`Scheduled Job Types`**.
* Run any Python function immediately, or on a repeating schedule.
* View the results of the function call in your web browser, by examining Task Logs.

----
### Features
#### Web-Centric
Background Tasks are created, edited, and scheduled entirely from the web browser.  You never need to edit `hooks.py`.

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

1. Install BTU as a Frappe App
```
bench get-app --branch version-13 https://github.com/Datahenge/btu
```

The installation process will automatically install Python package [rq-scheduler](https://pypi.org/project/rq-scheduler/).

2. An instance of `rqscheduler` must be running at all times, to perform the scheduling.

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
(documentation To Be Continued)

### Usage
Your website should have a new Workspace named `BTU Workspace`, with 3 new DocTypes:
  * Tasks
  * Task Schedules
  * Task Logs

(to be continued)

### BTU Project Roadmap
These are some of project tasks I intend want to finish:

* Create a *User Guide* here on GitHub.
* Ensure the Task Schedules are kickstarted on web server startup (more-difficult than it sounds)
* Create some HTML that displays what is happening on RQ.
    * It's rather difficult to **know** what is happening in Redis Queue.  You can install some GUI tools like [Another Redis Desktop Manager](https://www.electronjs.org/apps/anotherredisdesktopmanager) or [RQ Monitor](https://pypi.org/project/rqmonitor/).  But these tools still don't make it obvious to a User that everything is "okay" or "broken"
