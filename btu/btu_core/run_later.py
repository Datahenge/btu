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
	now = get_system_datetime_now() + timedelta(seconds=120)

	enqueue_for_later(
		short_name="test_one",
		not_before_time=now,
		target_queue="default",
		path_to_function="btu.manual_tests.ping_with_wait",
		arguments={ "seconds_to_wait": 10 }
	)


def enqueue_for_later(short_name: str,
					  not_before_time: DateTimeType,
					  target_queue: str,
					  path_to_function: str,
					  arguments: dict):

	# TODO : validate path to function
	validate_datatype("arguments", arguments, (dict, NoneType), False)

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
		"status": "pending"
	}
	new_redis_queue_connection().hmset(new_key, payload)
	print(f"Added a new key to Redis Queue database: {new_key}")


def lock_polling_task():
	"""
	Lock the BTU Task that is doing all the polling.
	This should help prevent 2 instances of the poll from running simultaneously.
	"""

	sql_query = """ SELECT name FROM `tabBTU Task` WHERE function_string = 'btu.btu_core.run_later.poll_for_ready_work' LIMIT 1; """
	sql_results = frappe.db.sql(sql_query)
	if (not sql_results) or (not sql_results[0]) or (not sql_results[0][0]):
		return

	btu_task_key = sql_results[0][0]
	print(f"Locking down BTU Task '{btu_task_key}' FOR UPDATE ...")
	sql_query = """ SELECT * FROM `tabBTU Task` WHERE name = %(btu_task_key)s FOR UPDATE; """
	frappe.db.sql(sql_query, values={"btu_task_key": btu_task_key}, as_dict=True)
	print("...row is now locked.")


def poll_for_ready_work():
	"""
	This function should be run continously, at least every 1 minute.

	CLI:  bench execute btu.btu_core.run_later.poll_for_ready_work
	"""
	# 1. Loop through everything that's Ready to be executed.
	# 2. For each found, create a One-Shot BTU Task, and then immediately run via queue.

	frappe.db.begin()
	lock_polling_task()  # prevent another instance of this function from running at the same time, to avoid double-enqueuing.

	redis_conn = new_redis_queue_connection()
	match_criteria = "btu_scheduler:run_later:*"
	tasks_to_examine = list(redis_conn.scan_iter(match=match_criteria, count=100))  # generator to List

	utc_now = get_system_datetime_now().astimezone(ZoneInfo("UTC"))
	timestamp_now = int(utc_now.timestamp())

	print(f"Examining {len(tasks_to_examine)} one-shot tasks, queued for future execution ...")
	for key in tasks_to_examine:

		data = redis_conn.hgetall(key)
		if data.get("status", "") != "pending":
			continue  # nothing to do here, the task is not in a "pending" status.

		if int(data.get("not_before_timestamp")) > timestamp_now:
			continue  # not time to enqueue this task yet

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
			# redis_conn.hset(key, "status", "enqueued")
		except Exception as ex:
			print("ERROR in poll_for_ready_work() : {ex}")
			raise ex

	print("Okay, finished polling all the 'pending' keys")
	frappe.db.commit()
