## User Guide: Web UI
In this Frappe application, there are 4 main DocTypes you interact with:

1. BTU Configuration
2. BTU Task
3. BTU Task Schedule
4. BTU Task Log

### 1. BTU Configuration
The purpose of this DocType is setup and configuration.  Before you create Tasks and Task Schedules, you should configure the App.

#### DocFields

##### BTU Scheduler
* Path to BTU Scheduler Unix socket (DocField name = `path_to_btu_scheduler_uds`)
  * This is the absolute path, on your Frappe Web, to the Unix Domain Socket file for the scheduler daemon.  The default value is `/tmp/btu_scheduler.sock`.  If you change this, you must also reconfigure the scheduler daemon to match.

* Time Zone for Scheduling
  * For now, I recommend using a value of **UTC**.  There are some complications with converting UTC cron expressions into non-UTC cron expressions, that this project has not-yet resolved.

**TESTS**:

* There is a button named "Send 'ping' to Schedule Bot".  When clicked, it will communicate with the BTU Scheduler daemon over the Unix Domain Socket, and send a 'ping' message.  If the communication is successful, the daemon should reply with 'pong'
* Send Hello Email:  When clicked, this button will send a simple "Hello" email to the User.  (see more information below about configuring email)

##### Advanced Logging
* Create 'In-Progress' Logs.
  * When marked, whenever a Task Schedule runs in a queue, it will *immediately* insert a BTU Task Log with a value of 'In-Progress'.  This can be useful for knowing when a Task has started.
  * When unmarked, no BTU Task Logs are written until the Task completes (success or fail).

##### Email
The BTU App allows you to configure your own Email connections, independent of the Frappe Framework. (offering both options is probably a good PR opportunity)

* SMTP Server Address:  For example, 'smtp.gmail.com'
* Email Server Port:  Usually 25, 587, or 465.
* Auth Username:  The username for authenticating with your email provider.
* Auth Password:  The password for authenticating with your email provider.
* Encryption Options: The value chosen will depend on your SMTP settings and email provider.  Generally, if using port 25 you want 'None', if port 587 then STARTTLS, and if encrypted 465 then SSL.
* Send email Body as HTML:  When checked, emails sent by BTU are HTML.  Otherwise when unchecked, plain text is transmitted.
* Environment Prefix:  This is optional.  If running in a non-production environment, you could enter a value here such as DEV, TEST, or STAGING.  Then whenever emails are transmitted, they will use this text as a prefix in the email subject and body.
  * Very useful if you're running multiple environment, and you want to know **which one** sent the email!
