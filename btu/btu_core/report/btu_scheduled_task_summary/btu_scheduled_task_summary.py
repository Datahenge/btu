# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

"""Script Report: most recent execution per enabled BTU Task Schedule."""

from typing import Any

import frappe
from frappe import _


def execute(
	filters: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
	"""Return column definitions and one row per enabled schedule."""
	return get_columns(), get_data()


def get_columns() -> list[dict[str, Any]]:
	"""Return Frappe report column metadata."""
	return [
		{
			"fieldname": "name",
			"label": _("Schedule ID"),
			"fieldtype": "Link",
			"options": "BTU Task Schedule",
			"width": 100,
		},
		{
			"fieldname": "task",
			"label": _("Task ID"),
			"fieldtype": "Link",
			"options": "BTU Task",
			"width": 100,
		},
		{
			"fieldname": "task_description",
			"label": _("Task Description"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "schedule_description",
			"label": _("Schedule"),
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"fieldname": "last_run_on",
			"label": _("Last Run On"),
			"fieldtype": "Data",
			"width": 250,
		},
		{
			"fieldname": "execution_time",
			"label": _("Last Duration (secs)"),
			"fieldtype": "Float",
			"precision": 1,
			"width": 150,
		},
		{
			"fieldname": "success_fail",
			"label": _("Last Result"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "hours_since_last",
			"label": _("Hours Since Last"),
			"fieldtype": "Float",
			"precision": 1,
			"width": 150,
		},
	]


def get_data() -> list[dict[str, Any]]:
	"""Fetch one row per enabled schedule, with datetime formatting done in Python."""
	rows = frappe.db.sql(
		"""
		SELECT
			TaskSchedule.name,
			TaskSchedule.task,
			TaskSchedule.task_description,
			TaskSchedule.schedule_description,
			drv1.date_time_started,
			drv1.execution_time,
			drv1.success_fail
		FROM `tabBTU Task Schedule` AS TaskSchedule
		LEFT JOIN (
			SELECT schedule, date_time_started, execution_time, success_fail,
			ROW_NUMBER() OVER (PARTITION BY schedule ORDER BY date_time_started DESC) AS occurrence
			FROM `tabBTU Task Log`
		) drv1
		ON drv1.schedule = TaskSchedule.name AND drv1.occurrence = 1
		WHERE TaskSchedule.enabled = 1
		""",
		as_dict=True,
	)

	now = frappe.utils.now_datetime()
	result = []
	for row in rows:
		dt = row.date_time_started
		result.append(
			{
				"name": row.name,
				"task": row.task,
				"task_description": row.task_description,
				"schedule_description": row.schedule_description,
				"last_run_on": dt.strftime("%A, %B %d %Y @ %I:%M %p") if dt else None,
				"execution_time": row.execution_time,
				"success_fail": row.success_fail,
				"hours_since_last": round((now - dt).total_seconds() / 3600, 1) if dt else None,
			}
		)
	return result
