"""Marker color data model."""

# Standard Library
import dataclasses


@dataclasses.dataclass(frozen=True)
class MarkerColor:
	"""One marker code and its chart-derived display color."""

	code: str
	name: str
	rgb: tuple[int, int, int]
