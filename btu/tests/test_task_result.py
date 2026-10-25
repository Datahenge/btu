"""A task can report an expected failure without an exception traceback."""

import unittest

from btu import Result
from btu.btu_core.task_runner import task_result


class TestTaskResult(unittest.TestCase):
	def test_explicit_failure_stays_failed_with_short_reason(self):
		result = task_result(Result(False, "ERPNext Company returned HTTP 403"), 0.25)
		self.assertFalse(result.okay)
		self.assertEqual(result.message, "ERPNext Company returned HTTP 403")
		self.assertEqual(result.execution_time, 0.25)

	def test_plain_return_and_exception_keep_existing_behavior(self):
		self.assertTrue(task_result({"created": 1}, 0.25).okay)
		self.assertFalse(task_result(None, 0.25, threw_exception=True).okay)
