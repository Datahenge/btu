"""BTU Task Log DocType controller."""

# Copyright (c) 2021-2025, Datahenge LLC and contributors
# For license information, please see license.txt

from datetime import datetime

import frappe
from frappe.model.document import Document
from pypika import functions as fn
from temporal_lib.core import get_system_datetime_now, is_datetime_naive, make_datetime_naive

from btu import Result, print_both
from btu.btu_core import btu_email


class BTUTaskLog(Document):
	"""Execution log for a BTU Task run."""

	def after_insert(self) -> None:
		"""Update task metadata and send start or conclusion emails."""
		if (not self.task_component) or (self.task_component) == "Main":
			datetime_string = frappe.utils.data.get_datetime_str(get_system_datetime_now())
			frappe.db.set_value("BTU Task", self.task, "last_runtime", datetime_string, update_modified=False)
			try:
				btu_email.email_on_task_start(self)
				if self.success_fail != "In-Progress":
					btu_email.email_on_task_conclusion(self)
			except Exception as ex:
				message = (
					"Error in BTU Task Log (after_insert) while attempting to send email about Task Log."
				)
				message += f"\n{ex!r}\n"
				print_both(message)
				frappe.set_value("BTU Task Log", self.name, "stdout", message + (self.stdout or ""))

	def on_update(self) -> None:
		"""Update task metadata and send conclusion emails when a log completes."""
		if (not self.task_component) or (self.task_component) == "Main":
			datetime_string = frappe.utils.data.get_datetime_str(get_system_datetime_now())
			frappe.db.set_value("BTU Task", self.task, "last_runtime", datetime_string, update_modified=False)
			try:
				if self.success_fail != "In-Progress":
					btu_email.email_on_task_conclusion(self)
			except Exception as ex:
				message = "Error in function email_on_task_conclusion(), during attempt to send email about Task Log."
				message += f"\n{ex!s}\n"
				print_both(message)
				frappe.db.set_value("BTU Task Log", self.name, "stdout", message + (self.stdout or ""))


def on_doctype_update() -> None:
	"""Create additional indexes and constraints for BTU Task Log."""
	frappe.db.add_index("BTU Task Log", ["task"], index_name="task_idx")
	frappe.db.add_index("BTU Task Log", ["schedule"], index_name="schedule_idx")
	frappe.db.add_index("BTU Task Log", ["task_desc_short"], index_name="description_idx")
	frappe.db.add_index("BTU Task Log", ["rq_job_id"], index_name="rq_job_id_idx")


def write_log_for_task(
	task_id: str,
	result: Result,
	log_name: str | None = None,
	stdout: str | None = None,
	date_time_started: datetime | None = None,
	schedule_id: str | None = None,
) -> str:
	"""Write or update a BTU Task Log row for the given task and result."""
	frappe.logger("btu").info("BTU Task %s overall result: %s", task_id, bool(result))

	if not isinstance(result, Result):
		raise ValueError(
			f"Argument 'result' should be an instance of BTU class 'Result'. Found '{type(result)}' instead."
		)
	if stdout and not isinstance(stdout, str):
		try:
			stdout = str(stdout)
		except Exception:
			raise ValueError(
				f"Argument 'stdout' should be a Python string.  Found datatype '{type(result)}' instead."
			)  # pylint: disable=raise-missing-from

	task_values = frappe.db.get_values(
		"BTU Task",
		filters={"name": task_id},
		fieldname=["name", "desc_short", "repeat_log_in_stdout"],
		cache=True,
		as_dict=True,
	)
	if task_values:
		task_values = task_values[0]

	if log_name:
		new_log = frappe.get_doc("BTU Task Log", log_name)
	else:
		new_log = frappe.new_doc("BTU Task Log")
		new_log.task = task_id
		new_log.task_desc_short = task_values["desc_short"] if task_values else "Unknown"
		if schedule_id:
			new_log.schedule = schedule_id
		if date_time_started:
			new_log.date_time_started = date_time_started

	if result.execution_time:
		new_log.execution_time = result.execution_time
	new_log.stdout = f"{new_log.stdout if new_log.stdout else ''}\n{stdout}"
	new_log.result_message = str(result.message)
	if result.okay:
		new_log.success_fail = "Success"
	else:
		new_log.success_fail = "Failed"

	new_log.save(ignore_permissions=True)
	frappe.db.commit()

	if task_values and task_values["repeat_log_in_stdout"]:
		print(new_log.stdout)

	return new_log.name


@frappe.whitelist()
def delete_logs_by_dates(from_date: str, to_date: str) -> int:
	"""Delete BTU Task Log rows whose start date falls within the given range."""
	task_log_table = frappe.qb.DocType("BTU Task Log")
	sql_statement: list = (
		frappe.qb.from_(task_log_table)
		.select(fn.Count("*"))
		.where(fn.Date(task_log_table.date_time_started) >= from_date)
		.where(fn.Date(task_log_table.date_time_started) <= to_date)
	)
	rows_to_delete: int = sql_statement.run()[0][0]

	(
		frappe.qb.from_(task_log_table)
		.delete()
		.where(fn.Date(task_log_table.date_time_started) >= from_date)
		.where(fn.Date(task_log_table.date_time_started) <= to_date)
	).run(auto_commit=True)

	return rows_to_delete


@frappe.whitelist()
def check_in_progress_logs_for_timeout(verbose: bool = False) -> None:
	"""Mark In-Progress logs as Timeout when they exceed max task duration."""
	if verbose:
		frappe.logger("btu").info(
			"Checking BTU Task Logs that are In-Progress and have exceeded Max Task Duration."
		)
	in_progress_logs = frappe.get_list("BTU Task Log", filters={"success_fail": "In-Progress"}, pluck="name")

	if verbose:
		frappe.logger("btu").info("Found %d BTU Task Logs that are In-Progress.", len(in_progress_logs))

	datetime_now_tz_aware = get_system_datetime_now()

	for each_document_name in in_progress_logs:
		doc_log = frappe.get_doc("BTU Task Log", each_document_name)
		max_task_duration = frappe.get_value("BTU Task", doc_log.task, "max_task_duration")
		try:
			max_task_duration = int(max_task_duration)
		except Exception as ex:
			raise ValueError(
				"Value of 'Max Task Duration' should be an integer representing seconds."
			) from ex

		log_creation_tz_aware = (
			make_datetime_naive(doc_log.creation) if is_datetime_naive(doc_log.creation) else doc_log.creation
		)
		seconds_since_log_creation = (datetime_now_tz_aware - log_creation_tz_aware).total_seconds()
		if seconds_since_log_creation > max_task_duration:
			frappe.logger("btu").warning(
				"BTU Task Log %s: %ss elapsed, exceeds max_task_duration=%s. Marking Timeout.",
				doc_log.name,
				seconds_since_log_creation,
				max_task_duration,
			)
			doc_log.success_fail = "Timeout"
			doc_log.save()
			frappe.db.commit()
		elif verbose:
			frappe.logger("btu").info(
				"BTU Task Log %s: %ss elapsed, within max_task_duration=%s.",
				doc_log.name,
				seconds_since_log_creation,
				max_task_duration,
			)
