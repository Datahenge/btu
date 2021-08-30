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
from btu import validate_cron_string, scheduler as btu_scheduler
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


def check_minutes(minute):
	if not minute or not 0 <= minute < 60:
		frappe.throw(_("Minute value must be between 0 and 59"))

def check_hours(hour):
	if not hour or not hour.isdigit() or not 0 <= int(hour) < 24:
		frappe.throw(_("Hour value must be between 0 and 23"))

def check_day_of_week(day_of_week):

	if not day_of_week or day_of_week is None:
		frappe.throw(_("Please select a day of the week"))

def check_day_of_month(run_frequency, day, month=None):

	if run_frequency == "Monthly" and not day:
		frappe.throw(_("Please select a day of the month"))

	elif run_frequency == "Yearly":
		if day and month:
			m = {value: key for key, value in enumerate(calendar.month_abbr)}
			last = monthrange(datetime.now().year,
							  m.get(str(month).title()))[1]
			if int(day) > last:
				frappe.throw(
					_("Day value for {0} must be between 1 and {1}").format(month, last))
		else:
			frappe.throw(_("Please select a day of the week and a month"))

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
def redis_rebuild_all_schedules():
	import time as _time

	# The following code kickstarts the BTU Scheduled Tasks during web server startup.
	#if not hasattr(_frappe.local.flags, 'btu_jobs_loaded'):
	#	print("Creating a new flag 'frappe.local.flags.btu_jobs_loaded'")
	#	_frappe.local.flags.btu_jobs_loaded = None

	# TODO: I have no way of knowing whether this already happened when the Web Server booted up.
	# Load jobs for the first time after server startup.
	print(f"Value of 'frappe.local.flags.btu_jobs_loaded' = {frappe.local.flags.btu_jobs_loaded}")
	_time.sleep(5)
	filters = { "enabled": True }
	job_schedules = frappe.db.get_all("BTU Task Schedule", filters=filters, pluck='name')
	for name in job_schedules:
		doc_schedule = frappe.get_doc("BTU Task Schedule", name)
		doc_schedule.validate()
		doc_schedule.reschedule_job()
		print(f"BTU Startup: Task Schedule '{doc_schedule.name}' stored in Redis.")
