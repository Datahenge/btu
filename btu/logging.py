"""BTU application logging configuration and helpers."""

from __future__ import annotations

import logging


class AppLoggerBuilder:
	"""Build and configure the BTU application logger."""

	FALLBACK_LOG_LEVEL = logging.INFO

	logger: logging.Logger

	@staticmethod
	def get_default_formatter() -> logging.Formatter:
		"""Return the standard BTU log line formatter."""
		return logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")

	def add_stdout_handler(self) -> None:
		"""Add a stdout handler for INFO-level and above."""
		stdout_handler = logging.StreamHandler()
		stdout_handler.setFormatter(AppLoggerBuilder.get_default_formatter())
		stdout_handler.setLevel(logging.INFO)
		self.logger.addHandler(stdout_handler)

	def set_level(self, new_level: int | None = None) -> None:
		"""Set the logger level, defaulting to INFO."""
		self.logger.setLevel(new_level or logging.INFO)

	def setup_logger(self, logger_name: str | None = None) -> logging.Logger:
		"""Find or create a configured logger instance."""
		self.logger = logging.getLogger(logger_name or __name__)
		self.logger.propagate = False
		self.set_level(logging.DEBUG)

		self.logger.handlers = []
		self.add_stdout_handler()

		return self.logger


logging.basicConfig(level=AppLoggerBuilder.FALLBACK_LOG_LEVEL)
logger = AppLoggerBuilder().setup_logger()

# NOTE: Do not call logger.debug/info at module level — can cause infinite loops during frappe.enqueue().
