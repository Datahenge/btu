# Copyright (c) 2021, Datahenge LLC and Contributors
# See license.txt

"""
Unit tests for schedule_to_cron_string().

Run via:  bench run-tests --app btu --module btu.btu_core.doctype.btu_task_schedule.test_btu_task_schedule

These tests create in-memory BTU Task Schedule documents (no database writes) and call
schedule_to_cron_string() directly.  No running services are needed.

Key invariant being tested:
    Hours and minutes must appear in the cron string exactly as the user entered them.
    The old code converted to UTC at save time, which broke DST.  These tests
    guard against that regression.
"""

import unittest

import frappe

from btu.btu_core.doctype.btu_task_schedule.btu_task_schedule import schedule_to_cron_string


def _doc(**kwargs):
	"""
	Build an in-memory BTU Task Schedule document without saving to the database.
	Only the fields read by schedule_to_cron_string() need to be set.
	"""
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

	# --- Basic frequency conversions ---

	def test_daily_returns_correct_cron(self):
		result = schedule_to_cron_string(_doc(run_frequency="Daily", hour="18", minute=0))
		self.assertEqual(result, "0 18 * * *")

	def test_hourly_sets_minute_only(self):
		result = schedule_to_cron_string(_doc(run_frequency="Hourly", hour=None, minute=30))
		self.assertEqual(result, "30 * * * *")

	def test_weekly_monday_9am(self):
		result = schedule_to_cron_string(_doc(
			run_frequency="Weekly",
			day_of_week="Mon",
			hour="9",
			minute=0,
		))
		self.assertEqual(result, "0 9 * * 1")

	def test_weekly_friday_midnight(self):
		result = schedule_to_cron_string(_doc(
			run_frequency="Weekly",
			day_of_week="Fri",
			hour="0",
			minute=0,
		))
		self.assertEqual(result, "0 0 * * 5")

	def test_monthly_15th_at_noon(self):
		result = schedule_to_cron_string(_doc(
			run_frequency="Monthly",
			day_of_month=15,
			hour="12",
			minute=0,
		))
		self.assertEqual(result, "0 12 15 * *")

	def test_cron_style_passes_through_unchanged(self):
		custom = "*/10 6-22 * * 1-5"
		result = schedule_to_cron_string(_doc(run_frequency="Cron Style", cron_string=custom))
		self.assertEqual(result, custom)

	# --- DST regression guard ---
	# These tests verify that hours are stored as the user typed them (local time),
	# not shifted to UTC.  The old code ran astimezone(UTC) at save time, which
	# would convert "18" → "23" for EST or "22" for EDT, depending on the season.

	def test_hour_18_is_not_utc_converted(self):
		"""Hour 18 must appear as '18' in the output, never as '22' or '23'."""
		result = schedule_to_cron_string(_doc(run_frequency="Daily", hour="18", minute=0))
		parts = result.split()
		self.assertEqual(parts[1], "18",
			msg=f"Expected hour '18' in cron '{result}'; got '{parts[1]}'. "
			    "UTC conversion at save time is a DST regression.")

	def test_hour_6_is_not_utc_converted(self):
		result = schedule_to_cron_string(_doc(run_frequency="Daily", hour="6", minute=0))
		parts = result.split()
		self.assertEqual(parts[1], "6")

	def test_hour_23_is_not_utc_converted(self):
		result = schedule_to_cron_string(_doc(run_frequency="Daily", hour="23", minute=30))
		parts = result.split()
		self.assertEqual(parts[1], "23")
		self.assertEqual(parts[0], "30")

	def test_minute_45_is_preserved(self):
		result = schedule_to_cron_string(_doc(run_frequency="Daily", hour="9", minute=45))
		parts = result.split()
		self.assertEqual(parts[0], "45")

	# --- Wildcard positions ---

	def test_daily_has_wildcard_day_and_month(self):
		result = schedule_to_cron_string(_doc(run_frequency="Daily", hour="8", minute=0))
		parts = result.split()
		# [minute, hour, day-of-month, month, day-of-week]
		self.assertEqual(parts[2], "*")  # day-of-month
		self.assertEqual(parts[3], "*")  # month
		self.assertEqual(parts[4], "*")  # day-of-week

	def test_hourly_has_wildcard_hour(self):
		result = schedule_to_cron_string(_doc(run_frequency="Hourly", hour=None, minute=15))
		parts = result.split()
		self.assertEqual(parts[1], "*")  # hour

	def test_monthly_has_wildcard_month_and_dow(self):
		result = schedule_to_cron_string(_doc(
			run_frequency="Monthly", day_of_month=1, hour="0", minute=0
		))
		parts = result.split()
		self.assertEqual(parts[3], "*")  # month
		self.assertEqual(parts[4], "*")  # day-of-week

	# --- Output format ---

	def test_result_is_five_fields(self):
		for freq in ("Daily", "Hourly"):
			result = schedule_to_cron_string(_doc(run_frequency=freq, hour="12", minute=0))
			self.assertEqual(len(result.split()), 5,
				msg=f"Cron string '{result}' for {freq} schedule should have exactly 5 fields")
