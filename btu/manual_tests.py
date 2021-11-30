"""
manual_tests.py

Purpose:
Call these functions from 'Bench Console' or 'Bench Execute'; then validate results manually.

"""

import inspect
import datetime
import frappe
from btu.email import send_email

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
	print(f"Waiting {seconds_to_wait} seconds before replying...")
	time.sleep(seconds_to_wait)
	print("Pong!")
	return "I have sent a 'pong'; this function is concluded."


@frappe.whitelist()
def ping_and_error():
	"""
	Wait 10 seconds, then throw an Exception.
	"""
	import time
	print("Waiting 10 seconds, then throwing an Exception ...")
	time.sleep(10)
	raise Exception("Simulating a serious error while executing this function.")


@frappe.whitelist()
def send_hello_email_to_user(debug=False):
	"""
		When run from Bench Execute, this will email the Administrator.
	    bench execute btu.manual_tests.send_hello_email_to_user
	"""

	caller_name = inspect.stack()[2][3]
	if caller_name == 'execute_cmd':
		caller_name = "JavaScript"
	if caller_name == '<lambda>':
		caller_name = "JavaScript"

	# Load the session User's document, and get their email address.
	user_doc = frappe.get_doc("User", frappe.session.user)
	if not user_doc.email:
		frappe.throw(f"Current user '{user_doc.name}' does not have an Email Address associated with their account.")

	datetime_now_string = datetime.datetime.now().strftime("%A, %B %d %Y, %-I:%M %p")
	# Construct a small message string, to pass in the email's body.
	message_body = f"Hello, {user_doc.full_name}."
	message_body += f"\n\nThis function was initiated by '{caller_name}'"
	message_body += f"\nThe current, local time is {datetime_now_string}"
	message_body += "\n\n--------\n"

	if debug:
		print(f"Sending test email to address '{user_doc.email}'")
	frappe.msgprint(f"Sending test email to address '{user_doc.email}' ...")

	# Create the subject of the email
	subject = f"From BTU: Hello {user_doc.full_name}"

	send_email(sender='testing@datahenge.com',
	           recipients=user_doc.email,
			   subject= subject,
			   body= message_body
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
