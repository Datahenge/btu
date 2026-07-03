"""RQ worker handlers for BTU Run Later document execution."""

import json

import frappe

from btu.btu_core.doctype.btu_task.btu_task import create_and_run_one_shot


class WrappedFunction:
	"""Placeholder for future run-later wrapper utilities."""


def enqueued_run_later_instance(run_later_key: str) -> None:
	"""Execute a BTU Run Later record (normally invoked from an RQ worker)."""
	# NOTE: This function will normally be running via RQ Workers.

	# Lock down the BTU Run Later record
	# TODO: The called function may contain a SQL Commit.  Which would break this lock.
	#       So I should lock using a different SQL transaction.
	doc_run_later = frappe.get_doc("BTU Run Later", run_later_key, for_update=True)
	# instantiate a class
	# write some logs
	# do some other stuff.
	try:
		if doc_run_later.btu_task:
			frappe.logger("btu").info("Running BTU Task '%s' on web server.", doc_run_later.btu_task)
			doc_btu_task = frappe.get_doc("BTU Task", doc_run_later.btu_task)
			result = doc_btu_task.run_task_on_webserver()
			frappe.logger("btu").info("Result = %s", result)
		else:
			frappe.logger("btu").info(
				"Creating and running a One-Shot task in the current thread of execution."
			)
			# Run a One-Shot task, but don't enqueue...we're already in one.
			create_and_run_one_shot(
				short_description=doc_run_later.new_task_name,
				function_path=doc_run_later.new_task_function_path,
				arguments=json.loads(doc_run_later.btu_task_arguments),
				queue_name=None,
			)

		# NOTE: Commits could have just happened, which will undo my Locks.

	except Exception as ex:
		# Something went wrong with whatever I'm supposed to be doing.
		frappe.logger("btu").error("Error during enqueued_run_later_instance(): %s", ex)
		doc_run_later.last_result = "Error"
		if doc_run_later.can_retry():
			doc_run_later.execution_status = "Pending Future"
		else:
			doc_run_later.execution_status = "Abandoned"  # albeit with an Error
		doc_run_later.save()

	else:
		doc_run_later.last_result = "Success"
		doc_run_later.execution_status = "Completed"
		doc_run_later.save()
	finally:
		frappe.db.commit()
