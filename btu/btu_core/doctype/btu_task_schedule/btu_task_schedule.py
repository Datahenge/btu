"""BTU Task Schedule DocType controller."""

# Copyright (c) 2015, Codrotech Inc. and contributors
#
# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

import ast
from datetime import datetime as datetime_type
from typing import Any

# Third Party
import cron_descriptor

# Frappe
import frappe
from frappe import _
from frappe.model.document import Document

# BTU
from btu import Result, print_both, validate_cron_string
from btu.btu_api.scheduler import SchedulerAPI
from btu.btu_core.form_options import validate_cron_timezone, validate_rq_queue_name
from btu.utils.datetime import get_system_timezone


class BTUTaskSchedule(Document):  # pylint: disable=too-many-instance-attributes
	"""Cron-based schedule binding a BTU Task to a recurring execution plan."""

	def after_insert(self) -> None:
		"""Inherit email recipients from the parent BTU Task on creation."""
		task_doc = self.get_task_doc()
		if not task_doc.email_recipients:
			return
		for row in task_doc.email_recipients:
			self.append("email_recipients", {
				"email_address": row.email_address,
				"email_on_start": row.email_on_start,
				"email_on_success": row.email_on_success,
				"email_on_error": row.email_on_error,
				"email_on_timeout": row.email_on_timeout,
			})
		self.save()

	def on_trash(self) -> None:
		"""Cancel scheduler state after this Task Schedule is deleted."""
		try:
			self.cancel_schedule(quiet=True, warn_only=True)
		except Exception as ex:
			frappe.log_error(title="BTU Task Schedule cancel on trash", message=str(ex))

	def before_validate(self) -> None:
		"""Normalize schedule fields before validation."""
		self.task_description = self.get_task_doc().desc_short
		if not self.cron_timezone:
			self.cron_timezone = frappe.db.get_system_setting("time_zone")

	def validate(self) -> None:
		"""Validate the cron string and derive its human-readable description."""
		validate_rq_queue_name(self.queue_name)
		validate_cron_timezone(self.cron_timezone)
		validate_cron_string(str(self.cron_string))
		self.schedule_description = cron_descriptor.get_description(self.cron_string)

	def before_save(self) -> None:
		"""Reject invalid primary keys before save."""
		if "|" in self.name:
			raise ValueError("Task Schedules cannot have the pipe character (|) in their primary key 'name'.")

	def on_update(self) -> None:
		"""Sync enabled schedules with the BTU Scheduler daemon after save."""
		self._sync_with_scheduler()

	def _sync_with_scheduler(self) -> None:
		"""Push schedule changes to the daemon without blocking document save."""
		doc_before = self.get_doc_before_save()
		if bool(self.enabled):
			self.resubmit_task_schedule(warn_only=True)
		elif doc_before and doc_before.enabled:
			self.cancel_schedule(quiet=True, warn_only=True)

	def resubmit_task_schedule(self, autosave: bool = False, warn_only: bool = False) -> None:
		"""Ask the BTU Scheduler daemon to reload this Task Schedule."""
		try:
			self.cancel_schedule(quiet=True, warn_only=True)
		except Exception as ex:
			if not warn_only:
				frappe.msgprint(_("Error while attempting to cancel Task Schedule {0}").format(self.name))
			print(ex)

		response = SchedulerAPI.reload_task_schedule(task_schedule_id=self.name)
		if not response:
			message = _(
				"No response from BTU Task Scheduler daemon. The schedule was saved locally, but the daemon may be offline. Check BTU Scheduler logs."
			)
			if warn_only:
				frappe.msgprint(message, indicator="orange", title=_("Scheduler unavailable"))
				return
			raise ConnectionError(message)
		scheduler_message = response.get("message", str(response))
		print(f"Response from BTU Scheduler: {scheduler_message}")
		if not warn_only:
			frappe.msgprint(_("Response from BTU Scheduler daemon:<br>{0}").format(scheduler_message))
		if autosave:
			self.save()

	def cancel_schedule(self, quiet: bool = False, warn_only: bool = False) -> dict[str, Any] | None:
		"""Ask the BTU Scheduler daemon to cancel this Task Schedule."""
		response = SchedulerAPI.cancel_task_schedule(task_schedule_id=self.name)
		if not response:
			message = _("No response from BTU Scheduler daemon.")
			if warn_only:
				if not quiet:
					frappe.msgprint(message, indicator="orange", title=_("Scheduler unavailable"))
				return None
			ack = message
		else:
			ack = response.get("message", str(response))
		if not quiet:
			frappe.msgprint(
				_("Request = Cancel Task Schedule.<br>Response from BTU Scheduler: {0}").format(ack)
			)
		print(f"Request = Cancel Task Schedule.\nResponse from BTU Scheduler: {ack}")
		return response

	def get_task_doc(self) -> Document:
		"""Return the linked BTU Task document."""
		return frappe.get_doc("BTU Task", self.task)

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
