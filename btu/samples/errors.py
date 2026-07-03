"""Sample task that fails after a delay."""

from typing import NoReturn

import frappe


@frappe.whitelist()
def wait_then_throw_error() -> NoReturn:
	"""Wait 10 seconds, then raise a RuntimeError."""
	import time

	print("Waiting 10 seconds, then throwing an Exception ...")
	time.sleep(10)
	raise RuntimeError("Simulating a serious error while executing this function.")
