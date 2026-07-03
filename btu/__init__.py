# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see LICENSE.txt
#
# Inspired by and initially based on:
#   https://github.com/meeerp/jobtaskscheduler
#   Copyright (c) 2015, Codrotech Inc. and contributors
"""Background Tasks Unleashed: A Frappe Framework task scheduling app."""

from __future__ import annotations

import copy
import os
import re
from datetime import date as DateType
from datetime import datetime as DateTimeType
from typing import Any

import frappe
import pytz
from dateutil.tz import tzutc

NoneType = type(None)

__version__ = "15.1.1"


class Result:
	"""Success/failure result inspired by Rust's Result type."""

	def __init__(
		self,
		success: bool,
		message: str | dict[str, Any] | list[Any] | int | None,
		execution_time: float | None = None,
	) -> None:
		"""Initialize with success flag, message, and optional execution time in seconds."""
		if not isinstance(success, bool):
			raise TypeError("Result class argument 'success' must be a boolean.")
		if message:
			if isinstance(message, bool):
				message = "True" if message else "False"
			if not isinstance(message, (str, dict, list, int, NoneType)):
				raise TypeError(
					f"Result class argument 'message' must be a Python String, Integer, List, or Dictionary.  Found a type '{type(message)}' instead."
				)
		self.okay = success
		self.message = message or None
		self.execution_time = round(execution_time, 2) if execution_time else None

	def __bool__(self) -> bool:
		"""Return whether this result represents success."""
		return self.okay

	def as_json(self) -> dict[str, Any]:
		"""Return a dictionary representation of this result."""
		return {"okay": self.okay, "message": self.message, "execution_time": self.execution_time}

	def as_msgprint(self) -> str:
		"""Return an HTML-formatted message suitable for frappe.msgprint."""
		msg = f"Success: {self.okay}"
		if self.execution_time:
			msg += f"<br>Execution Time: {self.execution_time} seconds."
		msg += f"<br><br>Message: {self.message}"
		return msg


def validate_cron_string(cron_string: str, error_on_invalid: bool = False) -> bool:
	"""Return True if the string is a valid Unix cron expression."""
	minute_component = r"(?P<minute>\*(\/[0-5]?\d)?|[0-5]?\d)"
	hour_component = r"(?P<hour>\*|[01]?\d|2[0-3])"
	day_component = r"(?P<day>\*|0?[1-9]|[12]\d|3[01])"
	month_component = r"(?P<month>\*|0?[1-9]|1[012])"
	day_of_week_component = r"(?P<day_of_week>\*|[0-6](\-[0-6])?)"

	crontab_time_format_regex = re.compile(
		rf"{minute_component}\s+{hour_component}\s+{day_component}\s+{month_component}\s+{day_of_week_component}"
	)

	if crontab_time_format_regex.match(cron_string) is None:
		if error_on_invalid:
			raise ValueError(f"String '{cron_string}' is not a valid Unix cron string.")
		return False
	return True


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


def encode_slack_text(any_text: str) -> str:
	"""Encode characters required for Slack message formatting."""
	any_text = any_text.replace("&", "&amp;")
	any_text = any_text.replace("<", "&lt;")
	any_text = any_text.replace(">", "&gt;")
	any_text = any_text.replace("|", "%7C")
	return any_text


def is_env_var_set(variable_name: str) -> bool:
	"""Return True if an environment variable is set to 1."""
	if not variable_name:
		return False
	variable_value = os.environ.get(variable_name)
	if not variable_value:
		return False
	try:
		return int(variable_value) == 1
	except Exception:
		return False


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


def print_both(message: str) -> None:
	"""Print a message to both stdout and the Frappe browser UI."""
	frappe.msgprint(message)
	print(message)


# Deprecated: use btu.btu_core.rq_admin
from btu.btu_core.rq_admin import list_failed_jobs, print_job_details, remove_failed_jobs
