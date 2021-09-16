""" btu.hooks.py """

from datetime import datetime as _datetime
from . import __version__ as app_version

# pylint: disable=invalid-name
# pylint: disable=pointless-string-statement

app_name = "btu"
app_title = "Background Tasks Unleashed"
app_publisher = "Datahenge LLC"
app_description = "Background Tasks Unleashed"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "brian@datahenge.com"
app_license = "MIT"

"""
--------
The Trouble with Hooks.py
--------

This file is loaded and executed by:
1. Web Server processes.  You could be running many separate instances of Gunicorn.
2. Workers.

So how do we know the "global" state of things?
We really don't know.  We can fetch "locals" per Werkzeug process.  But (to my knowledge) there is no "master", global thread.

So.  Unless you need code to run, over and over, all the time?  Don't put it here in hook.py.  It's going to be executed
uncontrollably.

The following code demonstrates the variety of ways that 'hooks.py is being used.

"""

import threading as _threading  # pylint: disable=wrong-import-position, wrong-import-order
import os as _os  # pylint: disable=wrong-import-position, wrong-import-order
print("\n--------\nHooks.py was executed.")
print(f"Current Time: {_datetime.now()}")
print(f"OS Process ID: {_os.getpid()}")
print(f"OS Thread Name: {_threading.current_thread().name}")
print("--------\n")


"""
Regarding extending 'bootinfo'

This doesn't behave like you'd expect.  The code will trigger on Webpage logins or refreshes.
The bootinfo code does -not- trigger on Web Server initialization.
It is a poorly-named feature.

# extend_bootinfo = "btu.boot.boot_session"
"""



def check_if_tasks_scheduled():
	"""
	Call the web server and get the value of 'frappe.local.flags.
	"""
	import requests

	# The function checks frappe.locals.flags, so that this doesn't execute more than once.

	api_key = "foo"
	api_secret = "bar"

	try:
		response = requests.get('http://localhost:8000/api/method/btu.scheduler.are_tasks.scheduled')
		print(f"Response from web server: {response}")
	except Exception as ex:
		print(f"Error in request call: {ex}\n")
		return False


#if not check_if_tasks_scheduled():
#	from btu.scheduler.doctype.btu_task_schedule.btu_task_schedule import resubmit_all_task_schedules
#	resubmit_all_task_schedules()
