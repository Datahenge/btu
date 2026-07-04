"""Email helpers for BTU task notifications and configuration tests."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

#
# NOTE: The Python standard library already has a module named 'email'
#       So, I am deliberately naming this module "btu_email" to avoid namespace collision or mistakes.
# NOTE: To avoiding spam detection, when sending HTML, it's important to send both the plain text --and-- HTML parts.

# Standard Library
import json
from enum import Enum
from typing import TYPE_CHECKING, Any

# Frappe Library
import frappe

# Third Party
import mailchimp_transactional as MailchimpTransactional  # This is the official Python SDK for Mandrill
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr

# BTU
from btu import print_both

if TYPE_CHECKING:
	from btu.btu_core.doctype.btu_task_log.btu_task_log import BTUTaskLog


class BTUEmailSendError(Exception):
	"""Raised when BTU cannot send a notification email."""


def _raise_btu_email_send_error(
	delivery_method: str,
	exc: Exception,
	account_name: str | None = None,
) -> None:
	"""Log a concise email failure and raise BTUEmailSendError."""
	if isinstance(exc, BTUEmailSendError):
		raise exc

	detail = cstr(exc).strip() or exc.__class__.__name__
	if account_name:
		message = f"BTU failed to send email via {delivery_method} (Email Account '{account_name}'): {detail}"
	else:
		message = f"BTU failed to send email via {delivery_method}: {detail}"

	frappe.logger("btu").error(message)
	print_both(message)
	raise BTUEmailSendError(message) from exc


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


def get_default_sender() -> str | None:
	"""Return the configured default sender address for BTU notification emails."""
	config = frappe.get_single("BTU Configuration")
	if config.send_email_via == "Email Account" and config.default_email_account:
		return frappe.db.get_value("Email Account", config.default_email_account, "email_id")
	if config.send_email_via == "Mandrill":
		return config.mandrill_from_email_address
	return None


class Emailer:
	"""Create and send emails using Frappe Email Account or Mandrill."""

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
		if self.doc_btu_config.send_email_via == "Email Account":
			self._send_via_email_account()

		elif self.doc_btu_config.send_email_via == "Mandrill":
			self._send_via_mandrill()
		else:
			raise ValueError(
				f"Unexpected configuration value '{self.doc_btu_config.send_email_via}' in BTU Configuration."
			)

	def _send_via_email_account(self) -> None:
		"""Send the email using a linked Frappe Email Account."""
		account_name = self.doc_btu_config.default_email_account
		if not account_name:
			raise BTUEmailSendError(_("BTU Configuration requires a Default Email Account."))

		email_account = frappe.get_doc("Email Account", account_name)
		if not email_account.enable_outgoing:
			raise BTUEmailSendError(
				_("Email Account {0} does not have outgoing email enabled.").format(account_name)
			)

		recipients = list(self.emailto_list)
		if not recipients:
			raise ValueError("At least one recipient is required to send email.")

		message = self.body
		if self.doc_btu_config.email_body_is_html:
			html_body = self.body.replace("\n", "<br>")
			message = f"<html><body>{html_body}</body></html>"

		try:
			frappe.sendmail(
				recipients=recipients,
				sender=self.sender or email_account.email_id,
				subject=self.subject,
				message=message,
				cc=list(self.ccto_list) or None,
				bcc=list(self.bccto_list) or None,
				delayed=False,
				now=True,
				reference_doctype="BTU Configuration",
				reference_name="BTU Configuration",
			)
		except BTUEmailSendError:
			raise
		except Exception as exc:
			_raise_btu_email_send_error("Email Account", exc, account_name=account_name)

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
				new_message["text"] = self.body

			response = new_mandrill_client().messages.send({"message": new_message})

			if get_mandrill_response_status_overall(response) == MandrillResponse.UNHANDLED_ERROR:
				print_both(f"Unhandled error response from Mandrill API: {response}")
				raise OSError(response)

		except BTUEmailSendError:
			raise
		except Exception as ex:
			frappe.logger("btu").debug("Message sent to Mandrill:\n%s", json.dumps(new_message, indent=4))
			_raise_btu_email_send_error("Mandrill", ex)

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

	# If Optionally, add emails associated with the Task Schedule:
	if doc_task_log.schedule:
		body += f"\nTask Schedule {doc_task_log.schedule}"

	for each_recipient in recipients:  # Value of 'each_recipient' is a String email address
		frappe.logger("btu").debug(
			"Sending email to %s because Task %s has started.", each_recipient, doc_task_log.task
		)
		if not send_via_queue:
			Emailer(sender=get_default_sender(), emailto_list=each_recipient or None, subject=subject, body=body).send()
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

		if not send_via_queue:
			Emailer(
				sender=get_default_sender(), emailto_list=each_recipient or None, subject=subject, body=body
			).send()
		else:
			raise NotImplementedError("Not Yet Implemented: Sending email via Redis Queue.")

	frappe.logger("btu").debug("Sent email message to recipients: %s", list(email_recipients))


@frappe.whitelist()
def send_hello_email_to_current_user(debug: bool = False) -> str:
	"""Send a short test email to the current session user (BTU Configuration smoke test)."""
	import datetime
	import inspect

	caller_name = inspect.stack()[2][3]
	if caller_name in ("execute_cmd", "<lambda>"):
		caller_name = "JavaScript on a web page."

	user_doc = frappe.get_doc("User", frappe.session.user)
	if not user_doc.email:
		frappe.throw(
			f"Current user '{user_doc.name}' does not have an Email Address associated with their account."
		)

	datetime_now_string = datetime.datetime.now().strftime("%A, %B %d %Y, %-I:%M %p")

	message_body = f"Hello, {user_doc.full_name}."
	message_body += "\n\nThis email was initiated by BTU's test-email helper."
	message_body += f"\n\n* Function caller is '{caller_name}'"
	message_body += f"\n* Current server time is {datetime_now_string}"
	message_body += "\n\n--------\n"

	if debug:
		print(f"Sending test email to address '{user_doc.email}'")
	frappe.msgprint(f"Sending test email to address '{user_doc.email}' ...")

	subject = f"From BTU: Hello {user_doc.full_name}"
	try:
		Emailer(subject=subject, body=message_body, sender=get_default_sender(), emailto_list=user_doc.email).send()
	except BTUEmailSendError as ex:
		frappe.throw(str(ex))

	return "If successful, a test email will arrive soon."
