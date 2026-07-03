"""Documentation site context configuration for BTU."""

from typing import Protocol


class DocsContext(Protocol):
	"""Minimal context object used by the BTU docs template."""

	brand_html: str


def get_context(context: DocsContext) -> None:
	"""Set branding for the BTU documentation context."""
	context.brand_html = "Background Tasks Unleashed"
