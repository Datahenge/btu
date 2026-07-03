"""BTU logging diagnostics."""

from btu.logging import logger


def test_with_try_except_logging() -> None:
	"""Exercise BTU logging around a deliberate exception."""
	import warnings
	from time import sleep

	warnings.filterwarnings("ignore", category=DeprecationWarning)

	try:
		sleep(1.5)
		print("Hello World")
		print("Hello Mars")
		raise RuntimeError()
	except Exception as ex:
		logger.error(f"test_with_try_except_logging() : Unhandled exception {ex!r}")
		raise ex
