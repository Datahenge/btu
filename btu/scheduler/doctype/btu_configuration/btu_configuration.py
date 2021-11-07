# Copyright (c) 2021, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from btu.manual_tests import send_hello_email_to_user


class BTUConfiguration(Document):

	@frappe.whitelist()
	def button_send_hello_email(self):
		"""
		Button for triggerering a short 'hello' email to the current session user.
		"""
		send_hello_email_to_user()
