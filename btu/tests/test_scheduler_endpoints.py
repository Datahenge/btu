"""The scheduler daemon's endpoints refuse callers without the BTU Scheduler role."""

import unittest
from unittest.mock import patch

import frappe

from btu.btu_api import endpoints

GUARDED = (
	(endpoints.get_pickled_task, ("TASK-1",)),
	(endpoints.test_function_ping_now_bytes, ()),
	(endpoints.get_enabled_task_schedules, ()),
	(endpoints.get_task_schedule_details, ("SCHED-1",)),
	(endpoints.get_pending_scheduler_commands, ()),
	(endpoints.enqueue_for_next_available_worker, ("SCHED-1",)),
)


class TestSchedulerEndpointRoles(unittest.TestCase):
	def test_every_scheduler_endpoint_checks_the_role_first(self):
		for function, args in GUARDED:
			with (
				self.subTest(function=function.__name__),
				patch.object(frappe, "only_for", side_effect=frappe.PermissionError) as only_for,
			):
				with self.assertRaises(frappe.PermissionError):
					function(*args)
				only_for.assert_called_once_with(("BTU Scheduler", "System Manager"))

	def test_ping_stays_open_to_any_signed_in_user(self):
		with patch.object(frappe, "only_for") as only_for:
			self.assertEqual(endpoints.test_ping(), "pong")
		only_for.assert_not_called()
