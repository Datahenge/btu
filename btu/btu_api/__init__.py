""" btu/btu_api """

from functools import partial
import inspect
import os
import pickle
import time

from rq.compat import string_types, as_text

import frappe
from frappe.utils import cstr


class Sanchez():

	def __init__(self):
		self.function_name = None
		self.instance = None
		self.args = ()
		self.kwargs = {}

	def build_internals(self, func, _args, _kwargs):
		"""
		Given a function (probably 'execute_job') and _kwargs, create an RQ job.
		"""
		if inspect.ismethod(func):
			self.instance = func.__self__
			self.function_name = func.__name__
		elif inspect.isfunction(func) or inspect.isbuiltin(func):
			self.function_name = f"{func.__module__}.{func.__qualname__}"
		elif isinstance(func, string_types):
			self.function_name = as_text(func)
		elif not inspect.isclass(func) and hasattr(func, '__call__'):  # a callable class instance
			self._instance = func
			self.function_name = '__call__'
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

	def get_serialized_rq_job(self):
		"""
		Create a tuple of RQ Job 'data', and return in a serialized (pickled) binary format.
		"""
		job_tuple = self.function_name, self.instance, self.args, self.kwargs
		dumps = partial(pickle.dumps, protocol=pickle.HIGHEST_PROTOCOL)  # defines how to do the pickling.
		return dumps(job_tuple)  # this is the serialized/pickled job

# The following function was copied from 'frappe.utils.background_jobs'
# pylint: disable=too-many-branches, inconsistent-return-statements
def execute_job(site, method, event, job_name, kwargs, user=None, is_async=True, retry=0):
	"""
	Executes job in a worker, performs commit/rollback and logs if there is any error
	"""
	if is_async:
		frappe.connect(site)
		if os.environ.get('CI'):
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

		if (retry < 5 and
			(isinstance(ex, frappe.RetryBackgroundJobError) or
				(frappe.db.is_deadlocked(ex) or frappe.db.is_timedout(ex)))):
			# retry the job if
			# 1213 = deadlock
			# 1205 = lock wait timeout
			# or RetryBackgroundJobError is explicitly raised
			frappe.destroy()
			time.sleep(retry+1)
			return execute_job(site, method, event, job_name, kwargs,
				is_async=is_async, retry=retry+1)

		frappe.log_error(title=method_name)
		raise

	except:
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


class TransientTask():
	"""
	The Transient Task is a kind of temporary BTU Task.  It only runs 1 time, then is discarded.

	Usage:

		from btu.btu_api import TransientTask
		TransientTask.create_new_transient(
			function_path = "path.to_some.function",
			description = "Description of this Function",
			max_task_duration='6000s',
			queue_name='short',
			argument1='foo',
			argument2='bar',
			argument3='baz'
		).enqueue()

	"""

	@staticmethod
	def create_new_transient(function_path, description, task_group="Transient",
	                         max_task_duration='600s', queue_name='short', **kwargs):
		"""
		Create a new, transient Subtask.
		"""
		doc_task = frappe.new_doc("BTU Task")
		doc_task.desc_short = description
		doc_task.task_group = task_group
		doc_task.task_type = 'Subtask'
		doc_task.function_string = function_path
		doc_task.arguments = str(kwargs)
		doc_task.run_only_as_worker = True
		doc_task.max_task_duration = max_task_duration
		doc_task.repeat_log_in_stdout = True
		doc_task.queue_name = queue_name
		document_name = frappe.generate_hash("BTU", 12)  # Don't use the Naming Series; transient documents just get hash names.
		doc_task.insert(set_name=document_name)
		doc_task.submit()
		transient_task = TransientTask(doc_task)
		return transient_task

	def __init__(self, doc_task):
		from btu.btu_core.doctype.btu_task.btu_task import BTUTask
		if not isinstance(doc_task, BTUTask):
			raise TypeError("Class instantiation argument 'doc_task' must be an instance of 'BTU Task' document.")
		self.doc_task = doc_task

	def enqueue(self):
		"""
		Called via button on document's main page.
		Sends a function call into the Redis Queue named 'default'
		"""
		if self.doc_task.task_type != 'Subtask':
			raise ValueError(f"BTU Task {self.doc_task.name} is not a transient Subtask.")

		self.doc_task.push_task_into_queue(extra_arguments=self.doc_task.built_in_arguments())

		message = f"Transient Task {self.doc_task.name} has been submitted to the Redis Queue."
		print(message)
		frappe.msgprint(message)
