""" btu.btu_core """

# Third Party
from rq_scheduler import Scheduler
# Frappe
import frappe


def get_redis_queue_conn():
	from frappe.utils.background_jobs import get_redis_conn
	return get_redis_conn()


def redis_cancel_by_queue_job_id(queue_job_id):
	# Note: The Redis Queue's Job ID is currently the same as BTU Task Scheduler ID.
	#       This is a design decision; not a Redis Queue requirement.
	if not queue_job_id:
		return
	scheduler = Scheduler(connection=get_redis_queue_conn())
	if queue_job_id not in scheduler:
		return
	scheduler.cancel(queue_job_id)
	print(f"Deleted Redis Job ID '{queue_job_id}' from queue.")


def schedule_job_in_redis(path_to_function, cron_string, queue_name,
                          description, job_id, kwarg_dict):
	"""
	For official documentation, see this article:
	    https://pypi.org/project/rq-scheduler/
	"""

	# Note: If 'path_to_function' is not a TaskRunner.function_wrapper(),
	#       then you will not see details in Task Schedule Log.

	if not queue_name:
		raise Exception("Cannot schedule a job without a valid 'queue_name'")

	scheduler = Scheduler(connection=get_redis_queue_conn())

	job = scheduler.cron(
		id=job_id,
		description=description,
		cron_string=cron_string,  # A cron string (e.g. "0 0 * * 0")
		func=path_to_function,  # Function to be queued
		# args=[arg1, arg2],  # Arguments passed into function when executed
		kwargs=kwarg_dict,  # Keyword arguments passed into function when executed
		repeat=None,  # Repeat this number of times (None means repeat forever)
		queue_name=queue_name,  # In which queue the job should be put in
		meta={'app': 'Background Tasks Unleashed'},        # Arbitrary pickleable data on the job itself.
		use_local_timezone=False,    # Interpret hours in the local timezone
		timeout="1h"
	)
	if not job.get_id():
		raise Exception("ERROR: Job is not yielding an ID.")

	print(" ** Added job to Redis Queue '" + queue_name + "' with Job ID: " + job.get_id() + " at " + cron_string)
	return job.get_id()


@frappe.whitelist()
def are_tasks_scheduled():
	"""
	Called by hooks.py
	Callable by REST API at any time.
	"""
	return frappe.local.flags.btu_tasks_scheduled or False


@frappe.whitelist()
def mark_tasks_as_scheduled():
	"""
	Once the worker has submitted all Tasks as Redis jobs, set this flag on the webserver.
	"""
	frappe.local.flags.btu_tasks_scheduled = True
