# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt
"""Desktop module configuration for the BTU app."""

from typing import Any

from frappe import _


def get_data() -> list[dict[str, Any]]:
	"""Return desktop module entries for the BTU_Core module."""
	return [
		{
			"module_name": "BTU_Core",
			"color": "grey",
			"icon": "octicon octicon-file-directory",
			"type": "module",
			"label": _("Background Task Core"),
		}
	]
