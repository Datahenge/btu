# Copyright (c) 2022, Datahenge LLC and contributors
# For license information, please see license.txt

import ast
from contextlib import redirect_stdout
import importlib
import inspect
import io
import time

# Frappe
import frappe
from frappe.model.document import Document

# BTU
from btu import Result, get_system_datetime_now, make_datetime_naive
from btu.btu_core.task_runner import TaskRunner
from btu.btu_core.doctype.btu_task_log.btu_task_log import write_log_for_task


class BTU_AWARE_FUNCTION():  # pylint: disable=invalid-name

	def __init__(self, btu_task_id):
		self.btu_task_id = btu_task_id
		self.btu_task_schedule_id = None


class BTUTask(Document):
	"""
	A SQL record that contains a path to a class of type TaskWrapper
	"""
	@frappe.whitelist()
	def revert_to_draft(self):
		# Revert the BTU Task back into an editable Draft status.
		frappe.db.set_value(self.doctype, self.name, "docstatus", 0)

	def _module_path(self):
		return '.'.join(self.function_string.split('.')[0:-1])

	def _function_name(self):
		return self.function_string.split('.')[-1]

	def _imported_module(self):
		this_module = importlib.import_module(self._module_path(), package=None)
		return this_module

	def _callable_function(self):
		"""
		Return the callable function associated with this BTU Task.
		"""
		result = getattr( self._imported_module(), self._function_name())
		if not hasattr(result, '__call__'):
			raise Exception(f"The function string '{self.function_string}' is not a callable function.")
		return result

	def validate(self, debug=False):
		"""
		Validate the BTUTask by ensuring the Python function exists, and is derived from TaskWrapper()
		"""
		if debug:
			print(f"Validating module = '{self._module_path()}', function = '{self._function_name}'")
		# 1. Import the Module.
		module_imported = self._imported_module()
		# 2. Ensure function exists in the Module.
		if not self._function_name() in dir(module_imported):
			raise ImportError(f"Cannot find function '{self. _function_name()}' in module path '{self._module_path()}'.")

		# 3. Ensure function is an instance of btu.TaskWrapper()
		# callable_function = self._callable_function()
		# if not isinstance(callable_function, TaskWrapper):
		# 	raise Exception(f"Function '{self. _function_name()}' is not an instance of btu.task_runner.TaskWrapper()")
		# frappe.msgprint("\u2713 Task module and function exist and are valid.")

	def built_in_arguments(self):
		"""
		Converts an argument String into an argument Dictionary.
		"""
		if not self.arguments:
			return None
		args_dict = ast.literal_eval(self.arguments)
		return args_dict

	def _can_run_on_webserver(self):
		"""
		Returns a boolean True if the Task can be executed by the Web Server, otherwise False.
		"""
		# First, check if the Tasks's function requires any arguments.
		# Next, if the Task doesn't provide values for these arguments, return a Boolean false with errors.

		callable_function = self._callable_function()
		function_argument_keys = inspect.getfullargspec(callable_function).args
		function_arguments = []

		for index, each in enumerate(function_argument_keys):
			function_arguments.append({
				'argument_name': each,
				'position': index,
				'has_default_value': False,
				'default_value': None
			})
		# Sort by reverse order
		if function_arguments:
			function_arguments.sort(key=lambda item: item.get("position"), reverse=True)  # inline sort

		# Are there default values for these function arguments?
		function_argument_defaults = inspect.getfullargspec(callable_function).defaults
		if function_argument_defaults:
			list(function_argument_defaults).reverse()  # inline reverse and convert to a List.
			for index, argument in enumerate(function_arguments):
				if len(function_argument_defaults) >= index + 1:
					argument['has_default_value'] = True
					argument['default_value'] = function_argument_defaults[index]
					# print(f"Argument {argument['argument_name']} has a default value  = {function_argument_defaults[index]}")

		if function_arguments:
			function_arguments.sort(key=lambda item: item.get("position"))  # inline sort

		if not self.is_this_btu_aware_function():
			mandatory_argument_names = [ arg['argument_name'] for arg in function_arguments if arg['has_default_value'] is False ]
		else:
			# TODO: Find the mandatory arguments by examining the run() method on the BTU-aware class function.
			mandatory_argument_names = []

		number_of_missing_arguments = 0
		message = None

		if self.built_in_arguments():  # there are arguments specifically annotated on the BTU Task

			for mandatory_argument in mandatory_argument_names:
				if mandatory_argument not in self.built_in_arguments().keys():
					if number_of_missing_arguments == 0:
						# If this is the 1st error, begin with a header row.
						message = "----ERROR----\n"
					message += f"\nTask's function has mandatory argument <b>'{mandatory_argument}'</b>, but this is undefined on the Task."
					number_of_missing_arguments += 1

		if number_of_missing_arguments:
			message += "\n\nTask is missing mandatory arguments.  It might be runnable as a Task Schedule, but not directly from the web server."
			frappe.msgprint(message)

		return number_of_missing_arguments == 0

	def is_this_btu_aware_function(self, debug=True):
		"""
		Returns True if the 'function_string' is actually the path to a BTU-Aware class.
		"""
		result = False
		callable_function = self._callable_function()
		if isinstance(callable_function, type):
			# To find out if this is a subclass of BTU_AWARE_FUNCTION, we have to instantiate it.
			# If it's not a subclass, it's going to throw a hard Exception.  So we should catch it and just return False.
			try:
				if isinstance(callable_function(btu_task_id=self.name), BTU_AWARE_FUNCTION):
					result = True
			except Exception as ex:
				print(ex)
		if debug:
			print(f"Is this a BTU-Aware function = {result}")
		return result

	@frappe.whitelist()
	def run_task_on_webserver(self):
		"""
		Run a BTU Task on the web server.
		  * Captures function return.
		  * Captures standard output.
		  * Captures function success/fail.
		  * Records above information in a BTU Task Log.
		"""

		# Note: This repeats some logic from TaskRunner; may be worth combining them later.

		if not self._can_run_on_webserver():
			return (self._callable_function().__name__, False, None)

		# If the target function has arguments, and the Task does not define them, this isn't going to work.
		callable_function = self._callable_function()

		buffer = io.StringIO()
		success = False
		execution_start = time.time()
		start_datetime = make_datetime_naive(get_system_datetime_now())

		try:
			with redirect_stdout(buffer):
				datetime_string = get_system_datetime_now().strftime("%m/%d/%Y, %H:%M:%S %Z")
				print(f"Task '{self.name}' starting at: {datetime_string}")
				if self.built_in_arguments():
					if self.is_this_btu_aware_function():
						any_result = callable_function(self.name).run(**self.built_in_arguments())  # create an instance of the BTU-aware class, and call its run() method.
					else:
						any_result = callable_function(**self.built_in_arguments())  # read function string, create callable function, and run it.
				else:
					# No keyword arguments for this Task:
					if self.is_this_btu_aware_function():
						any_result = callable_function(self.name).run()  # create an instance of the BTU-aware class, and call its run() method.
					else:
						any_result = callable_function()  # read function string, create callable function, and run it.
			success = True
		except Exception as ex:
			any_result = str(ex)
			success = False
		finally:
			stdout_buffer_for_log = buffer.getvalue()  	 # fetch any Stdout from the buffer.

		execution_time = round(time.time() - execution_start,3)
		# Create an instance of Result class:
		result_object = Result(success=success, message=any_result or "", execution_time=execution_time)

		# Write to `tabBTU Task Log`:
		new_log_id = write_log_for_task(task_id=self.name,
							result=result_object,
							stdout=stdout_buffer_for_log or None,
							date_time_started=start_datetime)

		self.reload()
		# Return a tuple to (probably) btu_task.js.
		return (self._callable_function().__name__, success, new_log_id)

	@frappe.whitelist()
	def btn_push_into_queue(self):
		"""
		Runs the BTU Task in the context of a Redis Queue (RQ) Worker.
		"""
		# Called via button on BTU Task document's main page.

		self.reload()
		if not self._can_run_on_webserver():
			return  # Cannot run without defining the appropriate arguments on the Task.

		self.push_task_into_queue(extra_arguments=self.built_in_arguments())

		message = f"Task {self.name} has been submitted to the Redis Queue. No callback alerts are possible."
		message += "\nTo see the status of this Task, review the Task Logs."
		frappe.msgprint(message)

	def push_task_into_queue(self, extra_arguments=None):
		"""
		Create an instance of TaskRunner() class, and put 'function_wrapper' into the queue.
		Execution will happen immediately (not on a schedule)
		"""
		task_runner = TaskRunner(self, site_name=frappe.local.site, enable_debug_mode=True)

		# This supports the idea of passing special keyword arguments to a Task:
		if extra_arguments:
			task_runner.add_keyword_arguments(**extra_arguments)  # pass them as kwargs

		# Using standard frappe.enqueue() to place the 'function_wrapper' into RQ.
		frappe.enqueue(method=task_runner.function_wrapper,
			queue=self.queue_name,
			timeout=self.max_task_duration or "3600",
			is_async=True)
