"""Manual test helpers for Bench Console and Bench Execute."""

import frappe

from btu.logging import logger


@frappe.whitelist()
def ping_with_wait(seconds_to_wait: int | str) -> str:
	"""Wait N seconds, then return a pong message."""
	import time

	if not seconds_to_wait:
		raise ValueError("Function argument 'seconds_to_wait' is mandatory and has no default.")
	seconds_to_wait = int(seconds_to_wait)
	if seconds_to_wait < 0:
		raise ValueError("Argument 'seconds_to_wait' cannot be less than 0.")
	print(f"Waiting {seconds_to_wait} seconds before replying...")
	time.sleep(seconds_to_wait)
	print("Pong!")
	return "I have sent a 'pong'; this function is concluded."


@frappe.whitelist()
def send_hello_email_to_user(debug: bool = False) -> str:
	"""Send a test email to the current session user (``bench execute btu.manual_tests.send_hello_email_to_user``)."""
	import datetime
	import inspect

	from btu.btu_core.btu_email import Emailer

	caller_name = inspect.stack()[2][3]
	if caller_name == "execute_cmd":
		caller_name = "JavaScript on a web page."
	if caller_name == "<lambda>":
		caller_name = "JavaScript on a web page."

	# Load the session User's document, to acquire their email address.
	user_doc = frappe.get_doc("User", frappe.session.user)
	if not user_doc.email:
		frappe.throw(
			f"Current user '{user_doc.name}' does not have an Email Address associated with their account."
		)

	datetime_now_string = datetime.datetime.now().strftime("%A, %B %d %Y, %-I:%M %p")

	# Construct a small message Body for the email.
	message_body = f"Hello, {user_doc.full_name}."
	message_body += "\n\nThis email was initiated by Python function 'send_hello_email_to_user()'"
	message_body += f"\n\n* Function caller is '{caller_name}'"
	message_body += f"\n* Current server time is {datetime_now_string}"
	message_body += "\n\n--------\n"

	if debug:
		print(f"Sending test email to address '{user_doc.email}'")
	frappe.msgprint(f"Sending test email to address '{user_doc.email}' ...")

	subject = f"From BTU: Hello {user_doc.full_name}"

	Emailer(subject=subject, body=message_body, sender=None, emailto_list=user_doc.email).send()

	return "Exiting function 'send_hello_email_to_user()'.  If successful, an email will arrive soon."


def ping_now() -> None:
	"""Print ``pong`` (used as a minimal RQ worker target)."""
	print("pong")


def test_rq_workers1() -> None:
	"""Enqueue ``ping_now`` and print the job handle (``bench execute btu.manual_tests.test_rq_workers1``)."""
	result = frappe.enqueue(method="btu.manual_tests.ping_now", queue="default", job_name="test_rq_workers1")
	print(result)


@frappe.whitelist()
def test_rq_workers2() -> None:
	"""Enqueue ``send_hello_email_to_user`` on the short queue (``bench execute btu.manual_tests.test_rq_workers2``)."""
	frappe.enqueue(
		method="btu.manual_tests.send_hello_email_to_user",
		queue="short",
	)
	print("Submitted a function 'send_hello_email_to_user()' to the Redis Queue.")


def _find_or_create_ping_task() -> "frappe.Document":
	"""Find or create the ``ping_with_wait`` BTU Task document."""
	filters = {"function_string": "btu.manual_tests.ping_with_wait"}
	task_names = frappe.get_list("BTU Task", filters=filters, pluck="name")
	if task_names:
		task_doc = frappe.get_doc("BTU Task", task_names[0])
	else:
		# Could not find the 'ping_with_wait' Task; create it:
		task_doc = frappe.new_doc("BTU Task")
		task_doc.desc_short = "Ping after N seconds"
		task_doc.desc_long = 'Wait N seconds, then return a "pong" to the caller.'
		task_doc.function_string = "btu.manual_tests.ping_with_wait"
		task_doc.save()
		task_doc.submit()
		frappe.db.commit()

	return task_doc


def test_taskrunner_1() -> None:
	"""Queue ``ping_with_wait`` with invalid extra arguments (should fail)."""
	doc_task = _find_or_create_ping_task()
	print(f"Immediately queuing Task '{doc_task.name}' in Redis.")
	print(
		"However, because we're passing invalid arguments, the Task should fail, and create a Task Log indicating this."
	)
	arguments = {"foo": "Hello", "bar": "Mars"}

	doc_task.push_task_into_queue(extra_arguments=arguments)


def test_taskrunner_2() -> None:
	"""Queue ``ping_with_wait`` without required arguments (should fail)."""
	doc_task = _find_or_create_ping_task()
	print(f"Immediately queuing Task '{doc_task.name}' in Redis.")
	print(
		"However, it's missing a mandatory argument.  So the Task should fail, and create a Task Log indicating this."
	)
	doc_task.push_task_into_queue(extra_arguments=None)


def test_taskrunner_3() -> None:
	"""Queue ``ping_with_wait`` with valid arguments (should succeed)."""
	doc_task = _find_or_create_ping_task()
	print(f"Immediately queuing Task '{doc_task.name}' in Redis.")
	doc_task.push_task_into_queue(extra_arguments={"seconds_to_wait": 5})


def bytes_as_list_of_hex(some_bytes: bytes) -> list[str]:
	"""Convert bytes to a list of ``0xNN`` hex string literals."""
	if not isinstance(some_bytes, bytes):
		raise ValueError("Expected 'some_bytes' to be of type 'bytes'.")

	bytes_as_hex = some_bytes.hex()
	array: list[str] = []
	for index in range(0, len(bytes_as_hex), 2):
		array.append("0x" + bytes_as_hex[index] + bytes_as_hex[index + 1])
	return array


def test_rq_pickling() -> None:
	"""Verify RQ pickling matches Sanchez output (``bench execute btu.manual_tests.test_rq_pickling``)."""
	# pylint: disable=protected-access
	from rq.job import Job

	from btu.btu_api.endpoints import test_function_ping_now_bytes

	queue_conn = frappe.utils.background_jobs.get_redis_conn()

	# Step 1: Create a new Job.
	new_job = frappe.enqueue(method="btu.manual_tests.ping_now", queue="default", job_name="Job Name Foo")

	print(f"Created new job with ID: {new_job._id}")

	# Step 2: Read it back from Redis
	rq_job = Job.fetch(new_job._id, connection=queue_conn)

	assert new_job.data == rq_job.data
	print("Successfully validated RQ Data contents.")
	print(f"Data ({type(rq_job.data)}):\n{rq_job.data}")

	# NOTE: The Python REPL tries to bytes as ASCII.  Whether you like that, or not.
	#       For me this, is not great.  So I created a short function to display them as hexidecimals.
	# print(f"In Hex:\n{bytes_as_list_of_hex(rq_job.data)}")

	test_pickler_results = test_function_ping_now_bytes()
	print(f"\nFunction 'data' as produced by Sanchez Pickler:\n{test_pickler_results}")

	assert test_pickler_results == new_job.data


def test_with_try_except_logging() -> None:
	"""Exercise BTU logging around a deliberate exception."""
	import warnings

	warnings.filterwarnings("ignore", category=DeprecationWarning)
	from time import sleep

	try:
		sleep(1.5)
		print("Hello World")
		print("Hello Mars")
		raise RuntimeError()
	except Exception as ex:
		logger.error(f"test_with_try_except_logging() : Unhandled exception {ex!r}")
		raise ex
