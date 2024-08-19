""" btu/btu_core/btu_email.py """

# Copyright (c) 2023-2024, Datahenge LLC and contributors
# For license information, please see license.txt

#
# Basic SMTP email functionality for BTU.
#

# pylint: disable=too-many-instance-attributes

# NOTE: The Python standard library already has a module named 'email'
#       So, I am deliberately naming this module "btu_email" to avoid namespace collision or mistakes.
# NOTE: To avoiding spam detection, when sending HTML, it's important to send both the plain text --and-- HTML parts.


# Standard Library
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import smtplib

# Frappe Library
import frappe
from frappe.utils.password import get_decrypted_password

# Mandrill App
from mailchimp.mailchimp_core.doctype.mailchimp_settings.mailchimp_settings import get_client, ApiClientError
from mailchimp.mailchimp_core import is_mandrill_response_okay

# BTU
from btu import dprint

DEBUG_ENV_VARIABLE="BTU_DEBUG"  # if this OS environment variable = 1, then dprint() messages will print to stdout.


class Emailer():
	"""
	Create and send emails without using standard DocTypes 'Email Domain' or 'Email Account'
	"""

	def __init__(self, subject, body, sender=None, emailto_list=None, ccto_list=None, bccto_list=None):
		"""
		Helper class to construct and send email messages from BTU.
		"""
		self.sender = sender
		self.emailto_list = emailto_list
		self.ccto_list = ccto_list
		self.bccto_list = bccto_list

		if not isinstance(subject, str):
			raise ValueError("Argument 'subject' should be a Python string type.")

		# Load the current BTU Configuration
		self.doc_btu_config = frappe.get_single("BTU Configuration")

		# Apply environment prefixes.
		self.subject = self._apply_subject_prefix(subject)
		self.body = self._apply_body_prefix(body)

		# Parse the target recipients into different objects
		self.parse_recipients()

	@staticmethod
	def _parse_recipients_into_list(recipients: object) -> list:
		"""
		Returns a list of recipients from an object of varying type.
		"""
		if not recipients:
			return []
		elif isinstance(recipients, str):
			return recipients.replace(',', ';').split(';')
		elif isinstance(recipients, list):
			return recipients
		else:
			raise TypeError(f"Argument 'recipients' has an unhandled data type '{type(recipients)}'")

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

	def parse_recipients(self):

		self.emailto_list = Emailer._parse_recipients_into_list(self.emailto_list)
		self.ccto_list    = Emailer._parse_recipients_into_list(self.ccto_list)
		self.bccto_list   = Emailer._parse_recipients_into_list(self.bccto_list)

		self.to_as_string = Emailer.recipients_to_csv_string(self.emailto_list)
		self.cc_as_string = Emailer.recipients_to_csv_string(self.ccto_list)
		self.bcc_as_string = Emailer.recipients_to_csv_string(self.bccto_list)

	@frappe.whitelist()
	def send(self):
		"""
		Send an email using BTU.
		"""
		if self.doc_btu_config.send_email_via == "SMTP":
			self._send_via_smtp()

		elif self.doc_btu_config.send_email_via == "Mandrill":
			self._send_via_mandrill()
		else:
			raise ValueError(f"Unexpected configuration value '{self.doc_btu_config.send_email_via}' in BTU Configuration.")

	def _send_via_smtp(self):
		"""
		Send the email using SMTP protocol and library.
		"""
		password = get_decrypted_password(doctype="BTU Configuration",
										  name="BTU Configuration",
										  fieldname="email_auth_password")

		if bool(self.doc_btu_config.email_body_is_html):
			# 1. Create a new MIMEMultipart object
			message = MIMEMultipart("alternative")
			message["Subject"] = self.subject
			message["From"] = self.sender if self.sender else self.doc_btu_config.email_auth_username
			# 2. Add various recipients as necessary:
			if self.to_as_string:
				message["To"] = self.to_as_string
			if self.cc_as_string:
				message["CC"] = self.cc_as_string
			if self.bcc_as_string:
				message["Bcc"] = self.bcc_as_string

			text_part = MIMEText(self.body, "plain")
			# 3. Create the HTML part of the message.
			html_body = self.body.replace('\n', '<br>')
			html_body = '<html> <head></head> <body>' + html_body + '</body></html>'
			html_part = MIMEText(html_body, "html")
			# 4. Attach the plain text and HTML parts.
			message.attach(text_part)
			message.attach(html_part)
			message = message.as_string()
		else:
			message = self._create_plaintext_message()

		with smtplib.SMTP(self.doc_btu_config.email_server, self.doc_btu_config.email_server_port) as smtp_server:

			if not smtp_server.ehlo()[0] == 250:
				raise ValueError("SMTP 'Hello' check failed.")

			# Use 'STARTTLS' if configured to do so:
			if self.doc_btu_config.email_encryption == 'STARTTLS':
				smtp_server.starttls() # Secure the connection

			smtp_server.login(user=self.doc_btu_config.email_auth_username,
							password=password)
			smtp_server.sendmail(from_addr=self.sender,
								 to_addrs=self.to_as_string.split(","),  # requires a Python List of Recipients
								 msg=message)

	def _send_via_mandrill(self):

		new_message = {
			"from_email": self.doc_btu_config.mandrill_from_email_address,
			"subject": self.subject,
			"to": [],
			'Reply-To': "technology@farmtopeople.com",  # TODO: This custom reply-to is not working.
		}

		# Loop through each Destination email address, and append to new_message.
		for each_email_address in self.emailto_list:
			new_message["to"].append({ "email": each_email_address, "type": "to" })

		# Loop through each CC email address, and append to new_message.
		for each_cc in self.ccto_list:
			if each_cc not in self.emailto_list:
				new_message["to"].append({ "email": each_cc, "type": "cc" })

		# Optional: Add BCC to the email, assuming the Recipient isn't the same value.
		for each_bcc in self.bccto_list:
			if each_bcc not in self.emailto_list:
				new_message['to'].append({ "email": each_bcc, "type": "bcc" })

		try:
			# ========
			# ERPNEXT TEMPLATE
			# ========
			if bool(self.doc_btu_config.email_body_is_html):
				html_body = self.body.replace('\n', '<br>')
				new_message["html"] = html_body
			else:
				new_message["text"] = MIMEText(self.body, "plain")

			response = get_client().messages.send({"message": new_message})

			if not is_mandrill_response_okay(response):
				frappe.msgprint(f"Error response from Mandrill API: {response}", to_console=True)
				raise ApiClientError(response, 500)

		except ApiClientError as error:
			print(f"An exception occurred in priv_send_mandrill_email(): {error.text}")
			print(f"Message sent to Mandrill:\n{json.dumps(new_message, indent=4)}")
			frappe.msgprint(f"Error while sending email via Mandrill: {error.text}")

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

	def _apply_subject_prefix(self, subject):
		"""
		Given an email subject, apply a Environment prefix (if applicable)
		"""
		return f"({self.doc_btu_config.environment_name}) {subject}" if self.doc_btu_config.environment_name else subject

	def _apply_body_prefix(self, body):
		"""
		Given an email body, apply an Environment prefix (if applicable)
		"""
		if not body:
			body = ""
		if self.doc_btu_config.environment_name:
			body = f"(sent from the ERPNext {self.doc_btu_config.environment_name} environment)\n\n" + body
		return body


# Non-Class Methods
def email_on_task_start(doc_task_log, send_via_queue=False):
	"""
	Sent immediately when a Task Log is first inserted into the database.
	"""
	from btu.btu_core.doctype.btu_task_log.btu_task_log import BTUTaskLog as BTUTaskLogType  # late import to avoid any circular reference problems.

	if not doc_task_log or not isinstance(doc_task_log, BTUTaskLogType):
		raise frappe.MandatoryError("Function requires argument 'doc_task_log', which should be an instance of BTU Task Log document.")

	if not doc_task_log.schedule:
		dprint("Warning: BTU Task Log does not reference a Task Schedule.  No email can be transmitted.")
		return  # only send emails for Tasks that were scheduled.

	doc_schedule = frappe.get_doc("BTU Task Schedule", doc_task_log.schedule)
	recipients = [ each for each in doc_schedule.email_recipients if each.email_on_start ]

	for each_recipient in recipients:
		subject = f"Started: BTU Task {doc_task_log.task_desc_short}"
		body = f"Task Schedule {doc_task_log.schedule}\nTask {doc_task_log.task} ({doc_task_log.task_desc_short}) is now In-Progress."
		sender = frappe.get_doc("BTU Configuration").email_auth_username

		dprint(f"Sending email to {each_recipient.email_address} because Task Schedule {doc_task_log.schedule} has started.")
		if not send_via_queue:
			Emailer(sender=sender,
					emailto_list=each_recipient.email_address or None,
					subject=subject,
					body=body).send()
		else:
			raise NotImplementedError("Not Yet Implemented: Sending email via Redis Queue.")

	dprint(f"Sent email message to Task Schedule's recipient {doc_schedule.email_recipients}", DEBUG_ENV_VARIABLE)


def email_on_task_conclusion(doc_task_log, send_via_queue=False):
	"""
	Send an email about the Task Log's success or failure.
	"""
	from btu.btu_core.doctype.btu_task_log.btu_task_log import BTUTaskLog as BTUTaskLogType  # late import to avoid any circular reference problems.

	if not doc_task_log or not isinstance(doc_task_log, BTUTaskLogType):
		raise frappe.MandatoryError("Function requires argument 'doc_task_log', which should be an instance of BTU Task Log document.")

	if not doc_task_log.schedule:
		dprint("Warning: BTU Task Log does not reference a Task Schedule.  No email can be transmitted.")
		return  # only send emails for Tasks that were scheduled.

	doc_schedule = frappe.get_doc("BTU Task Schedule", doc_task_log.schedule)
	for each_recipient in doc_schedule.email_recipients:

		if doc_task_log.success_fail == 'Success' and not each_recipient.email_on_success:
			continue
		if doc_task_log.success_fail == 'Failed' and not each_recipient.email_on_error:
			continue
		if doc_task_log.success_fail == 'Timeout' and not each_recipient.email_on_timeout:
			continue

		# Create the email "Subject" string:
		subject = f"{doc_task_log.success_fail}: BTU Task {doc_task_log.task_desc_short}"

		# Create a string that represents the "Body" of the email:
		body = f"Task {doc_task_log.task} : '{doc_task_log.task_desc_short}'\n"
		body += f"Outcome: {doc_task_log.success_fail}\n\n"
		if doc_task_log.result_message:
			body += f"Function returned this Result:\n'{doc_task_log.result_message}'\n\n"
		if doc_task_log.stdout:
			body += f"Standard Output:\n{doc_task_log.stdout}"
		if doc_task_log.success_fail == 'Timeout':
			body += "\nTimeout!\n"
			body += "Task has not returned results in a timely manner; it may have timed-out or died inside Python RQ."

		sender = frappe.get_doc("BTU Configuration").email_auth_username
		if not send_via_queue:
			Emailer(sender=sender,
					emailto_list=each_recipient.email_address or None,
					subject=subject,
					body=body).send()
		else:
			raise NotImplementedError("Not Yet Implemented: Sending email via Redis Queue.")

	dprint(f"Sent email message to Task Schedule's recipient {doc_schedule.email_recipients}", DEBUG_ENV_VARIABLE)
