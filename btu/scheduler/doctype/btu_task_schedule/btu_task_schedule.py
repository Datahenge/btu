# -*- coding: utf-8 -*-
# Copyright (c) 2015, Codrotech Inc. and contributors
#
# Copyright (c) 2021, Datahenge LLC and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import calendar
from calendar import monthrange, timegm
from datetime import datetime
from time import gmtime, localtime, mktime

# Third Party
# from rq_scheduler import Scheduler
import cron_descriptor  # get_description, ExpressionDescriptor

# Frappe
import frappe
from frappe import _
from frappe.model.document import Document

# BTU
from btu import ( validate_cron_string, scheduler as btu_scheduler, Result)
from btu.task_runner import TaskRunner


class BTUTaskSchedule(Document):

	def on_trash(self):
		"""
		After deleting this Task Schedule, delete the corresponding Redis Job.
		"""
		if self.redis_job_id:
			btu_scheduler.redis_cancel_by_queue_job_id(self.redis_job_id)

	def before_validate(self):
		self.task_description = self.task_doc().desc_short
		# Clear fields that are not relevant for this schedule type.
		if self.run_frequency == "Cron Style":
			self.day_of_week = None
			self.day_of_month = None
			self.month = None
			self.hour = None
			self.minute = None
		if self.run_frequency == "Hourly":
			self.day_of_week = None
			self.day_of_month = None
			self.month = None
			self.hour = None
		if self.run_frequency == "Daily":
			self.day_of_week = None
			self.day_of_month = None
			self.month = None

	def validate(self):
		if self.run_frequency == "Hourly":
			check_minutes(self.minute)
			self.cron_string = schedule_to_cron_string(self)

		elif self.run_frequency == "Daily":
			check_hours(self.hour)
			check_minutes(self.minute)
			self.cron_string = schedule_to_cron_string(self)

		elif self.run_frequency == "Weekly":
			check_day_of_week(self.day_of_week)
			check_hours(self.hour)
			check_minutes(self.minute)
			self.cron_string = schedule_to_cron_string(self)

		elif self.run_frequency == "Monthly":
			check_day_of_month(self.run_frequency, self.day_of_month)
			check_hours(self.hour)
			check_minutes(self.minute)
			self.cron_string = schedule_to_cron_string(self)

		elif self.run_frequency == "Yearly":
			check_day_of_month(self.run_frequency, self.day_of_month, self.month)
			check_hours(self.hour)
			check_minutes(self.minute)
			self.cron_string = schedule_to_cron_string(self)

		elif self.run_frequency == "Cron Style":
			validate_cron_string(str(self.cron_string))

	def before_save(self):

		# Create a friendly, human-readable description based on the cron string:
		self.schedule_description = cron_descriptor.get_description(self.cron_string)
		if self.enabled:
			self.reschedule_task()
		elif self.redis_job_id:
			self.cancel_schedule()

	def reschedule_task(self, autosave=False):
		"""
		Rewrite this BTU Task Schedule to the Redis Queue.
		"""
		# 1. Cancel the current Task Schedule (if it exists) in Redis Queue.
		btu_scheduler.redis_cancel_by_queue_job_id(self.redis_job_id)

		# 2. Schedule a new RQ job:
		task_runner = TaskRunner(self.task, site_name=frappe.local.site, enable_debug_mode=True)
		task_runner.redis_job_id = self.name  # This makes it easier to find the RQ Job, by making Job = Schedule's name

		new_job_id = task_runner.schedule_task_in_redis(cron_string=self.cron_string, queue_name=self.queue_name)

		if not new_job_id:
			raise Exception("Failure to get new Job ID from Redis.")
		# 3. Display message to User on on success.
		frappe.msgprint(f"Task {self.task} rescheduled in Redis." +
		                 f"\nFrequency: {self.schedule_description}" +
						 "\nRedis Job: " + new_job_id)
		self.redis_job_id = new_job_id
		if autosave:
			self.save()

	def cancel_schedule(self):
		# Referenced By:  before_save()
		btu_scheduler.redis_cancel_by_queue_job_id(self.redis_job_id)
		self.redis_job_id = ""
		frappe.msgprint("Job disabled")

	def task_doc(self):
		return frappe.get_doc("BTU Task", self.task)

	@frappe.whitelist()
	def get_last_job_results(self):
		import zlib
		from frappe.utils.background_jobs import get_redis_conn
		conn = get_redis_conn()
		# conn.type('rq:job:TS000001')
		# conn.hkeys('rq:job:TS000001')

		try:
			# job_data =  conn.hgetall(f'rq:job:{self.redis_job_id}').decode('utf-8')
			# frappe.msgprint(job_data)
			job_status =  conn.hget(f'rq:job:{self.redis_job_id}', 'status').decode('utf-8')
		except Exception:
			frappe.msgprint(f"No job information is available for Job {self.redis_job_id}")
			return

		if job_status == 'finished':
			frappe.msgprint(f"Job {self.redis_job_id} completed successfully.")
			return
		frappe.msgprint(f"Job status = {job_status}")
		compressed_data = conn.hget(f'rq:job:{self.redis_job_id}', 'exc_info')
		if not compressed_data:
			frappe.msgprint("No results available; job may not have been processed yet.")
		else:
			frappe.msgprint(zlib.decompress(compressed_data))

	@frappe.whitelist()
	def button_test_email_via_log(self):
		"""
		Write an entry to the BTU Task Log, which should trigger emails.  Then delete the entry.
		"""
		from btu.scheduler.doctype.btu_task_log.btu_task_log import write_log_for_task  # late import to avoid circular reference
		if not self.email_recipients:
			frappe.msgprint("Task Schedule does not have any Email Recipients; no emails can be tested.")
			return

		try:
			log_key = write_log_for_task(self.task, result=Result(True,"Email Test"), schedule_id=self.name)
			frappe.db.commit()
			frappe.delete_doc("BTU Task Log", log_key)
			frappe.msgprint("Log written; emails should arrive shortly.")

		except Exception as ex:
			frappe.msgprint(f"Errors while testing Task Emails: {ex}")
			raise ex

# ----------------
# STATIC FUNCTIONS
# ----------------
def check_minutes(minute):
	if not minute or not 0 <= minute < 60:
		raise ValueError(_("Minute value must be between 0 and 59"))

def check_hours(hour):
	if not hour or not hour.isdigit() or not 0 <= int(hour) < 24:
		raise ValueError(_("Hour value must be between 0 and 23"))

def check_day_of_week(day_of_week):

	if not day_of_week or day_of_week is None:
		raise ValueError(_("Please select a day of the week"))

def check_day_of_month(run_frequency, day, month=None):

	if run_frequency == "Monthly" and not day:
		raise ValueError(_("Please select a day of the month"))

	elif run_frequency == "Yearly":
		if day and month:
			m = {value: key for key, value in enumerate(calendar.month_abbr)}
			last = monthrange(datetime.now().year,
							  m.get(str(month).title()))[1]
			if int(day) > last:
				raise ValueError(
					_("Day value for {0} must be between 1 and {1}").format(month, last))
		else:
			raise ValueError(_("Please select a day of the week and a month"))

def schedule_to_cron_string(doc_schedule):
	"""
	Purpose of this function is to convert individual SQL columns (Hour, Day, Minute, etc.)
	into a valid Unix cron string.

	Input:   A BTU Task Schedule document class.
	Output:   A Unix cron string.
	"""

	def get_utc_time_diff():
		current_time = localtime()
		return (timegm(current_time) - timegm(gmtime(mktime(current_time)))) / 3600


	if not isinstance(doc_schedule, BTUTaskSchedule):
		raise ValueError("Function argument 'doc_schedule' should be a BTU Task Schedule document.")

	if doc_schedule.run_frequency == 'Cron Style':
		return doc_schedule.cron_string

	cron = [None] * 5
	cron[0] = "*" if doc_schedule.minute is None else str(doc_schedule.minute)
	cron[1] = "*" if doc_schedule.hour is None else str(
		int(doc_schedule.hour) - get_utc_time_diff())
	cron[2] = "*" if doc_schedule.day_of_month is None else str(doc_schedule.day_of_month)
	cron[3] = "*" if doc_schedule.month is None else doc_schedule.month
	cron[4] = "*" if doc_schedule.day_of_week is None else doc_schedule.day_of_week[:3]

	result = " ".join(cron)

	validate_cron_string(result, error_on_invalid=True)
	return result


@frappe.whitelist()
def resubmit_all_task_schedules():
	import time as _time

	# The following code kickstarts the BTU Scheduled Tasks during web server startup.
	if not hasattr(frappe.local.flags, 'btu_jobs_loaded'):
		frappe.local.flags.btu_jobs_loaded = False
		message = "Creating a new flag 'frappe.local.flags.btu_jobs_loaded'"
		print(message)

	# Load jobs for the first time after server startup.
	print(f"Value of 'frappe.local.flags.btu_jobs_loaded' = {frappe.local.flags.btu_jobs_loaded}")
	_time.sleep(5)

	if frappe.local.flags.btu_jobs_loaded is None:
		frappe.local.flags.btu_jobs_loaded = False

	if frappe.local.flags.btu_jobs_loaded is True:
		return

	filters = { "enabled": True }
	job_schedules = frappe.db.get_all("BTU Task Schedule", filters=filters, pluck='name')

	for name in job_schedules:
		try:
			doc_schedule = frappe.get_doc("BTU Task Schedule", name)
			doc_schedule.validate()
			doc_schedule.reschedule_task()
			print(f"BTU Startup: Task Schedule '{doc_schedule.name}' stored in Redis.")
		except Exception as ex:
			print(f"ERROR: Task {doc_schedule.name} : {ex}")
			doc_schedule.enabled = False
			doc_schedule.save()

	frappe.local.flags.btu_jobs_loaded = True
