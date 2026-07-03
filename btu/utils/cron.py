"""Cron expression validation."""

import re


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
