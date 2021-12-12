# -*- coding: utf-8 -*-
#
# Background Tasks Unleashed: A Frappe Framework task scheduling App.
#
# Copyright (c) 2021, Datahenge LLC and contributors
# For license information, please see LICENSE.txt
#
# Inspired by and initially based on:
#   https://github.com/meeerp/jobtaskscheduler
#   Copyright (c) 2015, Codrotech Inc. and contributors

import frappe

__version__ = '0.3.0'


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
		if message and (not isinstance(message, str)):
			raise TypeError("Result class argument 'message' must be a Python string.")
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


def validate_cron_string(cron_string, error_on_invalid=False):
	"""
	Validate that a string is a Unix cron string.
	"""
	import re

	# Note: This is also a Temporal function, but I'm trying to avoid making Temporal a dependency of BTU.
	crontab_time_format_regex = re.compile(
		r"{0}\s+{1}\s+{2}\s+{3}\s+{4}".format(
			r"(?P<minute>\*(\/[0-5]?\d)?|[0-5]?\d)",
			r"(?P<hour>\*|[01]?\d|2[0-3])",
			r"(?P<day>\*|0?[1-9]|[12]\d|3[01])",
			r"(?P<month>\*|0?[1-9]|1[012])",
			r"(?P<day_of_week>\*|[0-6](\-[0-6])?)")  # end of str.format()
	)  # end of re.compile()

	if crontab_time_format_regex.match(cron_string) is None:
		if error_on_invalid:
			raise Exception(f"String '{cron_string}' is not a valid Unix cron string.")
		return False
	return True


# While tempting to use the Temporal App for handling Date and Time functions,
# at least for now, I want to avoid creating a dependency with another Frappe App.

def get_system_timezone():
	"""
	Returns the Time Zone of the Site.
	"""
	import pytz
	system_time_zone = frappe.db.get_system_setting('time_zone')
	if not system_time_zone:
		raise Exception("Please configure a Time Zone under 'System Settings'.")
	return pytz.timezone(system_time_zone)


def get_system_datetime_now():
	from datetime import datetime
	from dateutil.tz import tzutc
	utc_datetime = datetime.now(tzutc())  # Get the current UTC datetime.
	return utc_datetime.astimezone( get_system_timezone())  # Convert to the site's Time Zone:


def make_datetime_naive(any_datetime):
	"""
	Takes a timezone-aware datetime, and makes it naive.
	Useful because Frappe is not storing timezone-aware datetimes in MySQL.
	"""
	return any_datetime.replace(tzinfo=None)
