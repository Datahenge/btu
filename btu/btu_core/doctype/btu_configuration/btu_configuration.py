# Copyright (c) 2021, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from btu.manual_tests import send_hello_email_to_user
from btu.btu_api.scheduler import send_message_to_scheduler_socket

class BTUConfiguration(Document):

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
		response = send_message_to_scheduler_socket("ping", debug=True)
		frappe.msgprint(response)
