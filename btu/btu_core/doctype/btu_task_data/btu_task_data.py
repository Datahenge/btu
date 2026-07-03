"""BTU Task Data DocType controller."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BTUTaskData(Document):
	"""Large text payload storage associated with a BTU Task."""

	@frappe.whitelist()
	def button_readme_clicked(self) -> None:
		"""Show help text about the hidden text_data field."""
		frappe.msgprint(
			"BTU Task Data has a DocField named 'text_data'.  But it could be gigantic.<br>To prevent web browser issues, it is always hidden."
		)
