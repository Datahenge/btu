"""Tests for auto-report delivery target validation."""

import unittest

from btu.btu_core.auto_report import DeliveryTarget


class TestDeliveryTargetSchema(unittest.TestCase):
	"""Tests for DeliveryTarget dictionary validation."""

	def _minimal_content(self) -> dict:
		return {
			"type": "tabular",
			"columns": [{"fieldname": "name", "label": "Name"}],
			"rows": [{"name": "TODO-1"}],
		}

	def test_valid_email_target(self) -> None:
		target = DeliveryTarget.init_from_dictionary(
			{
				"report_key": "ToDo",
				"report_content": self._minimal_content(),
				"target_type": "Email",
				"target_details": "reports@example.com",
				"report_format": "HTML",
			}
		)
		self.assertEqual(target.target_type, "Email")

	def test_invalid_target_type_rejected(self) -> None:
		with self.assertRaises(Exception):
			DeliveryTarget.init_from_dictionary(
				{
					"report_key": "ToDo",
					"report_content": self._minimal_content(),
					"target_type": "Fax",
					"target_details": "x",
					"report_format": "HTML",
				}
			)
