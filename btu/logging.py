""" ftp/logger/__init__.py """

# https://docs.python.org/3/howto/logging-cookbook.html

# ########
# EXAMPLE
#
# 	from ftp.app_logging import logger
#	logger.info("This is an info message")
#
# ########

from inspect import getfullargspec
import logging
import os
import pathlib

from frappe.utils import get_bench_path


class BraceMessage():
	""" Custom """
	def __init__(self, fmt, args, kwargs):
		self.fmt = fmt
		self.args = args
		self.kwargs = kwargs

	def __str__(self):
		return str(self.fmt).format(*self.args, **self.kwargs)


class StyleAdapter(logging.LoggerAdapter):
	""" Custom """
	# pylint: disable=super-init-not-called
	def __init__(self, some_logger):
		self.logger = some_logger

	def log(self, level, msg, *args, **kwargs):
		if self.isEnabledFor(level):
			msg, log_kwargs = self.process(msg, kwargs)
			# pylint: disable=protected-access
			self.logger._log(level, BraceMessage(msg, args, kwargs), (),
							 **log_kwargs)

	def process(self, msg, kwargs):
		# pylint: disable=protected-access
		return msg, {key: kwargs[key]
					 for key in getfullargspec(self.logger._log).args[1:] if key in kwargs}


class AppLogger(logging.Logger):
	"""
	Override the standard logging.logger() class
	"""

	def __init__(self, name, level=logging.NOTSET):
		super().__init__(name, level)
		self.linux_pid = os.getpid()
		self.extra_info = None

	def info(self, msg, *args, xtra=None, **kwargs):
		extra_info = xtra if xtra is not None else self.extra_info
		super().info(msg, *args, extra=extra_info, **kwargs)


class AppLoggerBuilder():

	LOGFILE_DIRPATH = pathlib.Path(get_bench_path()) / "logs"
	LOGFILE_NAME = 'ftp.log'
	FALLBACK_LOG_LEVEL = logging.INFO

	@staticmethod
	def get_default_formatter():
		formatter = logging.Formatter('%(asctime)s | %(name)s | %(levelname)s | %(message)s')
		# formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
		return formatter

	def add_file_handler(self):
		"""
		Add a file handler to the logger.
		"""
		if not AppLoggerBuilder.LOGFILE_DIRPATH.exists():
			raise IOError(f"Logging directory '{AppLoggerBuilder.LOGFILE_DIRPATH}' does not exist")

		logfile_path = AppLoggerBuilder.LOGFILE_DIRPATH / AppLoggerBuilder.LOGFILE_NAME
		file_handler = logging.FileHandler(filename=pathlib.Path(logfile_path).resolve(),
									       mode='a',
									       encoding='utf-8')
		file_handler.setFormatter(AppLoggerBuilder.get_default_formatter())
		file_handler.setLevel(logging.DEBUG)  # Log everything includding DEBUG messages
		self.logger.addHandler(file_handler)

	def add_stdout_handler(self):
		"""
		Add a stdout handler to the logger.
		"""
		stdout_handler = logging.StreamHandler()
		stdout_handler.setFormatter(AppLoggerBuilder.get_default_formatter())
		stdout_handler.setLevel(logging.INFO)  # Only show INFO or greater.
		self.logger.addHandler(stdout_handler)

	def set_level(self, new_level=None):
		# logger.level = logging.getLevelName(logging_level)
		self.logger.setLevel(new_level or logging.INFO)

	def setup_logger(self, logger_name=None):
		"""
		Find or create an instance of the logger.
		"""

		self.logger = logging.getLogger(logger_name or __name__)
		self.logger.propagate = False  # prevents automatically writing to STDOUT
		self.set_level(logging.DEBUG)  # TODO: Read this from Redis or SQL?

		# Handlers
		self.logger.handlers = []
		self.add_stdout_handler()
		self.add_file_handler()

		# return StyleAdapter(self.logger)  # Adds support for pseudo f-strings.
		return self.logger


def does_logger_exist(logger_name) -> bool:
	"""
	Useful to determine whether a logger needs to be fully instantiated, or not.
	"""
	return logger_name in logging.Logger.manager.loggerDict


# These should be the final 2 lines of the module:
logging.basicConfig(level=AppLoggerBuilder.FALLBACK_LOG_LEVEL)
logger = AppLoggerBuilder().setup_logger()

# NOTE: WARNING: Absolutely do NOT write any "logger.debug" or "logger.info" statements out here in the open.
#       You WILL trigger an INFINITE LOOP due to Python code initializing within FRAPPE.ENQUEUE()
#       You have been warned.
