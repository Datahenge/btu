"""Scheduled Tasks run as the configured User, not as the scheduler daemon's API user."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import frappe

from btu.btu_api import endpoints
from btu.btu_core import task_runner


class TestScheduledTaskUser(unittest.TestCase):
	def test_scheduled_enqueue_passes_the_configured_user(self):
		schedule = SimpleNamespace(task="BTU-1")
		task = SimpleNamespace(name="BTU-1", queue_name="default", max_task_duration=60)
		with (
			patch.object(frappe, "only_for"),
			patch.object(frappe, "get_doc", side_effect=[schedule, task]),
			patch.object(endpoints, "_task_has_active_log", return_value=None),
			patch.object(endpoints, "scheduled_task_user", return_value="Administrator"),
			patch.object(frappe, "enqueue") as enqueue,
			patch.object(frappe.local, "site", "test-site", create=True),
		):
			response = endpoints.enqueue_for_next_available_worker("SCHED-1")
		self.assertEqual(response["has_errors"], 0)
		self.assertEqual(enqueue.call_args.kwargs["run_as_user"], "Administrator")

	def test_runner_switches_to_an_enabled_user(self):
		with (
			patch.object(task_runner, "_user_is_enabled", return_value=True),
			patch.object(frappe, "set_user") as set_user,
		):
			task_runner._switch_to_scheduled_task_user("Administrator")
		set_user.assert_called_once_with("Administrator")

	def test_runner_refuses_a_missing_or_disabled_user(self):
		with (
			patch.object(task_runner, "_user_is_enabled", return_value=False),
			patch.object(frappe, "set_user") as set_user,
		):
			with self.assertRaises(frappe.ValidationError):
				task_runner._switch_to_scheduled_task_user("gone@example.com")
		set_user.assert_not_called()
