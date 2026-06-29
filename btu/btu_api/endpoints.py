""" endpoints.py """

# NOTE: This describes how to get rid of the outer 'message" key in Frappe HTTP responses:
# https://discuss.erpnext.com/t/returning-plain-text-from-whitelisted-method/32621

# Frappe Library
import frappe

# BTU Library
from btu.btu_api import Sanchez, execute_job


@frappe.whitelist()
def get_pickled_task(task_id, task_schedule_id=None):
	"""
	RPC HTTP Endpoint called by BTU Scheduler daemon and CLI.

	Builds a pre-serialized RQ job payload (pickled bytes) for the daemon to write
	directly to Redis. Only primitive strings are packed into the payload — no bound
	methods, no Frappe Document objects — so pickling is always safe.

	args:
		task_id:          primary key of a BTU Task
		task_schedule_id: primary key of a BTU Task Schedule (optional)
	"""
	doc_task = frappe.get_doc("BTU Task", task_id)

	queue_args = {
		"site": frappe.local.site,
		"user": frappe.session.user,
		"method": "btu.btu_core.task_runner.run_task_by_id",
		"event": None,
		"job_name": doc_task.desc_short,
		"is_async": True,
		"kwargs": {
			"task_id": task_id,
			"site_name": frappe.local.site,
			"schedule_id": task_schedule_id,
		},
	}

	new_sanchez = Sanchez()
	new_sanchez.build_internals(func=execute_job, _args=None, _kwargs=queue_args)
	return new_sanchez.get_serialized_rq_job()  # bytes

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


@frappe.whitelist(methods=["POST", "PUT"])
def enqueue_for_next_available_worker(task_schedule_key: str):
	"""
	Called by the BTU scheduler daemon when it's time to run a Task, based on its Schedule.
	"""
	# Added March of 2025 as part of BTU Scheduler - Python edition.
	#
	# Avoids headaches with having to:
	#    * Ask ERP to calculate the pickled version of a function + arguments.
	#    * Encode and transfer over HTTP.
	#    * Decode inside the schedule.
	#    * Assign the scheduler to generate an RQ Job with the pickled bytes.
	#
	# Since BTU Scheduler was having to call ERP *regardless*, why the complexity?  Just tell ERP "enqueue now"
	#
	# The only way to avoid HTTP is by writing some kind of Frappe CLI App that does the pickling + Redis.
	# And then call *that* standalone applicatoni via Unix domain sockets, or system calls.
	# It's just not worth the effort: the ERP Web Server should not be offline *anyway*

	response = {
		"has_errors": 0,
		"error_message": ""
	}

	try:
		import uuid
		from btu.btu_core.task_runner import on_btu_task_failure

		doc_task_schedule = frappe.get_doc("BTU Task Schedule", task_schedule_key, ignore_permissions=True)
		doc_task = frappe.get_doc("BTU Task", doc_task_schedule.task, ignore_permissions=True)

		rq_job_id = uuid.uuid4().hex
		frappe.enqueue(
			method="btu.btu_core.task_runner.run_task_by_id",
			queue=doc_task.queue_name,
			timeout=doc_task.max_task_duration or 3600,
			is_async=True,
			on_failure=on_btu_task_failure,
			job_id=rq_job_id,
			task_id=doc_task.name,
			site_name=frappe.local.site,
			schedule_id=task_schedule_key,
			rq_job_id=rq_job_id,
		)

	except Exception as ex:
		frappe.db.rollback()
		response = {
			"has_errors": 1,
			"error_message": str(ex)
		}

	return response
