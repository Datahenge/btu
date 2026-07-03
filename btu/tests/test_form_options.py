"""Tests for BTU form option helpers."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# See license.txt

import unittest

import frappe
from frappe.tests.utils import FrappeTestCase

from btu.btu_core.form_options import validate_cron_timezone, validate_rq_queue_name


class TestFormOptions(FrappeTestCase):
	"""Tests for queue and timezone validation helpers."""

	def test_validate_rq_queue_name_accepts_default(self) -> None:
		"""Default bench queues should pass validation."""
		validate_rq_queue_name("default")

	def test_validate_rq_queue_name_rejects_unknown(self) -> None:
		"""Unknown queue names should raise."""
		with self.assertRaises(frappe.ValidationError):
			validate_rq_queue_name("not-a-real-queue-name-xyz")

	def test_validate_cron_timezone_accepts_iana_name(self) -> None:
		"""Valid IANA timezone names should pass validation."""
		validate_cron_timezone("America/New_York")

	def test_validate_cron_timezone_rejects_typo(self) -> None:
		"""Invalid timezone strings should raise."""
		with self.assertRaises(frappe.ValidationError):
			validate_cron_timezone("America/NewYork")


if __name__ == "__main__":
	unittest.main()
