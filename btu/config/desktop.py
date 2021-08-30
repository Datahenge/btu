from frappe import _

def get_data():
	return [
		{
			"module_name": "Scheduler",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("Background Task Scheduler")
		}
	]
