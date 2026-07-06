# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see LICENSE.txt
#
# Inspired by and initially based on:
#   https://github.com/meeerp/jobtaskscheduler
#   Copyright (c) 2015, Codrotech Inc. and contributors
"""Background Tasks Unleashed: A Frappe Framework task scheduling app."""

from __future__ import annotations

__version__ = "15.2.0"

from btu.btu_core.rq_admin import list_failed_jobs, print_job_details, remove_failed_jobs
from btu.utils import (
	Result,
	date_to_iso_string,
	dict_to_dateless_dict,
	encode_slack_text,
	get_system_datetime_now,
	get_system_timezone,
	is_env_var_set,
	iso_string_to_date,
	make_datetime_naive,
	print_both,
	validate_cron_string,
)

__all__ = [
	"Result",
	"__version__",
	"date_to_iso_string",
	"dict_to_dateless_dict",
	"encode_slack_text",
	"get_system_datetime_now",
	"get_system_timezone",
	"is_env_var_set",
	"iso_string_to_date",
	"list_failed_jobs",
	"make_datetime_naive",
	"print_both",
	"print_job_details",
	"remove_failed_jobs",
	"validate_cron_string",
]
