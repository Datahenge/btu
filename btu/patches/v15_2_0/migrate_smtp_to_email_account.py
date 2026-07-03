# Copyright (c) 2021-2026, Datahenge LLC and contributors
# License: MIT
"""Migrate legacy BTU Configuration SMTP settings to a Frappe Email Account."""

import frappe


def execute() -> None:
	"""Copy SMTP singles into Email Account before those fields are removed from the schema."""
	if not frappe.db.table_exists("Singles"):
		return

	if frappe.db.get_single_value("BTU Configuration", "send_email_via") != "SMTP":
		return

	config = frappe.get_single("BTU Configuration")
	username = config.email_auth_username
	server = config.email_server
	port = config.email_server_port or 587
	encryption = config.email_encryption or "STARTTLS"
	password = config.get_password("email_auth_password", raise_exception=False)

	account_name = None
	if username:
		account_name = frappe.db.get_value(
			"Email Account",
			{"email_id": username, "enable_outgoing": 1},
			"name",
		)

	if not account_name and username and server:
		doc = frappe.new_doc("Email Account")
		doc.email_id = username
		doc.email_account_name = username
		doc.smtp_server = server
		doc.smtp_port = int(port) if str(port).isdigit() else 587
		doc.use_tls = 1 if encryption == "STARTTLS" else 0
		doc.use_ssl = 1 if encryption == "SSL" else 0
		doc.enable_outgoing = 1
		if password:
			doc.password = password
		doc.insert(ignore_permissions=True)
		account_name = doc.name

	if account_name:
		frappe.db.set_single_value("BTU Configuration", "default_email_account", account_name)

	frappe.db.set_single_value("BTU Configuration", "send_email_via", "Email Account")
	frappe.db.commit()
