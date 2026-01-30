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

	@staticmethod
	def send_ping():
		"""
		Ask the BTU Scheduler to reply with a 'pong'
		"""
		response = SchedulerAPI().send_message(RequestType.ping, content=None)
		return response

	@staticmethod
	def reload_task_schedule(task_schedule_id):
		"""
		Ask the BTU Scheduler to reload the Task Schedule in RQ, using the latest information.
		NOTE: This does not perform an immediate Task execution; it only refreshes the JQ Job and CRON schedule.
		"""
		response = SchedulerAPI().send_message(RequestType.create_task_schedule,
		                                       content=task_schedule_id)
		return response

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
			raise TypeError("Argument 'request_type' must be an enum of RequestType.")
		new_message = {
			'request_type': request_type.name,
			'request_content': content
		}
		message_as_string = json.dumps(new_message)
		return self._send_message_to_scheduler_socket(message_as_string)

	def _send_message_to_scheduler_socket(self, message, debug=False):
		"""
		Establish a connection to the BTU scheduler daemon and send a message.
		Supports both Unix Domain Socket (local) and TCP (Kubernetes).
		"""
		if not isinstance(message, str):
			raise TypeError("Argument 'message' must be a UTF-8 string.")

		# Check if TCP is enabled
		use_tcp = frappe.db.get_single_value("BTU Configuration", "use_tcp_socket")

		if use_tcp:
			return self._send_via_tcp(message, debug)
		else:
			return self._send_via_unix_socket(message, debug)

	def _send_via_tcp(self, message, debug=False):
		"""Send message via TCP socket."""
		tcp_host = frappe.db.get_single_value("BTU Configuration", "tcp_host")
		tcp_port = frappe.db.get_single_value("BTU Configuration", "tcp_port")

		if not tcp_host or not tcp_port:
			raise ValueError("BTU Configuration is missing TCP host or port.")

		try:
			scheduler_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			scheduler_socket.settimeout(5)
			scheduler_socket.connect((tcp_host, int(tcp_port)))
			if debug:
				print(f"Connected to BTU Scheduler via TCP at {tcp_host}:{tcp_port}")
		except Exception as ex:
			return f"Exception while connecting to BTU Scheduler via TCP: {str(ex)}"

		return self._send_and_receive(scheduler_socket, message, debug)

	def _send_via_unix_socket(self, message, debug=False):
		"""Send message via Unix Domain Socket."""
		socket_str = frappe.db.get_single_value("BTU Configuration", "path_to_btu_scheduler_uds")
		if not socket_str:
			raise ValueError("BTU Configuration is missing a path to the Unix Domain Socket for the scheduler daemon.")

		socket_path = pathlib.Path(socket_str)
		if not socket_path.exists():
			raise FileNotFoundError(f"Path to socket file does not exist: '{socket_path.absolute()}'")

		try:
			scheduler_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
			scheduler_socket.settimeout(5)
			scheduler_socket.connect(str(socket_path.absolute()))
			if debug:
				print(f"Connected to BTU Scheduler daemon via Unix Domain Socket at '{socket_path}'")
		except Exception as ex:
			return f"Exception while connecting to BTU Scheduler socket: {str(ex)}"

		return self._send_and_receive(scheduler_socket, message, debug)

	def _send_and_receive(self, scheduler_socket, message, debug=False):
		"""Common send/receive logic for both socket types."""
		message_bytes = message.encode('utf-8')
		response = None
		try:
			bytes_sent = scheduler_socket.send(message_bytes)
			if debug:
				print(f"Transmitted bytes: {bytes_sent}")
			time.sleep(0.5)  # brief wait for server to reply
			response = scheduler_socket.recv(2048)
			if debug:
				print(f"Response from BTU Scheduler: {response}")
		except Exception as ex:
			print(f"Exception during communication: {ex}")
		finally:
			scheduler_socket.close()
			if debug:
				print("Socket connection to BTU Scheduler daemon is now closed.")

		if response:
			response = response.decode('utf-8')
		return response
