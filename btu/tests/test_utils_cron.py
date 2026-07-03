"""Tests for btu.utils.cron."""

import unittest

from btu.utils.cron import validate_cron_string


class TestValidateCronString(unittest.TestCase):
	"""Tests for Unix cron expression validation."""

	def test_valid_daily_cron(self) -> None:
		self.assertTrue(validate_cron_string("0 18 * * *"))

	def test_valid_hourly_cron(self) -> None:
		self.assertTrue(validate_cron_string("30 * * * *"))

	def test_invalid_too_few_fields(self) -> None:
		self.assertFalse(validate_cron_string("0 18 * *"))

	def test_invalid_raises_when_requested(self) -> None:
		with self.assertRaises(ValueError):
			validate_cron_string("not a cron", error_on_invalid=True)
