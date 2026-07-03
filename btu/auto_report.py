"""Automatic report generation and delivery for BTU tasks."""

# A better replacement for the broken ERPNext "Auto Report" feature.
# Much of this code shamelessly borrowed from "frappe/frappe/email/doctype/auto_email_report/auto_email_report.py"

from typing import Any

import frappe
from frappe import _
from frappe.utils import (
	format_time,
	get_link_to_form,
	get_url_to_report,
	global_date_format,
	now,
	validate_email_address,
)
from frappe.utils.csvutils import to_csv
from frappe.utils.xlsxutils import make_xlsx
from schema import And, Schema

ReportColumns = list[Any]
ReportRows = list[dict[str, Any]]


def make_links(columns: ReportColumns, data: ReportRows) -> tuple[ReportColumns, ReportRows]:
	"""Replace Link and Currency field values with formatted HTML links."""
	for row in data:
		doc_name = row.get("name")
		for col in columns:
			if col.fieldtype == "Link" and col.options != "Currency":
				if col.options and row.get(col.fieldname):
					row[col.fieldname] = get_link_to_form(col.options, row[col.fieldname])
			elif col.fieldtype == "Dynamic Link":
				if col.options and row.get(col.fieldname) and row.get(col.options):
					row[col.fieldname] = get_link_to_form(row[col.options], row[col.fieldname])
			elif col.fieldtype == "Currency" and row.get(col.fieldname):
				doc = frappe.get_doc(col.parent, doc_name) if doc_name else None
				# Pass the Document to get the currency based on docfield option
				row[col.fieldname] = frappe.format_value(row[col.fieldname], col, doc=doc)
	return columns, data


def update_field_types(columns: ReportColumns) -> ReportColumns:
	"""Convert Link and Currency columns to plain Data columns for export."""
	for col in columns:
		if col.fieldtype in ("Link", "Dynamic Link", "Currency") and col.options != "Currency":
			col.fieldtype = "Data"
			col.options = ""
	return columns


def get_html_table(
	report_key: str,
	columns: ReportColumns | None = None,
	data: ReportRows | None = None,
) -> str:
	"""Render the auto-email report HTML template for the given report data."""
	date_time = global_date_format(now()) + " " + format_time(now())
	report_doctype, report_type = frappe.db.get_value(
		"Report", report_key, fieldname=["ref_doctype", "report_type"]
	)

	return frappe.render_template(
		"frappe/templates/emails/auto_email_report.html",
		{
			"title": "BTU Automatic Report",
			"description": report_key,
			"date_time": date_time,
			"columns": columns,
			"data": data,
			"report_url": get_url_to_report(report_key, report_type, report_doctype),
			"report_name": report_key,
			"edit_report_settings": "Not Applicable",
		},
	)


class DeliveryTarget:
	"""A single target for delivering report content."""

	valid_target_types = ("Email", "File", "Slack")
	valid_report_formats = ("HTML", "XLSX", "CSV")

	@staticmethod
	def get_data_dictionary_schema() -> Schema:
		"""Return the schema used to validate delivery-target dictionaries."""
		schema = Schema(
			{
				"report_key": str,
				"report_content": dict,
				"target_type": And(str, len, lambda s: s in DeliveryTarget.valid_target_types),
				"target_details": str,
				"report_format": And(str, len, lambda s: s in DeliveryTarget.valid_report_formats),
			}
		)
		return schema

	@staticmethod
	def init_from_dictionary(data_dictionary: dict[str, Any]) -> "DeliveryTarget":
		"""Construct a DeliveryTarget from a validated dictionary."""
		DeliveryTarget.get_data_dictionary_schema().validate(
			data_dictionary
		)  # validate the Dictionary matches required schema

		instance = DeliveryTarget(
			report_key=data_dictionary["report_key"],
			report_content=data_dictionary["report_content"],
			target_type=data_dictionary["target_type"],
			target_details=data_dictionary["target_details"],
			report_format=data_dictionary["report_format"],
		)
		return instance

	def __init__(
		self,
		report_key: str,
		report_content: dict[str, Any],
		target_type: str,
		target_details: str,
		report_format: str,
	) -> None:
		"""Initialize a new target for report delivery."""
		self.report_key = report_key

		if not isinstance(report_content, dict):
			raise TypeError("Argument 'report_content' should be a Python Dictionary type.")
		if report_content["type"] != "tabular":
			raise ValueError(f"Not sure how to handle content type '{report_content['type']}'")

		self.report_content = report_content
		self.target_type = target_type
		self.target_details = target_details
		self.report_format = report_format
		self.validate_all()

	@staticmethod
	def get_spreadsheet_data(columns: ReportColumns, data: ReportRows) -> list[list[Any]] | None:
		"""Convert report columns and rows into a 2-D list suitable for CSV/XLSX export."""
		if (not columns) or (not data):
			print("Warning: Function get_spreadsheet_data() does not have both columns and data.")
			return None

		out: list[list[Any]] = [
			[_(df.label) for df in columns],
		]
		for row in data:
			new_row: list[Any] = []
			out.append(new_row)
			for df in columns:
				if df.fieldname not in row:
					continue
				new_row.append(frappe.format(row[df.fieldname], df, row))

		return out

	def validate_all(self) -> None:
		"""Run all delivery-target validation checks."""
		self.validate_target_type()
		self.validate_report_format()
		self.validate_target_details()

	def validate_target_type(self) -> None:
		"""Validate the target type attribute."""
		if self.target_type not in DeliveryTarget.valid_target_types:
			frappe.throw(
				_("{0} is not a valid Target Type (should one of the following {1})").format(
					frappe.bold(self.report_format), frappe.bold(", ".join(DeliveryTarget.valid_target_types))
				)
			)

	def validate_report_format(self) -> None:
		"""Validate the report format attribute."""
		if self.report_format not in DeliveryTarget.valid_report_formats:
			frappe.throw(
				_("{0} is not a valid report format. Report format should one of the following {1}").format(
					frappe.bold(self.report_format),
					frappe.bold(", ".join(DeliveryTarget.valid_report_formats)),
				)
			)

	def validate_target_details(self) -> list[str]:
		"""Validate and return parsed email recipients for Email targets."""
		if self.target_type == "Email":
			recipients = self.target_details.replace(
				",", ";"
			)  # allows for splitting by either comma or semicolon
			valid: list[str] = []
			for each_email in recipients.split(";"):
				if each_email:
					validate_email_address(each_email, True)
					valid.append(each_email)

			return valid

		raise ValueError(f"DeliveryTarget : Unhandled target type = '{self.target_type}'")

	def get_email_recipients(self) -> list[str]:
		"""Return the validated list of email recipients."""
		return self.validate_target_details()

	def get_file_name(self) -> str:
		"""Return a filesystem-safe attachment filename for this report."""
		prefix = self.report_key.replace(" ", "-").replace("/", "-")
		suffix = self.report_format.lower()
		return f"{prefix}.{suffix}"

	def generate_output(self) -> str | bytes | None:
		"""Build report output in the configured format, or None when there are no rows."""
		report_columns = self.report_content["columns"]
		report_rows = self.report_content["rows"]
		if not report_rows:
			return None

		if self.report_format == "HTML":
			columns, data = make_links(report_columns, report_rows)
			columns = update_field_types(columns)
			return get_html_table(self.report_key, columns, data)

		if self.report_format == "XLSX":
			spreadsheet_data = self.get_spreadsheet_data(report_columns, report_rows)
			xlsx_file = make_xlsx(spreadsheet_data, "Auto Email Report")
			return xlsx_file.getvalue()

		if self.report_format == "CSV":
			spreadsheet_data = self.get_spreadsheet_data(report_columns, report_rows)
			return to_csv(spreadsheet_data)

		frappe.throw(_("Invalid Output Format"))
		return None

	def send(self) -> None:
		"""Deliver the generated report to the configured target."""
		# TODO: Send for different target destinations, not just frappe.sendmail

		email_content = self.generate_output()
		if not email_content:
			return  # do not transmit empty reports

		attachments = None
		if self.report_format == "HTML":
			message = email_content
		else:
			message = get_html_table(self.report_key, email_content)
			attachments = [{"fname": self.get_file_name(), "fcontent": email_content}]

		if self.target_type == "Email":
			frappe.sendmail(
				recipients=self.get_email_recipients(),
				subject=self.report_key,
				message=message,
				delayed=False,
				attachments=attachments,
				reference_doctype="Report",
				reference_name=self.report_key,
			)


class BTUReport:
	"""Build a Frappe report and deliver it to one or more targets."""

	def __init__(
		self,
		report_key: str,
		report_parameters: dict[str, Any] | None = None,
		delivery_targets: list[dict[str, Any]] | None = None,
	) -> None:
		"""Initialize a BTU report runner with delivery targets."""
		if (not report_key) or (not isinstance(report_key, str)):
			raise TypeError("Missing mandatory string argument 'report_key'")

		self.report_key = report_key
		self.doc_report = frappe.get_doc("Report", self.report_key)

		self.report_parameters = report_parameters or {}
		self.delivery_target_dicts = delivery_targets
		if not self.delivery_target_dicts:
			raise ValueError("BTU Report has no targets for report delivery.")

		self.validate_mandatory_fields()
		self.report_content: tuple[ReportColumns | None, ReportRows | None] = (None, None)

	def validate_mandatory_fields(self) -> None:
		"""Verify that the report's mandatory filters are specified."""
		filters = frappe.parse_json(self.report_parameters) if self.report_parameters else {}
		# filter_meta = frappe.parse_json(self.filter_meta) if self.filter_meta else {}
		filter_meta: list[dict[str, Any]] = []

		throw_list: list[str] = []
		for meta in filter_meta:
			if meta.get("reqd") and not filters.get(meta["fieldname"]):
				throw_list.append(meta["label"])
		if throw_list:
			frappe.throw(
				title=_("Missing Filters Required"),
				msg=_("Following Report Filters have missing values:")
				+ "<br><br><ul><li>"
				+ " <li>".join(throw_list)
				+ "</ul>",
			)

	def build_report(self) -> tuple[ReportColumns | None, ReportRows | None]:
		"""Build report columns and row data, or return ``(None, None)`` when empty."""
		filters = frappe.parse_json(self.report_parameters) if self.report_parameters else {}

		columns, data = self.doc_report.get_data(
			limit=None, user="Administrator", filters=filters, as_dict=True, ignore_prepared_report=True
		)

		if not data:
			return None, None

		# Add row numbers:
		columns.insert(0, frappe._dict(fieldname="idx", label="", width="30px"))  # pylint: disable=protected-access
		for index, each_dict in enumerate(data):
			each_dict["idx"] = index + 1

		# We now have data, a List of Dictionary.
		if len(data) == 0:
			return None, None

		return columns, data

	def transmit_report(self) -> None:
		"""Send the built report to each configured delivery target."""
		if not self.report_content:
			print("Report has no rows.  Nothing to transmit.")
			return

		# Loop through all the Targets, and transmit the report data.
		print(
			f"...report data built successfully.  Attempting to transmit to {len(self.delivery_target_dicts)} targets ..."
		)
		for each in self.delivery_target_dicts:
			each["report_key"] = self.report_key
			each["report_content"] = {
				"type": "tabular",
				"columns": self.report_content[0],
				"rows": self.report_content[1],
			}
			instance = DeliveryTarget.init_from_dictionary(each)
			instance.send()

	def run(self) -> None:
		"""Build the report, then transmit it to all target destinations."""
		print(f"BTU is attempting to run report '{self.report_key}' and automatically deliver...")
		self.report_content = self.build_report()
		self.transmit_report()
		print("---End of Function---")


@frappe.whitelist()
def run_btu_report(*_args: object, **kwargs: object) -> None:
	"""Whitelisted entry point for BTU automatic report tasks."""
	instance = BTUReport(
		**kwargs
	)  # dereference because BTUReport instance requires individual arguments; not a Dictionary.
	instance.run()
