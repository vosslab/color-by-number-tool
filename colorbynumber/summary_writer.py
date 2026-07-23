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
	merge_regions: bool,
	rendered_region_count: int,
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
		merge_regions: Whether same-color edge-connected shapes were merged.
		rendered_region_count: Number of printable regions after optional merging.
	"""
	rows, columns = errors.shape
	base_shape_count = columns * rows
	if isinstance(rendered_region_count, bool) or not isinstance(rendered_region_count, int):
		raise ValueError("Rendered region count must be an integer")
	if rendered_region_count <= 0 or rendered_region_count > base_shape_count:
		raise ValueError("Rendered region count must be within the assignment count")
	mean_error = float(numpy.mean(errors))
	maximum_error = float(numpy.max(errors))
	lines = [
		f"Input image: {input_path}",
		f"Palette: {palette_path}",
		f"Grid: {columns} columns x {rows} rows",
		f"Square assignments: {base_shape_count}",
		f"Merge same-color regions: {'enabled' if merge_regions else 'disabled'}",
		(
			f"Rendered regions: {rendered_region_count} "
			f"(reduction: {base_shape_count - rendered_region_count})"
		),
		"Codes per rendered region: 1",
		f"Fit mode: {fit_mode}",
		f"Page orientation: {page_orientation}",
		"Matching metric: CIE Delta E 76",
		f"Color enhancement: {enhancement}",
		f"Mean Delta E 76: {mean_error:.3f}",
		f"Maximum Delta E 76: {maximum_error:.3f}",
	]
	text = "\n".join(lines) + "\n"
	output_path.write_text(text, encoding="utf-8")
