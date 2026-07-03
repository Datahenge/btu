"""Minimal callables for worker and run-later smoke tests."""

import frappe


@frappe.whitelist()
def ping_with_wait(seconds_to_wait: int | str) -> str:
	"""Wait N seconds, then return a pong message."""
	import time

	if not seconds_to_wait:
		raise ValueError("Function argument 'seconds_to_wait' is mandatory and has no default.")
	seconds_to_wait = int(seconds_to_wait)
	if seconds_to_wait < 0:
		raise ValueError("Argument 'seconds_to_wait' cannot be less than 0.")
	print(f"Waiting {seconds_to_wait} seconds before replying...")
	time.sleep(seconds_to_wait)
	print("Pong!")
	return "I have sent a 'pong'; this function is concluded."


def ping_now() -> None:
	"""Print ``pong`` (used as a minimal RQ worker target)."""
	print("pong")
