# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see LICENSE.txt
#
# Inspired by and initially based on:
#   https://github.com/meeerp/jobtaskscheduler
#   Copyright (c) 2015, Codrotech Inc. and contributors
"""Background Tasks Unleashed: A Frappe Framework task scheduling app."""

from __future__ import annotations

import copy
import json
import os
import re
from datetime import date as DateType
from datetime import datetime as DateTimeType
from typing import Any

import frappe
import pytz
from dateutil.tz import tzutc
from frappe.utils.background_jobs import get_redis_conn
from rq import Queue
from rq.job import Job

NoneType = type(None)

__version__ = "15.1.0"


class Result:
	"""Success/failure result inspired by Rust's Result type."""

	def __init__(
		self,
		success: bool,
		message: str | dict[str, Any] | list[Any] | int | None,
		execution_time: float | None = None,
	) -> None:
		"""Initialize with success flag, message, and optional execution time in seconds."""
		if not isinstance(success, bool):
			raise TypeError("Result class argument 'success' must be a boolean.")
		if message:
			if isinstance(message, bool):
				message = "True" if message else "False"
			if not isinstance(message, (str, dict, list, int, NoneType)):
				raise TypeError(
					f"Result class argument 'message' must be a Python String, Integer, List, or Dictionary.  Found a type '{type(message)}' instead."
				)
		self.okay = success
		self.message = message or None
		self.execution_time = round(execution_time, 2) if execution_time else None

	def __bool__(self) -> bool:
		"""Return whether this result represents success."""
		return self.okay

	def as_json(self) -> dict[str, Any]:
		"""Return a dictionary representation of this result."""
		return {"okay": self.okay, "message": self.message, "execution_time": self.execution_time}

	def as_msgprint(self) -> str:
		"""Return an HTML-formatted message suitable for frappe.msgprint."""
		msg = f"Success: {self.okay}"
		if self.execution_time:
			msg += f"<br>Execution Time: {self.execution_time} seconds."
		msg += f"<br><br>Message: {self.message}"
		return msg


def validate_cron_string(cron_string: str, error_on_invalid: bool = False) -> bool:
	"""Return True if the string is a valid Unix cron expression."""
	minute_component = r"(?P<minute>\*(\/[0-5]?\d)?|[0-5]?\d)"
	hour_component = r"(?P<hour>\*|[01]?\d|2[0-3])"
	day_component = r"(?P<day>\*|0?[1-9]|[12]\d|3[01])"
	month_component = r"(?P<month>\*|0?[1-9]|1[012])"
	day_of_week_component = r"(?P<day_of_week>\*|[0-6](\-[0-6])?)"

	crontab_time_format_regex = re.compile(
		rf"{minute_component}\s+{hour_component}\s+{day_component}\s+{month_component}\s+{day_of_week_component}"
	)

	if crontab_time_format_regex.match(cron_string) is None:
		if error_on_invalid:
			raise ValueError(f"String '{cron_string}' is not a valid Unix cron string.")
		return False
	return True


def get_system_timezone() -> pytz.BaseTzInfo:
	"""Return the site timezone from Frappe System Settings."""
	system_time_zone = frappe.db.get_system_setting("time_zone")
	if not system_time_zone:
		raise ValueError("Please configure a Time Zone under 'System Settings'.")
	return pytz.timezone(system_time_zone)


def get_system_datetime_now() -> DateTimeType:
	"""Return the current datetime in the site's configured timezone."""
	utc_datetime = DateTimeType.now(tzutc())
	return utc_datetime.astimezone(get_system_timezone())


def make_datetime_naive(any_datetime: DateTimeType) -> DateTimeType:
	"""Strip timezone info from a timezone-aware datetime."""
	return any_datetime.replace(tzinfo=None)


def date_to_iso_string(any_date: DateType) -> str:
	"""Format a date as an ISO string (YYYY-MM-DD)."""
	if not isinstance(any_date, DateType):
		raise TypeError(f"Argument 'any_date' should have type 'datetime.date', not '{type(any_date)}'")
	return any_date.strftime("%Y-%m-%d")


def encode_slack_text(any_text: str) -> str:
	"""Encode characters required for Slack message formatting."""
	any_text = any_text.replace("&", "&amp;")
	any_text = any_text.replace("<", "&lt;")
	any_text = any_text.replace(">", "&gt;")
	any_text = any_text.replace("|", "%7C")
	return any_text


def is_env_var_set(variable_name: str) -> bool:
	"""Return True if an environment variable is set to 1."""
	if not variable_name:
		return False
	variable_value = os.environ.get(variable_name)
	if not variable_value:
		return False
	try:
		return int(variable_value) == 1
	except Exception:
		return False


def iso_string_to_date(any_string: str | DateTimeType | DateType) -> DateType:
	"""Convert an ISO date string or datetime into a date."""
	if isinstance(any_string, DateTimeType):
		return any_string.date()
	if isinstance(any_string, DateType):
		return any_string
	return DateTimeType.strptime(any_string, "%Y-%m-%d").date()


def rq_job_to_dict(rq_job: Job) -> dict[str, Any]:
	"""Build a display-friendly dictionary from an RQ Job."""
	result: dict[str, Any] = {
		"job_id": rq_job._id,  # pylint: disable=protected-access
		"created_at": date_to_iso_string(rq_job.created_at),
		"function_name": rq_job.func_name,
		"instance": rq_job._instance,  # pylint: disable=protected-access
		"description": rq_job.description,
		"origin": rq_job.origin,
		"datetime_enqueued": date_to_iso_string(rq_job.enqueued_at) if rq_job.enqueued_at else None,
		"datetime_started": date_to_iso_string(rq_job.started_at) if rq_job.started_at else None,
		"datetime_ended": date_to_iso_string(rq_job.ended_at) if rq_job.ended_at else None,
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
		"last_heartbeat": date_to_iso_string(rq_job.last_heartbeat),
	}
	return result


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
	date_from = iso_string_to_date(date_from)
	date_to = iso_string_to_date(date_to)

	conn = get_redis_conn()
	queues = Queue.all(conn)

	jobs_deleted = 0
	frappe.msgprint(
		f"Searching for Failed Jobs from {date_from} to {date_to}, with a description containing '{wildcard_text}' ..."
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
				and (job.last_heartbeat.date() >= date_from)
				and (job.last_heartbeat.date() <= date_to)
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


def dict_to_dateless_dict(some_object: object) -> object:
	"""Recursively convert dates in nested structures to ISO strings."""
	result = copy.deepcopy(some_object)

	if isinstance(result, DateType):
		return date_to_iso_string(some_object)

	if isinstance(some_object, list):
		return [dict_to_dateless_dict(v) for v in some_object]

	if isinstance(some_object, dict):
		new_dict: dict[Any, Any] = {}
		for key, value in some_object.items():
			new_dict[key] = dict_to_dateless_dict(value)
		return new_dict

	return some_object


def print_both(message: str) -> None:
	"""Print a message to both stdout and the Frappe browser UI."""
	frappe.msgprint(message)
	print(message)
