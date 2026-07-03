"""Tests for BTU Task default values from BTU Configuration."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from btu.btu_core.task_defaults import (
	TASK_DOCTYPE_FIELD_DEFAULTS,
	apply_task_defaults_from_configuration,
	get_task_defaults_from_configuration,
)


class TestTaskDefaults(FrappeTestCase):
	"""Tests for applying BTU Configuration defaults to new BTU Tasks."""

	def setUp(self) -> None:
		"""Store current configuration defaults and set known test values."""
		self.config = frappe.get_single("BTU Configuration")
		self._original = {
			"queue_name": self.config.queue_name,
			"max_task_duration": self.config.max_task_duration,
			"repeat_log_in_stdout": self.config.repeat_log_in_stdout,
		}
		self.config.queue_name = "short"
		self.config.max_task_duration = 900
		self.config.repeat_log_in_stdout = 1
		self.config.save(ignore_permissions=True)

	def tearDown(self) -> None:
		"""Restore configuration defaults."""
		self.config.queue_name = self._original["queue_name"]
		self.config.max_task_duration = self._original["max_task_duration"]
		self.config.repeat_log_in_stdout = self._original["repeat_log_in_stdout"]
		self.config.save(ignore_permissions=True)

	def test_get_task_defaults_from_configuration(self) -> None:
		"""Configuration singles should expose the configured task defaults."""
		defaults = get_task_defaults_from_configuration(self.config)
		self.assertEqual(defaults["queue_name"], "short")
		self.assertEqual(defaults["max_task_duration"], 900)
		self.assertEqual(defaults["repeat_log_in_stdout"], 1)

	def test_apply_task_defaults_replaces_doctype_defaults(self) -> None:
		"""Unchanged DocType defaults on a new task should be replaced by configuration."""
		task = frappe.get_doc(
			{
				"doctype": "BTU Task",
				"desc_short": "Defaults Test Task",
				"function_string": "btu.samples.simple.hello",
				"task_type": "Persistent",
				"queue_name": TASK_DOCTYPE_FIELD_DEFAULTS["queue_name"],
				"max_task_duration": TASK_DOCTYPE_FIELD_DEFAULTS["max_task_duration"],
				"repeat_log_in_stdout": TASK_DOCTYPE_FIELD_DEFAULTS["repeat_log_in_stdout"],
			}
		)
		apply_task_defaults_from_configuration(task, self.config)
		self.assertEqual(task.queue_name, "short")
		self.assertEqual(task.max_task_duration, 900)
		self.assertEqual(task.repeat_log_in_stdout, 1)

	def test_apply_task_defaults_preserves_user_changes(self) -> None:
		"""Explicit task field values should not be overwritten on insert."""
		task = frappe.get_doc(
			{
				"doctype": "BTU Task",
				"desc_short": "Custom Queue Task",
				"function_string": "btu.samples.simple.hello",
				"task_type": "Persistent",
				"queue_name": "long",
				"max_task_duration": 120,
				"repeat_log_in_stdout": 0,
			}
		)
		apply_task_defaults_from_configuration(
			task,
			self.config,
			fields=("queue_name", "max_task_duration"),
		)
		self.assertEqual(task.queue_name, "long")
		self.assertEqual(task.max_task_duration, 120)
		self.assertEqual(task.repeat_log_in_stdout, 0)
