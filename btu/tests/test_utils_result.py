"""Tests for btu.utils.result."""

import unittest

from btu.utils.result import Result


class TestResult(unittest.TestCase):
	"""Tests for the BTU Result type."""

	def test_bool_success(self) -> None:
		self.assertTrue(Result(True, "ok"))

	def test_bool_failure(self) -> None:
		self.assertFalse(Result(False, "nope"))

	def test_as_json_round_trip(self) -> None:
		result = Result(True, "done", execution_time=1.234)
		payload = result.as_json()
		self.assertEqual(payload["okay"], True)
		self.assertEqual(payload["message"], "done")
		self.assertEqual(payload["execution_time"], 1.23)

	def test_message_must_be_valid_type(self) -> None:
		with self.assertRaises(TypeError):
			Result(True, object())  # type: ignore[arg-type]
