### Installation
Background Task Unleashed consists of 2 separate (but cooperating) open source applications:

1. **BTU** : A Frappe web application (link to [GitHub repository](https://github.com/Datahenge/btu))
2. **BTU Scheduler** : A background daemon that schedules tasks by integrating BTU and Python RQ. (link to [GitHub repository](https://github.com/Datahenge/btu_scheduler_daemon))

To use the BTU, you *-must-* install both applications on the same device that hosts your Frappe web server.

##### Version/Branch
The BTU git branches will stay synchronized with the LTS branches of Frappe Framework.  The current support versions are:

* `version-13`

----

### Installation #1: BTU (the Frappe App)
The *front-end* of BTU is a Frappe web application. It is the command & control center for BTU.  From your web browser you will:

* **Create Tasks**:  Tasks are pointers to Python code that your web server will run in the background (via Python RQ worker threads)
* **Schedule Tasks**: Schedules might be once per week, or every 5 minutes, or Mondays and Wednesdays at 7 AM and 4 PM.  It's very flexible.
* **View Logs** to see what happened when you ran a Task.  Did it succeed or fail?  What messages did it print to standard output?

#### Instructions:

You install BTU like any other Frappe web application. You use the [Bench](https://github.com/frappe/bench) CLI application to download, install, and assign to your Sites.

From your Frappe web server, in a terminal:
```bash
bench get-app --branch version-13 https://github.com/Datahenge/btu
bench --site your_site_name install-app btu
```

----

### Installation #2: BTU Scheduler (the Linux daemon)
This is the *backend* application.  It is "always on" Linux daemon that you install on your Frappe web server.  The Scheduler is responsible for monitoring the Tasks, placing them into Queues at the correct datetime, and performing some light communication with the Frappe web server and Python RQ.

Unlike Frappe Apps, this Scheduler is a 64-bit Linux binary executable.  It does not require Python, JS, Frappe, or any 3rd party libraries or dependencies.

#### Instructions:

##### 1. Download the binary executable file from GitHub.
The latest versions can be found [on the 'Releases' web page](https://github.com/Datahenge/btu_scheduler_daemon/releases).  It's important to choose the correct release for your Linux distribution:

* Ubuntu 18/19 or Debian 10 "Buster" users should choose a **Debian 10** release.
* Ubuntu 20/21 or Debian 11 "Bullseye" users should choose a **Debian 11** release.

##### 2. Save the binary file.
You can save anywhere the binary executable anywhere on your server (*especially if you're comfortable creating symlinks*).  However, I recommend saving **btu_scheduler** file somewhere on your **[PATH](https://en.wikipedia.org/wiki/PATH_(variable))**.  A good place is this directory:
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

[Configuration](https://datahenge.github.io/btu/configuration.html)
