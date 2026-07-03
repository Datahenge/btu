# Copyright (c) 2021-2026, Datahenge LLC and contributors
# License: MIT
"""Migrate BTU Task max_task_duration from string values to integers."""

import frappe


def execute() -> None:
	"""Convert legacy max_task_duration string values to integer seconds."""
	if not frappe.db.table_exists("BTU Task"):
		return

	frappe.reload_doc(module="btu_core", dt="doctype", dn="btu_task", force=True)

	sql_statement = """
	UPDATE `tabBTU Task`
	SET max_task_duration = REPLACE(max_task_duration,'s','');
	"""
	frappe.db.sql(sql_statement)

	sql_statement = """
	UPDATE `tabBTU Task`
	SET max_task_duration = REPLACE(max_task_duration,'h','') / 3600
	WHERE max_task_duration like '%h%';
	"""
	frappe.db.sql(sql_statement)
	frappe.db.commit()
