"""Example functions you can point a BTU Task at."""

from typing import NoReturn

import frappe

from btu.btu_core.btu_task_component import TaskComponent
from btu.btu_core.doctype.btu_task.btu_task import BTU_AWARE_FUNCTION


class btu_aware_example1(BTU_AWARE_FUNCTION):  # pylint: disable=invalid-name
	"""Example BTU-aware class that spawns Task Components in a loop."""

	def run(self, **kwargs: object) -> str:
		"""Spawn Task Components in a loop and return a status string."""
		print(f"I'm a BTU-aware function.  I know I was run by BTU Task = {self.btu_task_id}")
		print(f"Class 'btu_aware_example1' was called with these kwargs: {kwargs}")

		self.btu_task_schedule_id = None

		for each_number in range(0, 50):
			print(f"* Spawning task component #{each_number}")
			TaskComponent(
				btu_task_id=self.btu_task_id,
				btu_component_id=each_number + 1,
				btu_task_schedule_id=self.btu_task_schedule_id,
				frappe_site_name=frappe.local.site,
				function="btu.examples.ordinary_function",
				number_to_count=30,
			).enqueue()
		return "I am the result of 'btu_aware_example1'"


def ordinary_function(number_to_count: int) -> None:
	"""Ordinary function with no knowledge of BTU."""
	import time

	for _ in range(0, number_to_count):
		time.sleep(0.1)
	print(f"An ordinary function finished counting to {number_to_count}.")


@frappe.whitelist()
def wait_then_throw_error() -> NoReturn:
	"""Wait 10 seconds, then raise a RuntimeError."""
	import time

	print("Waiting 10 seconds, then throwing an Exception ...")
	time.sleep(10)
	raise RuntimeError("Simulating a serious error while executing this function.")


def cleanup_transient_tasks(age_in_days: int = 30) -> None:
	"""Deprecated: use :func:`btu.btu_core.housekeeping.cleanup_transient_tasks`."""
	from btu.btu_core.housekeeping import cleanup_transient_tasks as _cleanup_transient_tasks

	_cleanup_transient_tasks(age_in_days=age_in_days)
