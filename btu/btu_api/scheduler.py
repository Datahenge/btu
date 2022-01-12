""" btu/but_api/scheduler.py """

from enum import Enum
import time

import json
import pathlib
import socket
import frappe

# https://realpython.com/python-sockets/#application-protocol-header

# pylint: disable=invalid-name
class RequestType(Enum):
	create_task_schedule = 0
	ping = 1
	cancel_task_schedule = 2

class SchedulerAPI():
	"""
	Static methods are for external use.
	"""

	@frappe.whitelist()
	@staticmethod
	def send_ping():
		"""
		Ask the BTU Scheduler to reply with a 'pong'
		"""
		response = SchedulerAPI().send_message(RequestType.ping, content=None)
		return response

	@frappe.whitelist()
	@staticmethod
	def reload_task_schedule(task_schedule_id):
		"""
		Ask the BTU Scheduler to reload the Task Schedule in RQ, using the latest information.
		NOTE: This does not perform an immediate Task execution; it only refreshes the JQ Job and CRON schedule.
		"""
		response = SchedulerAPI().send_message(RequestType.create_task_schedule,
		                                       content=task_schedule_id)
		return response

	@frappe.whitelist()
	@staticmethod
	def cancel_task_schedule(task_schedule_id):
		"""
		Ask the BTU Scheduler to cancel the Task Schedule in RQ.
		"""
		response = SchedulerAPI().send_message(RequestType.cancel_task_schedule,
		                                       content=task_schedule_id)
		return response


	def send_message(self, request_type: RequestType, content):

		if not isinstance(request_type, RequestType):
			raise Exception("Argument 'request_type' must be an enum of RequestType.")
		new_message = {
			'request_type': request_type.name,
			'request_content': content
		}
		message_as_string = json.dumps(new_message)
		return self._send_message_to_scheduler_socket(message_as_string)

	def _send_message_to_scheduler_socket(self, message, debug=False):
		"""
		Establish a connection to the BTU scheduler daemon's Unix Domain Socket, and send a message.
		"""
		if not isinstance(message, str):
			raise TypeError("Argument 'message' must be a UTF-8 string.")

		socket_str = frappe.db.get_single_value("BTU Configuration", "path_to_btu_scheduler_uds")
		if not socket_str:
			raise ValueError("BTU Configuration is missing a path to the Unix Domain Socket for the scheduler daemon.")

		# Create a UDS socket; connect to the port where the BTU Scheduler daemon is listening.
		socket_path = pathlib.Path(socket_str)
		if not socket_path.exists():
			raise FileNotFoundError(f"Path to socket file does not exists: '{socket_path.absolute()}'")

		try:
			scheduler_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			scheduler_socket.settimeout(5)  # Very important, otherwise indefinite wait time.
			scheduler_socket.connect(str(socket_path.absolute()))
			if debug:
				print(f"Connected to BTU Scheduler daemon via Unix Domain Socket at '{socket_path}'")
				print(f"Blocking: {scheduler_socket.getblocking()}")
				print(f"Timeout: {scheduler_socket.gettimeout()}")
		except Exception as ex:
			return f"Exception while connecting to BTU Scheduler socket: {str(ex)}"

		message_bytes = message.encode('utf-8')
		uds_response = None
		try:
			bytes_sent = scheduler_socket.send(message_bytes)
			if debug:
				print(f"Transmitted this quantity of bytes to UDS server: {bytes_sent}")
			time.sleep(0.5)  # brief wait for server to reply
			uds_response = scheduler_socket.recv(2048)  # response should be much smaller than 2kb
			if debug:
				print(f"Response (as bytes) from BTU Scheduler: {uds_response}")
		except Exception as ex:
			print(f"Exception while communicating with the BTU Scheduler daemon's Unix Domain Socket: {ex}")
		finally:
			scheduler_socket.close()
			if debug:
				print("Socket connection to BTU Scheduler daemon is now closed.")

		if uds_response:
			uds_response = uds_response.decode('utf-8')  # return UTF-8 string
		return uds_response
