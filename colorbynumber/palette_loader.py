"""Marker palette YAML loading and validation."""

# Standard Library
import pathlib

# PIP3 modules
import yaml

# local repo modules
import colorbynumber.marker_color


#============================================
def validate_rgb(rgb_value: object, code: str) -> tuple[int, int, int]:
	"""Validate one YAML RGB triplet.

	Args:
		rgb_value: Parsed YAML value.
		code: Marker code used in error messages.

	Returns:
		The RGB triplet as a tuple.

	Raises:
		ValueError: The value is not three integer channels from 0 through 255.
	"""
	if not isinstance(rgb_value, list) or len(rgb_value) != 3:
		raise ValueError(f"Marker {code} must have exactly three RGB channels")
	if any(type(channel) is not int for channel in rgb_value):
		raise ValueError(f"Marker {code} RGB channels must be integers")
	if any(channel < 0 or channel > 255 for channel in rgb_value):
		raise ValueError(f"Marker {code} RGB channels must be between 0 and 255")
	rgb = (rgb_value[0], rgb_value[1], rgb_value[2])
	return rgb


#============================================
def load_palette(palette_path: pathlib.Path) -> list[colorbynumber.marker_color.MarkerColor]:
	"""Load and validate a marker palette from YAML.

	Args:
		palette_path: YAML file containing a colors list.

	Returns:
		The marker colors in palette order.

	Raises:
		FileNotFoundError: The palette file does not exist.
		ValueError: Required palette data is missing or invalid.
	"""
	if not palette_path.is_file():
		raise FileNotFoundError(f"Palette file does not exist: {palette_path}")
	with palette_path.open("r", encoding="utf-8") as handle:
		document = yaml.safe_load(handle)
	if not isinstance(document, dict) or "colors" not in document:
		raise ValueError("Palette YAML must contain a colors list")
	if not isinstance(document["colors"], list) or not document["colors"]:
		raise ValueError("Palette colors must be a non-empty list")

	palette: list[colorbynumber.marker_color.MarkerColor] = []
	seen_codes: set[str] = set()
	for row in document["colors"]:
		if not isinstance(row, dict):
			raise ValueError("Every palette color must be a mapping")
		code = str(row["code"]).strip()
		name = str(row["name"]).strip()
		if not code or not name:
			raise ValueError("Marker codes and names must not be empty")
		if code in seen_codes:
			raise ValueError(f"Duplicate marker code: {code}")
		rgb = validate_rgb(row["rgb"], code)
		marker = colorbynumber.marker_color.MarkerColor(code=code, name=name, rgb=rgb)
		palette.append(marker)
		seen_codes.add(code)
	return palette
