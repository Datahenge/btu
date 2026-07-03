"""Tests for btu.utils.datetime adapters over temporal-lib."""

from __future__ import annotations

import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

from btu.utils.datetime import (
	date_to_iso_string,
	dict_to_dateless_dict,
	iso_string_to_date,
	make_datetime_naive,
)


class TestDatetimeAdapters(unittest.TestCase):
	def test_date_to_iso_string_delegates(self) -> None:
		self.assertEqual(date_to_iso_string(date(2024, 3, 15)), "2024-03-15")

	def test_make_datetime_naive_delegates(self) -> None:
		aware = datetime(2024, 3, 15, 12, 0, tzinfo=ZoneInfo("UTC"))
		naive = make_datetime_naive(aware)
		self.assertIsNone(naive.tzinfo)
		self.assertEqual(naive, datetime(2024, 3, 15, 12, 0))

	def test_iso_string_to_date_from_string(self) -> None:
		self.assertEqual(iso_string_to_date("2024-03-15"), date(2024, 3, 15))

	def test_iso_string_to_date_from_datetime(self) -> None:
		self.assertEqual(
			iso_string_to_date(datetime(2024, 3, 15, 18, 30, tzinfo=ZoneInfo("UTC"))),
			date(2024, 3, 15),
		)

	def test_iso_string_to_date_from_date(self) -> None:
		self.assertEqual(iso_string_to_date(date(2024, 3, 15)), date(2024, 3, 15))

	def test_iso_string_to_date_rejects_invalid_string(self) -> None:
		with self.assertRaises(ValueError):
			iso_string_to_date("not-a-date")

	def test_dict_to_dateless_dict(self) -> None:
		payload = {
			"when": date(2024, 3, 15),
			"items": [date(2024, 1, 1)],
			"run_at": datetime(2024, 3, 15, 18, 30),
		}
		self.assertEqual(
			dict_to_dateless_dict(payload),
			{
				"when": "2024-03-15",
				"items": ["2024-01-01"],
				"run_at": "2024-03-15 18:30:00",
			},
		)

	def test_dict_to_dateless_dict_datetime_before_date(self) -> None:
		"""datetime is a date subclass; must serialize as datetime, not date-only."""
		value = datetime(2024, 3, 15, 9, 15)
		self.assertEqual(dict_to_dateless_dict(value), "2024-03-15 09:15:00")

	def test_dict_to_dateless_dict_does_not_mutate_input(self) -> None:
		inner = {"due": date(2024, 3, 15)}
		payload = {"nested": inner}
		dict_to_dateless_dict(payload)
		self.assertEqual(inner["due"], date(2024, 3, 15))
