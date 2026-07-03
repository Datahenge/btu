"""User-visible messaging helpers."""

import frappe


def print_both(message: str) -> None:
	"""Print a message to both stdout and the Frappe browser UI."""
	frappe.msgprint(message)
	print(message)
