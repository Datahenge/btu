# Copyright (c) 2021-2023, Datahenge LLC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class BTUQueue(Document):

	def validate(self):
		"""
		Standard controller method.
		"""
		queue_names_per_common_site_config = [ each["name"] for each in frappe.local.conf.worker_queues ]
		if self.name not in queue_names_per_common_site_config:
			raise ValueError(f"Queue name '{self.rq_name}' is invalid; not found in 'common_site_config.json'")
