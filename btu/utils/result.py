"""Result type for BTU task outcomes."""

from __future__ import annotations

from typing import Any

NoneType = type(None)


class Result:
	"""Success/failure result inspired by Rust's Result type."""

	def __init__(
		self,
		success: bool,
		message: str | dict[str, Any] | list[Any] | int | None,
		execution_time: float | None = None,
	) -> None:
		"""Initialize with success flag, message, and optional execution time in seconds."""
		if not isinstance(success, bool):
			raise TypeError("Result class argument 'success' must be a boolean.")
		if message:
			if isinstance(message, bool):
				message = "True" if message else "False"
			if not isinstance(message, (str, dict, list, int, NoneType)):
				raise TypeError(
					f"Result class argument 'message' must be a Python String, Integer, List, or Dictionary.  Found a type '{type(message)}' instead."
				)
		self.okay = success
		self.message = message or None
		self.execution_time = round(execution_time, 2) if execution_time else None

	def __bool__(self) -> bool:
		"""Return whether this result represents success."""
		return self.okay

	def as_json(self) -> dict[str, Any]:
		"""Return a dictionary representation of this result."""
		return {"okay": self.okay, "message": self.message, "execution_time": self.execution_time}

	def as_msgprint(self) -> str:
		"""Return an HTML-formatted message suitable for frappe.msgprint."""
		msg = f"Success: {self.okay}"
		if self.execution_time:
			msg += f"<br>Execution Time: {self.execution_time} seconds."
		msg += f"<br><br>Message: {self.message}"
		return msg
