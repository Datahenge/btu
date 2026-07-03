"""BTU-aware sample task that spawns Task Components."""

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
				function="btu.samples.simple.ordinary_function",
				number_to_count=30,
			).enqueue()
		return "I am the result of 'btu_aware_example1'"
