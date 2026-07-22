"""Conversion metric summary writing."""

# Standard Library
import pathlib

# PIP3 modules
import numpy

# local repo modules
import colorbynumber.constants


#============================================
def write_summary(
	input_path: pathlib.Path,
	palette_path: pathlib.Path,
	fit_mode: str,
	errors: numpy.ndarray,
	output_path: pathlib.Path,
) -> None:
	"""Write a compact conversion summary and perceptual error baseline.

	Args:
		input_path: Original input image path.
		palette_path: Marker palette path.
		fit_mode: Applied image fitting mode.
		errors: Delta E 76 error for every square.
		output_path: Destination text path.
	"""
	columns = colorbynumber.constants.GRID_COLUMNS
	rows = colorbynumber.constants.GRID_ROWS
	mean_error = float(numpy.mean(errors))
	maximum_error = float(numpy.max(errors))
	lines = [
		f"Input image: {input_path}",
		f"Palette: {palette_path}",
		f"Grid: {columns} columns x {rows} rows",
		f"Square assignments: {columns * rows}",
		"Codes per square: 1",
		f"Fit mode: {fit_mode}",
		"Color distance: CIE Delta E 76",
		f"Mean color distance: {mean_error:.3f}",
		f"Maximum color distance: {maximum_error:.3f}",
	]
	text = "\n".join(lines) + "\n"
	output_path.write_text(text, encoding="utf-8")
