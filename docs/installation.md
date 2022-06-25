### Installation
Background Task Unleashed consists of 2 separate (but cooperating) applications:

1. **[BTU](https://github.com/Datahenge/btu)** : A Frappe web application.
2. **[BTU Scheduler](https://github.com/Datahenge/btu_scheduler_daemon)** : A background daemon for Linux that schedules tasks, and acts as a liason between BTU and Python RQ.

To use the BTU, you *must* install both applications on the same Linux device.

----

### Part One: BTU (the Frappe App)
The *front-end* of BTU is a Frappe web application. It is the command & control center for BTU.  From your web browser you will:

* Create **Tasks**:  Tasks are pointers to Python code that your web server will run in the background.
* **Schedule** those tasks to run automatically, on certain days or times of the day.
* View your **Logs** to see what happened.  Did the Task succeed or fail?  What messages did it print?


#### Instructions:

Installing BTU is just like installing any other Frappe web application. You use [Bench](https://github.com/frappe/bench) to download and install it.

From your Frappe web server, in a terminal:
```bash
bench get-app --branch version-13 https://github.com/Datahenge/btu
bench --site your_site_name install-app btu
```

----

### Part Two: BTU Scheduler (the Linux daemon)
This is the *backend* application.  It is "always on" Linux daemon that you install on your Frappe web server.  The Scheduler is responsible for monitoring the Tasks, placing them into Queues at the correct datetime, and performing some light communication with the Frappe web server and Python RQ.

Unlike Frappe Apps, this Scheduler is a 64-bit Linux binary executable.  It does not require Python, Frappe, or any 3rd party libraries or dependencies.

#### Instructions:

##### 1. Download the binary executable file from GitHub.
The latest versions can be found [on the 'Releases' web page](https://github.com/Datahenge/btu_scheduler_daemon/releases)

##### 2. Save the binary file.
You can save anywhere you want.  Especially if you're comfortable with creating symlinks in Linux.

However, I recommend saving **btu_scheduler** file somewhere on your **[PATH](https://en.wikipedia.org/wiki/PATH_(variable))**.  A good place is this directory:
```
/usr/local/bin/
```

So, a complete path to the Scheduler would be: `/usr/local/bin/btu-scheduler`

##### 3. Test your work

* To verify the Scheduler is accessible on your Linux PATH?  Type: `which btu-scheduler`
* To check the version you're using?  `btu-scheduler --version`

----

### Running the Scheduler
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
