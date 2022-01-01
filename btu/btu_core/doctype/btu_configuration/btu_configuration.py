# Copyright (c) 2021, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from btu.manual_tests import send_hello_email_to_user
from btu.btu_api.scheduler import SchedulerAPI

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
		response = SchedulerAPI.send_ping()
		frappe.msgprint(f"Response from BTU Scheduler daemon: {response}")

	@frappe.whitelist()
	def button_resubmit_all_task_schedules(self):
		"""
		Loop through all enabled Task Schedules, and ask the BTU Scheduler daemon to resubmit them for scheduling.
		NOTE: This does not immediately execute an RQ Job; only schedule it.
		"""
		from btu.btu_core.doctype.btu_task_schedule.btu_task_schedule import resubmit_all_task_schedules
		resubmit_all_task_schedules()
