"""BTU Run Later DocType controller."""

# Copyright (c) 2021-2026, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from btu import get_system_datetime_now
from btu.btu_core.form_options import validate_rq_queue_name


class BTURunLater(Document):
	"""Deferred task execution record with optional retry limits."""

	def validate(self) -> None:
		"""Validate deferred task configuration."""
		validate_rq_queue_name(self.redis_queue_name)

	def can_retry(self) -> bool:
		"""Return whether this deferred task may be attempted again."""
		if self.do_not_retry:
			return False
		if self.retry_until and (self.retry_until <= get_system_datetime_now()):
			return False
		return True
