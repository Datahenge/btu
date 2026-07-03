# Copyright (c) 2025, Datahenge LLC and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

from btu import get_system_datetime_now


class BTURunLater(Document):
	def can_retry(self) -> bool:
		"""
		Can this task be attempted again?
		"""
		if self.do_not_retry:
			return False
		if self.retry_until and (self.retry_until <= get_system_datetime_now()):
			return False
		return True
