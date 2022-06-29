""" examples.py """

import frappe
from frappe.modules.patch_handler import block_user
from frappe.model.sync import sync_for

# --------------------
# BTU-Aware Functions
# --------------------
from btu.btu_core.doctype.btu_task.btu_task import BTU_AWARE_FUNCTION
from btu.btu_core.btu_task_component import TaskComponent


class btu_aware_example1(BTU_AWARE_FUNCTION):  # pylint: disable=invalid-name

	def run(self, **kwargs):

		print(f"I'm a BTU-aware function.  I know I was run by BTU Task = {self.btu_task_id}")
		print(f"Class 'btu_aware_example1' was called with these kwargs: {kwargs}")

		self.btu_task_schedule_id = None

		for each_number in range(0, 50):
			# For each loop, spawn another Task Component

			print(f"* Spawning task component #{each_number}")
			TaskComponent(btu_task_id=self.btu_task_id,
			              btu_component_id=each_number+1,
						  btu_task_schedule_id=self.btu_task_schedule_id,
						  frappe_site_name=frappe.local.site,
						  function=ordinary_function,
						  number_to_count=30).enqueue()
		return "I am the result of 'btu_aware_example1'"


def ordinary_function(number_to_count):
	"""
	This is an ordinary function, with no knowledge of BTU.
	"""
	import time
	# This is an ordinary function.
	for _ in range(0, number_to_count):
		time.sleep(0.1)
	print(f"An ordinary function finished counting to {number_to_count}.")


@frappe.whitelist()
def wait_then_throw_error():
	"""
	Wait 10 seconds, then throw an Exception.
	"""
	import time
	print("Waiting 10 seconds, then throwing an Exception ...")
	time.sleep(10)
	raise Exception("Simulating a serious error while executing this function.")


@frappe.whitelist()
def perform_full_db_sync():

	print("Performing a full DB synchronization (JSON --> DocType/MariaDB).  Please standby...")
	block_user(True)

	for app in frappe.get_installed_apps():
		try:
			sync_for(app, force=True, reset_permissions=False)
		except Exception as ex:
			print(ex)

	block_user(False)
	frappe.clear_cache()
	print("DB synchronization complete")


def test_get_list():
	customers = frappe.get_list("ToDo")
	print("I got a list of customers.")
	if frappe.exist_uncommitted_sql_changes():
		print("Why are there uncommitted SQL changes?")

	print(f"Found {len(customers)} 'To Do' documents.")


def cleanup_transient_tasks(age_in_days=30):
	pass
	# TODO: Delete Transient Tasks/Logs older than a certain date/time.
