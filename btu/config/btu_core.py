from __future__ import unicode_literals
from frappe import _

# Adds items to the menu for 'BTU Core' Module
def get_data():
	return [
		{
			"label": _("Documents"),
			"icon": "fa fa-star",
			"items": [
				{
					"type": "doctype",
					"name": "BTU Task",
					"label": "Tasks",
					"description": _("BTU Tasks"),
					"onboard": 0,
				},
				{
					"type": "doctype",
					"name": "BTU Task Schedule",
					"label": "Schedules",
					"description": _("BTU Task Schedules"),
					"onboard": 0,
				},
				{
					"type": "doctype",
					"name": "BTU Task Log",
					"label": "Logs",
					"description": _("BTU Task Logs"),
					"onboard": 0,
				}
			]
		},
		{
			"label": _("Settings"),
			"items": [
				{
					"type": "doctype",
					"name": "BTU Configuration",
					"label": "Configuration",
					"description": _("Configuration"),
					"onboard": 1,
				},
				{
					"type": "doctype",
					"name": "BTU Queue",
					"label": "Queues",
					"description": _("Queues"),
					"onboard": 1,
				}
			]
		},
		{
			"label": _("Reports"),
			"icon": "fa fa-table",
			"items": [
				{
					"type": "report",
					"name": "BTU Scheduled Task Summary",
					"is_query_report": True,
					"label": _("Scheduled Task Summary"),
					"icon": "fa fa-bar-chart",
					"onboard": 1,
				},
			]
		}
	]
