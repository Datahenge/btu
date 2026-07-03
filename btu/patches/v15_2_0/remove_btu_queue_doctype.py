# Copyright (c) 2021-2026, Datahenge LLC and contributors
# License: MIT
"""Remove the deprecated BTU Queue DocType (queue names come from bench config)."""

import frappe


def execute() -> None:
	"""Delete BTU Queue records and DocType metadata."""
	if not frappe.db.table_exists("tabBTU Queue"):
		return

	for name in frappe.get_all("BTU Queue", pluck="name"):
		frappe.delete_doc("BTU Queue", name, force=1, ignore_permissions=True)

	if frappe.db.exists("DocType", "BTU Queue"):
		frappe.delete_doc("DocType", "BTU Queue", force=1, ignore_permissions=True)

	frappe.db.commit()
