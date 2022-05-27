"""
btu.task_runner.py
"""

from contextlib import redirect_stdout
from enum import Enum
import io
import sys
import time
import uuid

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
		"""
		args:
			btu_task : Either a Document or string that represents the primary key of a BTU Task.
			site_name : Name of the calling Site.
		"""
		from btu.btu_core.doctype.btu_task.btu_task import BTUTask as BTUTaskType  # late import required, due to circular reference risks.

		# Validate the 'btu_task' argument:
		if isinstance(btu_task, BTUTaskType):
			self.btu_task = btu_task
		elif isinstance(btu_task, str):
			self.btu_task = frappe.get_doc('BTU Task', btu_task)
		else:
			raise ValueError("Argument 'btu_task' is not a valid BTU Task Document or string name of a Document.")

		# Determine the current, active Site:
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

		# Fetch the Task's built-in arguments.
		self.kwarg_dict = self.btu_task.built_in_arguments() or {}
		if self.schedule_id:
			# Override any keys with those specified by the Task Schedule's arguments:
			schedule_arguments = frappe.get_doc("BTU Task Schedule", self.schedule_id).built_in_arguments() or {}
			if sys.version_info >= (3,9,0):
				self.kwarg_dict = self.kwarg_dict | schedule_arguments # merge the 2 dictionaries.
			else:
				self.kwarg_dict = {**self.kwarg_dict, **schedule_arguments}

	def function_name(self):
		"""
		Return a string that is the name of the Task's function, without it's parent modules.

		Example:  Function `btu.manual_tests.ping_with_wait` returns a String "ping_with_wait"
		"""
		return TaskRunner.split_function_path(self.btu_task.function_string)[1]

	def module_path(self):
		"""
		Return a dotted string, representing the path the Task's function's module.
		"""
		return TaskRunner.split_function_path(self.btu_task.function_string)[0]

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

	def is_this_btu_aware_function(self, callable_function, debug=True):
		"""
		Returns True if the 'function_string' is actually the path to a BTU-Aware class.
		"""
		from btu.btu_core.doctype.btu_task.btu_task import BTU_AWARE_FUNCTION
		result = False
		if isinstance(callable_function, type):
			# To find out if this is a subclass of BTU_AWARE_FUNCTION, we have to instantiate it.
			# If it's not a subclass, it's going to throw a hard Exception.  So we should catch it and just return False.
			try:
				if isinstance(callable_function(btu_task_id=self.btu_task.name), BTU_AWARE_FUNCTION):
					result = True
			except Exception as ex:
				print(ex)
		if debug:
			print(f"Is this a BTU-Aware function = {result}")
		return result

	def function_wrapper(self):  # pylint: disable=too-many-locals, too-many-statements, too-many-branches
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

		self.dprint(f"\n-------- Begin function_wrapper (Redis Job = {self.redis_job_id})--------\n")
		if not hasattr(frappe, 'boot'):
			# The missing 'boot' object is the best-indication that this function is running on RQ, not the web server.
			# This means we have to initialize the frappe namespace, choose a Site, and connect to the MySQL DB.
			self.dprint("This code is running independently from the Web Server.  Need to initialize a few things:")
			frappe.init(site=self.site_name)
			frappe.connect()
			self.dprint("\u2713 Initialization complete.")
		else:
			self.dprint("This code is being executed directly by the Web Server.")

		module_object = importlib.import_module(self.module_path())  # Need to import the function's module into scope.
		function_to_call = getattr(module_object, self.function_name())
		function_result = None

		self.dprint(f"Calling function '{self.function_name()}' in module '{self.module_path()}'.")
		self.dprint("Begin Standard Output (TaskRunner.function_wrapper):\n")

		start_datetime = make_datetime_naive(get_system_datetime_now()) # Recording this in the System Time Zone
		self.create_new_log(start_datetime)  # Create a new BTU Task Log, with a status of "In Progress"
		execution_start = time.time()

		try:
			stdout_buffer_for_log = None
			self.dprint(f"Keyword arguments are as follows: {self.kwarg_dict}")
			datetime_string = get_system_datetime_now().strftime("%m/%d/%Y, %H:%M:%S %Z")

			# Option 1: Function output will be routed to Standard Output, and saved to a log file on disk.
			if self.standard_output == StandardOutput.STDOUT:
				ret = self.option_standard_output(datetime_string, function_to_call)
			# Option 2: Standard output intercepted, and saved to a SQL table `tabBTU Task Log`
			elif self.standard_output == StandardOutput.DB_LOG:
				ret, stdout_buffer_for_log = self.option_log_to_sql(datetime_string, function_to_call)
			else:
				raise Exception(f"No code implemented for Standard Output = '{self.standard_output}'")

			execution_time = round(time.time() - execution_start,3)
			function_result = Result(True, ret, execution_time=execution_time)

		except Exception as ex:
			self.dprint(f"Error in call to function '{self.function_name()}'\n{ex}")
			execution_time = round(time.time() - execution_start,3)
			function_result = Result(False, str(ex), execution_time=execution_time)

		self.dprint(f"\nEnd Standard Output\nFunction Result: {function_result}")

		# The final step is to update BTU Task Log, and record the results!
		self.dprint("Attempting to write to BTU Task Logs:")
		new_log_id = write_log_for_task(task_id=self.btu_task.name,
							            result=function_result,
										log_name=self.task_log_name,
							            stdout=stdout_buffer_for_log or None,
							            date_time_started=start_datetime,
										schedule_id=self.schedule_id)
		self.dprint(f"Updated the BTU Task Log record: '{new_log_id}'")
		self.dprint("\n-------- End function_wrapper --------\n")

	def option_standard_output(self, datetime_string, function_to_call):
		print(f"--------\nBTU Task {self.btu_task.name} starting at: {datetime_string}")
		if self.kwarg_dict:
			if self.is_this_btu_aware_function(function_to_call):
				ret = function_to_call(self.btu_task.name).run(**self.kwarg_dict)    # create an instance of the BTU-aware class, and call its run() method.
			else:
				ret = function_to_call(**self.kwarg_dict)  # ---- call the underlying function + arguments ----
		else:
			# No keyword arguments for this Task:
			if self.is_this_btu_aware_function(function_to_call):
				ret = function_to_call(self.btu_task.name).run()    # create an instance of the BTU-aware class, and call its run() method.
			else:
				ret = function_to_call()  # ----call the underlying function----
		return ret

	def option_log_to_sql(self, datetime_string, function_to_call):
		"""
		Call the function, and capture STDOUT so we can write it to BTU Task Logs.
		"""
		print(f"--------\nBTU Task {self.btu_task.name} starting at: {datetime_string}")
		buffer = io.StringIO()
		with redirect_stdout(buffer):
			# Yes, has keyword arguments:
			if self.kwarg_dict:
				if self.is_this_btu_aware_function(function_to_call):
					ret = function_to_call(self.btu_task.name).run(**self.kwarg_dict)    # create an instance of the BTU-aware class, and call its run() method.
				else:
					ret = function_to_call(**self.kwarg_dict)  # ---- call the underlying function + arguments ----
			# No, does not have keyword arguments for this Task:
			else:
				if self.is_this_btu_aware_function(function_to_call):
					ret = function_to_call(self.btu_task.name).run()    # create an instance of the BTU-aware class, and call its run() method.
				else:
					ret = function_to_call()  # ----call the underlying function----
			stdout_buffer_for_log = buffer.getvalue()  	 # fetch any Stdout from the buffer.
		return ret, stdout_buffer_for_log

	def create_new_log(self, date_time_started):
		"""
		Create a new BTU Task Log with a status of 'In-Progress'
		Later, this log will be updated when the job succeeds or fails.

		The continued existing of a Log with the status 'In Progress' is a good indicator to administrators that
		the BTU Task failed inside the RQ, and will never return a result.
		"""
		new_log = frappe.new_doc("BTU Task Log")  # Create a new Log.
		new_log.task = self.btu_task.name
		new_log.task_desc_short = self.btu_task.desc_short
		new_log.schedule = self.schedule_id
		new_log.task_component = 'Main'
		new_log.date_time_started = date_time_started
		new_log.success_fail = 'In-Progress'
		new_log.save(ignore_permissions=True)  # Not even System Administrators are supposed to create and save these.
		frappe.db.commit()
		self.dprint(f"Created a new BTU Task Log record: '{new_log.name}'")
		self.task_log_name = new_log.name
