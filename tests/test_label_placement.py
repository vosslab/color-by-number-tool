"""Behavioral geometry tests for strictly contained PDF code placement."""

# Standard Library
import math

# PIP3 modules
import numpy
import pytest
import shapely

# local repo modules
import colorbynumber.constants
import colorbynumber.label_placement
import colorbynumber.marker_color
import colorbynumber.pdf_writer
import colorbynumber.render_regions
import colorbynumber.voronoi_geometry
import colorbynumber.voronoi_pdf_writer


#============================================
def test_convex_region_keeps_its_exact_area_centroid() -> None:
	region = shapely.box(0.0, 0.0, 100.0, 100.0)
	placement = colorbynumber.label_placement.place_label(region, "12", "Helvetica", 12.0, (4,))
	assert placement.used_centroid and not placement.used_best_effort
	assert placement.anchor == (50.0, 50.0)


#============================================
def test_holed_region_shifts_a_centroid_box_inside_its_printable_area() -> None:
	region = shapely.Polygon(
		[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],
		holes=[[(30.0, 30.0), (70.0, 30.0), (70.0, 70.0), (30.0, 70.0)]],
	)
	placement = colorbynumber.label_placement.place_label(region, "CENTER", "Helvetica", 12.0, (7, 8))
	assert not placement.used_centroid and not placement.used_best_effort
	assert region.contains_properly(placement.padded_box)


#============================================
def test_skinny_l_region_has_a_feasible_wide_label_configuration() -> None:
	region = shapely.union_all((shapely.box(0.0, 0.0, 120.0, 8.0), shapely.box(0.0, 0.0, 8.0, 100.0)))
	placement = colorbynumber.label_placement.place_label(region, "WIDE", "Helvetica", 5.0, (9,))
	assert placement.anchor[0] > 8.0 and region.contains_properly(placement.padded_box)


#============================================
@pytest.mark.parametrize(
	"region, manual_anchor, member_identifier",
	(
		(
			shapely.union_all(
				(
					shapely.box(0.0, 0.0, 8.0, 100.0),
					shapely.box(8.0, 39.0, 20.0, 41.0),
					shapely.box(20.0, 38.0, 34.0, 44.0),
				)
			),
			(27.0, 41.0),
			12,
		),
		(
			shapely.union_all(
				(
					shapely.box(0.0, 0.0, 10.0, 100.0),
					shapely.box(10.0, 10.5, 70.13, 11.0),
					shapely.box(70.13, 10.0, 84.0, 15.3),
				)
			),
			(77.065, 12.65),
			13,
		),
	),
)
def test_small_feasible_lobes_are_found_without_anchor_sampling(
	region: shapely.Polygon,
	manual_anchor: tuple[float, float],
	member_identifier: int,
) -> None:
	manual_padded_box = colorbynumber.label_placement.padded_text_box(
		colorbynumber.label_placement.text_box(manual_anchor, "WIDE", "Helvetica", 5.0),
		colorbynumber.label_placement.LABEL_PADDING_POINTS,
	)
	assert region.contains_properly(manual_padded_box)
	placement = colorbynumber.label_placement.place_label(
		region, "WIDE", "Helvetica", 5.0, (member_identifier,)
	)
	assert region.contains_properly(placement.padded_box)


#============================================
def test_impossible_measured_box_uses_best_effort_interior_anchor() -> None:
	region = shapely.box(0.0, 0.0, 2.0, 2.0)
	placement = colorbynumber.label_placement.place_label(
		region, "WIDE", "Helvetica", 12.0, (11,)
	)
	assert placement.used_best_effort
	assert region.contains(shapely.Point(placement.anchor))
	assert not region.contains_properly(placement.padded_box)
	diagnostics = colorbynumber.voronoi_pdf_writer.analyze_resolved_labels(
		12.0,
		(placement,),
	)
	assert diagnostics.best_effort_label_count == 1


#============================================
def test_boundary_touching_padded_box_uses_best_effort_placement() -> None:
	centroid = (0.0, 0.0)
	padded_box = colorbynumber.label_placement.padded_text_box(
		colorbynumber.label_placement.text_box(centroid, "WIDE", "Helvetica", 12.0),
		colorbynumber.label_placement.LABEL_PADDING_POINTS,
	)
	region = shapely.box(*padded_box.bounds)
	assert region.contains(padded_box) and not region.contains_properly(padded_box)
	placement = colorbynumber.label_placement.place_label(
		region, "WIDE", "Helvetica", 12.0, (14,)
	)
	assert placement.used_centroid and placement.used_best_effort


#============================================
def test_repeated_resolution_is_deterministic() -> None:
	region = shapely.Polygon(
		[(0.0, 0.0), (80.0, 0.0), (80.0, 20.0), (20.0, 20.0), (20.0, 80.0), (0.0, 80.0)]
	)
	first = colorbynumber.label_placement.place_label(region, "WIDE", "Helvetica", 8.0, (6,))
	second = colorbynumber.label_placement.place_label(region, "WIDE", "Helvetica", 8.0, (6,))
	assert first == second


#============================================
def test_square_and_voronoi_writers_resolve_shared_contained_pdf_boxes() -> None:
	palette = [colorbynumber.marker_color.MarkerColor("WIDE", "wide", (1, 2, 3))]
	square_layout = colorbynumber.pdf_writer.calculate_layout("landscape", 1, 1)
	square_regions = colorbynumber.render_regions.build_square_regions(
		numpy.array(((0,),), dtype=numpy.int64), False
	)
	square_placement = colorbynumber.pdf_writer.resolve_code_placements(square_layout, palette, square_regions)[0]
	square_polygon = colorbynumber.pdf_writer._region_polygon_pdf(square_layout, square_regions[0].polygon)
	domain = colorbynumber.voronoi_geometry.create_domain(1, 1)
	voronoi_layout = colorbynumber.voronoi_pdf_writer.calculate_layout(
		colorbynumber.constants.LANDSCAPE_ORIENTATION, domain
	)
	voronoi_region = colorbynumber.render_regions.RenderRegion(0, (0,), shapely.box(0.0, 0.0, 1.0, 1.0))
	voronoi_placement = colorbynumber.voronoi_pdf_writer.resolve_label_placements(
		domain, palette, voronoi_layout, (voronoi_region,)
	)[0]
	voronoi_polygon = colorbynumber.voronoi_pdf_writer._region_polygon_pdf(
		voronoi_layout, voronoi_region.polygon
	)
	assert square_polygon.contains_properly(square_placement.padded_box)
	assert voronoi_polygon.contains_properly(voronoi_placement.padded_box)


#============================================
def test_resolved_voronoi_diagnostics_report_shift_distance_and_overlap() -> None:
	region = shapely.Polygon(
		[(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)],
		holes=[[(30.0, 30.0), (70.0, 30.0), (70.0, 70.0), (30.0, 70.0)]],
	)
	placement = colorbynumber.label_placement.place_label(region, "CENTER", "Helvetica", 12.0, (3,))
	diagnostics = colorbynumber.voronoi_pdf_writer.analyze_resolved_labels(12.0, (placement,))
	assert diagnostics.best_effort_label_count == 0
	assert diagnostics.shifted_label_count == 1 and math.isclose(
		diagnostics.total_shift_points, diagnostics.maximum_shift_points
	)
