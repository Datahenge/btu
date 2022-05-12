""" btu.hooks.py """

from . import __version__ as app_version

#pylint: disable=invalid-name
app_name = "btu"
app_title = "Background Tasks Unleashed"
app_publisher = "Datahenge LLC"
app_description = "Background Tasks Unleashed"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "brian@datahenge.com"
app_license = "MIT"

# Uses the native ERPNext Scheduler to investigate BTU Tasks that are still In-Progress after N minutes.
scheduler_events = {

	"cron": {
	 	"0/5 * * * *": [
	 		"btu.btu_core.doctype.btu_task_log.btu_task_log.check_in_progress_logs_for_timeout",
	 	]
	}
}
