""" btu/btu_core/run_later.py """

# Standard Library
from datetime import datetime as DateTimeType, timedelta
import json
from zoneinfo import ZoneInfo

# Third Party
import redis

# Frappe Framework
import frappe

# Custom Apps
from temporal import datetime_to_iso_string, validate_datatype
from btu import get_system_datetime_now
from btu.btu_core.doctype.btu_task.btu_task import create_and_run_one_shot


NoneType = type(None)


def new_redis_queue_connection() -> redis.client.Redis:
	"""
	Return a connection to the Redis Queue database.
	NOTE: Frappe's connection doesn't decode responses, which is why I created this one instead.
	"""
	return redis.from_url(frappe.local.conf.redis_queue, decode_responses=True)


def test_one():
	"""
	CLI:  bench execute btu.btu_core.run_later.test_one
	"""
	now = get_system_datetime_now() + timedelta(seconds=180)

	enqueue_for_later(
		short_name="test_one",
		not_before_time=now,
		target_queue="default",
		path_to_function="btu.manual_tests.ping_with_wait",
		arguments={ "seconds_to_wait": 10 },
		unique_identifier="TEST-ONE"
	)


def exists_unique_identifier(unique_identifier: str) -> bool:
	"""
	CLI:
		bench execute btu.btu_core.run_later.exists_unique_identifier --args "['foo']"
	"""
	redis_conn = new_redis_queue_connection()
	match_criteria = "btu_scheduler:run_later:*"
	for each_key in redis_conn.scan_iter(match=match_criteria, count=100):
		if redis_conn.hget(each_key, "unique_identifier") == unique_identifier:
			return True
	return False


# pylint: disable=too-many-positional-arguments
def enqueue_for_later(short_name: str,
					  not_before_time: DateTimeType,
					  target_queue: str,
					  path_to_function: str,
					  arguments: dict,
					  unique_identifier: str = None):
	"""
	Option 1 of 2 for creating a BTU Run Later: write directly to Redis database.
	"""

	# TODO : validate path to function
	validate_datatype("arguments", arguments, (dict, NoneType), False)

	if unique_identifier and exists_unique_identifier(unique_identifier):
		print(f"Skipping; task with unique identifer '{unique_identifier}' is already pending future execution.")
		return  # do nothing, because the same task is already scheduled

	not_before_time_utc = not_before_time.astimezone(ZoneInfo("UTC"))
	not_before_timestamp_utc = int(not_before_time_utc.timestamp())  # round to nearest second

	uid = frappe.generate_hash(txt=short_name, length=30)
	new_key = f"btu_scheduler:run_later:{uid}"
	payload = {
		"uid": uid,
		"short_name": short_name,
		"target_queue": target_queue,
		"not_before_time": datetime_to_iso_string(not_before_time_utc),
		"not_before_timestamp": not_before_timestamp_utc,
		"path_to_function": path_to_function,
		"arguments": json.dumps(arguments) if arguments else "",
		"status": "pending",
		"unique_identifier": unique_identifier or ""
	}
	new_redis_queue_connection().hmset(new_key, payload)
	print(f"Added a new key to Redis Queue database: {new_key}")


def create_doc_run_later(comms_type: str,
                         hold_until_datetime: DateTimeType,
						 task_name: str,
						 task_function_path: str,
						 task_arguments,
						 redis_queue_name="short") -> "Document":
	"""
	Option 2 of 2 for creating a BTU Run Later: create a new Document 'BTU Run Later'
	"""
	doc_later = frappe.new_doc("BTU Run Later")
	doc_later.comms_type = comms_type
	doc_later.hold_until = hold_until_datetime
	doc_later.create_new_task = True
	doc_later.new_task_name = task_name
	doc_later.new_task_function_path = task_function_path
	if isinstance(task_arguments, dict):
		doc_later.btu_task_arguments = json.dumps(task_arguments)
	elif isinstance(task_arguments, str):
		doc_later.btu_task_arguments = task_arguments
	else:
		raise TypeError(f"task_arguments: {type(task_arguments)}")
	doc_later.redis_queue_name = redis_queue_name
	doc_later.save(ignore_permissions=True)
	return doc_later.name


def _acquire_poll_lock() -> bool:
	"""
	Acquire a session-scoped concurrency lock that survives frappe.db.commit().

	MariaDB GET_LOCK() and PostgreSQL pg_try_advisory_lock() are both session-scoped,
	not transaction-scoped. frappe.db.commit() releases row locks (SELECT FOR UPDATE)
	but has no effect on these — which is exactly what we need for a polling function
	that commits after each item it processes.

	Returns True if the lock was acquired, False if another instance already holds it.
	Auto-releases when the database session closes (process crash, connection drop, etc.).
	"""
	if frappe.db.db_type == "postgres":
		result = frappe.db.sql(
			"SELECT pg_try_advisory_lock(hashtext('btu_poll_for_ready_work')::bigint)"
		)[0][0]
		return bool(result)
	else:
		result = frappe.db.sql(
			"SELECT GET_LOCK('btu_poll_for_ready_work', 0)"
		)[0][0]
		return result == 1  # 1 = acquired, 0 = held by another session, NULL = error


def _release_poll_lock():
	"""Release the session-scoped concurrency lock acquired by _acquire_poll_lock()."""
	if frappe.db.db_type == "postgres":
		frappe.db.sql(
			"SELECT pg_advisory_unlock(hashtext('btu_poll_for_ready_work')::bigint)"
		)
	else:
		frappe.db.sql("SELECT RELEASE_LOCK('btu_poll_for_ready_work')")


@frappe.whitelist()
def poll_for_ready_work():
	"""
	This function should be run continously, at least every 1 minute.

	CLI:  bench execute btu.btu_core.run_later.poll_for_ready_work
	"""
	# 1. Loop through everything that's Ready to be executed.
	# 2. For each found, create a One-Shot BTU Task, and then immediately run via queue.

	if not _acquire_poll_lock():
		print("poll_for_ready_work: another instance is already running, skipping.")
		return

	try:
		_run_tasks_from_redis_database()
	except Exception as ex:
		print(f"Unhandled exception during poll_for_ready_work() : {ex}")
	print()
	try:
		_run_tasks_from_sql_database()
	except Exception as ex:
		print(f"Unhandled exception during poll_for_ready_work() : {ex}")
	print()
	identify_timeouts()
	_release_poll_lock()


def _run_tasks_from_redis_database():
	"""
	This is the simpler of the 2 possible 'run later' functions.
	It lacks features like:
	    * Advanced logging
		* Retry upon failure.
		* Relationships to other documents.
		* Persistence if the Redis database is truncated.
	"""
	utc_now = get_system_datetime_now().astimezone(ZoneInfo("UTC"))
	timestamp_now = int(utc_now.timestamp())

	redis_conn = new_redis_queue_connection()
	tasks_to_examine = list(redis_conn.scan_iter(match="btu_scheduler:run_later:*", count=100))  # generator to List
	print(f"Examining {len(tasks_to_examine)} one-shot Redis tasks, queued for future execution ...")

	for key in tasks_to_examine:

		data = redis_conn.hgetall(key)
		if data.get("status", "") != "pending":
			continue  # nothing to do here, the task is not in a "pending" status.

		if int(data.get("not_before_timestamp")) > timestamp_now:
			continue  # not-yet time to enqueue this task.

		arguments = data.get("arguments", {})
		if arguments:
			arguments = json.loads(arguments)

		try:
			print(f"Queuing task for execution: {data.get('uid')} ...")
			create_and_run_one_shot(
				short_description = data.get("short_name"),
				function_path = data.get("path_to_function"),
				arguments = arguments,
				queue_name = data.get("target_queue")
			)
			redis_conn.delete(key)  # remove the key from the "To Do" list
		except Exception as ex:
			print(f"ERROR in _run_tasks_from_redis_database() : {ex}.  Moving on to next Redis key ...")

	print("Okay, finished polling all the 'pending' keys")
	frappe.db.commit()


def _run_tasks_from_sql_database(disable_enqueue=False):
	"""
	This is a more-advanced function with better logging, retry capability, and more.
	"""

	datetime_now = get_system_datetime_now()
	filters = {
		"hold_until": ["<=", datetime_now ],
		"execution_status": 'Pending Future'
	}
	tasks_to_examine = frappe.get_list("BTU Run Later", filters, pluck="name")
	print(f"Examining {len(tasks_to_examine)} one-shot SQL tasks, queued for future execution ...")

	for run_later_key in tasks_to_examine:

		try:
			doc_run_later = frappe.get_doc("BTU Run Later", run_later_key, for_update=True)

			if doc_run_later.last_attempt and not doc_run_later.can_retry():
				doc_run_later.execution_status = 'Abandoned'
				doc_run_later.save()
				frappe.db.commit()
				continue

			# bench execute btu.btu_core.wrapped_function.enqueued_run_later_instance --kwargs "{'run_later_key': 'BTU-RL-20250408-134209'}"
			if disable_enqueue:
				from btu.btu_core.wrapped_function import enqueued_run_later_instance
				enqueued_run_later_instance(run_later_key=doc_run_later.name)
			else:
				# Enqueue the work:
				frappe.enqueue(
					method="btu.btu_core.wrapped_function.enqueued_run_later_instance",
					queue=doc_run_later.redis_queue_name or "short",
					timeout="3600",  # one hour
					run_later_key=doc_run_later.name
				)

			# Then update and release the lock
			doc_run_later.execution_status = 'In-Progress'
			doc_run_later.last_attempt = datetime_now
			doc_run_later.save()
			frappe.db.commit()
		except Exception as ex:
			frappe.db.rollback()
			print(f"ERROR in _run_tasks_from_sql_database() : {ex}.  Moving on to next SQL key ...")

	print("_run_tasks_from_sql_database() : function concluded.")


def identify_timeouts():
	"""
	Find any 'BTU Run Later' that have been running for too long, and mark them Failed.
	How long is too long?  Start Time = more than 1 hour ago.
	"""
	one_hour_ago = get_system_datetime_now() - timedelta(hours=1)

	filters = {
		"execution_status": 'In-Progress',
		"last_attempt": [ "<=", one_hour_ago ]
	}
	tasks_to_examine = frappe.get_list("BTU Run Later", filters, pluck="name")
	for run_later_key in tasks_to_examine:
		try:
			doc_run_later = frappe.get_doc("BTU Run Later", run_later_key, for_update=True)
			doc_run_later.last_result = 'Timeout'

			if not doc_run_later.can_retry():
				doc_run_later.execution_status = 'Abandoned'
				doc_run_later.save()
			else:
				doc_run_later.execution_status = 'Pending Future'
				doc_run_later.save()
				frappe.db.commit()
			frappe.db.commit()
		except Exception as ex:
			print(f"identify_timeouts() : {ex}")
