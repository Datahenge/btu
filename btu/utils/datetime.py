"""Date, time, and timezone helpers (Frappe-aware adapters over temporal-lib)."""

from __future__ import annotations

from datetime import date as DateType
from datetime import datetime as DateTimeType

import frappe
import pytz
from temporal_lib.core import get_system_datetime_now as _tlib_get_system_datetime_now
from temporal_lib.core import make_datetime_naive as _tlib_make_datetime_naive
from temporal_lib.tlib_types import date_to_iso_string as _tlib_date_to_iso_string
from temporal_lib.tlib_types import datestr_to_date
from temporal_lib.tlib_types import datetime_to_iso_string as _tlib_datetime_to_iso_string


def _get_frappe_site_timezone_name() -> str:
	system_time_zone = frappe.db.get_system_setting("time_zone")
	if not system_time_zone:
		raise ValueError("Please configure a Time Zone under 'System Settings'.")
	return system_time_zone


def get_system_timezone() -> pytz.BaseTzInfo:
	"""Return the site timezone from Frappe System Settings."""
	return pytz.timezone(_get_frappe_site_timezone_name())


def get_system_datetime_now() -> DateTimeType:
	"""Return the current datetime in the site's configured timezone."""
	return _tlib_get_system_datetime_now(_get_frappe_site_timezone_name())


def make_datetime_naive(any_datetime: DateTimeType) -> DateTimeType:
	"""Strip timezone info from a timezone-aware datetime."""
	return _tlib_make_datetime_naive(any_datetime)


def date_to_iso_string(any_date: DateType) -> str:
	"""Format a date as an ISO string (YYYY-MM-DD)."""
	return _tlib_date_to_iso_string(any_date)


def iso_string_to_date(any_string: str | DateTimeType | DateType) -> DateType:
	"""Convert an ISO date string or datetime into a date."""
	if isinstance(any_string, DateTimeType):
		return any_string.date()
	if isinstance(any_string, DateType):
		return any_string
	result = datestr_to_date(any_string)
	if result is None:
		raise ValueError(f"'{any_string}' is not a valid ISO date string.")
	return result


def dict_to_dateless_dict(some_object: object) -> object:
	"""Recursively convert date and datetime values in nested structures to ISO strings."""
	if isinstance(some_object, DateTimeType):
		return _tlib_datetime_to_iso_string(some_object)

	if isinstance(some_object, DateType):
		return date_to_iso_string(some_object)

	if isinstance(some_object, list):
		return [dict_to_dateless_dict(v) for v in some_object]

	if isinstance(some_object, dict):
		return {key: dict_to_dateless_dict(value) for key, value in some_object.items()}

	return some_object
