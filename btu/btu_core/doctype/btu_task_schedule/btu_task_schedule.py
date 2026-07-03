"""BTU Task Schedule DocType controller."""

# Copyright (c) 2015, Codrotech Inc. and contributors
#
# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

import ast
import calendar
from calendar import monthrange
from datetime import datetime as datetime_type
from typing import Any

# Third Party
import cron_descriptor

# Frappe
import frappe
import pytz
from frappe import _
from frappe.model.document import Document

# BTU
from btu import Result, print_both, validate_cron_string
from btu.btu_api.scheduler import SchedulerAPI

NoneType = type(None)
cron_day_dictionary = {"Sun": 0, "Mon": 1, "Tue": 2, "Wed": 3, "Thu": 4, "Fri": 5, "Sat": 6}


class BTUTaskSchedule(Document):  # pylint: disable=too-many-instance-attributes
	"""Cron-based schedule binding a BTU Task to a recurring execution plan."""

	def on_trash(self) -> None:
		"""Cancel scheduler state after this Task Schedule is deleted."""
		try:
			self.cancel_schedule()
		except Exception as ex:
			print(ex)
			frappe.msgprint(ex)

	def before_validate(self) -> None:
		"""Normalize schedule fields before validation."""
		self.task_description = self.get_task_doc().desc_short

		if not self.cron_timezone:
			self.cron_timezone = frappe.db.get_system_setting("time_zone")

		if self.run_frequency == "Cron Style":
			self.day_of_week = None
			self.day_of_month = None
			self.month = None
			self.hour = None
			self.minute = None
		if self.run_frequency == "Hourly":
			self.day_of_week = None
			self.day_of_month = None
			self.month = None
			self.hour = None
		if self.run_frequency == "Daily":
			self.day_of_week = None
			self.day_of_month = None
			self.month = None

	def validate(self) -> None:
		"""Validate schedule fields and build the cron string and description."""
		if self.run_frequency == "Hourly":
			check_minutes(self.minute)
			self.cron_string = schedule_to_cron_string(self)

		elif self.run_frequency == "Daily":
			check_hours(self.hour)
			check_minutes(self.minute)
			self.cron_string = schedule_to_cron_string(self)

		elif self.run_frequency == "Weekly":
			check_day_of_week(self.day_of_week)
			check_hours(self.hour)
			check_minutes(self.minute)
			self.cron_string = schedule_to_cron_string(self)

		elif self.run_frequency == "Monthly":
			check_day_of_month(self.run_frequency, self.day_of_month)
			check_hours(self.hour)
			check_minutes(self.minute)
			self.cron_string = schedule_to_cron_string(self)

		elif self.run_frequency == "Yearly":
			check_day_of_month(self.run_frequency, self.day_of_month, self.month)
			check_hours(self.hour)
			check_minutes(self.minute)
			self.cron_string = schedule_to_cron_string(self)

		elif self.run_frequency == "Cron Style":
			validate_cron_string(str(self.cron_string))

		self.schedule_description = cron_descriptor.get_description(self.cron_string)

	def before_save(self) -> None:
		"""Resubmit or cancel scheduler state when enabled status changes."""
		if "|" in self.name:
			raise ValueError("Task Schedules cannot have the pipe character (|) in their primary key 'name'.")

		if bool(self.enabled) is True:
			try:
				self.resubmit_task_schedule()
			except Exception as ex:
				frappe.msgprint(ex, indicator="red")
		else:
			doc_orig = self.get_doc_before_save()
			if doc_orig and doc_orig.enabled != self.enabled:
				try:
					self.cancel_schedule()
				except Exception as ex:
					print_both(ex)

	def resubmit_task_schedule(self, autosave: bool = False) -> None:
		"""Ask the BTU Scheduler daemon to reload this Task Schedule."""
		try:
			self.cancel_schedule()
		except Exception as ex:
			frappe.msgprint(f"Error while attempting to cancel Task Schedule {self.name}")
			print(ex)

		response = SchedulerAPI.reload_task_schedule(task_schedule_id=self.name)
		if not response:
			raise ConnectionError(
				"Error, no response from BTU Task Scheduler daemon. Check logs in '/etc/btu_scheduler/logs'."
			)
		message = response.get("message", str(response))
		print(f"Response from BTU Scheduler: {message}")
		frappe.msgprint(f"Response from BTU Scheduler daemon:<br>{message}")
		if autosave:
			self.save()

	def cancel_schedule(self) -> dict[str, Any] | None:
		"""Ask the BTU Scheduler daemon to cancel this Task Schedule."""
		response = SchedulerAPI.cancel_task_schedule(task_schedule_id=self.name)
		ack = response.get("message", str(response)) if response else "No response from BTU Scheduler daemon."
		message = f"Request = Cancel Task Schedule.\nResponse from BTU Scheduler: {ack}"
		print(message)
		frappe.msgprint(message)
		self.redis_job_id = ""
		return response

	def get_task_doc(self) -> Document:
		"""Return the linked BTU Task document."""
		return frappe.get_doc("BTU Task", self.task)

	@frappe.whitelist()
	def get_last_execution_results(self) -> None:
		"""Query Redis for information about the last execution of this job."""
		import zlib

		from frappe.utils.background_jobs import get_redis_conn

		if not self.redis_job_id:
			frappe.msgprint("No results available; Task may not have been processed yet.")
			return

		try:
			conn = get_redis_conn()
			job_status = conn.hget(f"rq:job:{self.redis_job_id}", "status").decode("utf-8")
		except Exception:
			frappe.msgprint(f"No job information is available for Job {self.redis_job_id}")
			return

		if job_status == "finished":
			frappe.msgprint(f"Job {self.redis_job_id} completed successfully.")
			return
		frappe.msgprint(f"Job status = {job_status}")
		compressed_data = conn.hget(f"rq:job:{self.redis_job_id}", "exc_info")
		if not compressed_data:
			frappe.msgprint("No results available; job may not have been processed yet.")
		else:
			frappe.msgprint(zlib.decompress(compressed_data))

	@frappe.whitelist()
	def button_test_email_via_log(self) -> None:
		"""Write a temporary Task Log to trigger test emails, then delete it."""
		from btu.btu_core.doctype.btu_task_log.btu_task_log import (
			write_log_for_task,
		)

		if not self.email_recipients:
			frappe.msgprint("Task Schedule does not have any Email Recipients; no emails can be tested.")
			return

		try:
			result_obj = Result(
				success=True,
				message="This test demonstrates how Task Logs can trigger an email on completion.",
			)
			log_key = write_log_for_task(task_id=self.task, result=result_obj, schedule_id=self.name)
			frappe.db.commit()
			frappe.delete_doc("BTU Task Log", log_key)
			frappe.msgprint("Log written; emails should arrive shortly.")

		except Exception as ex:
			frappe.msgprint(f"Errors while testing Task Emails: {ex}")
			raise ex

	def built_in_arguments(self) -> dict[str, Any] | None:
		"""Parse schedule argument overrides into a dictionary."""
		if not self.argument_overrides:
			return None
		return ast.literal_eval(self.argument_overrides)


def check_minutes(minute: int | None) -> None:
	"""Validate the minute field for hourly or finer schedules."""
	if isinstance(minute, NoneType) or not 0 <= int(minute) < 60:
		raise ValueError(_("Minute value must be between 0 and 59"))


def check_hours(hour: str | None) -> None:
	"""Validate the hour field for daily or finer schedules."""
	if not hour or not hour.isdigit() or not 0 <= int(hour) < 24:
		raise ValueError(_("Hour value must be between 0 and 23"))


def check_day_of_week(day_of_week: str | None) -> None:
	"""Validate the day-of-week field for weekly schedules."""
	if not day_of_week or day_of_week is None:
		raise ValueError(_("Please choose a day of the week"))


def check_day_of_month(run_frequency: str, day: int | None, month: str | None = None) -> None:
	"""Validate day-of-month and month fields for monthly or yearly schedules."""
	if run_frequency == "Monthly" and not day:
		raise ValueError(_("Please choose a day of the month"))

	if run_frequency == "Yearly":
		if day and month:
			month_dict = {value: key for key, value in enumerate(calendar.month_abbr)}
			last = monthrange(datetime_type.now().year, month_dict.get(str(month).title()))[1]
			if int(day) > last:
				raise ValueError(_("Day value for {0} must be between 1 and {1}").format(month, last))
		else:
			raise ValueError(_("Please choose a day of the week and a month"))


def schedule_to_cron_string(doc_schedule: "BTUTaskSchedule") -> str:
	"""Convert schedule fields into a Unix cron string in local time."""
	if not isinstance(doc_schedule, BTUTaskSchedule):
		raise ValueError("Function argument 'doc_schedule' should be a BTU Task Schedule document.")

	if doc_schedule.run_frequency == "Cron Style":
		return doc_schedule.cron_string

	cron = ["*", "*", "*", "*", "*"]

	if not isinstance(doc_schedule.minute, NoneType):
		cron[0] = str(int(doc_schedule.minute))

	if doc_schedule.hour:
		cron[1] = str(int(doc_schedule.hour))

	if doc_schedule.day_of_month:
		cron[2] = str(doc_schedule.day_of_month)

	if doc_schedule.month is not None:
		cron[3] = doc_schedule.month

	if doc_schedule.day_of_week:
		cron[4] = str(cron_day_dictionary[doc_schedule.day_of_week[:3]])

	result = " ".join(cron)
	validate_cron_string(result, error_on_invalid=True)
	return result


@frappe.whitelist()
def resubmit_all_task_schedules() -> None:
	"""Resubmit all enabled Task Schedules to the BTU Scheduler daemon."""
	filters = {"enabled": True}
	task_schedule_ids = frappe.db.get_all("BTU Task Schedule", filters=filters, pluck="name")
	for task_schedule_id in task_schedule_ids:
		try:
			doc_schedule = frappe.get_doc("BTU Task Schedule", task_schedule_id)
			doc_schedule.validate()
			doc_schedule.resubmit_task_schedule()
		except Exception as ex:
			message = f"Error from BTU Scheduler while submitting Task {doc_schedule.name} : {ex}"
			print_both(message)
			doc_schedule.enabled = False
			doc_schedule.save()


def get_system_timezone() -> pytz.BaseTzInfo:
	"""Return the site timezone from System Settings."""
	system_time_zone = frappe.db.get_system_setting("time_zone")
	if not system_time_zone:
		raise ValueError("Please configure a Time Zone under 'System Settings'.")
	return pytz.timezone(system_time_zone)


def localize_datetime(any_datetime: datetime_type) -> datetime_type:
	"""Return a timezone-aware datetime for a naive local datetime."""
	time_zone = get_system_timezone()
	if not isinstance(any_datetime, datetime_type):
		raise TypeError("Argument 'any_datetime' must be a Python datetime object.")

	if any_datetime.tzinfo:
		raise ValueError(
			f"Datetime value {any_datetime} is already localized and time zone aware (tzinfo={any_datetime.tzinfo})"
		)

	type_name = type(time_zone).__name__

	if type_name == "ZoneInfo":
		return any_datetime.replace(tzinfo=time_zone)

	return time_zone.localize(any_datetime)
