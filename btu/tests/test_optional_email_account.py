"""A missing Default Email Account warns and skips email instead of failing."""

import unittest
from unittest.mock import patch

import frappe

from btu.btu_core import btu_email


class _Config(frappe._dict):
	pass


def _config(**values):
	return _Config(default_email_account=None, environment_name=None, email_body_is_html=0, **values)


class TestOptionalEmailAccount(unittest.TestCase):
	def test_emailer_skips_with_a_warning_and_sends_nothing(self):
		with (
			patch.object(frappe, "get_single", return_value=_config()),
			patch.object(frappe, "sendmail") as sendmail,
			patch.object(frappe, "logger") as logger,
			patch.object(btu_email, "print_both"),
		):
			sent = btu_email.Emailer(subject="Hi", body="Body", emailto_list="a@example.com").send()
		self.assertFalse(sent)
		sendmail.assert_not_called()
		logger.return_value.warning.assert_called_once()

	def test_configuration_validate_warns_instead_of_throwing(self):
		from btu.btu_core.doctype.btu_configuration.btu_configuration import BTUConfiguration

		doc = BTUConfiguration.__new__(BTUConfiguration)
		doc.default_email_account = None
		doc.queue_name = "default"
		with (
			patch.object(frappe, "msgprint") as msgprint,
			patch.object(frappe, "throw") as throw,
			patch("btu.btu_core.doctype.btu_configuration.btu_configuration.validate_rq_queue_name"),
		):
			doc.validate()
		msgprint.assert_called_once()
		throw.assert_not_called()
