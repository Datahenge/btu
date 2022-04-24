""" btu_task_component.py """

# --------
#
# The purpose of this class is to "wrap" an ordinary function, and treat it as a Component of a larger BTU Task.
#
# --------

from contextlib import redirect_stdout
# from enum import Enum
import io
import time
# import uuid

import frappe

# pylint: disable=too-many-instance-attributes

def split_function_path(function_path):
	"""
	Takes a complete function path like this:    'btu.manual_tests.ping_with_wait'
	And splits into 'module_path' and 'function_name':    (btu.manual_tests, ping_with_wait)
	"""
	module_path = '.'.join(function_path.split('.')[:-1])
	function_name = function_path.split('.')[-1]
	return (module_path, function_name)

class TaskComponent():

	def __init__(self, btu_task_id, btu_component_id, btu_task_schedule_id, frappe_site_name,
				 function, queue='default', timeout=None, debug_mode=True, **kwargs):
		"""
		Initialize the class instance.
		"""
		self.btu_task_id = btu_task_id
		self.btu_component_id = btu_component_id
		self.btu_task_schedule_id = btu_task_schedule_id or None
		self.function_to_run = function
		self.max_runtime_seconds = 3600
		self.queue_name = queue
		self.timeout = timeout
		self.debug_mode_enabled = bool(debug_mode)
		if kwargs:
			self.kwarg_dict = kwargs
		else:
			self.kwarg_dict = None

		if frappe.local.site:
			self.frappe_site_name = frappe.local.site
		elif frappe_site_name:
			self.frappe_site_name = frappe_site_name
		else:
			raise Exception("TaskRunner requires an argument 'site_name'.")

	def validate_class_variables(self):
		if not frappe.db.exists("BTU Task", self.btu_task_id):
			raise ValueError(f"No such BTU Task with identifier = {self.btu_task_id}")
		if not frappe.db.exists("BTU Task Schedule", self.btu_task_schedule_id):
			raise ValueError(f"No such BTU Task with identifier = {self.btu_task_schedule_id}")

	def dprint(self, object_foo):
		"""
		Only prints 'object_foo' if the debug_mode is enabled in the class instance.
		"""
		if self.debug_mode_enabled:
			print(object_foo)

	def enqueue(self):
		"""
		Put this thingie into a queue.
		"""
		component_wrapper = TaskComponentWrapper(btu_task_id=self.btu_task_id,
												 btu_component_id=self.btu_component_id,
												 btu_task_schedule_id=self.btu_task_schedule_id,
												 frappe_site_name=self.frappe_site_name,
				 								 function=self.function_to_run,
												 debug_mode_enabled=self.debug_mode_enabled)

		# This supports the idea of passing special keyword arguments to a Task:
		if self.kwarg_dict:
			component_wrapper.add_keyword_arguments(**self.kwarg_dict)  # pass them as kwargs

		# Use standard frappe.enqueue() to place the 'function_payload' into RQ.
		frappe.enqueue(
			method=component_wrapper.function_payload,
			queue=self.queue_name,
			timeout=self.max_runtime_seconds,
			is_async=True
		)


class TaskComponentWrapper():

	def __init__(self, btu_task_id, btu_component_id, btu_task_schedule_id, frappe_site_name, function, debug_mode_enabled=False):
		"""
		Initialize the class instance.
		"""

		#if hasattr(frappe, 'boot'):
		#	raise Exception("Error: This class should never be instantiated from the Gunicorn Web Server.  It belongs in a Python RQ.")

		self.btu_task_id = btu_task_id
		self.btu_component_id = btu_component_id
		self.btu_task_schedule_id = btu_task_schedule_id
		self.frappe_site_name = frappe_site_name
		self.function_to_run = function  # This is a real function, not a path to a function.
		self.debug_mode_enabled = bool(debug_mode_enabled)
		self.kwarg_dict = None
		self.max_runtime_seconds = 3600

	def add_keyword_arguments(self, **kwargs):
		if kwargs:
			self.kwarg_dict = kwargs
		else:
			self.kwarg_dict = None
		self.dprint(f"Task Component Wrapper now has these keyword arguments: {self.kwarg_dict}")

	def dprint(self, object_foo):
		"""
		Only prints 'object_foo' if the debug_mode is enabled in the class instance.
		"""
		if self.debug_mode_enabled:
			print(object_foo)

	def function_payload(self):  # pylint: disable=too-many-locals, too-many-statements
		"""
		This function is effectively a 'decorator' or 'wrapper' around some other Python function.
		The code below is complex and very important.

		To help debug and explain what is happening, I've included a 'dprint()' function.
		This function only prints when TaskRunner argument 'enable_debug_mode' is True.
		"""
		# I'm not confident that importing here (instead of the module level) makes any difference.
		# Still, it "feels right", given this function is executed independently by the Queue.
		# It's possible that Python + RQ pickle the entire Class and namespace, though.
		# import importlib

		from btu import Result, get_system_datetime_now, make_datetime_naive
		from btu.btu_core.doctype.btu_task_log.btu_task_log import write_log_for_task

		self.dprint("\n-------- Begin execution of 'function_payload()' --------\n")

		frappe.init(site=self.frappe_site_name)
		frappe.connect()
		self.dprint("\u2713 Initialization complete.")

		function_result = None
		self.dprint(f"Calling function '{self.function_to_run.__name__}'")
		self.dprint("Begin Standard Output (function_payload):\n")

		start_datetime = make_datetime_naive(get_system_datetime_now()) # Recording this in the System Time Zone
		self.create_new_log(start_datetime)  # Create a new BTU Task Log, with a status of "In Progress"
		execution_start = time.time()

		try:
			stdout_buffer_for_log = None
			self.dprint(f"Keyword arguments are as follows: {self.kwarg_dict}")
			datetime_string = get_system_datetime_now().strftime("%m/%d/%Y, %H:%M:%S %Z")

			buffer = io.StringIO()
			with redirect_stdout(buffer):
				print(f"--------\nBTU Task Component {self.btu_task_id}-{self.btu_component_id} starting at: {datetime_string}")
				if self.kwarg_dict:
					ret = self.function_to_run (**self.kwarg_dict)  # ----call the underlying function----
				else:
					ret = self.function_to_run()  # ----call the underlying function----
				stdout_buffer_for_log = buffer.getvalue()  	 # fetch any Stdout from the buffer.

			execution_time = round(time.time() - execution_start,3)
			function_result = Result(True, ret, execution_time=execution_time)

		except Exception as ex:
			self.dprint(f"Error in call to function '{self.function_name()}'\n{ex}")
			execution_time = round(time.time() - execution_start,3)
			function_result = Result(False, str(ex), execution_time=execution_time)

		self.dprint(f"\nEnd Standard Output\nFunction Result: {function_result}")

		# The final step is to update BTU Task Log, and record the results!
		self.dprint("Attempting to write to BTU Task Logs:")
		new_log_id = write_log_for_task(task_id=self.btu_task_id,
							            result=function_result,
										log_name=self.task_log_name,
							            stdout=stdout_buffer_for_log or None,
							            date_time_started=start_datetime,
										schedule_id=self.btu_task_schedule_id)
		self.dprint(f"Updated the BTU Task Log record: '{new_log_id}'")
		self.dprint("\n-------- End function_wrapper --------\n")

	def create_new_log(self, date_time_started):
		"""
		Create a new BTU Task Log with a status of 'In-Progress'
		Later, this log will be updated when the job succeeds or fails.

		The continued existing of a Log with the status 'In Progress' is a good indicator to administrators that
		the BTU Task failed inside the RQ, and will never return a result.
		"""
		task_description = frappe.get_value("BTU Task", self.btu_task_id, "desc_short")
		new_log = frappe.new_doc("BTU Task Log")  # Create a new Log.
		new_log.task = self.btu_task_id
		new_log.task_desc_short = task_description
		new_log.task_component = self.btu_component_id
		new_log.schedule = self.btu_task_schedule_id
		new_log.date_time_started = date_time_started
		new_log.success_fail = 'In-Progress'
		new_log.save(ignore_permissions=True)  # Not even System Administrators are supposed to create and save these.
		frappe.db.commit()
		self.dprint(f"Created a new BTU Task Log record for a Component: '{new_log.name}'")
		self.task_log_name = new_log.name
