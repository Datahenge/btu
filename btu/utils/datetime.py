"""Date, time, and timezone helpers."""

from __future__ import annotations

import copy
from datetime import date as DateType
from datetime import datetime as DateTimeType
from typing import Any

import frappe
import pytz
from dateutil.tz import tzutc


def get_system_timezone() -> pytz.BaseTzInfo:
	"""Return the site timezone from Frappe System Settings."""
	system_time_zone = frappe.db.get_system_setting("time_zone")
	if not system_time_zone:
		raise ValueError("Please configure a Time Zone under 'System Settings'.")
	return pytz.timezone(system_time_zone)


def get_system_datetime_now() -> DateTimeType:
	"""Return the current datetime in the site's configured timezone."""
	utc_datetime = DateTimeType.now(tzutc())
	return utc_datetime.astimezone(get_system_timezone())


def make_datetime_naive(any_datetime: DateTimeType) -> DateTimeType:
	"""Strip timezone info from a timezone-aware datetime."""
	return any_datetime.replace(tzinfo=None)


def date_to_iso_string(any_date: DateType) -> str:
	"""Format a date as an ISO string (YYYY-MM-DD)."""
	if not isinstance(any_date, DateType):
		raise TypeError(f"Argument 'any_date' should have type 'datetime.date', not '{type(any_date)}'")
	return any_date.strftime("%Y-%m-%d")


def iso_string_to_date(any_string: str | DateTimeType | DateType) -> DateType:
	"""Convert an ISO date string or datetime into a date."""
	if isinstance(any_string, DateTimeType):
		return any_string.date()
	if isinstance(any_string, DateType):
		return any_string
	return DateTimeType.strptime(any_string, "%Y-%m-%d").date()


def dict_to_dateless_dict(some_object: object) -> object:
	"""Recursively convert dates in nested structures to ISO strings."""
	result = copy.deepcopy(some_object)

	if isinstance(result, DateType):
		return date_to_iso_string(some_object)

	if isinstance(some_object, list):
		return [dict_to_dateless_dict(v) for v in some_object]

	if isinstance(some_object, dict):
		new_dict: dict[Any, Any] = {}
		for key, value in some_object.items():
			new_dict[key] = dict_to_dateless_dict(value)
		return new_dict

	return some_object
