# Copyright (c) 2022-Present, Datahenge LLC and contributors
# For license information, please see license.txt

from mailchimp_transactional.api_client import ApiClientError

import frappe
from frappe.model.document import Document

from btu import print_both
from btu.manual_tests import send_hello_email_to_user
from btu.btu_api.scheduler import SchedulerAPI


class BTUConfiguration(Document):

	def validate(self):
		from pytz import timezone
		try:
			timezone(self.cron_time_zone)
		except Exception:
			link_text = '<a href="https://en.wikipedia.org/wiki/List_of_tz_database_time_zones" target="_blank"><u>this website.</u></a>'
			raise ValueError(f"Invalid name for Time Zone.  For a list of available names, visit {link_text}")  # pylint: disable=raise-missing-from

	@frappe.whitelist()
	def button_send_hello_email(self):
		"""
		Button for sending a short 'hello' email to the current session user.
		This demonstrates that BTU email is working.
		"""
		send_hello_email_to_user()

	@frappe.whitelist()
	def button_send_ping(self):
		"""
		Button sends a 'ping' to the BTU Scheduler daemon on its Unix Domain Socket.
		"""
		response = SchedulerAPI.send_ping()
		frappe.msgprint(f"Response from BTU Scheduler daemon:<br>{response}")

	@frappe.whitelist()
	def button_resubmit_all_task_schedules(self):
		"""
		Loop through all enabled Task Schedules, and ask the BTU Scheduler daemon to resubmit them for scheduling.
		NOTE: This does not immediately execute an RQ Job; only schedule it.
		"""
		from btu.btu_core.doctype.btu_task_schedule.btu_task_schedule import resubmit_all_task_schedules
		resubmit_all_task_schedules()

	@frappe.whitelist()
	def button_send_test_mandrill_email(self):
		"""
		Confirm configuration is working by sending an email to the current User.
		See also: https://mailchimp.com/developer/transactional/api/messages/send-new-message/
		"""
		from btu.btu_core.btu_email import new_mandrill_client, get_mandrill_response_status_overall, MandrillResponse

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
			"to": [
				{ "email": user_doc.email, "type": "to" }
			]
		}
		try:
			print_both(f"Attempting to send a test email via Mandrill to '{user_doc.email}'.")
			http_response = new_mandrill_client(self).messages.send({"message":message})
			response = get_mandrill_response_status_overall(http_response)
			if response == MandrillResponse.SUCCESS:
				message = f"Successfully sent a Mandrill Transactional Email to '{user_doc.email}'."
				print_both(message)
			else:
				raise IOError(response)
		except ApiClientError as error:
			message = f"An error occurred while sending email via Mandrill: {error.text}"
			print_both(message)
		except Exception as error:
			message = f"An error occurred while sending email via Mandrill: {repr(error)}"
			print_both(message)
