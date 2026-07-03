"""RQ worker entry point and TaskRunner for executing BTU Tasks."""

from __future__ import annotations

import importlib
import io
import logging
import os
import time
import traceback
from collections.abc import Callable
from contextlib import redirect_stdout
from datetime import datetime
from enum import Enum
from types import TracebackType
from typing import TYPE_CHECKING, Any

# Frappe
import frappe

# Third Party
import redis
from rq.job import Job

from btu import Result, get_system_datetime_now, make_datetime_naive
from btu.btu_core.doctype.btu_task_log.btu_task_log import write_log_for_task

if TYPE_CHECKING:
	from btu.btu_core.doctype.btu_task.btu_task import BTUTask


def _configure_btu_logger() -> logging.Logger:
	"""Return the ``btu`` logger; level from ``BTU_LOG_LEVEL`` or ``force_debug_mode``."""
	logger = frappe.logger("btu")
	env_level = getattr(logging, os.environ.get("BTU_LOG_LEVEL", "INFO").upper(), logging.INFO)
	try:
		force_debug = frappe.db.get_single_value("BTU Configuration", "force_debug_mode", cache=True)
		level = logging.DEBUG if force_debug else env_level
	except Exception:
		level = env_level  # DB not yet available (early init path)
	logger.setLevel(level)
	return logger


def run_task_by_id(
	task_id: str,
	site_name: str,
	schedule_id: str | None = None,
	extra_arguments: dict[str, Any] | None = None,
	rq_job_id: str | None = None,
) -> None:
	"""RQ entry point: load a BTU Task by id and run it in the worker process."""
	from rq import get_current_job

	if not getattr(frappe.local, "initialised", None):
		frappe.init(site=site_name)
		frappe.connect()

	logger = _configure_btu_logger()

	current_job = get_current_job()
	if current_job:
		if rq_job_id and current_job.id != rq_job_id:
			logger.warning(
				"BTU: Expected RQ Job ID '%s' does not match actual '%s'. Using actual.",
				rq_job_id,
				current_job.id,
			)
		rq_job_id = current_job.id  # actual always wins

	btu_task = frappe.get_doc("BTU Task", task_id)
	runner = TaskRunner(btu_task, site_name=site_name, schedule_id=schedule_id, rq_job_id=rq_job_id)
	if extra_arguments:
		runner.add_keyword_arguments(**extra_arguments)
	runner.function_wrapper()


def on_btu_task_failure(
	job: Job,
	connection: redis.client.Redis,
	exc_type: type[BaseException] | None,
	exc_value: BaseException | None,
	traceback_obj: TracebackType | None,
) -> None:
	"""RQ ``on_failure`` callback: mark the BTU Task Log as Failed with traceback."""
	task_kwargs = job.kwargs.get("kwargs", {})
	site_name = task_kwargs.get("site_name") or job.kwargs.get("site")

	if not site_name:
		frappe.logger("btu").warning(
			"BTU on_failure callback: cannot determine site_name for job %s; skipping log update.", job.id
		)
		return

	try:
		frappe.init(site=site_name)
		frappe.connect()

		log_name = frappe.db.get_value(
			"BTU Task Log", {"rq_job_id": job.id, "success_fail": "In-Progress"}, "name"
		)
		if not log_name:
			return

		exc_string = "".join(traceback.format_exception(exc_type, exc_value, traceback_obj))
		doc_log = frappe.get_doc("BTU Task Log", log_name)
		doc_log.success_fail = "Failed"
		doc_log.stdout = (doc_log.stdout or "") + f"\n\n--- RQ Worker Traceback ---\n{exc_string}"
		doc_log.save(ignore_permissions=True)
		frappe.db.commit()

	except Exception as ex:
		frappe.logger("btu").error("BTU on_failure callback error for job %s: %s", job.id, ex)
	finally:
		frappe.destroy()


class StandardOutput(Enum):
	"""Where TaskRunner routes function stdout during execution."""

	NONE = 0
	STDOUT = 1
	DB_LOG = 2
	# FILE was removed: writing to disk is not container-safe and was never used.


# Further Reading:
# https://www.geeksforgeeks.org/decorators-with-parameters-in-python/
# http://gael-varoquaux.info/programming/decoration-in-python-done-right-decorating-and-pickling.html


class TaskRunner:
	"""Execute a BTU Task callable with logging, stdout capture, and BTU Task Log updates."""

	@staticmethod
	def split_function_path(function_path: str) -> tuple[str, str]:
		"""Split a dotted function path into ``(module_path, function_name)``."""
		module_path = ".".join(function_path.split(".")[:-1])
		function_name = function_path.split(".")[-1]
		return (module_path, function_name)

	def __init__(
		self,
		btu_task: BTUTask | str,
		site_name: str,
		schedule_id: str | None = None,
		rq_job_id: str | None = None,
	) -> None:
		"""Initialize a runner for the given BTU Task document (or name) and site."""
		from btu.btu_core.doctype.btu_task.btu_task import (
			BTUTask as BTUTaskType,  # late import required, due to circular reference risks.
		)

		# Validate the 'btu_task' argument:
		if isinstance(btu_task, BTUTaskType):
			self.btu_task = btu_task
		elif isinstance(btu_task, str):
			self.btu_task = frappe.get_doc("BTU Task", btu_task)
		else:
			raise ValueError(
				"Argument 'btu_task' is not a valid BTU Task Document or string name of a Document."
			)

		# Determine the current, active Site:
		if not site_name:
			if frappe.local.site:
				self.site_name = frappe.local.site
			else:
				raise ValueError("TaskRunner requires an argument 'site_name'.")
		else:
			self.site_name = site_name

		self.schedule_id = schedule_id
		self.rq_job_id = rq_job_id  # real RQ job ID; None when running outside of an RQ worker
		self.standard_output = StandardOutput.DB_LOG

		# Fetch the Task's built-in arguments.
		self.kwarg_dict: dict[str, Any] | None = self.btu_task.built_in_arguments() or {}
		if self.schedule_id:
			# Override any keys with those specified by the Task Schedule's arguments:
			schedule_arguments = (
				frappe.get_doc("BTU Task Schedule", self.schedule_id).built_in_arguments() or {}
			)
			self.kwarg_dict = self.kwarg_dict | schedule_arguments

	def function_name(self) -> str:
		"""Return the bare function name from the task's ``function_string``."""
		return TaskRunner.split_function_path(self.btu_task.function_string)[1]

	def module_path(self) -> str:
		"""Return the dotted module path from the task's ``function_string``."""
		return TaskRunner.split_function_path(self.btu_task.function_string)[0]

	def add_keyword_arguments(self, **kwargs: object) -> None:
		"""Replace stored keyword arguments with ``kwargs`` (or clear if empty)."""
		if kwargs:
			self.kwarg_dict = kwargs
		else:
			self.kwarg_dict = None
		frappe.logger("btu").debug("TaskRunner keyword arguments: %s", self.kwarg_dict)

	def is_this_btu_aware_function(self, callable_function: object) -> bool:
		"""Return True if ``callable_function`` is a BTU-aware class constructor."""
		from btu.btu_core.doctype.btu_task.btu_task import BTU_AWARE_FUNCTION

		result = False
		if isinstance(callable_function, type):
			# To find out if this is a subclass of BTU_AWARE_FUNCTION, we have to instantiate it.
			# If it's not a subclass, it's going to throw a hard Exception.  So we should catch it and just return False.
			try:
				if isinstance(callable_function(btu_task_id=self.btu_task.name), BTU_AWARE_FUNCTION):
					result = True
			except Exception as ex:
				frappe.logger("btu").debug("BTU-aware check failed (not a BTU-aware class): %s", ex)
		frappe.logger("btu").debug("TaskRunner: BTU-aware=%s, user=%s", result, frappe.session.user)
		return result

	def _initialize_site_and_database(self) -> None:
		# TODO: This is not longer working in Frappe v15.  Presence of boot doesn't seem to indicate anything??
		if not hasattr(frappe, "boot"):
			frappe.logger("btu").debug("function_wrapper(): running outside web server, initializing Frappe.")
			frappe.init(site=self.site_name)
			frappe.connect()
			frappe.logger("btu").debug("Frappe initialization complete.")
		else:
			frappe.logger("btu").debug("function_wrapper(): running directly on web server.")

	def function_wrapper(self) -> None:  # pylint: disable=too-many-locals, too-many-statements, too-many-branches
		"""Import, invoke, and log the task function; update the BTU Task Log with the result."""
		logger = frappe.logger("btu")
		logger.info("Begin function_wrapper: task=%s rq_job_id=%s", self.btu_task.name, self.rq_job_id)
		self._initialize_site_and_database()
		start_datetime = make_datetime_naive(
			get_system_datetime_now()
		)  # Recording this in the System Time Zone
		self.create_new_log(start_datetime)  # Create a new BTU Task Log, with a status of "In Progress"

		function_threw_exception = False
		function_result: Result | None = None
		execution_start = time.time()
		datetime_string = get_system_datetime_now().strftime("%m/%d/%Y, %H:%M:%S %Z")
		stdout_buffer_for_log: str | None = None

		try:
			module_object = importlib.import_module(
				self.module_path()
			)  # Need to import the function's module into scope.
			function_to_call = getattr(module_object, self.function_name())
			logger.info("Calling function '%s' in module '%s'.", self.function_name(), self.module_path())
			logger.debug("Keyword arguments: %s", self.kwarg_dict)

			# Option 1: Function output will be routed to Standard Output, and saved to a log file on disk.
			if self.standard_output == StandardOutput.STDOUT:
				ret = self.option_standard_output(datetime_string, function_to_call)
			# Option 2: Standard output intercepted, and saved to a SQL table "tabBTU Task Log"
			elif self.standard_output == StandardOutput.DB_LOG:
				function_threw_exception, ret, stdout_buffer_for_log = self.option_log_to_sql(
					datetime_string, function_to_call
				)
			else:
				# StandardOutput.FILE was explicitly removed (not container-safe, never used).
				raise ValueError(
					f"Unsupported StandardOutput mode '{self.standard_output}'. Only STDOUT and DB_LOG are valid."
				)

			execution_time = round(time.time() - execution_start, 3)
			if function_threw_exception:
				function_result = Result(False, ret, execution_time=execution_time)
			else:
				function_result = Result(True, ret, execution_time=execution_time)

		except Exception as ex:
			logger.error("Error in function '%s': %s", self.function_name(), ex)
			execution_time = round(time.time() - execution_start, 3)
			function_result = Result(False, str(ex), execution_time=execution_time)

		logger.info("Function result: %s", function_result)
		new_log_id = write_log_for_task(
			task_id=self.btu_task.name,
			result=function_result,
			log_name=self.task_log_name,
			stdout=stdout_buffer_for_log or None,
			date_time_started=start_datetime,
			schedule_id=self.schedule_id,
		)
		logger.info("Updated BTU Task Log: '%s'", new_log_id)
		logger.info("End function_wrapper: task=%s", self.btu_task.name)

	def option_standard_output(self, datetime_string: str, function_to_call: Callable[..., object]) -> object:
		"""Invoke the task function with stdout routed to the process (no SQL capture)."""
		print(
			f"--------\nBTU Task {self.btu_task.name} starting at: {datetime_string}"
		)  # intentional: STDOUT mode streams directly to process stdout (e.g. log file via supervisor)
		if self.kwarg_dict:
			if self.is_this_btu_aware_function(function_to_call):
				ret = function_to_call(self.btu_task.name).run(
					**self.kwarg_dict
				)  # create an instance of the BTU-aware class, and call its run() method.
			else:
				ret = function_to_call(
					**self.kwarg_dict
				)  # ---- call the underlying function + arguments ----
		else:
			# No keyword arguments for this Task:
			if self.is_this_btu_aware_function(function_to_call):
				ret = function_to_call(
					self.btu_task.name
				).run()  # create an instance of the BTU-aware class, and call its run() method.
			else:
				ret = function_to_call()  # ----call the underlying function----
		return ret

	def option_log_to_sql(
		self, datetime_string: str, function_to_call: Callable[..., object]
	) -> tuple[bool, object, str]:
		"""Call the function, capture stdout, and return exception flag, result, and buffer."""
		function_threw_exception = False
		function_response: object = None
		buffer = io.StringIO()
		with redirect_stdout(buffer):
			# All print() calls inside this block are intentional: redirect_stdout captures them
			# into stdout_buffer_for_log, which is written to the BTU Task Log's stdout field.
			# Replacing these with logger calls would bypass the buffer and lose the captured output.
			try:
				print(f"--------\nBTU Task {self.btu_task.name} starting at: {datetime_string}")
				# Yes, has keyword arguments:
				if self.kwarg_dict:
					if self.is_this_btu_aware_function(function_to_call):
						function_response = function_to_call(self.btu_task.name).run(
							**self.kwarg_dict
						)  # create an instance of the BTU-aware class, and call its run() method.
					else:
						function_response = function_to_call(
							**self.kwarg_dict
						)  # ---- call the underlying function + arguments ----
				# No, does not have keyword arguments for this Task:
				else:
					if self.is_this_btu_aware_function(function_to_call):
						function_response = function_to_call(
							self.btu_task.name
						).run()  # create an instance of the BTU-aware class, and call its run() method.
					else:
						function_response = function_to_call()  # ----call the underlying function----
			except Exception as ex:
				function_threw_exception = True
				print(f"ERROR: Exception during function call.  Type = {type(ex)}, Value = {ex}")
				print(traceback.format_exc())
			finally:
				stdout_buffer_for_log = buffer.getvalue()  # fetch any Stdout from the buffer.

		return function_threw_exception, function_response, stdout_buffer_for_log

	def create_new_log(self, date_time_started: datetime) -> None:
		"""Create an In-Progress BTU Task Log for this run."""
		new_log = frappe.new_doc("BTU Task Log")  # Create a new Log.
		new_log.task = self.btu_task.name
		new_log.task_desc_short = self.btu_task.desc_short
		new_log.schedule = self.schedule_id
		new_log.task_component = "Main"
		new_log.date_time_started = date_time_started
		new_log.success_fail = "In-Progress"
		new_log.rq_job_id = self.rq_job_id  # real RQ job ID, or None if running outside a worker
		new_log.save(
			ignore_permissions=True
		)  # Not even System Administrators are supposed to create and save these.
		frappe.db.commit()
		frappe.logger("btu").info("Created BTU Task Log: '%s'", new_log.name)
		self.task_log_name = (
			new_log.name
		)  # Save the BTU Task Log 'name' to this class, so we can reference it later.
