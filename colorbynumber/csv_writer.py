"""Per-square assignment and palette legend CSV writing."""

# Standard Library
import csv
import pathlib

# PIP3 modules
import numpy

# local repo modules
import colorbynumber.marker_color
import colorbynumber.render_regions


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
	palette: list[colorbynumber.marker_color.MarkerColor],
	output_path: pathlib.Path,
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
) -> None:
	"""Write palette colors and their base-square and rendered-region counts.

	Args:
		palette: Available marker colors.
		output_path: Destination CSV path.
		regions: Concrete printable regions derived from square assignments.
	"""
	colorbynumber.render_regions.validate_regions(regions, len(palette))
	base_counts = [0] * len(palette)
	region_counts = [0] * len(palette)
	for region in regions:
		palette_index = region.palette_index
		base_counts[palette_index] += len(region.member_identifiers)
		region_counts[palette_index] += 1
	with output_path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.writer(handle)
		writer.writerow(("code", "color_name", "red", "green", "blue", "square_count", "region_count"))
		for index, marker in enumerate(palette):
			writer.writerow((
				marker.code,
				marker.name,
				*marker.rgb,
				base_counts[index],
				region_counts[index],
			))
