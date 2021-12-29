""" endpoints.py """

# NOTE: VERY IMPORTANT: How to get rid of the 'message" key in Frappe HTTP responses:
# https://discuss.erpnext.com/t/returning-plain-text-from-whitelisted-method/32621

import inspect
import os
import time

# Third Party
from werkzeug.wrappers import Response
from rq.compat import string_types, as_text #  , decode_redis_hash
# from rq.job import Job

# Frappe Library
import frappe
from frappe.utils import cstr

# BTU Library
from btu.btu_core.task_runner import TaskRunner


@frappe.whitelist()
def ping_from_caller():
	return "pong"  # when called by HTTP client, returns a JSON string { "message" : "pong" }


@frappe.whitelist()
def bytes_from_caller():
	"""
	Return some raw bytes to the HTTP client.
	"""
	hello_bytes: bytes = "Hello World".encode()
	response = Response()
	response.mimetype = "application/octet-stream"
	response.data = hello_bytes
	response.status_code = 200
	return response

@frappe.whitelist()
def test_pickler():
	"""
	Picking the 'ping_now' function and return as bytes.
	"""
	from btu.manual_tests import ping_now

	queue_args = {
		"site": frappe.local.site,
		"user": frappe.session.user,
		"method": ping_now,
		"event": None,
		"job_name": "Job Name Foo",
		"is_async": True,  # always true; we want to run things in the Redis Queue, not on the Web Server.
		"kwargs": None  # if ping_now had any keyword arguments, this is where you'd store them.
	}

	new_sanchez = Sanchez()
	new_sanchez.build_internals(func=execute_job, _args=None, _kwargs=queue_args)
	http_result = new_sanchez.create_serialized_rq_job()
	return http_result


@frappe.whitelist()
def get_pickled_task(task_id):
	"""
	RPC HTTP Endpoint called by BTU Scheduler daemon and CLI.
	Given a BTU Task identifier:
		1. Create some pickled, binary data for that Task's function.
		2. Return the binary data to the caller.
	"""
	# Step 1: Retrieve the BTU Task Document.
	doc_task = frappe.get_doc("BTU Task", task_id)

	# Step 2: Wrap it in the TaskRunner class.  This handles logging, capturing Standard Output, and much more.
	this_taskrunner = TaskRunner(btu_task=doc_task, site_name=frappe.local.site, enable_debug_mode=True)

	# This allows for adding additional keyword arguments to a Task:
	extra_arguments = doc_task.built_in_arguments()
	if extra_arguments:
		this_taskrunner.add_keyword_arguments(**extra_arguments)  # pass them as kwargs

	# Step 3: Wrap again, this time using some Frappe code from 'background_jobs.py'
	queue_args = {
		"site": frappe.local.site,
		"user": frappe.session.user,
		"method": this_taskrunner.function_wrapper,
		"event": None,
		"job_name": "Job Name Foo",
		"is_async": True,  # always true; we want to run things in the Redis Queue, not on the Web Server.
		"kwargs": None  # if ping_now had any keyword arguments, this is where you'd store them.
	}

	new_sanchez = Sanchez()
	new_sanchez.build_internals(func=execute_job, _args=None, _kwargs=queue_args)

	# Step 4. Create a serialized RQ Job.  Don't save it to Redis.  Just grab the Binary.
	http_result = new_sanchez.create_serialized_rq_job()
	return http_result
	# import binascii
	# print(binascii.hexlify(serialized_data))


class Sanchez():

	def __init__(self):
		self.function_name = None
		self.instance = None
		self.args = None
		self.kwargs = None

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
		self.args = _args
		self.kwargs = _kwargs

	def create_serialized_rq_job(self):
		"""
		Python Redis Queue(RQ) requires a serialized (binary) tuple of information.
		"""
		import pickle
		from functools import partial

		dumps = partial(pickle.dumps, protocol=pickle.HIGHEST_PROTOCOL)  # tells the function how to do the pickling.

		# VERY IMPORTANT: Substitute () instead of None
		# This solves errors such as "argument after ** must be a mapping, not NoneType"
		if self.args is None:
			self.args = ()
		if self.kwargs is None:
			self.kwargs = {}

		job_tuple = self.function_name, self.instance, self.args, self.kwargs
		serialized_data = dumps(job_tuple)
		return serialized_data


# The following was copied verbatim from 'background_jobs.py'
def execute_job(site, method, event, job_name, kwargs, user=None, is_async=True, retry=0):
	'''Executes job in a worker, performs commit/rollback and logs if there is any error'''
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

	# VERY IMPORTANT: Substitute () instead of None
	# This solves errors such as "argument after ** must be a mapping, not NoneType"
	if kwargs is None:
		kwargs = {}

	frappe.monitor.start("job", method_name, kwargs)
	try:
		method(**kwargs)

	except (frappe.db.InternalError, frappe.RetryBackgroundJobError) as e:
		frappe.db.rollback()

		if (retry < 5 and
			(isinstance(e, frappe.RetryBackgroundJobError) or
				(frappe.db.is_deadlocked(e) or frappe.db.is_timedout(e)))):
			# retry the job if
			# 1213 = deadlock
			# 1205 = lock wait timeout
			# or RetryBackgroundJobError is explicitly raised
			frappe.destroy()
			time.sleep(retry+1)

			return execute_job(site, method, event, job_name, kwargs,
				is_async=is_async, retry=retry+1)

		else:
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
