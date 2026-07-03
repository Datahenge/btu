"""BTU application logging configuration and helpers."""

from __future__ import annotations

import logging
import os
import pathlib
from inspect import getfullargspec
from typing import Any

from frappe.utils import get_bench_path


class BraceMessage:
	"""Format string with deferred args/kwargs for logging."""

	def __init__(self, fmt: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
		"""Store format string and deferred formatting arguments."""
		self.fmt = fmt
		self.args = args
		self.kwargs = kwargs

	def __str__(self) -> str:
		"""Return the formatted message string."""
		return str(self.fmt).format(*self.args, **self.kwargs)


class StyleAdapter(logging.LoggerAdapter):
	"""Logger adapter that supports brace-style message formatting."""

	# pylint: disable=super-init-not-called
	def __init__(self, some_logger: logging.Logger) -> None:
		"""Wrap the given logger for brace-style formatting."""
		self.logger = some_logger

	def log(self, level: int, msg: str, *args: object, **kwargs: object) -> None:
		"""Log a message at the given level using brace-style formatting."""
		if self.isEnabledFor(level):
			msg, log_kwargs = self.process(msg, kwargs)
			# pylint: disable=protected-access
			self.logger._log(level, BraceMessage(msg, args, kwargs), (), **log_kwargs)

	def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
		"""Filter kwargs to those accepted by the underlying logger."""
		# pylint: disable=protected-access
		return msg, {key: kwargs[key] for key in getfullargspec(self.logger._log).args[1:] if key in kwargs}


class AppLogger(logging.Logger):
	"""Logger subclass with optional extra context for info messages."""

	def __init__(self, name: str, level: int = logging.NOTSET) -> None:
		"""Initialize logger with process id and optional extra context."""
		super().__init__(name, level)
		self.linux_pid = os.getpid()
		self.extra_info: dict[str, Any] | None = None

	def info(self, msg: str, *args: object, xtra: dict[str, Any] | None = None, **kwargs: object) -> None:
		"""Log an info message with optional extra context."""
		extra_info = xtra if xtra is not None else self.extra_info
		super().info(msg, *args, extra=extra_info, **kwargs)


class AppLoggerBuilder:
	"""Build and configure the BTU application logger."""

	LOGFILE_DIRPATH = pathlib.Path(get_bench_path()) / "logs"
	LOGFILE_NAME = "ftp.log"
	FALLBACK_LOG_LEVEL = logging.INFO

	logger: logging.Logger

	@staticmethod
	def get_default_formatter() -> logging.Formatter:
		"""Return the standard BTU log line formatter."""
		return logging.Formatter("%(asctime)s | %(name)s | %(levelname)s | %(message)s")

	def add_file_handler(self) -> None:
		"""Add a file handler writing to the bench logs directory."""
		if not AppLoggerBuilder.LOGFILE_DIRPATH.exists():
			raise OSError(f"Logging directory '{AppLoggerBuilder.LOGFILE_DIRPATH}' does not exist")

		logfile_path = AppLoggerBuilder.LOGFILE_DIRPATH / AppLoggerBuilder.LOGFILE_NAME
		file_handler = logging.FileHandler(
			filename=pathlib.Path(logfile_path).resolve(), mode="a", encoding="utf-8"
		)
		file_handler.setFormatter(AppLoggerBuilder.get_default_formatter())
		file_handler.setLevel(logging.DEBUG)
		self.logger.addHandler(file_handler)

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
		self.add_file_handler()

		return self.logger


def does_logger_exist(logger_name: str) -> bool:
	"""Return True if a logger with the given name is already registered."""
	return logger_name in logging.Logger.manager.loggerDict


logging.basicConfig(level=AppLoggerBuilder.FALLBACK_LOG_LEVEL)
logger = AppLoggerBuilder().setup_logger()

# NOTE: Do not call logger.debug/info at module level — can cause infinite loops during frappe.enqueue().
