"""Conversion metric summary writing."""

# Standard Library
import pathlib

# PIP3 modules
import numpy

#============================================
def write_summary(
	input_path: pathlib.Path,
	palette_path: pathlib.Path,
	fit_mode: str,
	page_orientation: str,
	enhancement: str,
	errors: numpy.ndarray,
	output_path: pathlib.Path,
) -> None:
	"""Write a compact conversion summary and perceptual error baseline.

	Args:
		input_path: Original input image path.
		palette_path: Marker palette path.
		fit_mode: Applied image fitting mode.
		page_orientation: Resolved PDF page orientation.
		enhancement: Configured color-enhancement preset.
		errors: Delta E 76 error for every square.
		output_path: Destination text path.
	"""
	rows, columns = errors.shape
	mean_error = float(numpy.mean(errors))
	maximum_error = float(numpy.max(errors))
	lines = [
		f"Input image: {input_path}",
		f"Palette: {palette_path}",
		f"Grid: {columns} columns x {rows} rows",
		f"Square assignments: {columns * rows}",
		"Codes per square: 1",
		f"Fit mode: {fit_mode}",
		f"Page orientation: {page_orientation}",
		"Matching metric: CIE Delta E 76",
		f"Color enhancement: {enhancement}",
		f"Mean Delta E 76: {mean_error:.3f}",
		f"Maximum Delta E 76: {maximum_error:.3f}",
	]
	text = "\n".join(lines) + "\n"
	output_path.write_text(text, encoding="utf-8")
