"""BTU API helpers for RQ job serialization and transient tasks."""

import inspect
import os
import pickle
import time
from collections.abc import Callable
from functools import partial
from typing import TYPE_CHECKING, Any

import frappe
from frappe.utils import cstr
from rq.compat import as_text, string_types

if TYPE_CHECKING:
	from btu.btu_core.doctype.btu_task.btu_task import BTUTask


class Sanchez:
	"""Build and pickle RQ job payloads from callables and arguments."""

	def __init__(self) -> None:
		"""Initialize an empty RQ job serializer."""
		self.function_name: str | None = None
		self.instance: Any = None
		self.args: tuple[Any, ...] = ()
		self.kwargs: dict[str, Any] = {}

	def build_internals(
		self,
		func: Callable[..., Any] | str,
		_args: tuple[Any, ...] | None,
		_kwargs: dict[str, Any] | None,
	) -> None:
		"""Populate job metadata from a callable (or path string) and arguments."""
		if inspect.ismethod(func):
			self.instance = func.__self__
			self.function_name = func.__name__
		elif inspect.isfunction(func) or inspect.isbuiltin(func):
			self.function_name = f"{func.__module__}.{func.__qualname__}"
		elif isinstance(func, string_types):
			self.function_name = as_text(func)
		elif not inspect.isclass(func) and callable(func):  # a callable class instance
			self.instance = func
			self.function_name = "__call__"
		else:
			raise TypeError(f"Expected a callable or a string, but got: {func}")

		self.args = _args or ()
		self.kwargs = _kwargs or {}

		# NOTE: Important to substitute () or {} instead of None.
		# This prevents errors such as "argument after ** must be a mapping, not NoneType"
		# if self.args is None:
		# self.args = ()
		# if self.kwargs is None:
		#  self.kwargs = {}

	def get_serialized_rq_job(self) -> bytes:
		"""Return the RQ job tuple as pickled bytes."""
		job_tuple = self.function_name, self.instance, self.args, self.kwargs
		dumps = partial(pickle.dumps, protocol=pickle.HIGHEST_PROTOCOL)  # defines how to do the pickling.
		return dumps(job_tuple)  # this is the serialized/pickled job


# The following function was copied from 'frappe.utils.background_jobs'
# pylint: disable=too-many-branches, inconsistent-return-statements
def execute_job(
	site: str,
	method: Callable[..., Any] | str,
	event: str | None,
	job_name: str,
	kwargs: dict[str, Any] | None,
	user: str | None = None,
	is_async: bool = True,
	retry: int = 0,
) -> None:
	"""Execute a job in a worker, with commit/rollback and error logging."""
	if is_async:
		frappe.connect(site)
		if os.environ.get("CI"):
			frappe.flags.in_test = True

		if user:
			frappe.set_user(user)

	if isinstance(method, string_types):
		method_name = method
		method = frappe.get_attr(method)
	else:
		method_name = cstr(method.__name__)

	# VERY IMPORTANT: Substitute {} instead of None for kwargs.
	# This solves the error "argument after ** must be a mapping, not NoneType"
	if kwargs is None:
		kwargs = {}

	frappe.monitor.start("job", method_name, kwargs)
	try:
		method(**kwargs)
	except (frappe.db.InternalError, frappe.RetryBackgroundJobError) as ex:
		frappe.db.rollback()

		if retry < 5 and (
			isinstance(ex, frappe.RetryBackgroundJobError)
			or (frappe.db.is_deadlocked(ex) or frappe.db.is_timedout(ex))
		):
			# retry the job if
			# 1213 = deadlock
			# 1205 = lock wait timeout
			# or RetryBackgroundJobError is explicitly raised
			frappe.destroy()
			time.sleep(retry + 1)
			return execute_job(site, method, event, job_name, kwargs, is_async=is_async, retry=retry + 1)

		frappe.log_error(title=method_name)
		raise

	except Exception:
		frappe.db.rollback()
		frappe.log_error(title=method_name)
		frappe.db.commit()
		print(frappe.get_traceback())
		raise

	else:
		frappe.db.commit()

	finally:
		frappe.monitor.stop()
		if is_async:
			frappe.destroy()


class TransientTask:
	"""Temporary BTU Task that runs once, then is discarded (see ``create_new_transient``)."""

	@staticmethod
	def create_new_transient(
		function_path: str,
		description: str,
		task_group: str = "Transient",
		max_task_duration: str = "600s",
		queue_name: str = "short",
		**kwargs: object,
	) -> "TransientTask":
		"""Create a new transient Subtask document and wrap it in a TransientTask."""
		doc_task = frappe.new_doc("BTU Task")
		doc_task.desc_short = description
		doc_task.task_group = task_group
		doc_task.task_type = "Subtask"
		doc_task.function_string = function_path
		doc_task.arguments = str(kwargs)
		doc_task.run_only_as_worker = True
		doc_task.max_task_duration = max_task_duration
		doc_task.repeat_log_in_stdout = True
		doc_task.queue_name = queue_name
		document_name = frappe.generate_hash(
			"BTU", 12
		)  # Don't use the Naming Series; transient documents just get hash names.
		# NOTE: Ignoring permissions, because employees should never have access to BTU Tasks.
		doc_task.flags.ignore_permissions = 1
		doc_task.insert(set_name=document_name)
		doc_task.submit()
		transient_task = TransientTask(doc_task)
		return transient_task

	def __init__(self, doc_task: "BTUTask") -> None:
		"""Wrap an existing BTU Task document as a transient Subtask."""
		from btu.btu_core.doctype.btu_task.btu_task import BTUTask

		if not isinstance(doc_task, BTUTask):
			raise TypeError(
				"Class instantiation argument 'doc_task' must be an instance of 'BTU Task' document."
			)
		self.doc_task = doc_task

	def enqueue(self) -> None:
		"""Push this transient Subtask into the Redis queue."""
		if self.doc_task.task_type != "Subtask":
			raise ValueError(f"BTU Task {self.doc_task.name} is not a transient Subtask.")

		self.doc_task.push_task_into_queue()

		message = f"Transient Task {self.doc_task.name} has been submitted to the Redis Queue."
		print(message)
		frappe.msgprint(message)
