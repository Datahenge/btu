# Copyright (c) 2025, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BTUTaskData(Document):
	pass

	@frappe.whitelist()
	def button_readme_clicked(self):
		frappe.msgprint(
			"BTU Task Data has a DocField named 'text_data'.  But it could be gigantic.<br>To prevent web browser issues, it is always hidden."
		)
