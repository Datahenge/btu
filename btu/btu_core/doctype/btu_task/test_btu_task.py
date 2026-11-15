"""Tests for BTU Task DocType."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# See license.txt

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from btu.btu_core.doctype.btu_task.btu_task import BTUTask


class TestBTUTask(unittest.TestCase):
	"""Tests for BTU Task."""

	def test_on_trash_deletes_task_logs_through_query_builder(self):
		task = SimpleNamespace(name="TASK-0001", flags=SimpleNamespace())
		# frappe.db is an unbound proxy outside a site, so replace the module's frappe reference.
		with patch("btu.btu_core.doctype.btu_task.btu_task.frappe") as frappe:
			BTUTask.on_trash(task)
		db = frappe.db
		db.delete.assert_called_once_with("BTU Task Log", {"task": "TASK-0001"})
		db.sql.assert_not_called()
		self.assertTrue(task.flags.ignore_submitted)
