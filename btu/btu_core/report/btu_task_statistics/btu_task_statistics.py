# Copyright (c) 2025, Datahenge LLC and contributors
# For license information, please see license.txt

"""Query report: min, max, and average execution times per persistent BTU Task."""

from typing import Any

import frappe
from frappe import _
from pypika import functions as fn
from pypika.terms import Function


def execute(
	filters: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
	"""Return column definitions and aggregated task timing rows for the report."""
	columns, data = get_columns(), get_data()
	return columns, data


# For some reason, PyPika has a Floor function but not a Ceiling.  So guerilla patching it ...
class Ceiling(Function):
	"""PyPika ``CEIL`` aggregate patched onto ``fn`` because Ceiling was missing."""

	def __init__(self, term: object, alias: str | None = None) -> None:
		"""Initialize CEIL with the given PyPika term and optional alias."""
		super().__init__("CEIL", term, alias=alias)


fn.Ceiling = Ceiling


def get_data() -> list[dict[str, Any]]:
	"""Return per-task min, max, and average execution times from successful main logs."""
	task_log = frappe.qb.DocType("BTU Task Log")
	task = frappe.qb.DocType("BTU Task")

	query = (
		frappe.qb.from_(task_log)
		.inner_join(task)
		.on((task.task_type == "Persistent") & (task.name == task_log.task))
		.select(
			task_log.task,
			task_log.task_desc_short,
			fn.Ceiling(fn.Min(task_log.execution_time)).as_("minimum_time"),
			fn.Ceiling(fn.Max(task_log.execution_time)).as_("maximum_time"),
			fn.Ceiling(fn.Avg(task_log.execution_time)).as_("average_time"),
		)
		.where(
			(task_log.success_fail == "Success")
			& (fn.Coalesce(task_log.task_component, "Main").isin(["Main", ""]))
		)
		.groupby(task_log.task, task_log.task_desc_short)
		.orderby(task_log.task)
	)
	return query.run(as_dict=True)


def get_columns() -> list[dict[str, Any]]:
	"""Return Frappe report column metadata for the statistics grid."""
	columns = [
		{
			"fieldname": "task",
			"label": _("Task"),
			"fieldtype": "Link",
			"options": "BTU Task",
			"width": 200,
		},
		{
			"fieldname": "task_desc_short",
			"label": _("Short Description"),
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"fieldname": "minimum_time",
			"label": _("Minimum Time (secs)"),
			"fieldtype": "Float",
			"precision": 1,
			"width": 200,
		},
		{
			"fieldname": "maximum_time",
			"label": _("Maximum Time (secs)"),
			"fieldtype": "Float",
			"precision": 1,
			"width": 200,
		},
		{
			"fieldname": "average_time",
			"label": _("Average Time (secs)"),
			"fieldtype": "Float",
			"precision": 1,
			"width": 200,
		},
	]
	return columns
