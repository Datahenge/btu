"""Site-wide default values for new BTU Task documents."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import cint

TASK_DEFAULT_FIELDS = ("queue_name", "max_task_duration", "repeat_log_in_stdout")

# DocType JSON defaults on BTU Task; used to detect unchanged fields on insert.
TASK_DOCTYPE_FIELD_DEFAULTS = {
	"queue_name": "default",
	"max_task_duration": 600,
	"repeat_log_in_stdout": 0,
}


@frappe.whitelist()
def get_new_task_defaults() -> dict[str, object]:
	"""Return BTU Configuration values to pre-fill a new BTU Task form."""
	return get_task_defaults_from_configuration()


def get_task_defaults_from_configuration(config: Document | None = None) -> dict[str, object]:
	"""Read task default field values from BTU Configuration."""
	if config is None:
		config = frappe.get_single("BTU Configuration")
	return {
		"queue_name": config.queue_name or TASK_DOCTYPE_FIELD_DEFAULTS["queue_name"],
		"max_task_duration": cint(config.max_task_duration) or TASK_DOCTYPE_FIELD_DEFAULTS["max_task_duration"],
		"repeat_log_in_stdout": cint(config.repeat_log_in_stdout),
	}


def apply_task_defaults_from_configuration(
	task: Document,
	config: Document | None = None,
	fields: tuple[str, ...] | None = None,
) -> None:
	"""Apply BTU Configuration defaults to a new BTU Task when fields are still at DocType defaults."""
	defaults = get_task_defaults_from_configuration(config)
	fieldnames = fields or TASK_DEFAULT_FIELDS
	for fieldname in fieldnames:
		current = task.get(fieldname)
		if fieldname == "repeat_log_in_stdout":
			if cint(current) == TASK_DOCTYPE_FIELD_DEFAULTS[fieldname]:
				task.set(fieldname, defaults[fieldname])
			continue
		if fieldname == "max_task_duration":
			if cint(current) == TASK_DOCTYPE_FIELD_DEFAULTS[fieldname]:
				task.set(fieldname, defaults[fieldname])
			continue
		if not current or current == TASK_DOCTYPE_FIELD_DEFAULTS[fieldname]:
			task.set(fieldname, defaults[fieldname])
