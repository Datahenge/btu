# Copyright (c) 2022, Datahenge LLC and contributors
# For license information, please see license.txt


from frappe import _

def get_data():
	return [
		{
			"module_name": "BTU_Core",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("Background Task Core")
		}
	]
