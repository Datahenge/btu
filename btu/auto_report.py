"""Deprecated import path; use :mod:`btu.btu_core.auto_report`."""

from btu.btu_core.auto_report import (
	BTUReport,
	DeliveryTarget,
	get_html_table,
	make_links,
	run_btu_report,
	update_field_types,
)

__all__ = [
	"BTUReport",
	"DeliveryTarget",
	"get_html_table",
	"make_links",
	"run_btu_report",
	"update_field_types",
]
