"""Redis RPC client for communicating with the BTU Scheduler daemon."""

import json
import uuid
from enum import Enum
from typing import TYPE_CHECKING, Any

import frappe

if TYPE_CHECKING:
	import redis

# Redis key where the BTU Scheduler daemon listens for incoming commands.
REDIS_COMMAND_QUEUE = "btu:scheduler:commands"

# Prefix for per-request response keys.  Each call appends a UUID: btu:scheduler:rpc:{uuid}
REDIS_RPC_RESPONSE_PREFIX = "btu:scheduler:rpc"

# How long (seconds) the web worker blocks waiting for the scheduler's receipt ACK.
# The scheduler ACKs on receipt, before executing, so this should be near-instant
# under normal conditions.  5 seconds is generous; a timeout means the scheduler is
# down, unreachable, or its Redis connection is broken.
REDIS_RPC_TIMEOUT_SECONDS = 5


class RequestType(Enum):
	"""Command types accepted by the BTU Scheduler daemon."""

	create_task_schedule = 0
	ping = 1
	cancel_task_schedule = 2


def _get_redis_connection() -> "redis.Redis[str]":
	"""Return a Redis connection pointed at Frappe's RQ database."""
	import redis as redis_lib

	return redis_lib.from_url(frappe.local.conf.redis_queue, decode_responses=True)


class SchedulerAPI:
	"""Redis RPC client for the BTU Scheduler daemon (see ``docs/scheduler_redis_rpc.md``)."""

	@staticmethod
	def send_ping() -> dict[str, Any] | None:
		"""Ask the BTU Scheduler to reply with a receipt acknowledgement."""
		return SchedulerAPI().send_message(RequestType.ping, content=None)

	@staticmethod
	def reload_task_schedule(task_schedule_id: str) -> dict[str, Any] | None:
		"""Reload a Task Schedule in RQ without triggering immediate execution."""
		return SchedulerAPI().send_message(RequestType.create_task_schedule, content=task_schedule_id)

	@staticmethod
	def cancel_task_schedule(task_schedule_id: str) -> dict[str, Any] | None:
		"""Ask the BTU Scheduler to remove a Task Schedule from RQ."""
		return SchedulerAPI().send_message(RequestType.cancel_task_schedule, content=task_schedule_id)

	def send_message(self, request_type: RequestType, content: str | None) -> dict[str, Any] | None:
		"""Send a typed command to the scheduler and return its JSON acknowledgement."""
		if not isinstance(request_type, RequestType):
			raise TypeError("Argument 'request_type' must be an enum of RequestType.")
		return self._send_message_via_redis_rpc(request_type.name, content)

	def _send_message_via_redis_rpc(
		self, request_type_name: str, content: str | None
	) -> dict[str, Any] | None:
		"""Push a scheduler command and block-wait for the receipt ACK (or return None)."""
		response_key = f"{REDIS_RPC_RESPONSE_PREFIX}:{uuid.uuid4().hex}"
		command = json.dumps(
			{
				"request_type": request_type_name,
				"request_content": content,
				"response_key": response_key,
			}
		)

		try:
			redis_conn = _get_redis_connection()
			redis_conn.lpush(REDIS_COMMAND_QUEUE, command)

			# BLPOP blocks until the scheduler pushes an ACK, or the timeout expires.
			result = redis_conn.blpop(response_key, timeout=REDIS_RPC_TIMEOUT_SECONDS)

			if result is None:
				frappe.logger("btu").warning(
					"BTU Scheduler did not acknowledge command '%s' within %s seconds. "
					"Scheduler may be down or Redis connectivity is broken.",
					request_type_name,
					REDIS_RPC_TIMEOUT_SECONDS,
				)
				return None

			_, response_json = result  # BLPOP returns (key_name, value)
			return json.loads(response_json)

		except Exception as ex:
			frappe.logger("btu").error("Error communicating with BTU Scheduler via Redis RPC: %s", ex)
			return None
