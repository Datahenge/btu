"""RQ failed-job admin helpers used from BTU Configuration."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils.background_jobs import get_redis_conn
from rq import Queue
from rq.job import Job
from temporal_lib.tlib_types import datetime_to_iso_string

from btu.utils.datetime import iso_string_to_date
from btu.utils.messaging import print_both


def rq_job_to_dict(rq_job: Job) -> dict[str, Any]:
	"""Build a display-friendly dictionary from an RQ Job."""
	return {
		"job_id": rq_job._id,  # pylint: disable=protected-access
		"created_at": datetime_to_iso_string(rq_job.created_at),
		"function_name": rq_job.func_name,
		"instance": rq_job._instance,  # pylint: disable=protected-access
		"description": rq_job.description,
		"origin": rq_job.origin,
		"datetime_enqueued": datetime_to_iso_string(rq_job.enqueued_at) if rq_job.enqueued_at else None,
		"datetime_started": datetime_to_iso_string(rq_job.started_at) if rq_job.started_at else None,
		"datetime_ended": datetime_to_iso_string(rq_job.ended_at) if rq_job.ended_at else None,
		"result": str(rq_job._result),  # pylint: disable=protected-access
		"execution_info": str(rq_job.exc_info),
		"timeout": rq_job.timeout,
		"result_ttl": rq_job.result_ttl,
		"failure_ttl": rq_job.failure_ttl,
		"ttl": rq_job.ttl,
		"worker_name": rq_job.worker_name,
		"status": rq_job._status,  # pylint: disable=protected-access
		"serializer": rq_job.serializer.__name__,
		"retries_left": rq_job.retries_left,
		"retry_intervals": rq_job.retry_intervals,
		"redis_server_version": rq_job.redis_server_version,
		"last_heartbeat": datetime_to_iso_string(rq_job.last_heartbeat),
	}


@frappe.whitelist()
def list_failed_jobs() -> None:
	"""List all failed RQ jobs across queues via frappe.msgprint."""
	conn = get_redis_conn()
	queues = Queue.all(conn)
	message = "Failed Jobs:<br><br>"

	for each_queue in queues:
		fail_registry = each_queue.failed_job_registry
		for job_id in fail_registry.get_job_ids():
			job = each_queue.fetch_job(job_id)
			if job:
				message += f"Queue={each_queue.name} : Job={job_id} : {job.description}<br>"
			else:
				message += f"Unable to retrieve details for Queue={each_queue.name} : Job={job_id}<br>"
	frappe.msgprint(message)


@frappe.whitelist()
def print_job_details(queue_name: str, job_id: str) -> None:
	"""Fetch and display details for a single RQ job."""
	conn = get_redis_conn()
	this_queue_key = "rq:queue:" + queue_name
	this_queue = Queue.from_queue_key(queue_key=this_queue_key, connection=conn)

	this_job = this_queue.fetch_job(job_id)
	if not this_job:
		frappe.msgprint(f"Unable to find RQ Job with identifier = '{job_id}' in queue named '{queue_name}'")
	else:
		rq_job_dict = rq_job_to_dict(this_job)
		prettier_string = json.dumps(rq_job_dict, indent=4)
		prettier_string = prettier_string.replace("\n", "<br>")
		frappe.msgprint(prettier_string)


@frappe.whitelist(methods=["DELETE"])
def remove_failed_jobs(date_from: str, date_to: str, wildcard_text: str | None = None) -> None:
	"""Delete failed RQ jobs matching date range and optional description filter."""
	date_from_parsed = iso_string_to_date(date_from)
	date_to_parsed = iso_string_to_date(date_to)

	conn = get_redis_conn()
	queues = Queue.all(conn)

	jobs_deleted = 0
	frappe.msgprint(
		f"Searching for Failed Jobs from {date_from_parsed} to {date_to_parsed}, with a description containing '{wildcard_text}' ..."
	)
	for each_queue in queues:
		fail_registry = each_queue.failed_job_registry
		failed_job_ids = fail_registry.get_job_ids()
		print_both(f"Total quantity of failed Jobs in queue '{each_queue.name}' = {len(failed_job_ids)}")
		for job_id in failed_job_ids:
			job = each_queue.fetch_job(job_id)
			if not job:
				frappe.msgprint(f"Unable to find details for Job with identifier = '{job_id}'")
				continue
			if (
				job.last_heartbeat
				and (job.last_heartbeat.date() >= date_from_parsed)
				and (job.last_heartbeat.date() <= date_to_parsed)
			):
				if not wildcard_text:
					fail_registry.remove(job, delete_job=True)
					jobs_deleted += 1
				elif job.description.find(wildcard_text) >= 0:
					fail_registry.remove(job, delete_job=True)
					jobs_deleted += 1

	if not jobs_deleted:
		print_both("No RQ Jobs found that match this criteria.")
	else:
		print_both(f"{jobs_deleted} jobs deleted from the Redis Queue.")
