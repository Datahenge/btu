""" endpoints.py """

# NOTE: This describes how to get rid of the outer 'message" key in Frappe HTTP responses:
# https://discuss.erpnext.com/t/returning-plain-text-from-whitelisted-method/32621

# Frappe Library
import frappe

# BTU Library
from btu.btu_core.task_runner import TaskRunner
from btu.btu_api import Sanchez, execute_job


@frappe.whitelist()
def get_pickled_task(task_id, task_schedule_id=None):
	"""
	RPC HTTP Endpoint called by BTU Scheduler daemon and CLI.

	args:
		task_id:				primary key of a BTU Task
		task_schedule_id:		primary key of a BTU Task Schedule

	Steps:
		1. Create some pickled, binary data for a Task's function.
		2. Return the binary data to the caller.
	"""

	# Step 1: Retrieve the BTU Task Document.
	doc_task = frappe.get_doc("BTU Task", task_id)

	# Step 2: Wrap it in the TaskRunner class.  This handles logging, capturing Standard Output, and much more.
	this_taskrunner = TaskRunner(btu_task=doc_task,
	                             site_name=frappe.local.site,
								 schedule_id=task_schedule_id,	# very important, so TaskRunner can Log per Schedule!
								 enable_debug_mode=True)

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
		"job_name": doc_task.desc_short,
		"is_async": True,  # always true; we want to run things in the Redis Queue, not on the Web Server.
		"kwargs": None  # if function requires keyword arguments, this is where you'd store them.
	}

	# Step 4. Use the Sanchez class to pickle the Task Runner
	new_sanchez = Sanchez()
	new_sanchez.build_internals(func=execute_job, _args=None, _kwargs=queue_args)

	# Step 4. Create a serialized RQ Job, but do not save to Redis.  Return the binary over HTTP.
	http_result: bytes = new_sanchez.get_serialized_rq_job()
	return http_result

# The purpose of the following endpoints: to enable the BTU CLI and Scheduler
# to test and validate connectivity with the Frappe web server.

@frappe.whitelist()
def test_ping():
	"""
	When called by an HTTP client, returns a JSON string { "message" : "pong" }
	"""
	return "pong"

@frappe.whitelist()
def test_hello_world_bytes():
	"""
	Return some raw bytes to the HTTP client.
	"""
	from werkzeug.wrappers import Response

	hello_bytes: bytes = "Hello World".encode()
	response = Response()
	response.mimetype = "application/octet-stream"
	response.data = hello_bytes
	response.status_code = 200
	return response

@frappe.whitelist()
def test_function_ping_now_bytes():
	"""
	Picking the 'ping_now' function and return as bytes.
	"""
	from btu.manual_tests import ping_now

	queue_args = {
		"site": frappe.local.site,
		"user": frappe.session.user,
		"method": ping_now,
		"event": None,
		"job_name": "ping_now",
		"is_async": True,  # always true; we want to run Tasks via the Redis Queue, not on the Web Server.
		"kwargs": {}  # if 'ping_now' had keyword arguments, we'd set them here.
	}

	new_sanchez = Sanchez()
	new_sanchez.build_internals(func=execute_job, _args=None, _kwargs=queue_args)
	http_result: bytes = new_sanchez.get_serialized_rq_job()
	return http_result
