"""Suppress DeprecationWarning in RQ workers.

Frappe sets ``warnings.simplefilter('always', DeprecationWarning)`` when
``DEV_SERVER`` is true (``bench start`` sets this for all Procfile processes).
That overrides ``PYTHONWARNINGS`` ignore rules. The worker Procfile line sets
``DEV_SERVER=0`` so the env var can take effect.  This module is a fallback when
jobs run with dev-mode warning filters still active.
"""

import warnings


def init() -> None:
	"""Register after Frappe import; must run after its 'always' DeprecationWarning filter."""
	warnings.filterwarnings("ignore", category=DeprecationWarning)
