"""BTU-specific housekeeping utilities."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

from datetime import timedelta

import frappe

from btu import get_system_datetime_now


def cleanup_transient_tasks(age_in_days: int = 30) -> None:
	"""Delete BTU Task Log rows for transient Subtasks older than ``age_in_days``.

	Example::

	    bench --site mysite execute btu.btu_core.housekeeping.cleanup_transient_tasks
	"""
	older_than_date = get_system_datetime_now().date() + timedelta(days=-age_in_days)
	task_log_table = frappe.qb.DocType("BTU Task Log")
	task_table = frappe.qb.DocType("BTU Task")

	sql_statement = (
		frappe.qb.from_(task_log_table)
		.delete()
		.inner_join(task_table)
		.on(task_table.name == task_log_table.task & task_table.task_type == "Subtask")
		.where(task_log_table.creation <= older_than_date)
	)

	frappe.logger("btu").info("Deleting transient task logs: %s", sql_statement.get_sql())
	sql_statement.run()
	frappe.logger("btu").info(
		"Deleted BTU Task Log records for transient Subtasks older than %s", older_than_date
	)
