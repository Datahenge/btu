""" btu/monitor.py """

import json
import pathlib

# Third Party
import requests
import frappe

from btu import encode_slack_text


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
	Post a message in a Slack channel.
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
