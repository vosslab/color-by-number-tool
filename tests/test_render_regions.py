"""Fast behavioral coverage for output-only same-color region merging."""

# PIP3 modules
import numpy
import pytest
import shapely

# local repo modules
import colorbynumber.render_regions
import colorbynumber.voronoi_geometry


#============================================
def test_square_regions_merge_edge_neighbors_but_not_diagonals() -> None:
	"""Edge-connected assignments become one shape while corner touches stay separate."""
	regions = colorbynumber.render_regions.build_square_regions(
		numpy.array(((1, 1), (0, 1)), dtype=numpy.int64), True
	)
	assert [(region.palette_index, len(region.member_identifiers)) for region in regions] == [
		(1, 3),
		(0, 1),
	]


#============================================
def test_square_regions_keep_checkerboard_diagonals_and_membership_separate() -> None:
	"""Corner-only checkerboard contacts must not become one printable region."""
	indices = numpy.array(((0, 1), (1, 0)), dtype=numpy.int64)
	regions = colorbynumber.render_regions.build_square_regions(indices, True)
	assert [region.member_identifiers for region in regions] == [(0,), (1,), (2,), (3,)]
	member_identifiers = sorted(
		identifier for region in regions for identifier in region.member_identifiers
	)
	assert member_identifiers == [0, 1, 2, 3]
	assert sum(region.polygon.area for region in regions) == 4.0


#============================================
def test_unmerged_square_regions_retain_one_authoritative_shape_per_assignment() -> None:
	"""The unmerged projection is still a concrete render-region sequence."""
	indices = numpy.array(((1, 1), (0, 1)), dtype=numpy.int64)
	regions = colorbynumber.render_regions.build_square_regions(indices, False)
	assert [region.member_identifiers for region in regions] == [(0,), (1,), (2,), (3,)]
	assert [region.palette_index for region in regions] == [1, 1, 0, 1]


#============================================
def test_square_regions_preserve_enclosed_holes() -> None:
	"""A ring of one assigned color stays one printable polygon with a hole."""
	regions = colorbynumber.render_regions.build_square_regions(
		numpy.array(((1, 1, 1), (1, 0, 1), (1, 1, 1)), dtype=numpy.int64), True
	)
	ring = next(region for region in regions if region.palette_index == 1)
	assert len(ring.polygon.interiors) == 1 and len(ring.member_identifiers) == 8


#============================================
def test_regions_keep_disconnected_same_color_components_stable() -> None:
	"""Separated same-color components retain deterministic assignment-order output."""
	regions = colorbynumber.render_regions.build_square_regions(
		numpy.array(((1, 0, 1),), dtype=numpy.int64), True
	)
	assert [region.member_identifiers for region in regions] == [(0,), (1,), (2,)]


#============================================
def test_regions_reject_empty_source_polygon() -> None:
	"""Render merging rejects an empty source polygon before output generation."""
	with pytest.raises(ValueError, match="nonempty valid polygon"):
		colorbynumber.render_regions.build_regions(
			[shapely.Polygon()], numpy.array((0,), dtype=numpy.int64), True
		)


#============================================
@pytest.mark.parametrize(
	("regions", "palette_size", "message"),
	[
		((), 1, "nonempty tuple"),
		((object(),), 1, "RenderRegion"),
		(
			(
				colorbynumber.render_regions.RenderRegion(0, (0,), shapely.box(0, 0, 1, 1)),
				colorbynumber.render_regions.RenderRegion(0, (0,), shapely.box(1, 0, 2, 1)),
			),
			1,
			"must not repeat",
		),
		(
			(colorbynumber.render_regions.RenderRegion(1, (0,), shapely.box(0, 0, 1, 1)),),
			1,
			"outside",
		),
	],
)
def test_region_validation_rejects_bad_public_output_contracts(
	regions: tuple[object, ...],
	palette_size: int,
	message: str,
) -> None:
	"""Public writers receive only valid, palette-addressable concrete regions."""
	with pytest.raises(ValueError, match=message):
		colorbynumber.render_regions.validate_regions(regions, palette_size)  # type: ignore[arg-type]


#============================================
def test_voronoi_builder_projects_cells_into_the_shared_region_type() -> None:
	"""Voronoi assignment conversion belongs to the render-region boundary."""
	domain = colorbynumber.voronoi_geometry.create_domain(2, 1)
	sites = colorbynumber.voronoi_geometry.generate_square_grid_sites(domain)
	partition = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites).partition
	regions = colorbynumber.render_regions.build_voronoi_regions(
		partition,
		numpy.array((0, 0), dtype=numpy.int64),
		True,
	)
	assert len(regions) == 1 and len(regions[0].member_identifiers) == 2
