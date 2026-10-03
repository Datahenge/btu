"""Whitelisted HTTP endpoints for the BTU scheduler daemon and CLI."""

# NOTE: This describes how to get rid of the outer 'message" key in Frappe HTTP responses:
# https://discuss.erpnext.com/t/returning-plain-text-from-whitelisted-method/32621

import frappe
from werkzeug.wrappers import Response

from btu.btu_api import Sanchez, execute_job
from btu.btu_core.doctype.btu_task.btu_task import _task_has_active_log


@frappe.whitelist()
def get_pickled_task(task_id: str, task_schedule_id: str | None = None) -> bytes:
	"""Return pickled RQ job bytes for ``task_id`` (optional ``task_schedule_id``)."""
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
def test_ping() -> str:
	"""Return ``pong`` for connectivity checks."""
	return "pong"


@frappe.whitelist()
def test_hello_world_bytes() -> Response:
	"""Return raw bytes to the HTTP client."""
	hello_bytes: bytes = b"Hello World"
	response = Response()
	response.mimetype = "application/octet-stream"
	response.data = hello_bytes
	response.status_code = 200
	return response


@frappe.whitelist()
def test_function_ping_now_bytes() -> bytes:
	"""Return pickled RQ job bytes for the ``ping_now`` test function."""
	from btu.diagnostics.smoke import ping_now

	queue_args = {
		"site": frappe.local.site,
		"user": frappe.session.user,
		"method": ping_now,
		"event": None,
		"job_name": "ping_now",
		"is_async": True,  # always true; we want to run Tasks via the Redis Queue, not on the Web Server.
		"kwargs": {},  # if 'ping_now' had keyword arguments, we'd set them here.
	}

	new_sanchez = Sanchez()
	new_sanchez.build_internals(func=execute_job, _args=None, _kwargs=queue_args)
	http_result: bytes = new_sanchez.get_serialized_rq_job()
	return http_result


@frappe.whitelist()
def get_enabled_task_schedules() -> list[dict[str, str]]:
	"""
	Return every enabled BTU Task Schedule as {'schedule_key': ..., 'task_key': ...}.

	Used by the BTU Scheduler daemon in 'webserver' connectivity mode, replacing the
	direct SQL read in btu_scheduler's lib/sql.py::get_enabled_task_schedules(). See
	docs/technical/04-webserver-only-architecture.md in btu_scheduler_py.
	"""
	rows = frappe.get_all(
		"BTU Task Schedule",
		filters={"enabled": 1},
		fields=["name", "task"],
	)
	return [{"schedule_key": row.name, "task_key": row.task} for row in rows]


@frappe.whitelist()
def get_task_schedule_details(task_schedule_key: str) -> dict[str, str | int]:
	"""
	Return one BTU Task Schedule's scheduling details.

	Used by the BTU Scheduler daemon in 'webserver' connectivity mode, replacing the
	direct SQL read in btu_scheduler's lib/sql.py::get_task_schedule_by_id(). Reads the
	document directly rather than joining against BTU Configuration, since
	BTUTaskSchedule.before_validate() already guarantees cron_timezone is populated
	(falling back to the system time zone) at save time.
	"""
	if not frappe.db.exists("BTU Task Schedule", task_schedule_key):
		frappe.throw(
			f"BTU Task Schedule '{task_schedule_key}' not found.",
			exc=frappe.DoesNotExistError,
		)

	doc = frappe.get_doc("BTU Task Schedule", task_schedule_key)
	return {
		"name": doc.name,
		"task": doc.task,
		"task_description": doc.task_description,
		"enabled": doc.enabled,
		"queue_name": doc.queue_name,
		"argument_overrides": doc.argument_overrides,
		"schedule_description": doc.schedule_description,
		"cron_string": doc.cron_string,
		"cron_timezone": doc.cron_timezone,
	}


@frappe.whitelist()
def get_pending_scheduler_commands() -> list[dict[str, str]]:
	"""
	Drain and return commands queued for the BTU Scheduler daemon.

	Used by the BTU Scheduler daemon in 'webserver' connectivity mode, which polls this
	endpoint instead of blocking on Redis RPC (see btu.btu_api.scheduler.SchedulerAPI).
	Commands pushed in poll mode omit 'response_key', since nothing blocks waiting for
	a synchronous acknowledgement.

	Uses LPOP to match the pop side of the direct-mode listener's BLPOP (both LPUSH
	is the producer side), so command ordering is identical between the two modes.
	"""
	import json

	from btu.btu_api.scheduler import REDIS_COMMAND_QUEUE, _get_redis_connection

	redis_conn = _get_redis_connection()
	commands = []
	while True:
		raw_message = redis_conn.lpop(REDIS_COMMAND_QUEUE)
		if raw_message is None:
			break
		try:
			command = json.loads(raw_message)
		except json.JSONDecodeError:
			frappe.logger("btu").warning("Discarding non-JSON scheduler command: %r", raw_message)
			continue
		commands.append(
			{
				"request_type": command.get("request_type", ""),
				"request_content": command.get("request_content", ""),
			}
		)
	return commands


@frappe.whitelist(methods=["POST", "PUT"])
def enqueue_for_next_available_worker(task_schedule_key: str) -> dict[str, int | str]:
	"""Enqueue a scheduled task when the BTU scheduler daemon fires its cron."""
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
	# The only way to avoid HTTP is a Frappe CLI that pickles jobs and enqueues via Redis.
	# It's just not worth the effort: the ERP Web Server should not be offline *anyway*

	response: dict[str, int | str] = {"has_errors": 0, "error_message": ""}

	try:
		import uuid

		from btu.btu_core.task_runner import on_btu_task_failure

		doc_task_schedule = frappe.get_doc("BTU Task Schedule", task_schedule_key, ignore_permissions=True)
		doc_task = frappe.get_doc("BTU Task", doc_task_schedule.task, ignore_permissions=True)

		existing_log = _task_has_active_log(doc_task.name)
		if existing_log:
			frappe.logger("btu").warning(
				"Task %s already has an In-Progress log (%s); skipping scheduled enqueue for schedule %s.",
				doc_task.name,
				existing_log,
				task_schedule_key,
			)
			return response

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
		response = {"has_errors": 1, "error_message": str(ex)}

	return response
