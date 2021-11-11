""" btu/email.py"""

#
# Basic SMTP email functionality for BTU.
#

# from email import encoders
# from email.mime.base import MIMEBase

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

import frappe
from frappe.utils.password import get_decrypted_password


def send_email(sender, recipients, subject, body):

	if not isinstance(subject, str):
		raise Exception("Argument 'subject' should be a Python string type.")

	if isinstance(recipients, list):
		recipient_str = ", ".join(recipients)
	elif isinstance(recipients, str):
		recipient_str = recipients
	else:
		raise TypeError(recipients)

	# Apply environment prefixes.
	subject = apply_subject_prefix(subject)
	body = apply_body_prefix(body)

	btu_config = frappe.get_doc("BTU Configuration")
	use_html = bool(btu_config.email_body_is_html)
	password = get_decrypted_password(doctype="BTU Configuration",
	                                  name="BTU Configuration",
	                                  fieldname="email_auth_password")

	if use_html:
		# 1. Replace newlines with breaks:
		body = body.replace('\n', '<br>')
		# 2. Create MIMEMultipart object
		message = MIMEMultipart("alternative")
		message["Subject"] = subject
		message["From"] = sender
		message["To"] = recipient_str
		part = MIMEText(body, "html")
		message.attach(part)
		message = message.as_string()
	else:
		message = _create_plaintext_message(sender, recipient_str, subject, body)

	with smtplib.SMTP(btu_config.email_server, btu_config.email_server_port) as smtp_server:

		if not smtp_server.ehlo()[0] == 250:
			frappe.msgprint("SMTP 'Hello' failed for email server.")
			return

		# Use 'STARTTLS' if configured to do so:
		if btu_config.email_encryption == 'STARTTLS':
			smtp_server.starttls() # Secure the connection

		smtp_server.login(user=btu_config.email_auth_username,
		                  password=password)
		smtp_server.sendmail(from_addr=sender,
		                     to_addrs=recipient_str.split(","),  # requires a List of Recipients
							 msg=message)


def _create_plaintext_message(sender, recipients, subject, body):

	if isinstance(recipients, list):
		recipient_str = ", ".join(recipients)
	elif isinstance(recipients, str):
		recipient_str = recipients
	else:
		raise TypeError(recipients)

	header = f"From: {sender}\n"
	header += f"To: {recipient_str}\n"
	header += f"Subject: {subject}\n\n"
	result = header + body
	return result


def get_environment_name():
	"""
	Returns the current environment name from the BTU Configuration document.
	"""
	return frappe.db.get_single_value("BTU Configuration", "environment_name")


def apply_subject_prefix(subject):
	"""
	Given an email subject, apply a prefix (if applicable)
	"""
	environment_name = get_environment_name()
	if not environment_name:
		return subject
	return f"({environment_name}) {subject}"


def apply_body_prefix(body):
	"""
	Given an email subject, apply a prefix (if applicable)
	"""
	environment_name = get_environment_name()
	if not environment_name:
		return body
	return f"(sent from the ERPNext {environment_name} environment)\n\n" + body
