# Copyright (c) 2023, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from btu import Result, get_system_datetime_now
from btu.btu_core import btu_email

class BTUTaskLog(Document):

	def after_insert(self):

		if (not self.task_component) or (self.task_component) == 'Main':
			# Update the "Last Result" column on the BTU Task.
			# NOTE: Setting update_modified prevents "Refresh" errors on the web page.
			datetime_string = frappe.utils.data.get_datetime_str( get_system_datetime_now())
			frappe.db.set_value("BTU Task", self.task, "last_runtime", datetime_string, update_modified=False)
			try:
				# First, may need to send an email when the task begins.
				btu_email.email_on_task_start(self)
				# Next, may need to send an email if the Log is already Success or Failed.
				if self.success_fail != "In-Progress":
					btu_email.email_on_task_conclusion(self)
			except Exception as ex:
				message = "Error in BTU Task Log (after_insert) while attempting to send email about Task Log."
				message += f"\n{str(ex)}\n"
				frappe.msgprint(message)
				print(message)
				frappe.set_value("BTU Task Log", self.name, "stdout", message + (self.stdout or ""))

	def on_update(self):

		if (not self.task_component) or (self.task_component) == 'Main':
			# Update the "Last Result" column on the BTU Task.
			# NOTE: Setting update_modified prevents "Refresh" errors on the web page.
			datetime_string = frappe.utils.data.get_datetime_str( get_system_datetime_now())
			frappe.db.set_value("BTU Task", self.task, "last_runtime", datetime_string, update_modified=False)
			# Email a summary of the Task to Users:
			try:
				if self.success_fail != "In-Progress":
					btu_email.email_on_task_conclusion(self)
			except Exception as ex:
				message = "Error in function email_on_task_conclusion(), during attempt to send email about Task Log."
				message += f"\n{str(ex)}\n"
				frappe.msgprint(message)
				print(message)
				frappe.db.set_value("BTU Task Log", self.name, "stdout", message + (self.stdout or ""))
				frappe.db.set_value("BTU Task Log", self.name, "success_fail", "Failed")


def write_log_for_task(task_id, result, log_name=None, stdout=None, date_time_started=None, schedule_id=None):
	"""
	Given a Task and Result, write to SQL table 'BTU Task Log'
	References:
		* btu_task.run_task_on_webserver()
		* TaskRunner().function_wrapper()

	Arguments
		task_id	: 	Primary key (name) of a BTU Task.
		result	:	A Result object.
		log_name :	Optional.  The name of the Task Log.  Useful when updating an existing, pending log.
	"""

	# Important Fields in BTU Task Log:
	#     1.  task
	#     2.  task_desc_short
	#     3.  execution_time
	#     4.  stdout
	#     5.  schedule
	#     6.  result_message
	#     7.  success_fail
	#     8.  date_time_started

	if not isinstance(result, Result):
		raise ValueError(f"Argument 'result' should be an instance of BTU class 'Result'. Found '{type(result)}' instead.")
	if stdout and not isinstance(stdout, str):
		raise ValueError(f"Argument 'stdout' should be a Python string.  Found '{type(result)}' instead.")

	# Slightly faster than 'get_doc()', which would return a complete Document.
	task_values = frappe.db.get_values('BTU Task', filters={'name': task_id},
	                                   fieldname=["name", "desc_short", "repeat_log_in_stdout"],
									   cache=True, as_dict=True)
	if task_values:
		task_values = task_values[0]  # get first Dictionary in the List.

	if log_name:
		new_log = frappe.get_doc("BTU Task Log", log_name)
	else:
		new_log = frappe.new_doc("BTU Task Log")  # Create a new Log.
		new_log.task = task_id  # Field 1
		new_log.task_desc_short = task_values['desc_short'] if task_values else "Unknown"  # Field 2.
		if schedule_id:
			new_log.schedule = schedule_id  # Field 5
		if date_time_started:
			new_log.date_time_started = date_time_started  # Field 8

	if result.execution_time:
		new_log.execution_time = result.execution_time  # Field 3
	new_log.stdout = stdout  # Field 4
	new_log.result_message = str(result.message)  # Field 6.  Could be a List or Dictionary, so must convert to a String.
	if result.okay:
		new_log.success_fail = 'Success'
	else:
		new_log.success_fail = 'Failed'  # Field 7

	# NOTE: Calling new_log.insert() will --not-- trigger Document class controller methods, like 'after_insert'
	#       Use save() instead.
	new_log.save(ignore_permissions=True)  # Not even System Administrators are supposed to create and save these.
	frappe.db.commit()

	if task_values and task_values["repeat_log_in_stdout"]:
		print(new_log.stdout)

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
	rows_to_delete = result[0][0]

	# Delete the rows:
	sql_statement = """ DELETE FROM `tabBTU Task Log`
	                    WHERE DATE(date_time_started) between %(from_date)s and %(to_date)s """
	frappe.db.sql(sql_statement,
	              values={"from_date": from_date, "to_date": to_date},
				  auto_commit=True)

	return rows_to_delete

@frappe.whitelist()
def check_in_progress_logs_for_timeout(verbose=False):
	"""
	Examine all logs that are In-Progress.  If they have exceeded the BTU Timeout Minutes, mark them as 'Failed'.
	"""

	# This function is called via a cron schedule in BTU hooks.py
	if verbose:
		print("Checking for any BTU Task Logs that are 'In-Progress' and have exceeded their Max Task Duration...")
	in_progress_logs = frappe.get_list("BTU Task Log", filters={"success_fail": "In-Progress"}, pluck="name")

	if verbose:
		print(f"Found {len(in_progress_logs)} BTU Task Logs that are In-Progress.")
	for each_document_name in in_progress_logs:
		doc_log = frappe.get_doc("BTU Task Log", each_document_name)
		max_task_duration = frappe.get_value("BTU Task", doc_log.task, "max_task_duration")
		try:
			max_task_duration = int(max_task_duration)  # in seconds
		except Exception as ex:
			raise Exception("Value of 'Max Task Duration' should be an integer representing seconds.") from ex

		seconds_since_log_creation = (now_datetime() - doc_log.creation).total_seconds()
		if seconds_since_log_creation > max_task_duration:
			print(f"BTU Task Log {doc_log.name}.  {seconds_since_log_creation} seconds have passed since creation.  Changing status from 'In-Progress' to 'Failed'")
			doc_log.success_fail = 'Timeout'
			doc_log.save()
			frappe.db.commit()
		elif verbose:
			print(f"BTU Task Log {doc_log.name}.  {seconds_since_log_creation} seconds have passed since creation, but 'max_task_duration' is {max_task_duration}")
