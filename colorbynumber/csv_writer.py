"""Per-square assignment and palette legend CSV writing."""

# Standard Library
import csv
import pathlib

# PIP3 modules
import numpy

# local repo modules
import colorbynumber.marker_color


#============================================
def write_assignments_csv(
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
	output_path: pathlib.Path,
) -> None:
	"""Write the selected marker code for every grid position.

	Args:
		indices: Palette index for every square.
		palette: Available marker colors.
		output_path: Destination CSV path.
	"""
	rows, columns = indices.shape
	with output_path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.writer(handle)
		writer.writerow(("row", "column", "code", "color_name", "red", "green", "blue"))
		for row in range(rows):
			for column in range(columns):
				marker = palette[int(indices[row, column])]
				writer.writerow((row + 1, column + 1, marker.code, marker.name, *marker.rgb))


#============================================
def write_legend_csv(
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
	output_path: pathlib.Path,
) -> None:
	"""Write palette colors and the number of assigned squares.

	Args:
		indices: Palette index for every square.
		palette: Available marker colors.
		output_path: Destination CSV path.
	"""
	counts = numpy.bincount(indices.reshape(-1), minlength=len(palette))
	with output_path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.writer(handle)
		writer.writerow(("code", "color_name", "red", "green", "blue", "square_count"))
		for marker, count in zip(palette, counts, strict=True):
			writer.writerow((marker.code, marker.name, *marker.rgb, int(count)))
