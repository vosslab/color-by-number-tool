"""Prototype-only polygon preview and comparison PNG writing."""

# Standard Library
import pathlib

# PIP3 modules
import numpy
import PIL.Image
import PIL.ImageDraw

# local repo modules
import colorbynumber.voronoi_geometry
import colorbynumber.render_regions


COMPARISON_HEADER_HEIGHT = 28


#============================================
def _pixel_vertex(
	domain: colorbynumber.voronoi_geometry.Domain,
	vertex: tuple[float, float],
	width: int,
	height: int,
) -> tuple[float, float]:
	"""Map one domain vertex to top-left raster coordinates."""
	x = vertex[0] * width / domain.width
	y = (domain.height - vertex[1]) * height / domain.height
	point = (x, y)
	return point


#============================================
def draw_partition_lines(
	image: PIL.Image.Image,
	partition: colorbynumber.voronoi_geometry.Partition,
	line_color: tuple[int, int, int] = (42, 42, 42),
	line_width: int = 1,
) -> None:
	"""Draw stable ordered polygon edges onto an RGB preview image."""
	if line_width <= 0:
		raise ValueError("Preview line width must be greater than zero")
	draw = PIL.ImageDraw.Draw(image)
	for cell in partition.cells:
		points = [
			_pixel_vertex(partition.domain, vertex, image.width, image.height)
			for vertex in cell.vertices
		]
		points.append(points[0])
		draw.line(points, fill=line_color, width=line_width, joint="curve")
	# Domain maxima map to the outside edge of the raster, so redraw the
	# complete partition border on the last in-bounds pixel coordinates.
	border = (0, 0, image.width - 1, image.height - 1)
	draw.rectangle(border, outline=line_color, width=line_width)


#============================================
def draw_region_lines(
	image: PIL.Image.Image,
	domain: colorbynumber.voronoi_geometry.Domain,
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
	line_color: tuple[int, int, int] = (42, 42, 42),
	line_width: int = 1,
) -> None:
	"""Draw printable-region exterior and hole boundaries onto a preview."""
	if line_width <= 0:
		raise ValueError("Preview line width must be greater than zero")
	draw = PIL.ImageDraw.Draw(image)
	for region in regions:
		for ring in (region.polygon.exterior, *region.polygon.interiors):
			points = [
				_pixel_vertex(domain, vertex, image.width, image.height)
				for vertex in ring.coords
			]
			draw.line(points, fill=line_color, width=line_width, joint="curve")
	draw.rectangle((0, 0, image.width - 1, image.height - 1), outline=line_color, width=line_width)


#============================================
def write_polygon_preview(
	reconstruction_rgb: numpy.ndarray,
	domain: colorbynumber.voronoi_geometry.Domain,
	output_path: pathlib.Path,
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
) -> None:
	"""Write one palette-colored preview with visible printable-region boundaries."""
	colorbynumber.render_regions.validate_region_geometries(regions)
	image = PIL.Image.fromarray(reconstruction_rgb.astype(numpy.uint8), mode="RGB")
	draw_region_lines(image, domain, regions)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	image.save(output_path)


#============================================
def _labeled_panel(image: PIL.Image.Image, label: str) -> PIL.Image.Image:
	"""Place a compact ASCII label above one comparison panel."""
	panel = PIL.Image.new(
		"RGB",
		(image.width, image.height + COMPARISON_HEADER_HEIGHT),
		(246, 246, 246),
	)
	panel.paste(image, (0, COMPARISON_HEADER_HEIGHT))
	draw = PIL.ImageDraw.Draw(panel)
	draw.text((8, 7), label, fill=(24, 24, 24))
	return panel


#============================================
def write_comparison(
	source_rgb: numpy.ndarray,
	square_rgb: numpy.ndarray,
	voronoi_rgb: numpy.ndarray,
	partition: colorbynumber.voronoi_geometry.Partition,
	output_path: pathlib.Path,
) -> None:
	"""Write equal-scale source, square-control, and Voronoi reference panels."""
	if source_rgb.shape != square_rgb.shape or source_rgb.shape != voronoi_rgb.shape:
		raise ValueError("Comparison rasters must have matching shapes")
	source_image = PIL.Image.fromarray(source_rgb.astype(numpy.uint8), mode="RGB")
	square_image = PIL.Image.fromarray(square_rgb.astype(numpy.uint8), mode="RGB")
	voronoi_image = PIL.Image.fromarray(voronoi_rgb.astype(numpy.uint8), mode="RGB")
	draw_partition_lines(voronoi_image, partition)
	panels = (
		_labeled_panel(source_image, "Fitted source"),
		_labeled_panel(square_image, "Square control"),
		_labeled_panel(voronoi_image, "Voronoi prototype"),
	)
	comparison = PIL.Image.new(
		"RGB",
		(sum(panel.width for panel in panels), panels[0].height),
		(255, 255, 255),
	)
	x_offset = 0
	for panel in panels:
		comparison.paste(panel, (x_offset, 0))
		x_offset += panel.width
	output_path.parent.mkdir(parents=True, exist_ok=True)
	comparison.save(output_path)
