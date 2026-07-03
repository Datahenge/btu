"""Unit tests for schedule_to_cron_string()."""

# Copyright (c) 2021, Datahenge LLC and Contributors
# See license.txt

import unittest

import frappe
from frappe.model.document import Document

from btu.btu_core.doctype.btu_task_schedule.btu_task_schedule import schedule_to_cron_string


def _doc(**kwargs: object) -> Document:
	"""Build an in-memory BTU Task Schedule document without saving."""
	defaults = {
		"doctype": "BTU Task Schedule",
		"run_frequency": "Daily",
		"cron_timezone": "America/New_York",
		"hour": "18",
		"minute": 0,
		"day_of_week": None,
		"day_of_month": None,
		"month": None,
		"cron_string": None,
	}
	defaults.update(kwargs)
	return frappe.get_doc(defaults)


class TestScheduleToCronString(unittest.TestCase):
	"""Tests for converting BTU Task Schedule fields into cron strings."""

	def test_daily_returns_correct_cron(self) -> None:
		"""Daily schedule should produce the expected five-field cron string."""
		result = schedule_to_cron_string(_doc(run_frequency="Daily", hour="18", minute=0))
		self.assertEqual(result, "0 18 * * *")

	def test_hourly_sets_minute_only(self) -> None:
		"""Hourly schedule should set only the minute field."""
		result = schedule_to_cron_string(_doc(run_frequency="Hourly", hour=None, minute=30))
		self.assertEqual(result, "30 * * * *")

	def test_weekly_monday_9am(self) -> None:
		"""Weekly Monday 9:00 schedule should include the correct day-of-week."""
		result = schedule_to_cron_string(
			_doc(
				run_frequency="Weekly",
				day_of_week="Mon",
				hour="9",
				minute=0,
			)
		)
		self.assertEqual(result, "0 9 * * 1")

	def test_weekly_friday_midnight(self) -> None:
		"""Weekly Friday midnight schedule should use day-of-week 5."""
		result = schedule_to_cron_string(
			_doc(
				run_frequency="Weekly",
				day_of_week="Fri",
				hour="0",
				minute=0,
			)
		)
		self.assertEqual(result, "0 0 * * 5")

	def test_monthly_15th_at_noon(self) -> None:
		"""Monthly schedule should set day-of-month and hour fields."""
		result = schedule_to_cron_string(
			_doc(
				run_frequency="Monthly",
				day_of_month=15,
				hour="12",
				minute=0,
			)
		)
		self.assertEqual(result, "0 12 15 * *")

	def test_cron_style_passes_through_unchanged(self) -> None:
		"""Cron Style frequency should return the configured cron string unchanged."""
		custom = "*/10 6-22 * * 1-5"
		result = schedule_to_cron_string(_doc(run_frequency="Cron Style", cron_string=custom))
		self.assertEqual(result, custom)

	def test_hour_18_is_not_utc_converted(self) -> None:
		"""Hour 18 must appear as 18 in the output, never as a UTC-shifted value."""
		result = schedule_to_cron_string(_doc(run_frequency="Daily", hour="18", minute=0))
		parts = result.split()
		self.assertEqual(
			parts[1],
			"18",
			msg=f"Expected hour '18' in cron '{result}'; got '{parts[1]}'. "
			"UTC conversion at save time is a DST regression.",
		)

	def test_hour_6_is_not_utc_converted(self) -> None:
		"""Hour 6 must be preserved without UTC conversion."""
		result = schedule_to_cron_string(_doc(run_frequency="Daily", hour="6", minute=0))
		parts = result.split()
		self.assertEqual(parts[1], "6")

	def test_hour_23_is_not_utc_converted(self) -> None:
		"""Hour 23 and minute 30 must be preserved without UTC conversion."""
		result = schedule_to_cron_string(_doc(run_frequency="Daily", hour="23", minute=30))
		parts = result.split()
		self.assertEqual(parts[1], "23")
		self.assertEqual(parts[0], "30")

	def test_minute_45_is_preserved(self) -> None:
		"""Minute 45 must be preserved in the cron output."""
		result = schedule_to_cron_string(_doc(run_frequency="Daily", hour="9", minute=45))
		parts = result.split()
		self.assertEqual(parts[0], "45")

	def test_daily_has_wildcard_day_and_month(self) -> None:
		"""Daily schedule should wildcard day-of-month, month, and day-of-week."""
		result = schedule_to_cron_string(_doc(run_frequency="Daily", hour="8", minute=0))
		parts = result.split()
		self.assertEqual(parts[2], "*")
		self.assertEqual(parts[3], "*")
		self.assertEqual(parts[4], "*")

	def test_hourly_has_wildcard_hour(self) -> None:
		"""Hourly schedule should wildcard the hour field."""
		result = schedule_to_cron_string(_doc(run_frequency="Hourly", hour=None, minute=15))
		parts = result.split()
		self.assertEqual(parts[1], "*")

	def test_monthly_has_wildcard_month_and_dow(self) -> None:
		"""Monthly schedule should wildcard month and day-of-week."""
		result = schedule_to_cron_string(_doc(run_frequency="Monthly", day_of_month=1, hour="0", minute=0))
		parts = result.split()
		self.assertEqual(parts[3], "*")
		self.assertEqual(parts[4], "*")

	def test_result_is_five_fields(self) -> None:
		"""Daily and hourly schedules should always produce exactly five cron fields."""
		for freq in ("Daily", "Hourly"):
			result = schedule_to_cron_string(_doc(run_frequency=freq, hour="12", minute=0))
			self.assertEqual(
				len(result.split()),
				5,
				msg=f"Cron string '{result}' for {freq} schedule should have exactly 5 fields",
			)
