"""
btu.task_runner.py
"""

from enum import Enum
from contextlib import redirect_stdout
import io
import time

# Frappe
import frappe


class StandardOutput(Enum):
	NONE = 0
	STDOUT = 1
	DB_LOG = 2
	FILE = 3

# Further Reading:
# https://www.geeksforgeeks.org/decorators-with-parameters-in-python/
# http://gael-varoquaux.info/programming/decoration-in-python-done-right-decorating-and-pickling.html

class TaskRunner():

	@staticmethod
	def split_function_path(function_path):
		"""
		Takes a complete function path like this:    'btu.manual_tests.ping_with_wait'
		And splits into 'module_path' and 'function_name':    (btu.manual_tests, ping_with_wait)
		"""
		module_path = '.'.join(function_path.split('.')[:-1])
		function_name = function_path.split('.')[-1]
		return (module_path, function_name)

	def __init__(self, btu_task, site_name, schedule_id=None, enable_debug_mode=True):
		# Note: Argument 'btu_task' can be either a Document or 'name' of BTU Task
		import uuid
		from btu.btu_core.doctype.btu_task.btu_task import BTUTask  # late import needed because of circular reference.

		if not site_name:
			if frappe.local.site:
				self.site_name = frappe.local.site
			else:
				raise Exception("TaskRunner requires an argument 'site_name'.")
		else:
			self.site_name = site_name

		self.schedule_id = schedule_id
		self.debug_mode_enabled = enable_debug_mode
		self.redis_job_id = uuid.uuid4().hex
		self.standard_output = StandardOutput.DB_LOG

		# Validate the associated BTU Task document:
		if isinstance(btu_task, BTUTask):
			self.btu_task = btu_task
		elif isinstance(btu_task, str):
			self.btu_task = frappe.get_doc('BTU Task', btu_task)
		else:
			raise ValueError("Argument 'btu_task' is not a valid BTU Task document or document's name.")
		# Fetch the Task's built-in arguments.  These may (optionally) be overwritten by the Task Schedule.
		self.kwarg_dict = self.btu_task.built_in_arguments() or None

	def module_path(self):
		return TaskRunner.split_function_path(self.btu_task.function_string)[0]

	def function_name(self):
		return TaskRunner.split_function_path(self.btu_task.function_string)[1]

	def dprint(self, object_foo):
		"""
		Only prints 'object_foo' if the debug_mode is enabled in the class instance.
		"""
		if self.debug_mode_enabled:
			print(object_foo)

	def add_keyword_arguments(self, **kwargs):
		if kwargs:
			self.kwarg_dict = kwargs
		else:
			self.kwarg_dict = None
		self.dprint(f"Task Runner now has these keyword arguments: {self.kwarg_dict}")

	def function_wrapper(self):  # pylint: disable=too-many-locals, too-many-statements
		"""
		This function is effectively a 'decorator' or 'wrapper' around some other Python function.
		The code below is complex and very important.

		To help debug and explain what is happening, I've included a 'dprint()' function.
		This function only prints when TaskRunner argument 'enable_debug_mode' is True.
		"""

		# I'm not confident that importing here (instead of the module level) makes any difference.
		# Still, it "feels right", given this function is executed independently by the Queue.
		# It's possible that Python + RQ pickle the entire Class and namespace, though.
		import importlib
		from btu import Result, get_system_datetime_now, make_datetime_naive
		from btu.btu_core.doctype.btu_task_log.btu_task_log import write_log_for_task

		self.dprint(f"\n-------- Begin function_wrapper (job {self.redis_job_id})--------\n")
		if not hasattr(frappe, 'boot'):
			# The missing 'boot' object is the best-indication that this function is running on RQ, not the web server.
			# This means we have to initialize the frappe namespace, choose a Site, and connect to the MySQL DB.
			self.dprint("This code is running independently from the Web Server.  Need to initialize a few things:")
			frappe.init(site=self.site_name)
			frappe.connect()
			self.dprint("\u2713 Initialization complete.")
		else:
			self.dprint("This code is being executed by the Web Server.")

		module_object = importlib.import_module(self.module_path())  # Need to import the function's module into scope.
		function_to_call = getattr(module_object, self.function_name())
		function_result = None

		self.dprint(f"Calling function '{self.function_name()}' in module '{self.module_path()}'.")
		self.dprint("Begin Standard Output:\n")

		start_datetime = make_datetime_naive(get_system_datetime_now()) # Recording this in the System Time Zone
		execution_start = time.time()
		try:
			stdout_buffer_for_log = None
			self.dprint(f"Keyword arguments are as follows: {self.kwarg_dict}")
			# Option 1: Function will output to console.
			if self.standard_output == StandardOutput.STDOUT:
				print(f"--------\nBTU Task {self.btu_task.name} starting at: {get_system_datetime_now()}")
				if self.kwarg_dict:
					ret = function_to_call(**self.kwarg_dict)  # ----call the underlying function----
				else:
					ret = function_to_call()  # ----call the underlying function----
			elif self.standard_output == StandardOutput.DB_LOG:
				buffer = io.StringIO()
				with redirect_stdout(buffer):
					print(f"--------\nBTU Task {self.btu_task.name} starting at: {get_system_datetime_now()}")
					if self.kwarg_dict:
						ret = function_to_call(**self.kwarg_dict)  # ----call the underlying function----
					else:
						ret = function_to_call()  # ----call the underlying function----
					stdout_buffer_for_log = buffer.getvalue()  	 # fetch any Stdout from the buffer.
			else:
				raise Exception(f"No code implemented for Standard Output = '{self.standard_output}'")

			execution_time = round(time.time() - execution_start,3)
			function_result = Result(True, ret, execution_time=execution_time)
		except Exception as ex:
			self.dprint(f"Error in call to function '{self.function_name()}'\n{ex}")
			execution_time = round(time.time() - execution_start,3)
			function_result = Result(False, str(ex), execution_time=execution_time)

		self.dprint("\nEnd Standard Output")
		self.dprint(f"Function Result: {function_result}")

		# Code below was mostly a sanity check: Can we successfully read from the ERPNext Database?
		# print("Querying the Site database for User 'Administrator' ...")
		# doc_user_admin = frappe.get_doc("User", "Administrator")
		# print(f"\u2713 Found it: {doc_user_admin.name}")

		# STEP 4. If applicable, write a new record to BTU Task Log.
		self.dprint("Attempting to write to BTU Task Logs:")
		new_log_id = write_log_for_task(task_id=self.btu_task.name,
							            result=function_result,
							            stdout=stdout_buffer_for_log or None,
							            date_time_started=start_datetime,
										schedule_id=self.schedule_id)
		self.dprint(f"Wrote a new BTU Task Log record: '{new_log_id}'")
		self.dprint("\n-------- End function_wrapper --------\n")
