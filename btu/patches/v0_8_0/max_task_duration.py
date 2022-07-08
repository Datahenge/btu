# Background Tasks Unleashed, Copyright (c) 2022, Datahenge LLC
# License: MIT

from __future__ import unicode_literals
import frappe

def execute():

	# 1. Max Task Duration is changing from a String to an Integer.
	if not frappe.db.table_exists('BTU Task'):
		return

	frappe.reload_doc(module='btu_core', dt='doctype', dn='btu_task', force=True)

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
