"""Deprecated import path; use :mod:`btu.samples` instead."""

from btu.btu_core.housekeeping import cleanup_transient_tasks
from btu.samples.aware import btu_aware_example1
from btu.samples.errors import wait_then_throw_error
from btu.samples.simple import ordinary_function

__all__ = [
	"btu_aware_example1",
	"cleanup_transient_tasks",
	"ordinary_function",
	"wait_then_throw_error",
]
