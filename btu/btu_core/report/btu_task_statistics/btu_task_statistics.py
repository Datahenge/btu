# Copyright (c) 2025, Datahenge LLC and contributors
# For license information, please see license.txt

from pypika import functions as fn
from pypika.terms import Function
import frappe
from frappe import _


def execute(filters=None):  # pylint: disable=unused-argument
	columns, data = get_columns(), get_data()
	return columns, data

# For some reason, PyPika has a Floor function but not a Ceiling.  So guerilla patching it ...
class Ceiling(Function):
	def __init__(self, term, alias=None):
		super(Ceiling, self).__init__('CEIL', term, alias=alias)

fn.Ceiling = Ceiling


def get_data():
	"""
	bench execute btu.btu_core.report.task_log_averages.task_log_averages.get_data
	"""
	task_log = frappe.qb.DocType('BTU Task Log')
	task = frappe.qb.DocType('BTU Task')

	query = (
	frappe.qb.from_(task_log)
	.inner_join(task)
	.on(
		(task.task_type == "Persistent") &
		(task.name == task_log.task)
	)
	.select(task_log.task,
	        task_log.task_desc_short,
			fn.Ceiling(fn.Min(task_log.execution_time)).as_("minimum_time"),
			fn.Ceiling(fn.Max(task_log.execution_time)).as_("maximum_time"),
			fn.Ceiling(fn.Avg(task_log.execution_time)).as_("average_time")
	)
	.where(
		(task_log.success_fail == 'Success') &
		(fn.Coalesce(task_log.task_component, 'Main').isin(['Main', '']))
	)
	.groupby(task_log.task, task_log.task_desc_short)
	.orderby(task_log.task)
	)
	return query.run(as_dict=True)


def get_columns():
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
		}
	]
	return columns
