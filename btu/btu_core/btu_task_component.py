""" btu_task_component.py """

# --------
#
# The purpose of this class is to "wrap" an ordinary function, and treat it as a Component of a larger BTU Task.
#
# --------

from contextlib import redirect_stdout
import importlib
import io
import re
import time
import frappe

from btu.btu_core.task_runner import _configure_btu_logger

_DOTTED_PATH_RE = re.compile(r'^[a-zA-Z_]\w*(\.[a-zA-Z_]\w*)+$')


def get_function_name(function_path: str) -> str:
    """Return the bare function name from a dotted module path string."""
    return function_path.rsplit(".", 1)[-1]


# pylint: disable=too-many-instance-attributes

class TaskComponent():

	def __init__(self, btu_task_id, btu_component_id, btu_task_schedule_id, frappe_site_name,
				 function, queue='default', timeout=None, **kwargs):
		"""
		Initialize the class instance.
		"""
		self.btu_task_id = btu_task_id
		self.btu_component_id = btu_component_id
		self.btu_task_schedule_id = btu_task_schedule_id or None

		if not isinstance(function, str):
			raise TypeError(
				f"TaskComponent 'function' must be a dotted string path "
				f"(e.g. 'myapp.module.function_name'), got {type(function).__name__}."
			)
		if not _DOTTED_PATH_RE.match(function):
			raise ValueError(
				f"TaskComponent 'function' must be a fully-qualified dotted path "
				f"(e.g. 'myapp.module.function_name'). Got: '{function}'."
			)
		self.function_path = function
		self.max_runtime_seconds = 3600
		self.queue_name = queue
		self.timeout = timeout
		if kwargs:
			self.kwarg_dict = kwargs
		else:
			self.kwarg_dict = None

		if frappe.local.site:
			self.frappe_site_name = frappe.local.site
		elif frappe_site_name:
			self.frappe_site_name = frappe_site_name
		else:
			raise RuntimeError("TaskRunner requires an argument 'site_name'.")

	def enqueue(self):
		"""
		Put this thingie into a queue.
		"""
		component_wrapper = TaskComponentWrapper(btu_task_id=self.btu_task_id,
												 btu_component_id=self.btu_component_id,
												 btu_task_schedule_id=self.btu_task_schedule_id,
												 frappe_site_name=self.frappe_site_name,
				 								 function=self.function_path)

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

	def __init__(self, btu_task_id, btu_component_id, btu_task_schedule_id, frappe_site_name, function):
		"""
		Initialize the class instance.
		"""
		self.btu_task_id = btu_task_id
		self.btu_component_id = btu_component_id
		self.btu_task_schedule_id = btu_task_schedule_id
		self.frappe_site_name = frappe_site_name
		self.function_path = function  # dotted string path, e.g. 'myapp.module.function_name'
		self.kwarg_dict = None
		self.max_runtime_seconds = 3600

	def add_keyword_arguments(self, **kwargs):
		if kwargs:
			self.kwarg_dict = kwargs
		else:
			self.kwarg_dict = None
		frappe.logger("btu").debug("TaskComponentWrapper keyword arguments: %s", self.kwarg_dict)

	def function_payload(self):  # pylint: disable=too-many-locals, too-many-statements
		"""
		Wrapper around the component function. Initializes Frappe if needed, resolves
		the function path, captures stdout, writes BTU Task Log entries.
		"""
		from btu import Result, get_system_datetime_now, make_datetime_naive
		from btu.btu_core.doctype.btu_task_log.btu_task_log import write_log_for_task

		if not getattr(frappe.local, "initialised", None):
			frappe.init(site=self.frappe_site_name)
			frappe.connect()

		logger = _configure_btu_logger()
		logger.info("Begin function_payload: task=%s component=%s", self.btu_task_id, self.btu_component_id)

		# Resolve the dotted string path to a callable here in the worker, not at enqueue time.
		module_path, func_name = self.function_path.rsplit(".", 1)
		function_to_call = getattr(importlib.import_module(module_path), func_name)
		logger.info("Calling function '%s'", get_function_name(self.function_path))
		logger.debug("Keyword arguments: %s", self.kwarg_dict)

		start_datetime = make_datetime_naive(get_system_datetime_now()) # Recording this in the System Time Zone
		self.create_new_log(start_datetime)  # Create a new BTU Task Log, with a status of "In Progress"
		execution_start = time.time()

		function_result = None
		try:
			stdout_buffer_for_log = None
			datetime_string = get_system_datetime_now().strftime("%m/%d/%Y, %H:%M:%S %Z")

			buffer = io.StringIO()
			with redirect_stdout(buffer):
				print(f"--------\nBTU Task Component {self.btu_task_id}-{self.btu_component_id} starting at: {datetime_string}")
				if self.kwarg_dict:
					ret = function_to_call(**self.kwarg_dict)
				else:
					ret = function_to_call()
				stdout_buffer_for_log = buffer.getvalue()

			execution_time = round(time.time() - execution_start, 3)
			function_result = Result(True, ret, execution_time=execution_time)

		except Exception as ex:
			logger.error("Error in function '%s': %s", get_function_name(self.function_path), ex)
			execution_time = round(time.time() - execution_start, 3)
			function_result = Result(False, str(ex), execution_time=execution_time)

		logger.info("Function result: %s", function_result)
		new_log_id = write_log_for_task(task_id=self.btu_task_id,
							            result=function_result,
										log_name=self.task_log_name,
							            stdout=stdout_buffer_for_log or None,
							            date_time_started=start_datetime,
										schedule_id=self.btu_task_schedule_id)
		logger.info("Updated BTU Task Log: '%s'", new_log_id)
		logger.info("End function_payload: task=%s component=%s", self.btu_task_id, self.btu_component_id)

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
		frappe.logger("btu").info("Created BTU Task Log (component): '%s'", new_log.name)
		self.task_log_name = new_log.name
