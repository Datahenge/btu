""" btu/btu_api/btu_email.py """

# Copyright (c) 2021, Datahenge LLC and contributors
# For license information, please see license.txt

#
# Basic SMTP email functionality for BTU.
#

# NOTE: The Python standard library already has a module named 'email'
#       So, I am deliberately naming this module "btu_email" to avoid namespace collision or mistakes.

# Standard Library
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

import frappe
from frappe.utils.password import get_decrypted_password


class Emailer():
	"""
	Create and send emails without using standard DocTypes 'Email Domain' or 'Email Account'
	"""

	def __init__(self, sender, subject, body, emailto_list=None, ccto_list=None, bccto_list=None):
		"""
		Helper class to construct and send email messages from BTU.
		"""
		self.sender = sender
		self.to_as_string = Emailer.recipients_to_csv_string(emailto_list)
		self.cc_as_string = Emailer.recipients_to_csv_string(ccto_list)
		self.bcc_as_string = Emailer.recipients_to_csv_string(bccto_list)
		if not isinstance(subject, str):
			raise Exception("Argument 'subject' should be a Python string type.")
		# Apply environment prefixes.
		self._set_environment_name()
		self.subject = self._apply_subject_prefix(subject)
		self.body = self._apply_body_prefix(body)

	@staticmethod
	def recipients_to_csv_string(recipients):
		"""
		Given a variable of unknown type, try to return a comma-separated set of recipients.
		"""
		if not recipients:
			return None
		if isinstance(recipients, list):
			return ", ".join(recipients)
		if isinstance(recipients, str):
			return recipients
		raise TypeError(recipients)



	@frappe.whitelist()
	def send(self):

		btu_config = frappe.get_single("BTU Configuration")
		use_html = bool(btu_config.email_body_is_html)
		password = get_decrypted_password(doctype="BTU Configuration",
										  name="BTU Configuration",
										  fieldname="email_auth_password")

		if use_html:
			# 1. Replace newlines with breaks:
			self.body = self.body.replace('\n', '<br>')
			# 2. Create MIMEMultipart object
			message = MIMEMultipart("alternative")
			message["Subject"] = self.subject
			message["From"] = self.sender

			# Add various recipients as necessary:
			if self.to_as_string:
				message["To"] = self.to_as_string
			if self.cc_as_string:
				message["CC"] = self.cc_as_string
			if self.bcc_as_string:
				message["Bcc"] = self.bcc_as_string

			part = MIMEText(self.body, "html")
			message.attach(part)
			message = message.as_string()
		else:
			message = self._create_plaintext_message()

		with smtplib.SMTP(btu_config.email_server, btu_config.email_server_port) as smtp_server:

			if not smtp_server.ehlo()[0] == 250:
				raise ValueError("SMTP 'Hello' check failed.")

			# Use 'STARTTLS' if configured to do so:
			if btu_config.email_encryption == 'STARTTLS':
				smtp_server.starttls() # Secure the connection

			smtp_server.login(user=btu_config.email_auth_username,
							password=password)
			smtp_server.sendmail(from_addr=self.sender,
								 to_addrs=self.to_as_string.split(","),  # requires a Python List of Recipients
								 msg=message)

	def _create_plaintext_message(self):
		"""
		A plain text message requires a different type of header object.
		"""
		header = f"From: {self.sender}\n"
		header += f"To: {self.to_as_string}\n"
		if self.cc_as_string:
			header += f"CC: {self.cc_as_string}\n"
		if self.bcc_as_string:
			header += f"CC: {self.bcc_as_string}\n"
		header += f"Subject: {self.subject}\n\n"
		return header + self.body

	def _set_environment_name(self):
		"""
		Returns the current environment name from the BTU Configuration document.
		"""
		self.environment_name = frappe.db.get_single_value("BTU Configuration", "environment_name")
		return self.environment_name

	def _apply_subject_prefix(self, subject):
		"""
		Given an email subject, apply a prefix (if applicable)
		"""
		if not self.environment_name:
			return subject
		return f"({self.environment_name}) {subject}"

	def _apply_body_prefix(self, body):
		"""
		Given an email subject, apply a prefix (if applicable)
		"""
		if not self.environment_name:
			return body
		return f"(sent from the ERPNext {self.environment_name} environment)\n\n" + body


def email_task_log_summary(doc_task_log, send_via_queue=False, debug=True):
	"""
	Send an email about the Task's success or failure.
	"""
	if not doc_task_log.schedule:
		if debug:
			print("Warning: BTU Task Log does not reference a Task Schedule.  No email can be transmitted.")
		return  # only send emails for Tasks that were scheduled.

	doc_schedule = frappe.get_doc("BTU Task Schedule", doc_task_log.schedule)
	if not doc_schedule.email_recipients:
		if debug:
			print("BTU Task Schedule has no email recipients.")
		return  # no email recipients defined

	recipient_list = [ row.email_address for row in doc_schedule.email_recipients if row.recipient_type == 'TO' ]
	cc_list = [ row.email_address for row in doc_schedule.email_recipients if row.recipient_type == 'CC' ]
	bcc_list = [ row.email_address for row in doc_schedule.email_recipients if row.recipient_type == 'BCC' ]

	# Create the email "Subject" string:
	if doc_task_log.success_fail == 'Success':
		subject = f"Success: BTU Task {doc_task_log.task}"
	else:
		subject = f"Failure: BTU Task {doc_task_log.task}"

	# Create the email "Body" string:
	body = f"Task Description: '{doc_task_log.task_desc_short}'\n\n"
	if doc_task_log.result_message:
		body += f"Function returned this Result:\n'{doc_task_log.result_message}'\n\n"
	if doc_task_log.stdout:
		body += f"Standard Output:\n{doc_task_log.stdout}"

	sender = frappe.get_doc("BTU Configuration").email_auth_username
	if not send_via_queue:
		Emailer(sender=sender,
				emailto_list=recipient_list or None,
				ccto_list=cc_list or None,
				bccto_list=bcc_list or None,
				subject=subject,
				body=body).send()
	else:
		raise Exception("Sending email via Redis Queue is not-yet-implemented")

	if debug:
		print("Sent email message to Task Schedule's recipients.")

	# pylint: disable=pointless-string-statement
	"""
	email_args = {
		"recipients": ";".join(recipient_list) if recipient_list else None,
		"cc": ";".join(cc_list) if cc_list else None,
		"bcc": ";".join(bcc_list) if bcc_list else None,
		"sender": "technology@farmtopeople.com",
		"subject": subject,
		"message": self.result_message + self.stdout,
		"now": True,
		"attachments": None
	}
	# frappe.enqueue(method=frappe.sendmail, queue='short', timeout=300, is_async=True, **email_args)
	"""
