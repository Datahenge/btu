"""BTU Task DocType controller."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

import ast
import importlib
import inspect
import io
import json
import time
from collections.abc import Callable
from contextlib import redirect_stdout
from types import ModuleType
from typing import Any

# Frappe
import frappe
from frappe.model.document import Document

# BTU
from btu import Result, dict_to_dateless_dict, get_system_datetime_now, make_datetime_naive
from btu.btu_core.doctype.btu_task_log.btu_task_log import write_log_for_task

NoneType = type(None)


class BTU_AWARE_FUNCTION:  # pylint: disable=invalid-name
	"""Mixin base for BTU-aware callable classes."""

	def __init__(self, btu_task_id: str) -> None:
		"""Store the BTU Task id for a BTU-aware callable class instance."""
		self.btu_task_id = btu_task_id
		self.btu_task_schedule_id = None


class FunctionPathString:
	"""String representing the path to a Python function."""

	def __init__(self, function_path_string: str, debug: bool = False) -> None:
		"""Parse and store a dotted Python function path."""
		self.function_path_string = function_path_string
		self.debug_mode = bool(debug)

	def module_path(self) -> str:
		"""Return the dotted module path portion of the function path."""
		return ".".join(self.function_path_string.split(".")[0:-1])

	def function_name(self) -> str:
		"""Return the function name portion of the function path."""
		return self.function_path_string.split(".")[-1]

	def create_module_object(self) -> ModuleType:
		"""Import and return the module referenced by the function path."""
		return importlib.import_module(self.module_path(), package=None)

	def validate(self) -> None:
		"""Ensure the module imports and exposes the target function."""
		if self.debug_mode:
			print(f"Validating module = '{self.module_path()}', function = '{self.function_name}'")
		# 1. Import the Module.
		module_imported = self.create_module_object()
		# 2. Ensure function exists in the Module.
		if self.function_name() not in dir(module_imported):
			raise ImportError(
				f"Cannot find function '{self.function_name()}' in module path '{self.module_path()}'."
			)


class BTUTask(Document):
	"""A SQL record that contains a path to a class of type TaskWrapper."""

	@frappe.whitelist()
	def revert_to_draft(self) -> None:
		"""Revert the BTU Task and child email recipients to draft status."""
		frappe.db.set_value(self.doctype, self.name, "docstatus", 0)
		for each_email in self.email_recipients:
			frappe.db.set_value(each_email.doctype, each_email.name, "docstatus", 0)

	def _function_name(self) -> str:
		"""Return the function name from this task's function string."""
		return FunctionPathString(self.function_string).function_name()

	def _imported_module(self) -> ModuleType:
		"""Return the imported module for this task's function string."""
		return FunctionPathString(self.function_string).create_module_object()

	def _callable_function(self) -> Callable[..., Any]:
		"""Return the callable function associated with this BTU Task."""
		result = getattr(self._imported_module(), self._function_name())
		if not callable(result):
			raise RuntimeError(f"The function string '{self.function_string}' is not a callable function.")
		return result

	def validate(self, debug: bool = False) -> None:
		"""Validate that the configured Python function exists."""
		FunctionPathString(self.function_string, debug).validate()

		# TODO: Ensure function is an instance of btu.TaskWrapper()
		# callable_function = self._callable_function()
		# if not isinstance(callable_function, TaskWrapper):
		# 	raise Exception(f"Function '{self. _function_name()}' is not an instance of btu.task_runner.TaskWrapper()")
		# frappe.msgprint("\u2713 Task module and function exist and are valid.")

	def before_save(self) -> None:
		"""Normalize curly quote characters in the arguments field."""
		if self.arguments:
			self.arguments = self.arguments.replace(
				"“", '"'
			)  # replace the unsupported curly forward double quote with the regular one.
			self.arguments = self.arguments.replace(
				"”", '"'
			)  # replace the unsupported curly backward double quote with the regular one.

	def before_insert(self) -> None:
		"""Copy default email recipients from BTU Configuration for new tasks."""
		if self.email_recipients:
			return
		doc_config = frappe.get_single("BTU Configuration")
		if not doc_config.email_recipients:
			return
		for each_recipient in doc_config.email_recipients:
			self.append(
				"email_recipients",
				{
					"email_address": each_recipient.email_address,
					"email_on_start": each_recipient.email_on_start,
					"email_on_success": each_recipient.email_on_success,
					"email_on_error": each_recipient.email_on_error,
					"email_on_timeout": each_recipient.email_on_timeout,
				},
			)

	def on_trash(self) -> None:
		"""Delete related BTU Task Log rows when this task is deleted."""
		self.flags.ignore_submitted = True  # tell a lie, to bypass the Submitted checks
		sql_statement = """ DELETE FROM "tabBTU Task Log" WHERE task = %(task_id)s """
		frappe.db.sql(sql_statement, values={"task_id": self.name})

	def built_in_arguments(self) -> dict[str, Any] | None:
		"""Parse the task arguments field into a dictionary (JSON first, then ast.literal_eval)."""
		# TODO (v16): The 'arguments' field was originally documented as a "Python Dictionary
		# of key-values", so early adopters stored values as Python literals (single-quoted
		# strings, bare True/False, etc.) rather than valid JSON.  Commit 41a3813 (Nov 2022)
		# reflects this original design.  Commit fb91e4c (Jun 2025) added json.loads() as the
		# preferred parser and kept ast.literal_eval only for backward compatibility with
		# existing tasks stored in Python-literal format.
		#
		# In v16, run a migration that reads every BTU Task's 'arguments' field, parses it
		# with ast.literal_eval, and re-saves it as canonical JSON.  Once all rows are
		# migrated, remove the ast.literal_eval fallback and enforce JSON-only at save time
		# via BTUTask.validate().
		if not self.arguments:
			return None
		if isinstance(self.arguments, dict):
			return self.arguments
		try:
			return json.loads(self.arguments)
		except Exception as ex:
			print(f"built_in_arguments() : {ex}")

		# TODO (v16): remove this fallback once the migration to JSON is complete.
		return ast.literal_eval(self.arguments)

	def _can_run_on_webserver(self) -> bool:
		"""Return whether the task has all mandatory arguments for web-server execution."""
		callable_function = self._callable_function()
		function_argument_keys = inspect.getfullargspec(callable_function).args
		function_arguments = []

		for index, each in enumerate(function_argument_keys):
			function_arguments.append(
				{"argument_name": each, "position": index, "has_default_value": False, "default_value": None}
			)
		if function_arguments:
			function_arguments.sort(key=lambda item: item.get("position"), reverse=True)

		function_argument_defaults = inspect.getfullargspec(callable_function).defaults
		if function_argument_defaults:
			list(function_argument_defaults).reverse()
			for index, argument in enumerate(function_arguments):
				if len(function_argument_defaults) >= index + 1:
					argument["has_default_value"] = True
					argument["default_value"] = function_argument_defaults[index]

		if function_arguments:
			function_arguments.sort(key=lambda item: item.get("position"))

		if not self.is_this_btu_aware_function():
			mandatory_argument_names = [
				arg["argument_name"] for arg in function_arguments if arg["has_default_value"] is False
			]
		else:
			mandatory_argument_names = []

		number_of_missing_arguments = 0
		message = None

		if self.built_in_arguments():
			for mandatory_argument in mandatory_argument_names:
				if mandatory_argument not in self.built_in_arguments().keys():
					if number_of_missing_arguments == 0:
						message = "----ERROR----\n"
					message += f"\nTask's function has mandatory argument <b>'{mandatory_argument}'</b>, but this is undefined on the Task."
					number_of_missing_arguments += 1

		if number_of_missing_arguments:
			message += "\n\nTask is missing mandatory arguments.  It might be runnable as a Task Schedule, but not directly from the web server."
			frappe.msgprint(message)

		return number_of_missing_arguments == 0

	def is_this_btu_aware_function(self) -> bool:
		"""Return whether the function string points to a BTU-aware class."""
		result = False
		callable_function = self._callable_function()
		if isinstance(callable_function, type):
			try:
				if isinstance(callable_function(btu_task_id=self.name), BTU_AWARE_FUNCTION):
					result = True
			except Exception as ex:
				print(ex)
		return result

	@frappe.whitelist()
	def run_task_on_webserver(self) -> tuple[str, bool, str | None]:
		"""Run a BTU Task on the web server and record the result in a Task Log."""
		if not self._can_run_on_webserver():
			return (self._callable_function().__name__, False, None)

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
						any_result = callable_function(self.name).run(**self.built_in_arguments())
					else:
						any_result = callable_function(**self.built_in_arguments())
				else:
					if self.is_this_btu_aware_function():
						any_result = callable_function(self.name).run()
					else:
						any_result = callable_function()
			success = True
		except Exception as ex:
			any_result = str(ex)
			success = False
		finally:
			stdout_buffer_for_log = buffer.getvalue()

		execution_time = round(time.time() - execution_start, 3)
		result_object = Result(success=success, message=any_result or "", execution_time=execution_time)

		new_log_id = write_log_for_task(
			task_id=self.name,
			result=result_object,
			stdout=stdout_buffer_for_log or None,
			date_time_started=start_datetime,
		)

		self.reload()
		return (self._callable_function().__name__, success, new_log_id)

	@frappe.whitelist()
	def btn_push_into_queue(self, quiet: bool = False) -> None:
		"""Enqueue the BTU Task for execution by an RQ worker."""
		self.reload()
		if not self._can_run_on_webserver():
			return

		self.push_task_into_queue()

		message = (
			f"BTU Task {self.name} has been submitted to the Redis Queue. No callback alerts are possible."
		)
		message += "\nTo see the status of this Task, review the BTU Task Logs."
		if not quiet:
			frappe.msgprint(message)
		print(message)

	def push_task_into_queue(
		self,
		schedule_id: str | None = None,
		extra_arguments: dict[str, Any] | None = None,
	) -> None:
		"""Enqueue this BTU Task for execution by the next available RQ worker."""
		import uuid

		from btu.btu_core.task_runner import on_btu_task_failure

		existing_log = _task_has_active_log(self.name)
		if existing_log:
			frappe.logger("btu").warning(
				"Task %s already has an In-Progress log (%s); skipping enqueue.", self.name, existing_log
			)
			return

		rq_job_id = uuid.uuid4().hex
		frappe.enqueue(
			method="btu.btu_core.task_runner.run_task_by_id",
			queue=self.queue_name,
			timeout=self.max_task_duration or 3600,
			is_async=True,
			on_failure=on_btu_task_failure,
			job_id=rq_job_id,
			task_id=self.name,
			site_name=frappe.local.site,
			schedule_id=schedule_id,
			extra_arguments=extra_arguments,
			rq_job_id=rq_job_id,
		)


def _task_has_active_log(task_id: str) -> str | None:
	"""Return the In-Progress BTU Task Log name for task_id, if one exists."""
	return frappe.db.get_value("BTU Task Log", {"task": task_id, "success_fail": "In-Progress"}, "name")


def create_and_run_one_shot(
	short_description: str,
	function_path: str,
	arguments: dict[str, Any] | None,
	queue_name: str = "short",
	quiet: bool = False,
) -> str:
	"""Create and run a one-shot BTU Task, returning the new task name."""
	if not function_path or not isinstance(function_path, str):
		raise ValueError("Argument 'function_path' is mandatory and must be a Python string.")
	if not isinstance(arguments, (dict, NoneType)):
		raise ValueError("Argument 'arguments' must be a Python dictionary.")

	arguments = dict_to_dateless_dict(arguments)

	doc_task = frappe.new_doc("BTU Task")
	doc_task.task_type = "One-Shot"
	doc_task.desc_short = short_description
	doc_task.function_string = function_path
	doc_task.arguments = json.dumps(arguments, indent=4) if arguments else None
	doc_task.run_only_as_worker = bool(queue_name)
	doc_task.queue_name = queue_name
	doc_task.max_task_duration = 3600
	doc_task.flags.ignore_permissions = 1
	doc_task.save()
	doc_task.submit()
	frappe.db.commit()

	if doc_task.queue_name:
		doc_task.btn_push_into_queue(quiet=quiet)
	else:
		doc_task.run_task_on_webserver()
	return doc_task.name
