"""Suppress DeprecationWarning in RQ workers before job execution."""

import warnings

print("Module 'supress_deprecation_warnings' is loading")


def init() -> None:
	"""Register a filter to ignore DeprecationWarning in worker processes."""
	warnings.filterwarnings("ignore", category=DeprecationWarning)
