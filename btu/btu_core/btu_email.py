"""SMTP and Mandrill email helpers for BTU."""

# Copyright (c) 2021-2025, Datahenge LLC and contributors
# For license information, please see license.txt

#
# Basic SMTP email functionality for BTU.
#

# pylint: disable=too-many-instance-attributes

# NOTE: The Python standard library already has a module named 'email'
#       So, I am deliberately naming this module "btu_email" to avoid namespace collision or mistakes.
# NOTE: To avoiding spam detection, when sending HTML, it's important to send both the plain text --and-- HTML parts.

# Standard Library
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import TYPE_CHECKING, Any

# Frappe Library
import frappe

# Third Party
import mailchimp_transactional as MailchimpTransactional  # This is the official Python SDK for Mandrill
from frappe.model.document import Document
from frappe.utils.password import get_decrypted_password

# BTU
from btu import print_both

if TYPE_CHECKING:
	from btu.btu_core.doctype.btu_task_log.btu_task_log import BTUTaskLog


def new_mandrill_client(doc_configuration: Document | None = None) -> MailchimpTransactional.Client:
	"""Create a new, authenticated Mandrill client."""
	if not doc_configuration:
		doc_configuration = frappe.get_doc("BTU Configuration")  # singles DocType
	api_key = doc_configuration.get_password(fieldname="mandrill_api_key")
	return MailchimpTransactional.Client(api_key)


class MandrillResponse(Enum):
	"""Overall status of a Mandrill API send response."""

	SUCCESS = 1
	REJECTED = 2
	UNHANDLED_ERROR = 3


def get_mandrill_response_status_overall(mandrill_response: list[dict[str, Any]]) -> MandrillResponse:
	"""Interpret Mandrill API send response status from a list of per-recipient dicts."""
	# Look for bad 'status' or any kind of rejection reason.
	try:
		for each_dict in mandrill_response:
			if each_dict.get("status", None) != "sent":
				return MandrillResponse.REJECTED
	except Exception as ex:
		frappe.logger("btu").warning("Unhandled exception in get_mandrill_response_status_overall(): %s", ex)
		return MandrillResponse.UNHANDLED_ERROR
	return MandrillResponse.SUCCESS


class Emailer:
	"""Create and send emails without using standard DocTypes 'Email Domain' or 'Email Account'."""

	def __init__(
		self,
		subject: str,
		body: str,
		sender: str | None = None,
		emailto_list: str | list[str] | set[str] | None = None,
		ccto_list: str | list[str] | set[str] | None = None,
		bccto_list: str | list[str] | set[str] | None = None,
	) -> None:
		"""Construct an email message from BTU configuration and recipient lists."""
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
	def _parse_recipients_into_list(recipients: object) -> list[str] | set[str]:
		"""Return a recipient list from a string, list, set, or empty value."""
		if not recipients:
			return []
		if isinstance(recipients, str):
			temp = recipients.replace(",", ";").split(";")
			return {each.strip() for each in temp}
		if isinstance(recipients, list):
			return recipients
		raise TypeError(f"Argument 'recipients' has an unhandled data type '{type(recipients)}'")

	@staticmethod
	def recipients_to_csv_string(recipients: str | list[str] | set[str] | None) -> str | None:
		"""Return a comma-separated recipient string from a string, list, or set."""
		if not recipients:
			return None
		if isinstance(recipients, (list, set)):
			return ", ".join(recipients)
		if isinstance(recipients, str):
			return recipients
		raise TypeError(f"Argument 'recipients' is a Python type {type(recipients)} with value {recipients}")

	def parse_recipients(self) -> None:
		"""Normalize recipient fields into lists and CSV header strings."""
		self.emailto_list = Emailer._parse_recipients_into_list(self.emailto_list)
		self.ccto_list = Emailer._parse_recipients_into_list(self.ccto_list)
		self.bccto_list = Emailer._parse_recipients_into_list(self.bccto_list)

		self.to_as_string = Emailer.recipients_to_csv_string(self.emailto_list)
		self.cc_as_string = Emailer.recipients_to_csv_string(self.ccto_list)
		self.bcc_as_string = Emailer.recipients_to_csv_string(self.bccto_list)

	@frappe.whitelist()
	def send(self) -> None:
		"""Send an email using BTU."""
		if self.doc_btu_config.send_email_via == "SMTP":
			self._send_via_smtp()

		elif self.doc_btu_config.send_email_via == "Mandrill":
			self._send_via_mandrill()
		else:
			raise ValueError(
				f"Unexpected configuration value '{self.doc_btu_config.send_email_via}' in BTU Configuration."
			)

	def _send_via_smtp(self) -> None:
		"""Send the email using SMTP protocol and library."""
		password = get_decrypted_password(
			doctype="BTU Configuration", name="BTU Configuration", fieldname="email_auth_password"
		)

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
			html_body = self.body.replace("\n", "<br>")
			html_body = "<html> <head></head> <body>" + html_body + "</body></html>"
			html_part = MIMEText(html_body, "html")
			# 4. Attach the plain text and HTML parts.
			message.attach(text_part)
			message.attach(html_part)
			message = message.as_string()
		else:
			message = self._create_plaintext_message()

		with smtplib.SMTP(
			self.doc_btu_config.email_server, self.doc_btu_config.email_server_port
		) as smtp_server:
			if not smtp_server.ehlo()[0] == 250:
				raise ValueError("SMTP 'Hello' check failed.")

			# Use 'STARTTLS' if configured to do so:
			if self.doc_btu_config.email_encryption == "STARTTLS":
				smtp_server.starttls()  # Secure the connection

			smtp_server.login(user=self.doc_btu_config.email_auth_username, password=password)
			smtp_server.sendmail(
				from_addr=self.sender,
				to_addrs=self.to_as_string.split(","),  # requires a Python List of Recipients
				msg=message,
			)

	def _send_via_mandrill(self) -> None:
		new_message = {
			"from_email": self.doc_btu_config.mandrill_from_email_address,
			"subject": self.subject,
			"to": [],
			"Reply-To": "",  # TODO: This custom reply-to is not working.
		}

		# Loop through each Destination email address, and append to new_message.
		for each_email_address in self.emailto_list:
			new_message["to"].append({"email": each_email_address, "type": "to"})

		# Loop through each CC email address, and append to new_message.
		for each_cc in self.ccto_list:
			if each_cc not in self.emailto_list:
				new_message["to"].append({"email": each_cc, "type": "cc"})

		# Optional: Add BCC to the email, assuming the Recipient isn't the same value.
		for each_bcc in self.bccto_list:
			if each_bcc not in self.emailto_list:
				new_message["to"].append({"email": each_bcc, "type": "bcc"})

		try:
			# ========
			# ERPNEXT TEMPLATE
			# ========
			if bool(self.doc_btu_config.email_body_is_html):
				html_body = self.body.replace("\n", "<br>")
				new_message["html"] = html_body
			else:
				new_message["text"] = MIMEText(self.body, "plain")

			response = new_mandrill_client().messages.send({"message": new_message})

			if get_mandrill_response_status_overall(response) == MandrillResponse.UNHANDLED_ERROR:
				print_both(f"Unhandled error response from Mandrill API: {response}")
				raise OSError(response)

		except OSError as ex:
			if isinstance(ex, list):
				error_string = json.dumps(ex)
			else:
				error_string = str(ex)
			print_both(f"Error while sending email via Mandrill: {error_string}")
			frappe.logger("btu").debug("Message sent to Mandrill:\n%s", json.dumps(new_message, indent=4))
			frappe.msgprint(f"Error while sending email via Mandrill: {error_string}")

	def _create_plaintext_message(self) -> str:
		"""Build a plain-text email message with RFC-style headers."""
		header = f"From: {self.sender}\n"
		header += f"To: {self.to_as_string}\n"
		if self.cc_as_string:
			header += f"CC: {self.cc_as_string}\n"
		if self.bcc_as_string:
			header += f"CC: {self.bcc_as_string}\n"
		header += f"Subject: {self.subject}\n\n"
		return header + self.body

	def _apply_subject_prefix(self, subject: str) -> str:
		"""Apply an environment prefix to the email subject when configured."""
		return (
			f"({self.doc_btu_config.environment_name}) {subject}"
			if self.doc_btu_config.environment_name
			else subject
		)

	def _apply_body_prefix(self, body: str) -> str:
		"""Apply an environment prefix to the email body when configured."""
		if not body:
			body = ""
		if self.doc_btu_config.environment_name:
			body = f"(sent from the ERPNext {self.doc_btu_config.environment_name} environment)\n\n" + body
		return body


def _build_recipients_from_task_log(doc_task_log: "BTUTaskLog") -> dict[str, dict[str, int]]:
	"""Build email recipient options from a BTU Task Log and its related Task or Schedule."""
	from btu.btu_core.doctype.btu_task_log.btu_task_log import (
		BTUTaskLog as BTUTaskLogType,  # late import to avoid any circular reference problems.
	)

	if not doc_task_log or not isinstance(doc_task_log, BTUTaskLogType):
		raise frappe.MandatoryError(
			"Function requires argument 'doc_task_log', which should be an instance of 'BTU Task Log' document."
		)

	result: dict[str, dict[str, int]] = {}
	doc_task = frappe.get_doc("BTU Task", doc_task_log.task)
	for each_recipient in doc_task.email_recipients:
		result[each_recipient.email_address] = {
			"email_on_start": each_recipient.email_on_start,
			"email_on_success": each_recipient.email_on_success,
			"email_on_error": each_recipient.email_on_error,
			"email_on_timeout": each_recipient.email_on_timeout,
		}

	if doc_task_log.schedule:
		doc_schedule = frappe.get_doc("BTU Task Schedule", doc_task_log.schedule)
		for each_recipient in doc_schedule.email_recipients:
			# Add new key to dictionary:
			if not result.get(each_recipient.email_address):
				result[each_recipient.email_address] = {
					"email_on_start": each_recipient.email_on_start,
					"email_on_success": each_recipient.email_on_success,
					"email_on_error": each_recipient.email_on_error,
					"email_on_timeout": each_recipient.email_on_timeout,
				}
			else:
				# Apply "OR" logic to each selection:
				result[each_recipient.email_address]["email_on_start"] = (
					result[each_recipient.email_address]["email_on_start"] or each_recipient.email_on_start
				)
				result[each_recipient.email_address]["email_on_success"] = (
					result[each_recipient.email_address]["email_on_success"]
					or each_recipient.email_on_success
				)
				result[each_recipient.email_address]["email_on_error"] = (
					result[each_recipient.email_address]["email_on_error"] or each_recipient.email_on_error
				)
				result[each_recipient.email_address]["email_on_timeout"] = (
					result[each_recipient.email_address]["email_on_timeout"]
					or each_recipient.email_on_timeout
				)

	return result


# Non-Class Methods
def email_on_task_start(doc_task_log: "BTUTaskLog", send_via_queue: bool = False) -> None:
	"""Send email when a Task Log is first inserted into the database."""
	from btu.btu_core.doctype.btu_task_log.btu_task_log import (
		BTUTaskLog as BTUTaskLogType,  # late import to avoid any circular reference problems.
	)

	if not doc_task_log or not isinstance(doc_task_log, BTUTaskLogType):
		raise frappe.MandatoryError(
			"Function requires argument 'doc_task_log', which should be an instance of BTU Task Log document."
		)

	# Add emails associated with the Task:
	recipients: dict[str, dict[str, int]] = _build_recipients_from_task_log(doc_task_log)
	recipients = {
		key: value for key, value in recipients.items() if value["email_on_start"]
	}  # reduce to recipients who opted-in 'Email on Start'

	subject = f"Started: BTU Task {doc_task_log.task_desc_short}"
	body = f"Task {doc_task_log.task} ({doc_task_log.task_desc_short}) is now In-Progress."
	sender = frappe.get_doc("BTU Configuration").email_auth_username

	# If Optionally, add emails associated with the Task Schedule:
	if doc_task_log.schedule:
		body += f"\nTask Schedule {doc_task_log.schedule}"

	for each_recipient in recipients:  # Value of 'each_recipient' is a String email address
		frappe.logger("btu").debug(
			"Sending email to %s because Task %s has started.", each_recipient, doc_task_log.task
		)
		if not send_via_queue:
			Emailer(sender=sender, emailto_list=each_recipient or None, subject=subject, body=body).send()
		else:
			raise NotImplementedError("Not Yet Implemented: Sending email via Redis Queue.")

	frappe.logger("btu").debug("Sent email message to recipients: %s", recipients)


def email_on_task_conclusion(doc_task_log: "BTUTaskLog", send_via_queue: bool = False) -> None:
	"""Send an email about the Task Log's success or failure."""
	from btu.btu_core.doctype.btu_task_log.btu_task_log import (
		BTUTaskLog as BTUTaskLogType,  # late import to avoid any circular reference problems.
	)

	if not doc_task_log or not isinstance(doc_task_log, BTUTaskLogType):
		raise frappe.MandatoryError(
			"Function requires argument 'doc_task_log', which should be an instance of BTU Task Log document."
		)

	email_recipients: dict[str, dict[str, int]] = _build_recipients_from_task_log(doc_task_log)
	for each_recipient, options in email_recipients.items():
		if doc_task_log.success_fail == "Success" and not options["email_on_success"]:
			continue
		if doc_task_log.success_fail == "Failed" and not options["email_on_error"]:
			continue
		if doc_task_log.success_fail == "Timeout" and not options["email_on_timeout"]:
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
		if doc_task_log.success_fail == "Timeout":
			body += "\nTimeout!\n"
			body += "Task has not returned results in a timely manner; it may have timed-out or died inside Python RQ."

		sender = frappe.get_doc("BTU Configuration").email_auth_username
		if not send_via_queue:
			Emailer(sender=sender, emailto_list=each_recipient or None, subject=subject, body=body).send()
		else:
			raise NotImplementedError("Not Yet Implemented: Sending email via Redis Queue.")

	frappe.logger("btu").debug("Sent email message to recipients: %s", list(email_recipients))
