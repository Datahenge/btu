"""
manual_tests.py

Purpose:
Call these functions from 'Bench Console' or 'Bench Execute'; then validate results manually.

"""
import frappe


@frappe.whitelist()
def ping_with_wait(seconds_to_wait):
	"""
	Wait N seconds, then reply with a message.
	"""
	import time
	if not seconds_to_wait:
		raise ValueError("Function argument 'seconds_to_wait' is mandatory and has no default.")
	seconds_to_wait = int(seconds_to_wait)
	if seconds_to_wait < 0:
		raise ValueError("Argument 'seconds_to_wait' cannot be less than 0.")
	if seconds_to_wait > 30:
		raise ValueError("Argument 'seconds_to_wait' cannot be greater than 30.")
	print(f"Waiting {seconds_to_wait} seconds before replying...")
	time.sleep(seconds_to_wait)
	print("Pong!")
	return "I have sent a 'pong'; this function is concluded."


@frappe.whitelist()
def ping_and_error():
	"""
	Wait 10 seconds, then throwing an Exception.
	"""
	import time
	print("Waiting 10 seconds, then throwing an Exception ...")
	time.sleep(10)
	raise Exception("Simulating a serious error while executing this function.")


@frappe.whitelist()
def send_hello_email_to_user():
	"""
		When run from Bench Execute, this will email the Administrator.
	    bench execute btu.manual_tests.send_hello_email_to_user
	"""
	import inspect
	import datetime
	caller_name = inspect.stack()[2][3]
	if caller_name == 'execute_cmd':
		caller_name = "JavaScript"
	else:
		caller_name = "Redis Queue"

	# Print message to the console
	user_doc = frappe.get_doc("User", frappe.session.user)
	message = f"\n--------\nHello {user_doc.full_name}."
	message += f"\nThis function was called by '{caller_name}'"
	message += f"\nThe current, local time is {datetime.datetime.now()}"
	message += "\n--------\n"
	print(message)

	frappe.sendmail(
		recipients=user_doc.email,
		message=message.replace('\n', '<br>'),
		subject=f"From Queue: Hello {user_doc.full_name}"
	)
	return "Leaving function 'send_hello_email_to_user()'.  Confirmation email should arrive soon."


@frappe.whitelist()
def test_frappe_enqueue():
	"""
	A simple test to demonstrate that Redis Queue and workers are online and operational.

	bench execute btu.manual_tests.test_frappe_enqueue
	"""
	frappe.enqueue(
			method="btu.manual_tests.send_hello_email_to_user",
			queue='short',
	)
	print("Submitted a function 'send_hello_email_to_user()' to the Redis Queue.")


def _find_or_create_ping_task():
	"""
	Finds or creates a 'ping_with_wait' BTU Task document.
	Returns: Document class.
	"""
	filters = { 'function_string': 'btu.manual_tests.ping_with_wait'}
	task_names = frappe.get_list('BTU Task', filters=filters, pluck='name')
	if task_names:
		task_doc = frappe.get_doc('BTU Task', task_names[0])
	else:
		# Could not find the 'ping_with_wait' Task; create it:
		task_doc = frappe.new_doc('BTU Task')
		task_doc.desc_short = 'Ping after N seconds'
		task_doc.desc_long = 'Wait N seconds, then return a "pong" to the caller.'
		task_doc.function_string = 'btu.manual_tests.ping_with_wait'
		task_doc.save()
		task_doc.submit()
		frappe.db.commit()

	return task_doc


def test_taskrunner_1():
	"""
	This should fail, because 'ping_with_wait' doesn't take arguments 'foo' and 'bar'
	"""
	doc_task = _find_or_create_ping_task()
	print(f"Immediately queuing Task '{doc_task.name}' in Redis.")
	print("However, because we're passing invalid arguments, the Task should fail, and create a Task Log indicating this.")
	arguments = { 'foo': 'Hello', 'bar': 'Mars'}

	doc_task.push_task_into_queue(extra_arguments=arguments)


def test_taskrunner_2():
	"""
	This should fail, because it's missing the 'seconds_to_wait' argument
	"""
	doc_task = _find_or_create_ping_task()
	print(f"Immediately queuing Task '{doc_task.name}' in Redis.")
	print("However, it's missing a mandatory argument.  So the Task should fail, and create a Task Log indicating this.")
	doc_task.push_task_into_queue(extra_arguments=None)


def test_taskrunner_3():
	"""
	This should succeed.
	"""
	doc_task = _find_or_create_ping_task()
	print(f"Immediately queuing Task '{doc_task.name}' in Redis.")
	doc_task.push_task_into_queue(extra_arguments={'seconds_to_wait': 5})
