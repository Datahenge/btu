## Frequently Asked Questions

### Do I need ERPNext?
No!  BTU has no dependencies on ERPNext.

### Why not Scheduled Tasks?
There were many reasons I wrote the BTU, instead of using Frappe framework's 'Scheduled Tasks'.\
In the standard Frappe framework...

   * Users cannot create new task schedules, without *writing Python code* in `'hooks.py'`.  Users without access to this file (or Python know-how), have no alternatives or options.

   * Users cannot -edit- the schedule, without editing Python code.

   * Users cannot run a task one-time, on demand.
  
   * Users cannot pause or suspend a schedule.

   * Developers have limited capability of controlling the overall Success/Failure response from a scheduled task.

   * There are no Email Alerts when a task succeeds, fails, or completes.

   * The task's standard output is either lost forever, or saved inside Redis, or saved in a text file on the host.  Regardless, this information is not easily accessible by web Users.

   * There are few reports about background tasks.

### Why two applications?
Because of the Unix philosophy: "Make each program do one thing well."

1. For users, the Frappe framework and web server is the best tool (imo) for interacting with the scheduler.
2. However, the web server is *not* the best tool (imo) for performing the role of a scheduler daemon.  I wanted a program to fulfill that singular role, and to perform it well.  So I wrote the Scheduler application separately.
