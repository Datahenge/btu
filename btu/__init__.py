# -*- coding: utf-8 -*-
#
# Background Tasks Unleashed: A Frappe Framework task scheduling App.
#
# Copyright (c) 2022, Datahenge LLC and contributors
# For license information, please see LICENSE.txt
#
# Inspired by and initially based on:
#   https://github.com/meeerp/jobtaskscheduler
#   Copyright (c) 2015, Codrotech Inc. and contributors

from datetime import datetime as DateTimeType # standard Python library
from datetime import date as DateType
import json
import os  # standard Python library
import re  # standard Python library

from dateutil import parser
from dateutil.parser._parser import ParserError
from dateutil.tz import tzutc
import pytz  # https://pypi.org/project/pytz/
from rq import Queue

import frappe
from frappe.utils.background_jobs import get_redis_conn

__version__ = '0.8.0'


class Result():
	"""
	Inspired by Rust's Result type which has Ok(None) or Error(message)
	Functions can return an instance of this class, instead of True/False or None.
	"""
	def __init__(self, success, message, execution_time=None):
		"""
		Arguments:
			success: True/False that the function succeeded.
			message: Text explaining the success message.
			execution_time:  (Optional) How long the function took to complete, in seconds.
		"""
		if not isinstance(success, bool):
			raise TypeError("Result class argument 'success' must be a boolean.")
		if message:
			if not isinstance(message, (str, dict, list)):
				raise TypeError(f"Result class argument 'message' must be a Python String, List, or Dictionary.  Found value '{message}' instead.")
		self.okay = success
		self.message = message or None
		self.execution_time = round(execution_time,2) if execution_time else None

	def __bool__(self):
		"""
		A useful overload.  For example: 'if Result():'
		"""
		return self.okay

	def as_json(self):
		"""
		Dictionary representation of the class instance.
		"""
		return {
		    "okay": self.okay,
		    "message": self.message,
		    "execution_time": self.execution_time
		}

	def as_msgprint(self):
		msg = f"Success: {self.okay}"
		msg += f"<br>Execution Time: {self.execution_time} seconds."
		msg += f"<br><br>Message: {self.message}"
		return msg


# Some date and time functions are included below.
#
#   * It's tempting to use my own Temporal App for handling Date and Time functions.
#   * But for now, I don't want to create a cross-dependency with another App.


def validate_cron_string(cron_string, error_on_invalid=False):
	"""
	Validate that a string is a Unix cron string.
	"""

	# Note: This is also a Temporal function, but I'm trying to avoid making Temporal a dependency of BTU.
	minute_component = r"(?P<minute>\*(\/[0-5]?\d)?|[0-5]?\d)"
	hour_component = r"(?P<hour>\*|[01]?\d|2[0-3])"
	day_component = r"(?P<day>\*|0?[1-9]|[12]\d|3[01])"
	month_component = r"(?P<month>\*|0?[1-9]|1[012])"
	day_of_week_component = r"(?P<day_of_week>\*|[0-6](\-[0-6])?)"  # end of str.format()

	crontab_time_format_regex = re.compile(
		rf"{minute_component}\s+{hour_component}\s+{day_component}\s+{month_component}\s+{day_of_week_component}"
	)  # end of re.compile()

	if crontab_time_format_regex.match(cron_string) is None:
		if error_on_invalid:
			raise Exception(f"String '{cron_string}' is not a valid Unix cron string.")
		return False
	return True


def get_system_timezone():
	"""
	Returns the Time Zone of the Site.
	"""
	system_time_zone = frappe.db.get_system_setting('time_zone')
	if not system_time_zone:
		raise Exception("Please configure a Time Zone under 'System Settings'.")
	return pytz.timezone(system_time_zone)


def get_system_datetime_now():
	"""
	Return a timezone-aware DateTime value, using the Frappe webserver's System Settings.
	"""
	utc_datetime = DateTimeType.now(tzutc())  # Get the current UTC datetime.
	return utc_datetime.astimezone( get_system_timezone())  # Convert to the site's Time Zone:


def make_datetime_naive(any_datetime):
	"""
	Takes a timezone-aware datetime, and makes it naive.
	Useful because Frappe is not storing timezone-aware datetimes in MySQL.
	"""
	return any_datetime.replace(tzinfo=None)


def is_env_var_set(variable_name):
	"""
	Returns true if an Environment Variable is set to 1.
	"""
	if not variable_name:
		return False
	variable_value = os.environ.get(variable_name)
	if not variable_value:
		return False
	try:
		return int(variable_value) == 1
	except Exception:
		return False


def dprint(msg, check_env=None, force=None):
	"""
	A print() that only prints when an environment variable is set.
	Very useful for conditional printing, depending on whether you want to debug code, or not.
	"""
	if force:
		print(msg)
	elif is_env_var_set(check_env):
		print(msg)


def date_to_iso_string(any_date):
	"""
	Given a date, create an ISO String.  For example, 2021-12-26.
	"""
	if not isinstance(any_date, DateType):
		raise Exception(f"Argument 'any_date' should have type 'datetime.date', not '{type(any_date)}'")
	return any_date.strftime("%Y-%m-%d")


def iso_string_to_date(any_string):
	"""
	Converts an ISO string into a datetime.date
	"""
	if isinstance(any_string, DateTimeType):
		return any_string.date()
	elif isinstance(any_string, DateType):
		return any_string
	return parser.parse(any_string).date()


def rq_job_to_dict(rq_job):
	"""
	Given a Python RQ job, create a Dictionary of values that is display-friendly.
	"""
	# Ignoring these fields:  data

	result = {
		"job_id": rq_job._id,  # pylint: disable=protected-access
		"created_at": date_to_iso_string(rq_job.created_at),
		"function_name": rq_job.func_name,
		"instance": rq_job._instance,  # pylint: disable=protected-access
		# "args": rq_job._args,  # pylint: disable=protected-access
		#"kwargs": rq_job._kwargs,  # pylint: disable=protected-access
		"description": rq_job.description,
		"origin": rq_job.origin,
		"datetime_enqueued": date_to_iso_string(rq_job.enqueued_at) if rq_job.enqueued_at else None,
		"datetime_started": date_to_iso_string(rq_job.started_at) if rq_job.started_at else None,
		"datetime_ended": date_to_iso_string(rq_job.ended_at) if rq_job.ended_at else None,
		"result": str(rq_job._result),  # pylint: disable=protected-access
		"execution_info": str(rq_job.exc_info),  # NOTE: This can be a very large amount of string text.
		"timeout":	rq_job.timeout,
		"result_ttl": rq_job.result_ttl,
		"failure_ttl": rq_job.failure_ttl,
		"ttl": rq_job.ttl,
		"worker_name":	rq_job.worker_name,
		"status":	rq_job._status,  # pylint: disable=protected-access
		#"dependency_ids": rq_job._dependency_ids,  # pylint: disable=protected-access
		#"meta":	rq_job.meta,
		"serializer":	rq_job.serializer.__name__,
		"retries_left":	rq_job.retries_left,
		"retry_intervals":	rq_job.retry_intervals,
		"redis_server_version":	rq_job.redis_server_version,
		"last_heartbeat":  date_to_iso_string(rq_job.last_heartbeat),
	}
	#for each_key, each_value in rq_job_dict.items():
	#	print(f"key = {each_key}, value type = {type(each_value)}")
	return result


@frappe.whitelist()
def list_failed_jobs():
	"""
	List all RQ Jobs that are marked as fail inside a queue.
	"""
	conn = get_redis_conn()
	queues = Queue.all(conn)
	failed_jobs = []
	message = "Failed Jobs:<br><br>"

	for each_queue in queues:
		fail_registry = each_queue.failed_job_registry
		for job_id in fail_registry.get_job_ids():
			job = each_queue.fetch_job(job_id)
			if job:
				failed_jobs.append(job_id)
				message += f"Queue={each_queue.name} : Job={job_id} : {job.description}<br>"
			else:
				message += f"Unable to retrieve details for Queue={each_queue.name} : Job={job_id}<br>"
	frappe.msgprint(message)

@frappe.whitelist()
def print_job_details(queue_name, job_id):
	"""
	Given the name of a Queue and Job, fetch details about the Job.
	"""
	conn = get_redis_conn()
	this_queue_key = "rq:queue:" + queue_name
	this_queue = Queue.from_queue_key(queue_key=this_queue_key, connection=conn)

	this_job = this_queue.fetch_job(job_id)
	if not this_job:
		frappe.msgprint(f"Unable to find RQ Job with identifier = '{job_id}' in queue named '{queue_name}'")
	else:
		rq_job_dict = rq_job_to_dict(this_job)
		#for each_key, each_value in rq_job_dict.items():
		#	print(f"key = {each_key}, value type = {type(each_value)}")
		prettier_string = json.dumps(rq_job_dict, indent=4)
		prettier_string = prettier_string.replace("\n", "<br>")
		# print(prettier_string)
		frappe.msgprint(prettier_string)

@frappe.whitelist(methods=['DELETE'])
def remove_failed_jobs(date_from, date_to, wildcard_text=None):
	"""
	Delete RQ Jobs from the Redis database, with filters for dates and text.
	"""

	# Convert JS arguments to dates:
	date_from = iso_string_to_date(date_from)
	date_to = iso_string_to_date(date_to)

	conn = get_redis_conn()
	queues = Queue.all(conn)

	jobs_deleted = 0
	frappe.msgprint(f"Searching for Failed Jobs from {date_from} to {date_to}, with a description containing '{wildcard_text}' ...")
	for each_queue in queues:
		fail_registry = each_queue.failed_job_registry
		for job_id in fail_registry.get_job_ids():
			# Get the details about this particular Job.
			job = each_queue.fetch_job(job_id)
			if not job:
				frappe.msgprint(f"Unable to find details for Job with identifier = '{job_id}'")
				continue
			if job.last_heartbeat and (job.last_heartbeat.date() >= date_from) and (job.last_heartbeat.date() <= date_to):
				# Delete this job:
				if not wildcard_text:
					fail_registry.remove(job, delete_job=True)
					jobs_deleted += 1
				else:
					if job.description.find(wildcard_text) >= 0:
						fail_registry.remove(job, delete_job=True)
						jobs_deleted += 1

	if not jobs_deleted:
		frappe.msgprint("No RQ Jobs found that match this criteria.")
	else:
		frappe.msgprint(f"{jobs_deleted} jobs deleted from the Redis Queue.")
