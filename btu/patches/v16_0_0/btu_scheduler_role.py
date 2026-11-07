"""Make the BTU Scheduler role an API-only role (no Desk access)."""

from btu.setup import ensure_scheduler_role


def execute():
	ensure_scheduler_role()
