"""BTU Configuration DocType controller."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from mailchimp_transactional.api_client import ApiClientError

from btu import print_both
from btu.btu_api.scheduler import SchedulerAPI
from btu.btu_core.btu_email import send_hello_email_to_current_user
from btu.btu_core.form_options import validate_rq_queue_name


class BTUConfiguration(Document):
	"""Site-wide BTU settings including email and scheduler configuration."""

	def validate(self) -> None:
		"""Ensure email settings are complete for the selected delivery method."""
		if self.send_email_via == "Email Account" and not self.default_email_account:
			frappe.throw(_("Default Email Account is required when sending via Email Account."))
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
	def button_reload_timezone_cache(self) -> None:
		"""Rebuild the Redis IANA timezone cache from the OS zoneinfo database."""
		from btu.btu_core.form_options import reload_timezone_cache

		message = reload_timezone_cache()
		frappe.msgprint(message)

	@frappe.whitelist()
	def button_send_test_mandrill_email(self) -> None:
		"""Send a test Mandrill transactional email to the current user."""
		from btu.btu_core.btu_email import (
			MandrillResponse,
			get_mandrill_response_status_overall,
			new_mandrill_client,
		)

		subject = "Hello from ERPNext + Mailchimp Transactional"
		# Prefix the Subject with an environment name, if configured to do so
		environment_name = frappe.db.get_single_value("BTU Configuration", "environment_name")
		if environment_name:
			subject = f"{environment_name}: {subject}"

		user_doc = frappe.get_doc("User", frappe.session.user)

		message = {
			"from_email": self.mandrill_from_email_address,
			"subject": subject,
			"html": """<ul><li>Name of this function: 'send_test_email'</li>
			<li>Path to this function: 'btu.btu_core.doctype.btu_configuration.btu_configuration, BTUConfiguration.button_send_test_mandrill_email()'</li>
			<li>By reading this email, you can be confident that ERPNext is successfully authenticating and communicating with Mailchimp Transactional (Mandrill) email.</li>
			</ul>""",
			"to": [{"email": user_doc.email, "type": "to"}],
		}
		try:
			print_both(f"Attempting to send a test email via Mandrill to '{user_doc.email}'.")
			http_response = new_mandrill_client(self).messages.send({"message": message})
			response = get_mandrill_response_status_overall(http_response)
			if response == MandrillResponse.SUCCESS:
				message = f"Successfully sent a Mandrill Transactional Email to '{user_doc.email}'."
				print_both(message)
			else:
				raise OSError(response)
		except ApiClientError as error:
			message = f"An error occurred while sending email via Mandrill: {error.text}"
			print_both(message)
		except Exception as error:
			message = f"An error occurred while sending email via Mandrill: {error!r}"
			print_both(message)
