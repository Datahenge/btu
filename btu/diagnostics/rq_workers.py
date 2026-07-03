"""RQ worker enqueue and pickling diagnostics."""

import frappe


def test_rq_workers1() -> None:
	"""Enqueue ``ping_now`` and print the job handle."""
	result = frappe.enqueue(
		method="btu.diagnostics.smoke.ping_now", queue="default", job_name="test_rq_workers1"
	)
	print(result)


@frappe.whitelist()
def test_rq_workers2() -> None:
	"""Enqueue the BTU hello-email test on the short queue."""
	frappe.enqueue(
		method="btu.btu_core.btu_email.send_hello_email_to_current_user",
		queue="short",
	)
	print("Submitted hello-email test to the Redis Queue.")


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
	"""Verify RQ pickling matches Sanchez output."""
	# pylint: disable=protected-access
	from rq.job import Job

	from btu.btu_api.endpoints import test_function_ping_now_bytes

	queue_conn = frappe.utils.background_jobs.get_redis_conn()

	new_job = frappe.enqueue(
		method="btu.diagnostics.smoke.ping_now", queue="default", job_name="Job Name Foo"
	)

	print(f"Created new job with ID: {new_job._id}")

	rq_job = Job.fetch(new_job._id, connection=queue_conn)

	assert new_job.data == rq_job.data
	print("Successfully validated RQ Data contents.")
	print(f"Data ({type(rq_job.data)}):\n{rq_job.data}")

	test_pickler_results = test_function_ping_now_bytes()
	print(f"\nFunction 'data' as produced by Sanchez Pickler:\n{test_pickler_results}")

	assert test_pickler_results == new_job.data
