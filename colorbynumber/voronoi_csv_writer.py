"""Stable CSV artifacts for the separate bounded-Voronoi output pathway."""

# Standard Library
import csv
import pathlib

# PIP3 modules
import numpy

# local repo modules
import colorbynumber.marker_color
import colorbynumber.render_regions
import colorbynumber.voronoi_geometry


#============================================
def _validate_palette(
	palette: list[colorbynumber.marker_color.MarkerColor],
) -> None:
	"""Validate the marker palette shared by Voronoi CSV artifacts.

	Args:
		palette: Ordered marker colors available to the polygon assignments.

	Raises:
		ValueError: The palette is empty or has an unsupported marker entry.
	"""
	if not palette:
		raise ValueError("Voronoi palette must not be empty")
	for marker in palette:
		if not isinstance(marker, colorbynumber.marker_color.MarkerColor):
			raise ValueError("Voronoi palette entries must be MarkerColor values")


#============================================
def _validate_indices(
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
	*,
	expected_count: int | None,
) -> None:
	"""Validate one-dimensional integer palette assignments.

	Args:
		indices: Site-ordered palette indexes.
		palette: Ordered marker colors available to the assignments.
		expected_count: Required site count, or ``None`` for legend-only output.

	Raises:
		ValueError: Assignment shape, type, count, or bounds are invalid.
	"""
	if not isinstance(indices, numpy.ndarray):
		raise ValueError("Voronoi palette assignments must be a NumPy array")
	if indices.ndim != 1 or indices.size == 0:
		raise ValueError("Voronoi palette assignments must be a nonempty one-dimensional array")
	if not numpy.issubdtype(indices.dtype, numpy.integer):
		raise ValueError("Voronoi palette assignments must be integers")
	if expected_count is not None and indices.size != expected_count:
		raise ValueError("Voronoi palette assignments must follow stable site order")
	if numpy.any(indices < 0) or numpy.any(indices >= len(palette)):
		raise ValueError("Voronoi palette assignments must identify available colors")


#============================================
def _validate_partition(
	partition: colorbynumber.voronoi_geometry.Partition,
) -> None:
	"""Validate that a partition keeps the owned zero-based site order.

	Args:
		partition: Bounded partition used to identify assignment rows.

	Raises:
		ValueError: The partition does not preserve a complete owned site order.
	"""
	if not isinstance(partition, colorbynumber.voronoi_geometry.Partition):
		raise ValueError("Voronoi assignments require a bounded Partition")
	if len(partition.sites) != partition.domain.site_count:
		raise ValueError("Voronoi partition sites must match the domain site count")
	if len(partition.cells) != partition.domain.site_count:
		raise ValueError("Voronoi partition cells must match the domain site count")
	for identifier, (site, cell) in enumerate(zip(partition.sites, partition.cells, strict=True)):
		if site.identifier != identifier or cell.site_identifier != identifier:
			raise ValueError("Voronoi partition sites must use stable zero-based identifiers")


#============================================
def _validate_source_values(
	polygon_rgb: numpy.ndarray,
	errors: numpy.ndarray,
	site_count: int,
) -> None:
	"""Validate per-polygon sampled RGB and Delta E values.

	Args:
		polygon_rgb: Source RGB sample for every site.
		errors: Delta E 76 error for every site.
		site_count: Required number of stable polygon rows.

	Raises:
		ValueError: Source samples or matching errors have invalid shape or values.
	"""
	if not isinstance(polygon_rgb, numpy.ndarray):
		raise ValueError("Voronoi source RGB values must be a NumPy array")
	if polygon_rgb.shape != (site_count, 3):
		raise ValueError("Voronoi source RGB values must have one RGB triplet per site")
	if not numpy.issubdtype(polygon_rgb.dtype, numpy.number) or numpy.issubdtype(
		polygon_rgb.dtype, numpy.complexfloating
	):
		raise ValueError("Voronoi source RGB values must be numeric")
	if not numpy.all(numpy.isfinite(polygon_rgb)):
		raise ValueError("Voronoi source RGB values must be finite")
	if not isinstance(errors, numpy.ndarray):
		raise ValueError("Voronoi Delta E values must be a NumPy array")
	if errors.shape != (site_count,):
		raise ValueError("Voronoi Delta E values must have one value per site")
	if not numpy.issubdtype(errors.dtype, numpy.number) or numpy.issubdtype(
		errors.dtype, numpy.complexfloating
	):
		raise ValueError("Voronoi Delta E values must be numeric")
	if not numpy.all(numpy.isfinite(errors)):
		raise ValueError("Voronoi Delta E values must be finite")


#============================================
def write_assignments_csv(
	partition: colorbynumber.voronoi_geometry.Partition,
	polygon_rgb: numpy.ndarray,
	indices: numpy.ndarray,
	errors: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
	output_path: pathlib.Path,
) -> None:
	"""Write one stable site-ordered Voronoi marker assignment per polygon.

	Args:
		partition: Bounded partition that owns zero-based site identifiers.
		polygon_rgb: Source RGB sample for every polygon in site order.
		indices: Selected palette index for every polygon in site order.
		errors: Delta E 76 error for every polygon in site order.
		palette: Available marker colors in stable legend order.
		output_path: Destination CSV path.

	Raises:
		ValueError: Inputs do not form one complete stable polygon assignment.
	"""
	_validate_partition(partition)
	_validate_palette(palette)
	_validate_indices(indices, palette, expected_count=partition.domain.site_count)
	_validate_source_values(polygon_rgb, errors, partition.domain.site_count)
	with output_path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.writer(handle)
		writer.writerow(
			(
				"site_identifier",
				"site_x",
				"site_y",
				"source_red",
				"source_green",
				"source_blue",
				"code",
				"color_name",
				"red",
				"green",
				"blue",
				"delta_e_76",
			)
		)
		for site in partition.sites:
			identifier = site.identifier
			marker = palette[int(indices[identifier])]
			writer.writerow(
				(
					identifier,
					site.x,
					site.y,
					*polygon_rgb[identifier],
					marker.code,
					marker.name,
					*marker.rgb,
					errors[identifier],
				)
			)


#============================================
def write_legend_csv(
	palette: list[colorbynumber.marker_color.MarkerColor],
	output_path: pathlib.Path,
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
) -> None:
	"""Write every marker color and its stable Voronoi polygon count.

	Args:
		palette: Available marker colors in stable legend order.
		output_path: Destination CSV path.
		regions: Concrete printable regions derived from polygon assignments.

	Raises:
		ValueError: Palette or regions are invalid.
	"""
	_validate_palette(palette)
	colorbynumber.render_regions.validate_regions(regions, len(palette))
	base_counts = [0] * len(palette)
	region_counts = [0] * len(palette)
	for region in regions:
		palette_index = region.palette_index
		base_counts[palette_index] += len(region.member_identifiers)
		region_counts[palette_index] += 1
	with output_path.open("w", encoding="utf-8", newline="") as handle:
		writer = csv.writer(handle)
		writer.writerow(("code", "color_name", "red", "green", "blue", "polygon_count", "region_count"))
		for index, marker in enumerate(palette):
			writer.writerow((
				marker.code,
				marker.name,
				*marker.rgb,
				base_counts[index],
				region_counts[index],
			))
