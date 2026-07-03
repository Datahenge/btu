"""Example BTU-aware functions and maintenance utilities."""

from datetime import timedelta
from typing import NoReturn

import frappe
from frappe.model.sync import sync_for
from frappe.modules.patch_handler import _patch_mode

from btu import get_system_datetime_now
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
			# For each loop, spawn another Task Component

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

	# This is an ordinary function.
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


@frappe.whitelist()
def perform_full_db_sync() -> None:
	"""Force a full JSON-to-database DocType sync for every installed app."""
	print("Performing a full DB synchronization (JSON --> DocType/MariaDB).  Please standby...")
	_patch_mode(True)

	for app in frappe.get_installed_apps():
		try:
			sync_for(app, force=True, reset_permissions=False)
		except Exception as ex:
			print(ex)

	_patch_mode(False)
	frappe.clear_cache()
	print("DB synchronization complete")


def test_get_list() -> None:
	"""Print how many ToDo documents exist (manual sanity check)."""
	customers = frappe.get_list("ToDo")
	print("I got a list of customers.")
	if frappe.exist_uncommitted_sql_changes():
		print("Why are there uncommitted SQL changes?")

	print(f"Found {len(customers)} 'To Do' documents.")


def cleanup_transient_tasks(age_in_days: int = 30) -> None:
	"""Delete historic transient task logs (``bench execute btu.examples.cleanup_transient_tasks``)."""
	older_than_date = get_system_datetime_now().date() + timedelta(days=-age_in_days)
	task_log_table = frappe.qb.DocType("BTU Task Log")
	task_table = frappe.qb.DocType("BTU Task")

	sql_statement = (
		frappe.qb.from_(task_log_table)
		.delete()
		.inner_join(task_table)
		.on(task_table.name == task_log_table.task & task_table.task_type == "Subtask")
		.where(task_log_table.creation <= older_than_date)
	)

	print(sql_statement.get_sql())
	sql_statement.run()
	print(
		f"Deleted historic BTU Task Log records associated with Transient Tasks, older than {older_than_date}"
	)
