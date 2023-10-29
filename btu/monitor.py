""" btu/monitor.py """

import json
import pathlib

# Third Party
from pystemd.systemd1 import Unit, Manager
import requests
import frappe

from btu import encode_slack_text

### Prerequisites

#   sudo apt install libsystemd-dev
#   pip install pystemd==0.13.2

# The 'pystemd' library allows you to talk to systemd over dbus from python.  This is rather nicer than using subprocess and Bash commands.abs(


# The above code operates on root user units by default. To operate on userspace units, explicitly pass in a user mode DBus instance:
def check_all_services(expected_services: list, slack_webhook_name=None):
	"""
	bench execute btu.monitor.check_all_services
	"""

	if not expected_services:
		raise ValueError("Function argument 'expected_services' is mandatory.")
	if isinstance(expected_services, str):
		expected_services = [ expected_services ]

	known_unit_files = [ each["name"] for each in list_unit_files() ]
	errors_found = 0

	for each_service in expected_services:

		try:
			if each_service not in known_unit_files:
				raise ValueError(f"An expected systemd service '{each_service}' is not configured on this device.")
			unit = Unit(each_service)
			unit.load()

			if unit.Unit.ActiveState == b"active" and unit.Unit.SubState == b"running":
				print(f"\u2713 Service '{each_service}' : {unit.Unit.SubState.decode()}")
			else:
				raise RuntimeError(f"Warning: Systemd Service '{each_service}' : is {unit.Unit.ActiveState} and {unit.Unit.SubState}")

		except Exception as ex:
			errors_found += 1
			print(f"Error: {ex}")
			if slack_webhook_name:
				post_error_in_slack(slack_webhook_name, error_message=ex)

	if not errors_found:
		print("All services are online and functioning correctly.")


def list_unit_files(print_to_stdout=False):
	"""
	bench execute btu.monitor.list_unit_files
	"""
	manager = Manager()
	manager.load()
	all_unit_files = manager.Manager.ListUnitFiles()

	result = [
		{
			"name": pathlib.Path(each[0].decode()).name,
			"enabled": each[1].decode()
		}
		for each in all_unit_files
	]

	result.sort(key=lambda each: each["name"] )  # inline sort

	if print_to_stdout:
		for each_service in result:
			print(f"Service: {each_service['name']}, State: {each_service['enabled']}")

	return result


def show_sql_processes():
	"""
	bench execute btu.monitor.show_sql_processes
	"""
	statement = """ SHOW FULL PROCESSLIST """
	result = frappe.db.sql(statement, as_dict=True)
	if result:
		print("Results:")
		for each_row in result:
			print(each_row)


def post_error_in_slack(webhook_name, error_message: str, verbose=False):
	"""
	Post a message in the FTP Slack 'registrations' channel, mentioning this new customer.
	"""

	if not webhook_name:
		raise ValueError("Argument 'webhook_name' is mandatory for function 'post_error_in_slack()'")
	if not error_message:
		raise ValueError("Argument 'error_message' is mandatory for function 'post_error_in_slack()'")

	slack_url = frappe.db.get_value("Slack Webhook URL", webhook_name, "webhook_url", cache=True)
	if not slack_url:
		print("Warning: Please configure a Slack Webhook URL named 'registrations' if you want Customer Registrations to post in Slack.")
		return

	text = f"""
     -------------------------
     :warning: BTU Monitor

{error_message}
"""

	encoded_text = text # encode_slack_text(text)
	blocks_object = [
		{
			"type": "section",
			"text": {
				"type": "mrkdwn",
				"text": encoded_text
			}
		}
	]

	blocks_text = json.dumps(blocks_object)
	encoded_blocks_text = encode_slack_text(blocks_text)

	response = requests.post(
		url = slack_url,
		json = { 'text': text, 'blocks': encoded_blocks_text},
		data = None,
		headers = None,
		timeout=3600
	)

	if response.status_code	!= 200:
		print(f"Error while calling Slack API for BTU monitor: {error_message}.")
		print(f"    Status Code: {response.status_code}")
		print(f"    {response.text}")
	elif verbose:
		print(f"Slack Response HTTP 200: {response.text}")
