"""Webserver-mode liveness: the daemon's last poll, and a ping that is not sent."""

import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import frappe

from btu.btu_api import scheduler


def _cache(value):
	cache = MagicMock()
	cache.get_value.return_value = value
	return cache


class TestSchedulerStatus(unittest.TestCase):
	def test_direct_mode_reports_no_poll_information(self):
		with patch.object(scheduler, "_scheduler_poll_mode", return_value=False):
			status = scheduler.scheduler_status()
		self.assertEqual((status["poll_mode"], status["polling"]), (False, None))

	def test_recent_poll_is_polling_and_an_old_one_is_not(self):
		for age, polling in ((10, True), (scheduler.POLL_STALE_AFTER_SECONDS + 60, False)):
			last = (datetime.now(UTC) - timedelta(seconds=age)).isoformat()
			with (
				self.subTest(age=age),
				patch.object(scheduler, "_scheduler_poll_mode", return_value=True),
				patch.object(frappe, "cache", _cache(last)),
			):
				status = scheduler.scheduler_status()
			self.assertEqual(status["polling"], polling)
			self.assertGreaterEqual(status["seconds_since_poll"], age)

	def test_no_recorded_poll_is_not_polling(self):
		with (
			patch.object(scheduler, "_scheduler_poll_mode", return_value=True),
			patch.object(frappe, "cache", _cache(None)),
		):
			status = scheduler.scheduler_status()
		self.assertEqual((status["polling"], status["last_poll_utc"]), (False, None))

	def test_polling_for_commands_records_the_poll(self):
		from btu.btu_api import endpoints

		redis_conn = MagicMock()
		redis_conn.lpop.return_value = None
		with (
			patch.object(frappe, "only_for"),
			patch.object(scheduler, "_get_redis_connection", return_value=redis_conn),
			patch.object(scheduler, "record_scheduler_poll") as record,
		):
			self.assertEqual(endpoints.get_pending_scheduler_commands(), [])
		record.assert_called_once()
