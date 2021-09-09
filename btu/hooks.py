""" btu.hooks.py """

from datetime import datetime as _datetime
import frappe as _frappe

from . import __version__ as app_version

# pylint: disable=invalid-name
app_name = "btu"
app_title = "Background Tasks Unleashed"
app_publisher = "Datahenge LLC"
app_description = "Background Tasks Unleashed"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "brian@datahenge.com"
app_license = "MIT"

# Hooks is executed by Workers, which have no idea about Web Server's global state.
# Code running here will not know about Frappe Flags.

# Not even sure how it knows what Site it is?

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
		print(f"Error in request call: {ex}")
		return False


# The problem with hooks.py is it's called All. The. Time.  It's annoying how often it's loaded again and again.
# I don't want to ping the web server every 60 seconds.

# _frappe.whatis("foo")

print(f"\n--------\nHooks.py was executed at {_datetime.now()}\n--------\n")
if not check_if_tasks_scheduled():
	from btu.scheduler.doctype.btu_task_schedule.btu_task_schedule import resubmit_all_task_schedules
	# resubmit_all_task_schedules()
