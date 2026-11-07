"""BTU Configuration DocType controller."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document
from btu import print_both
from btu.btu_api.scheduler import SchedulerAPI
from btu.btu_core.btu_email import send_hello_email_to_current_user
from btu.btu_core.form_options import validate_rq_queue_name
from btu.diagnostics.task_runner import PING_WITH_WAIT_PATH

PING_TASK_WAIT_SECONDS = 10


class BTUConfiguration(Document):
	"""Site-wide BTU settings including email and scheduler configuration."""

	def validate(self) -> None:
		"""Warn, without blocking, when no Default Email Account is configured."""
		if not self.default_email_account:
			frappe.msgprint(
				_("No Default Email Account is set, so BTU will not send its notification emails."),
				title=_("Email Not Configured"),
				indicator="orange",
			)
		validate_rq_queue_name(self.queue_name)

	@frappe.whitelist()
	def button_send_hello_email(self) -> None:
		"""Send a short hello email to the current session user."""
		send_hello_email_to_current_user()

	@frappe.whitelist()
	def button_send_ping(self) -> None:
		"""Send a ping to the BTU Scheduler daemon via Redis RPC."""
		response = SchedulerAPI.send_ping()
		frappe.msgprint(f"Response from BTU Scheduler daemon:<br>{response}")

	@frappe.whitelist()
	def button_resubmit_all_task_schedules(self) -> None:
		"""Resubmit all enabled Task Schedules to the BTU Scheduler daemon."""
		from btu.btu_core.doctype.btu_task_schedule.btu_task_schedule import resubmit_all_task_schedules

		resubmit_all_task_schedules()

	@frappe.whitelist()
	def button_create_ping_task(self) -> str:
		"""Create and submit a BTU Task that runs ``ping_with_wait`` with a 10-second wait."""
		task = frappe.get_doc(
			{
				"doctype": "BTU Task",
				"desc_short": _("Ping with wait (10 seconds)"),
				"function_string": PING_WITH_WAIT_PATH,
				"arguments": json.dumps({"seconds_to_wait": PING_TASK_WAIT_SECONDS}),
				"task_type": "Persistent",
				"queue_name": self.queue_name or "default",
			}
		)
		task.insert()  # the BTU Task naming series sets the name
		task.submit()
		frappe.msgprint(_("Created BTU Task {0}.").format(frappe.utils.get_link_to_form("BTU Task", task.name)))
		return task.name

	@frappe.whitelist()
	def button_reload_timezone_cache(self) -> None:
		"""Rebuild the Redis IANA timezone cache from the OS zoneinfo database."""
		from btu.btu_core.form_options import reload_timezone_cache

		message = reload_timezone_cache()
		frappe.msgprint(message)

