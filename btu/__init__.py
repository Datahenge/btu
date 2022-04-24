# -*- coding: utf-8 -*-
#
# Background Tasks Unleashed: A Frappe Framework task scheduling App.
#
# Copyright (c) 2022, Datahenge LLC and contributors
# For license information, please see LICENSE.txt
#
# Inspired by and initially based on:
#   https://github.com/meeerp/jobtaskscheduler
#   Copyright (c) 2015, Codrotech Inc. and contributors

from datetime import datetime  # standard Python library
import re  # standard Python library
from dateutil.tz import tzutc
import pytz  # https://pypi.org/project/pytz/

import frappe

__version__ = '0.5.0'


class Result():
	"""
	Inspired by Rust's Result type which has Ok(None) or Error(message)
	Functions can return an instance of this class, instead of True/False or None.
	"""
	def __init__(self, success, message, execution_time=None):
		"""
		Arguments:
			success: True/False that the function succeeded.
			message: Text explaining the success message.
			execution_time:  (Optional) How long the function took to complete, in seconds.
		"""
		if not isinstance(success, bool):
			raise TypeError("Result class argument 'success' must be a boolean.")
		if message:
			if not isinstance(message, (str, dict, list)):
				raise TypeError(f"Result class argument 'message' must be a Python String, List, or Dictionary.  Found value '{message}' instead.")
		self.okay = success
		self.message = message or None
		self.execution_time = round(execution_time,2) if execution_time else None

	def __bool__(self):
		"""
		A useful overload.  For example: 'if Result():'
		"""
		return self.okay

	def as_json(self):
		"""
		Dictionary representation of the class instance.
		"""
		return {
		    "okay": self.okay,
		    "message": self.message,
		    "execution_time": self.execution_time
		}

	def as_msgprint(self):
		msg = f"Success: {self.okay}"
		msg += f"<br>Execution Time: {self.execution_time} seconds."
		msg += f"<br><br>Message: {self.message}"
		return msg


# Some date and time functions are included below.
#
#   * It's tempting to use my own Temporal App for handling Date and Time functions.
#   * But for now, I don't want to create a cross-dependency with another App.


def validate_cron_string(cron_string, error_on_invalid=False):
	"""
	Validate that a string is a Unix cron string.
	"""

	# Note: This is also a Temporal function, but I'm trying to avoid making Temporal a dependency of BTU.
	minute_component = r"(?P<minute>\*(\/[0-5]?\d)?|[0-5]?\d)"
	hour_component = r"(?P<hour>\*|[01]?\d|2[0-3])"
	day_component = r"(?P<day>\*|0?[1-9]|[12]\d|3[01])"
	month_component = r"(?P<month>\*|0?[1-9]|1[012])"
	day_of_week_component = r"(?P<day_of_week>\*|[0-6](\-[0-6])?)"  # end of str.format()

	crontab_time_format_regex = re.compile(
		rf"{minute_component}\s+{hour_component}\s+{day_component}\s+{month_component}\s+{day_of_week_component}"
	)  # end of re.compile()

	if crontab_time_format_regex.match(cron_string) is None:
		if error_on_invalid:
			raise Exception(f"String '{cron_string}' is not a valid Unix cron string.")
		return False
	return True


def get_system_timezone():
	"""
	Returns the Time Zone of the Site.
	"""
	system_time_zone = frappe.db.get_system_setting('time_zone')
	if not system_time_zone:
		raise Exception("Please configure a Time Zone under 'System Settings'.")
	return pytz.timezone(system_time_zone)


def get_system_datetime_now():
	"""
	Return a timezone-aware DateTime value, using the Frappe webserver's System Settings.
	"""
	utc_datetime = datetime.now(tzutc())  # Get the current UTC datetime.
	return utc_datetime.astimezone( get_system_timezone())  # Convert to the site's Time Zone:


def make_datetime_naive(any_datetime):
	"""
	Takes a timezone-aware datetime, and makes it naive.
	Useful because Frappe is not storing timezone-aware datetimes in MySQL.
	"""
	return any_datetime.replace(tzinfo=None)
