""" endpoints.py """

# NOTE: VERY IMPORTANT: How to get rid of the 'message" key in Frappe HTTP responses:
# https://discuss.erpnext.com/t/returning-plain-text-from-whitelisted-method/32621

import inspect
from werkzeug.wrappers import Response
from rq.compat import string_types, as_text #  , decode_redis_hash
# from rq.job import Job
# Frappe Library
import frappe
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
def get_pickled_task(task_id):
	"""
	RPC HTTP Endpoint.  Given a BTU Task identifier, create the pickled, binary data that is compatible with RQ.  Return to the caller.
	"""
	# Step 1: Retrieve the BTU Task Document.
	doc_task = frappe.get_doc("BTU Task", task_id)

	# Step 2: Wrap it in the TaskRunner class, which handles logging, capturing Standard Output, and much more.
	this_taskrunner = TaskRunner(btu_task=doc_task, site_name=frappe.local.site, enable_debug_mode=True)

	# This allows for adding additional keyword arguments to a Task:
	extra_arguments=doc_task.built_in_arguments()
	if extra_arguments:
		this_taskrunner.add_keyword_arguments(**extra_arguments)  # pass them as kwargs

	# Step 3.  We need to use Python pickle to serialize object "this_taskrunner.function_wrapper"
	new_sanchez = Sanchez()
	new_sanchez.build_internals(func=this_taskrunner.function_wrapper, _args=None, _kwargs=None)
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

		job_tuple = self.function_name, self.instance, self.args, self.kwargs
		serialized_data = dumps(job_tuple)
		return serialized_data
