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
		message["To"] = recipients
		part = MIMEText(body, "html")
		message.attach(part)
		message = message.as_string()
	else:
		message = _create_plaintext_message(sender, recipients, subject, body)

	with smtplib.SMTP(btu_config.email_server, btu_config.email_server_port) as smtp_server:

		if not smtp_server.ehlo()[0] == 250:
			frappe.msgprint("SMTP 'Hello' failed for email server.")
			return

		# Use 'STARTTLS' if configured to do so:
		if btu_config.email_encryption == 'STARTTLS':
			smtp_server.starttls() # Secure the connection

		smtp_server.login(user=btu_config.email_auth_username,
		                  password=password)
		smtp_server.sendmail(sender, recipients, msg=message)


def _create_plaintext_message(sender, recipient, subject, body):
	header = 'From: %s\n' % sender
	header +='To: %s\n' % recipient
	header +='Subject: %s\n\n' % subject
	result = header + body
	return result
