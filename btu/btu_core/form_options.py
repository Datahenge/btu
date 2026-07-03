"""Whitelisted helpers for BTU form field options."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
import pytz
from frappe import _
from frappe.utils.background_jobs import get_queues_timeout


@frappe.whitelist()
def get_rq_queue_names() -> list[str]:
	"""Return RQ queue names from bench ``common_site_config`` (authoritative)."""
	return sorted(get_queues_timeout().keys())


@frappe.whitelist()
def get_cron_timezones() -> list[str]:
	"""Return IANA timezone names for schedule forms."""
	from frappe.utils.momentjs import get_all_timezones

	return get_all_timezones()


def validate_rq_queue_name(queue_name: str | None) -> None:
	"""Reject queue names that are not configured in bench workers."""
	if not queue_name:
		return
	if queue_name not in get_queues_timeout():
		valid = ", ".join(sorted(get_queues_timeout().keys()))
		frappe.throw(
			_("Queue '{0}' is not configured in bench workers. Valid queues: {1}").format(queue_name, valid)
		)


def validate_cron_timezone(timezone_name: str | None) -> None:
	"""Reject invalid IANA timezone strings."""
	if not timezone_name:
		return
	if timezone_name not in pytz.all_timezones_set:
		frappe.throw(_("Invalid IANA time zone: {0}").format(timezone_name))
