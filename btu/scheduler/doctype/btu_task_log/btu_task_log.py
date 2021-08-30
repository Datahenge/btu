# Copyright (c) 2021, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from btu import Result

class BTUTaskLog(Document):
	pass

def write_log_for_task(task_id, result, stdout=None, date_time_started=None, schedule_id=None):
	"""
	Given a Task and Result, write to SQL table 'BTU Task Log'
	References:
		* btu_task.run_task_on_webserver()
		* TaskRunner().function_wrapper()
	"""

	if not isinstance(result, Result):
		raise ValueError(f"Argument 'result' should be an instance of BTU class 'Result'. Found '{type(result)}' instead.")
	if stdout and not isinstance(stdout, str):
		raise ValueError(f"Argument 'stdout' should be a Python string.  Found '{type(result)}' instead.")

	# Create new log
	new_log = frappe.new_doc("BTU Task Log")
	# Argument 1: Task ID
	new_log.task = task_id
	# also, fetch the Task's short description
	doc_task = frappe.get_doc("BTU Task", task_id)
	new_log.task_name = doc_task.desc_short
	# Argument 2: Result
	if result.okay:
		new_log.success_fail = 'Success'
	else:
		new_log.success_fail = 'Failed'
	new_log.result_message = result.message
	if result.execution_time:
		new_log.execution_time = result.execution_time
	# Argument 3: Standard Output
	new_log.stdout = stdout
	# Argument 4: Standard Output
	if 	date_time_started:
		new_log.date_time_started = date_time_started
	# Argument 5: Task Schedule ID
	if schedule_id:
		new_log.schedule = schedule_id

	new_log.insert(ignore_permissions=True)  # Not even System Administrators are supposed to create and save these.
	frappe.db.commit()
	return new_log.name


@frappe.whitelist()
def delete_logs_by_dates(from_date, to_date):
	"""
	Delete records in 'BTU Task Log' where execution date is between a date range.
	"""

	# Count the rows first, so we can return this value to the web page.
	sql_statement = """ SELECT count(*) as RowCount FROM `tabBTU Task Log`
	                    WHERE DATE(date_time_started) between %(from_date)s and %(to_date)s """

	result = frappe.db.sql(sql_statement,
	                       values={"from_date": from_date, "to_date": to_date},
				           debug=False,
				           explain=False)
	rows_deleted = result[0][0]

	# Delete the rows:
	sql_statement = """ DELETE FROM `tabBTU Task Log`
	                    WHERE DATE(date_time_started) between %(from_date)s and %(to_date)s """

	frappe.db.sql(sql_statement,
	              values={"from_date": from_date, "to_date": to_date},
				  auto_commit=True)

	return rows_deleted
