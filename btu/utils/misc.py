"""Miscellaneous small helpers."""

import os


def encode_slack_text(any_text: str) -> str:
	"""Encode characters required for Slack message formatting."""
	any_text = any_text.replace("&", "&amp;")
	any_text = any_text.replace("<", "&lt;")
	any_text = any_text.replace(">", "&gt;")
	any_text = any_text.replace("|", "%7C")
	return any_text


def is_env_var_set(variable_name: str) -> bool:
	"""Return True if an environment variable is set to 1."""
	if not variable_name:
		return False
	variable_value = os.environ.get(variable_name)
	if not variable_value:
		return False
	try:
		return int(variable_value) == 1
	except Exception:
		return False
