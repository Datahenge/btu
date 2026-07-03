"""BTU Task and TaskRunner integration diagnostics."""

import frappe

PING_WITH_WAIT_PATH = "btu.diagnostics.smoke.ping_with_wait"


def _find_or_create_ping_task() -> "frappe.Document":
	"""Find or create the ``ping_with_wait`` BTU Task document."""
	for legacy_path in (PING_WITH_WAIT_PATH, "btu.manual_tests.ping_with_wait"):
		task_names = frappe.get_list("BTU Task", filters={"function_string": legacy_path}, pluck="name")
		if task_names:
			return frappe.get_doc("BTU Task", task_names[0])

	task_doc = frappe.new_doc("BTU Task")
	task_doc.desc_short = "Ping after N seconds"
	task_doc.desc_long = 'Wait N seconds, then return a "pong" to the caller.'
	task_doc.function_string = PING_WITH_WAIT_PATH
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
	doc_task.push_task_into_queue(extra_arguments={"foo": "Hello", "bar": "Mars"})


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
