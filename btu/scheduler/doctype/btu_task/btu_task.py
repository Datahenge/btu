# Copyright (c) 2021, Datahenge LLC and contributors
# For license information, please see license.txt

import ast
from contextlib import redirect_stdout
from datetime import datetime
import importlib
import inspect
import io
import time

# Frappe
import frappe
from frappe.model.document import Document

# BTU
from btu import Result, get_system_datetime_now, make_datetime_naive
from btu.task_runner import TaskRunner
from btu.scheduler.doctype.btu_task_log.btu_task_log import write_log_for_task


class BTUTask(Document):
	"""
	A SQL records that contains a path to a class of type TaskWrapper
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
		return getattr( self._imported_module(), self._function_name())

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
			frappe.throw(f"Cannot find function '{self. _function_name()}' in module path '{self._module_path()}'.")
		# 3. Ensure function is an instance of btu.TaskWrapper()
		# callable_function = self._callable_function()
		# if not isinstance(callable_function, TaskWrapper):
		# 	frappe.throw(f"Function '{self. _function_name()}' is not an instance of btu.task_runner.TaskWrapper()")
		# frappe.msgprint("\u2713 Task module and function exist and are valid.")

	def push_task_into_queue(self, queue_name='default', extra_arguments=None):
		"""
		Create an instance of TaskRunner() class, and put 'function_wrapper' into the queue.
		Execution will happen immediately (not on a schedule)
		"""
		task_runner = TaskRunner(self, site_name=frappe.local.site, enable_debug_mode=True)

		# This supports the idea of passing special keyword arguments to a Task:
		if extra_arguments:
			task_runner.add_keyword_arguments(**extra_arguments)  # pass them as kwargs

		# Use standard frappe.enqueue() to place the 'function_wrapper' into RQ.
		frappe.enqueue(method=task_runner.function_wrapper,
			queue=queue_name,
			is_async=True)

	def built_in_arguments(self):
		if not self.arguments:
			return None
		return ast.literal_eval(self.arguments)

	@frappe.whitelist()
	def btn_push_into_queue(self, queue_name='default'):
		"""
		Called via button on document's main page.
		Sends a function call into the Redis Queue named 'default'
		"""
		if not self._can_run_on_webserver():
			# Cannot run without defining the appropriate arguments on the Task.
			return

		if not queue_name:
			# Workaround: I suspect the DocType button Options are overriding
			#             the default argument in the function signature?
			queue_name='default'

		self.push_task_into_queue(queue_name=queue_name, extra_arguments=self.built_in_arguments())

		message = f"Task {self.name} has been submitted to the Redis Queue. No callback alerts are possible."
		message += "\nTo see the status of this Task, review the Task Logs."
		frappe.msgprint(message)

	def _can_run_on_webserver(self):
		"""
		Check if the Tasks's function requires arguments.
		If the Task does not specify these 'arguments', warn about this to the user.
		"""
		callable_function = self._callable_function()
		function_arguments = inspect.getfullargspec(callable_function).args
		has_missing_arguments = False
		message = None

		if self.built_in_arguments():
			for argument in function_arguments:
				if argument not in self.built_in_arguments().keys():
					if not has_missing_arguments:
						# If this is the 1st error, begin with a header row.
						has_missing_arguments = True
						message = "----ERROR----\n"
					message += f"\nTask's function requires argument <b>'{argument}'</b> but this is not defined on the Task."

		if has_missing_arguments:
			message += "\n\nYou might be able to run this via a Task Schedule, but not directly here."
			frappe.msgprint(message)

		return not has_missing_arguments


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
				time_now_string = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
				print(f"Task '{self.name}' starting at: {time_now_string}")
				if self.built_in_arguments():
					any_result = callable_function(**self.built_in_arguments())  # read function string, create callable function, and run it.
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

		# Return a tuple to (probably) btu_task.js.
		return (self._callable_function().__name__, success, new_log_id)
