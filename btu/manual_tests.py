"""Deprecated import path; use :mod:`btu.diagnostics` instead."""

from btu.btu_core.btu_email import send_hello_email_to_current_user as send_hello_email_to_user
from btu.diagnostics.logging_test import test_with_try_except_logging
from btu.diagnostics.rq_workers import (
	bytes_as_list_of_hex,
	test_rq_pickling,
	test_rq_workers1,
	test_rq_workers2,
)
from btu.diagnostics.smoke import ping_now, ping_with_wait
from btu.diagnostics.task_runner import test_taskrunner_1, test_taskrunner_2, test_taskrunner_3

__all__ = [
	"bytes_as_list_of_hex",
	"ping_now",
	"ping_with_wait",
	"send_hello_email_to_user",
	"test_rq_pickling",
	"test_rq_workers1",
	"test_rq_workers2",
	"test_taskrunner_1",
	"test_taskrunner_2",
	"test_taskrunner_3",
	"test_with_try_except_logging",
]
