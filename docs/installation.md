### Installation
Background Task Unleashed consists of 2 separate (but cooperating) applications:

1. **[BTU](https://github.com/Datahenge/btu)** : A Frappe web application.
2. **[BTU Scheduler](https://github.com/Datahenge/btu_scheduler_daemon)** : A background daemon for Linux that schedules tasks, and acts as a liason between BTU and Python RQ.

To use the BTU, you *must* install both.

----

### Part One: BTU (the Frappe App)
The *front-end* of BTU is a Frappe web application. It's your command & control center for BTU.  From your web browser you will:

* Create **Tasks**
* **Schedule** those tasks to run automatically.
* View your **Logs** to see what happened.

Installing BTU is just like installing any other Frappe web application. You use [Bench](https://github.com/frappe/bench) to download and install it.

From your Frappe web server, in a terminal:
```bash
bench get-app --branch version-13 https://github.com/Datahenge/btu
bench --site your_site_name install-app btu
```

----

### Part Two: BTU Scheduler (the Linux daemon)
This is the *back end* application.  It's an "always on" Linux daemon, responsible for scheduling your Tasks and communicating with both Frappe and Python RQ.

The scheduler is provided as a 64-bit Linux binary executable.  It does not require Python, Frappe, or any 3rd party libraries or dependencies.

[Download a binary from the 'Releases' web page](https://github.com/Datahenge/btu_scheduler_daemon/releases)

#### Where to save the binary?
Technically, you -can- save anywhere you want.  Especially if you're comfortable with creating symlinks in Linux.

However, for simplicity, I suggest you save **btu_scheduler** somewhere on your **[PATH](https://en.wikipedia.org/wiki/PATH_(variable))**, such as:
```
/usr/local/bin
```

#### Running the Scheduler
After you download and save, execute by opening a terminal and typing:
```
btu-scheduler
```

The BTU Scheduler keeps running forever, until you force it to stop.  When running in a terminal, just enter **CTRL+C**

#### How To Start the Scheduler automatically?
While you "could" just keep BTU Scheduler running all the time in a terminal?  It was really designed to be run as a background daemon.  There are many ways you can accomplish this, but I recommend using systemd and writing a Systemd Unit File.

1. Use your favorite text editor (vim, nano, [micro](https://micro-editor.github.io/)) to create a new Unit file: `/etc/systemd/system/erpnext_rqscheduler.service`

Add the following contents:

```
[Unit]
Description=BTU Scheduler

Wants=network.target
After=syslog.target network-online.target

[Service]
Type=simple
WorkingDirectory=<path_to_your_bench>

ExecStart=/usr/local/bin/btu-scheduler
StandardOutput=/erpnext/v13bench/logs/btu-scheduler.log
StandardError=/erpnext/v13bench/logs/btu-scheduler_error.log
Restart=on-failure
RestartSec=10
KillMode=process

[Install]
WantedBy=multi-user.target
```


## Next Up:  Configuration
Now that you have installed BTU and BTU Scheduler, you must **configure** them to communicate with each other, and Python RQ.
