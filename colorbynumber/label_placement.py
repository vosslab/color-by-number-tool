"""Deterministic PDF label placement for printable polygons."""

# Standard Library
import dataclasses
import math

# PIP3 modules
import reportlab.pdfbase.pdfmetrics
import shapely
import shapely.ops
from shapely.geometry.base import BaseGeometry


LABEL_PADDING_POINTS = 0.25


#============================================
@dataclasses.dataclass(frozen=True)
class LabelPlacement:
	"""One resolved code anchor and the exact measured boxes it protects."""

	anchor: tuple[float, float]
	text_box: shapely.Polygon
	padded_box: shapely.Polygon
	used_centroid: bool
	used_best_effort: bool
	shift_distance_points: float


#============================================
def centered_text_baseline(y_center: float, font_name: str, font_size: float) -> float:
	"""Return the ReportLab baseline that vertically centers measured glyph extents."""
	ascent = reportlab.pdfbase.pdfmetrics.getAscent(font_name) * font_size / 1000.0
	descent = reportlab.pdfbase.pdfmetrics.getDescent(font_name) * font_size / 1000.0
	baseline = y_center - (ascent + descent) / 2.0
	return baseline


#============================================
def text_box(
	anchor: tuple[float, float],
	code: str,
	font_name: str,
	font_size: float,
) -> shapely.Polygon:
	"""Return the actual ReportLab glyph-extents box for a centered code in points."""
	if not code:
		raise ValueError("Label code must be nonempty")
	if not math.isfinite(font_size) or font_size <= 0.0:
		raise ValueError("Label font size must be a positive finite number")
	width = reportlab.pdfbase.pdfmetrics.stringWidth(code, font_name, font_size)
	ascent = reportlab.pdfbase.pdfmetrics.getAscent(font_name) * font_size / 1000.0
	descent = reportlab.pdfbase.pdfmetrics.getDescent(font_name) * font_size / 1000.0
	x_center, y_center = anchor
	baseline = centered_text_baseline(y_center, font_name, font_size)
	box = shapely.box(
		x_center - width / 2.0,
		baseline + descent,
		x_center + width / 2.0,
		baseline + ascent,
	)
	return box


#============================================
def padded_text_box(text_bounds: shapely.Polygon, padding_points: float) -> shapely.Polygon:
	"""Expand a measured glyph box by the required inward region-clearance margin."""
	if not math.isfinite(padding_points) or padding_points < 0.0:
		raise ValueError("Label padding must be a nonnegative finite number")
	minimum_x, minimum_y, maximum_x, maximum_y = text_bounds.bounds
	padded = shapely.box(
		minimum_x - padding_points,
		minimum_y - padding_points,
		maximum_x + padding_points,
		maximum_y + padding_points,
	)
	return padded


#============================================
def _placement_for_anchor(
	polygon: shapely.Polygon,
	anchor: tuple[float, float],
	code: str,
	font_name: str,
	font_size: float,
	padding_points: float,
	centroid: tuple[float, float],
) -> LabelPlacement | None:
	"""Build one placement only when the original polygon strictly contains its box."""
	measured_box = text_box(anchor, code, font_name, font_size)
	padded_box = padded_text_box(measured_box, padding_points)
	if not polygon.contains_properly(padded_box):
		return None
	shift_distance = math.dist(anchor, centroid)
	placement = LabelPlacement(
		anchor=anchor,
		text_box=measured_box,
		padded_box=padded_box,
		used_centroid=shift_distance == 0.0,
		used_best_effort=False,
		shift_distance_points=shift_distance,
	)
	return placement


#============================================
def _ring_sweep_parallelograms(
	ring: shapely.LinearRing,
	start_x: float,
	start_y: float,
	end_x: float,
	end_y: float,
) -> list[shapely.Polygon]:
	"""Return the quadrilaterals traced by one boundary ring over one segment."""
	coordinates = tuple(ring.coords)
	return [
		shapely.Polygon(
			(
				(x0 + start_x, y0 + start_y),
				(x1 + start_x, y1 + start_y),
				(x1 + end_x, y1 + end_y),
				(x0 + end_x, y0 + end_y),
			)
		)
		for (x0, y0), (x1, y1) in zip(coordinates, coordinates[1:])
	]


#============================================
def _sweep_by_segment(
	geometry: BaseGeometry,
	start_x: float,
	start_y: float,
	end_x: float,
	end_y: float,
) -> BaseGeometry:
	"""Dilate polygonal geometry by a segment using endpoint copies and boundary sweeps.

	For a closed polygonal set ``G`` and segment ``S``, ``G + S`` equals the union
	of endpoint copies of ``G`` and the parallelograms swept by every exterior and
	interior boundary segment.  Applying the horizontal and vertical sweeps in
	sequence therefore dilates by the axis-aligned rectangle formed by the padded
	text box's half-extents.
	"""
	parts: list[BaseGeometry] = [
		shapely.affinity.translate(geometry, xoff=start_x, yoff=start_y),
		shapely.affinity.translate(geometry, xoff=end_x, yoff=end_y),
	]
	for polygon in shapely.get_parts(geometry):
		if not isinstance(polygon, shapely.Polygon):
			continue
		parts.extend(_ring_sweep_parallelograms(polygon.exterior, start_x, start_y, end_x, end_y))
		for interior in polygon.interiors:
			parts.extend(_ring_sweep_parallelograms(interior, start_x, start_y, end_x, end_y))
	return shapely.union_all(parts)


#============================================
def _feasible_anchor_components(
	polygon: shapely.Polygon,
	text_bounds: shapely.Polygon,
	padding_points: float,
) -> tuple[shapely.Polygon, ...]:
	"""Return every positive-area center component whose padded box fits ``polygon``.

	This builds the configuration space exactly as ``P - ((E - P) + R)`` inside a
	finite envelope ``E``.  ``R`` is the centered padded text rectangle.  The
	complement is dilated by the rectangle's horizontal and vertical generating
	segments; no finite anchor sampling is involved.
	"""
	padded_bounds = padded_text_box(text_bounds, padding_points).bounds
	half_width = (padded_bounds[2] - padded_bounds[0]) / 2.0
	half_height = (padded_bounds[3] - padded_bounds[1]) / 2.0
	if half_width <= 0.0 or half_height <= 0.0:
		raise ValueError("Measured padded label box must have positive width and height")
	minimum_x, minimum_y, maximum_x, maximum_y = polygon.bounds
	# Two half-extents leave the entire one-half-extent dilation neighborhood of
	# every possible center inside E, including along P's bounding box boundary.
	envelope = shapely.box(
		minimum_x - 2.0 * half_width,
		minimum_y - 2.0 * half_height,
		maximum_x + 2.0 * half_width,
		maximum_y + 2.0 * half_height,
	)
	obstacle = envelope.difference(polygon)
	horizontally_dilated = _sweep_by_segment(obstacle, -half_width, 0.0, half_width, 0.0)
	dilated_obstacle = _sweep_by_segment(horizontally_dilated, 0.0, -half_height, 0.0, half_height)
	feasible = polygon.difference(dilated_obstacle)
	components = tuple(
		component
		for component in shapely.get_parts(feasible)
		if isinstance(component, shapely.Polygon) and component.area > 0.0
	)
	return components


#============================================
def _feasible_anchor_candidates(
	components: tuple[shapely.Polygon, ...],
	centroid: tuple[float, float],
) -> tuple[tuple[float, float], ...]:
	"""Return one deterministic interior candidate from each feasible component."""
	def component_key(component: shapely.Polygon) -> tuple[float, float, float, float, float]:
		component_centroid = component.centroid
		return (
			math.dist((component_centroid.x, component_centroid.y), centroid),
			component_centroid.x,
			component_centroid.y,
			component.area,
			component.length,
		)

	ordered_components = sorted(components, key=component_key)
	return tuple(
		(point.x, point.y)
		for component in ordered_components
		for point in (shapely.ops.polylabel(component, tolerance=0.01),)
	)


#============================================
def place_label(
	polygon: shapely.Polygon,
	code: str,
	font_name: str,
	font_size: float,
	member_identifiers: tuple[int, ...],
	padding_points: float = LABEL_PADDING_POINTS,
) -> LabelPlacement:
	"""Resolve one code to a deterministic PDF-space anchor.

	The area centroid remains the exact preferred anchor.  When its padded measured
	box crosses an edge or hole, its feasible anchor configuration space is built
	by subtracting the padded-box dilation of the polygon complement.  One stable
	interior point from every positive-area feasible component is then rechecked
	against the original polygon in PDF points.  If the full box cannot fit, the
	code uses the polygon's maximum-clearance interior point instead of blocking
	the complete PDF.

	Args:
		polygon: Valid printable region geometry transformed into PDF points.
		code: Marker code drawn at the resolved anchor.
		font_name: Registered ReportLab font name used for drawing.
		font_size: Font size in PDF points.
		member_identifiers: Source members retained for useful failure context.
		padding_points: Required clearance from the region boundary.

	Returns:
		The measured code placement and whether it used best-effort positioning.
	"""
	if not isinstance(polygon, shapely.Polygon) or polygon.is_empty or not polygon.is_valid:
		raise ValueError("Label placement requires one nonempty valid polygon")
	if not member_identifiers:
		raise ValueError("Label placement requires source member identifiers")
	centroid_point = polygon.centroid
	centroid = (centroid_point.x, centroid_point.y)
	centroid_placement = _placement_for_anchor(
		polygon,
		centroid,
		code,
		font_name,
		font_size,
		padding_points,
		centroid,
	)
	if centroid_placement is not None:
		return centroid_placement
	centroid_box = text_box(centroid, code, font_name, font_size)
	components = _feasible_anchor_components(polygon, centroid_box, padding_points)
	for candidate in _feasible_anchor_candidates(components, centroid):
		placement = _placement_for_anchor(
			polygon,
			candidate,
			code,
			font_name,
			font_size,
			padding_points,
			centroid,
		)
		if placement is not None:
			return placement
	best_effort_point = shapely.ops.polylabel(polygon, tolerance=0.01)
	best_effort_anchor = (best_effort_point.x, best_effort_point.y)
	measured_box = text_box(best_effort_anchor, code, font_name, font_size)
	padded_box = padded_text_box(measured_box, padding_points)
	shift_distance = math.dist(best_effort_anchor, centroid)
	return LabelPlacement(
		anchor=best_effort_anchor,
		text_box=measured_box,
		padded_box=padded_box,
		used_centroid=shift_distance == 0.0,
		used_best_effort=True,
		shift_distance_points=shift_distance,
	)
