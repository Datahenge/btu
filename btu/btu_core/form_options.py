"""Whitelisted helpers for BTU form field options."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils.background_jobs import get_queues_timeout

_TIMEZONE_CACHE_KEY = "btu_iana_timezones"


def _build_timezone_list() -> list[str]:
	"""Build a sorted IANA timezone list directly from the OS zoneinfo database."""
	from zoneinfo import available_timezones

	return sorted(available_timezones())


def _get_cached_timezones() -> list[str]:
	"""Return the IANA timezone list from Redis, populating it on first call."""
	cached = frappe.cache.get_value(_TIMEZONE_CACHE_KEY)
	if cached is None:
		cached = _build_timezone_list()
		frappe.cache.set_value(_TIMEZONE_CACHE_KEY, cached)
	return cached


@frappe.whitelist()
def get_rq_queue_names() -> list[str]:
	"""Return RQ queue names from bench ``common_site_config`` (authoritative)."""
	return sorted(get_queues_timeout().keys())


@frappe.whitelist()
def get_cron_timezones() -> list[str]:
	"""Return IANA timezone names from the Redis cache (populated lazily from zoneinfo)."""
	return _get_cached_timezones()


@frappe.whitelist()
def reload_timezone_cache() -> str:
	"""Force a rebuild of the IANA timezone cache from the OS zoneinfo database.

	Called by the 'Reload Timezone Cache' button in BTU Configuration.
	Otherwise the cache self-populates on first use after a Redis flush.
	"""
	tzs = _build_timezone_list()
	frappe.cache.set_value(_TIMEZONE_CACHE_KEY, tzs)
	return _("Timezone cache reloaded: {0} zones loaded from zoneinfo.").format(len(tzs))


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
	"""Reject timezone strings that are not valid IANA zone names.

	Validates against the Redis-cached zoneinfo list. If the cache is cold
	(e.g. Redis was just flushed), falls back to querying zoneinfo directly
	so that valid timezones are never incorrectly rejected.
	"""
	if not timezone_name:
		return
	valid_zones = set(_get_cached_timezones())
	if timezone_name not in valid_zones:
		frappe.throw(_("Invalid IANA time zone: '{0}'").format(timezone_name))
