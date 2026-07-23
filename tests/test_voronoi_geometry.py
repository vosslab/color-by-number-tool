"""Focused invariants and independent oracles for bounded Voronoi geometry."""

# Standard Library
import math
import dataclasses

# PIP3 modules
import pytest
import shapely
import numpy
import shapely.geometry

# local repo modules
import colorbynumber.voronoi_geometry


#============================================
def _oracle_clip_cell(
	domain: colorbynumber.voronoi_geometry.Domain,
	sites: tuple[colorbynumber.voronoi_geometry.Site, ...],
	owner_index: int,
) -> shapely.Polygon:
	"""Clip one test cell without calling the runtime clipping implementation."""
	owner = sites[owner_index]
	vertices = [
		(0.0, 0.0),
		(domain.width, 0.0),
		(domain.width, domain.height),
		(0.0, domain.height),
	]
	for other in sites:
		if other.identifier == owner.identifier:
			continue
		axis_x = other.x - owner.x
		axis_y = other.y - owner.y
		limit = (
			other.x * other.x + other.y * other.y
			- owner.x * owner.x - owner.y * owner.y
		) / 2.0
		new_vertices: list[tuple[float, float]] = []
		for edge_index, first in enumerate(vertices):
			second = vertices[(edge_index + 1) % len(vertices)]
			first_side = axis_x * first[0] + axis_y * first[1] - limit
			second_side = axis_x * second[0] + axis_y * second[1] - limit
			first_inside = first_side <= 0.0
			second_inside = second_side <= 0.0
			if first_inside != second_inside:
				weight = first_side / (first_side - second_side)
				crossing = (
					first[0] + weight * (second[0] - first[0]),
					first[1] + weight * (second[1] - first[1]),
				)
				if first_inside:
					new_vertices.extend((first, crossing))
				else:
					new_vertices.append(crossing)
			elif first_inside:
				new_vertices.append(first)
		vertices = new_vertices
	polygon = shapely.geometry.Polygon(vertices)
	return polygon


#============================================
def _maximum_oracle_cell_difference(
	domain: colorbynumber.voronoi_geometry.Domain,
	sites: tuple[colorbynumber.voronoi_geometry.Site, ...],
	cells: tuple[colorbynumber.voronoi_geometry.Cell, ...],
) -> float:
	"""Return the largest cell difference from the independent clipper."""
	differences = []
	for index, cell in enumerate(cells):
		actual = shapely.geometry.Polygon(cell.vertices)
		expected = _oracle_clip_cell(domain, sites, index)
		differences.append(actual.symmetric_difference(expected).area)
	maximum_difference = max(differences)
	return maximum_difference


#============================================
def test_independent_oracle_places_two_site_bisector() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(2, 1)
	sites = (
		colorbynumber.voronoi_geometry.Site(0, 0.2, 0.5),
		colorbynumber.voronoi_geometry.Site(1, 1.2, 0.5),
	)
	first = _oracle_clip_cell(domain, sites, 0)
	second = _oracle_clip_cell(domain, sites, 1)
	assert (first.bounds[2], second.bounds[0]) == pytest.approx((0.7, 0.7))


#============================================
@pytest.mark.parametrize("columns,rows", ((43, 30), (86, 60), (100, 75)))
def test_standard_dimensions_resolve_count_aspect_and_unit_area(
	columns: int,
	rows: int,
) -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(columns, rows)
	assert domain.site_count == columns * rows
	assert (domain.width / domain.height, domain.width * domain.height) == pytest.approx(
		(columns / rows, 1.0)
	)


#============================================
def test_orientation_swap_preserves_site_count() -> None:
	landscape = colorbynumber.voronoi_geometry.create_domain(43, 30)
	portrait = colorbynumber.voronoi_geometry.create_domain(30, 43)
	assert landscape.site_count == portrait.site_count == 43 * 30
	assert landscape.width == pytest.approx(portrait.height)


#============================================
def test_conditioning_accepts_representable_extreme_aspect() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(1_000_000_000_000, 1)
	assert 2.0 * domain.coordinate_tolerance < min(
		domain.height, domain.nominal_spacing
	)


#============================================
def test_conditioning_rejects_unrepresentable_tolerance_bands() -> None:
	with pytest.raises(
		colorbynumber.voronoi_geometry.NumericConditioningError,
		match="10000000000000000x1",
	):
		colorbynumber.voronoi_geometry.create_domain(10_000_000_000_000_000, 1)


#============================================
def test_conditioning_converts_giant_integer_overflow() -> None:
	with pytest.raises(colorbynumber.voronoi_geometry.NumericConditioningError):
		colorbynumber.voronoi_geometry.create_domain(10 ** 1000, 1)


#============================================
def test_square_grid_generator_has_exact_centered_control_geometry() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(3, 2)
	sites = colorbynumber.voronoi_geometry.generate_square_grid_sites(domain)
	actual = tuple((site.x, site.y) for site in sites)
	expected = tuple(
		(
			(column + 0.5) * domain.width / domain.columns,
			(row + 0.5) * domain.height / domain.rows,
		)
		for row in range(domain.rows)
		for column in range(domain.columns)
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	assert actual == expected
	assert result.partition.constructor_family == "analytical-square-grid"


#============================================
def test_near_grid_input_uses_general_constructor_without_coordinate_repair() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(3, 2)
	sites = list(colorbynumber.voronoi_geometry.generate_square_grid_sites(domain))
	sites[0] = dataclasses.replace(
		sites[0], x=sites[0].x + 0.5 * domain.coordinate_tolerance
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, tuple(sites))
	assert result.partition.constructor_family == "shapely-geos-voronoi"


#============================================
def test_uniform_generator_replays_seed_without_global_state() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(3, 2)
	first = colorbynumber.voronoi_geometry.generate_uniform_sites(domain, 90210)
	replay = colorbynumber.voronoi_geometry.generate_uniform_sites(domain, 90210)
	other = colorbynumber.voronoi_geometry.generate_uniform_sites(domain, 90211)
	assert first == replay
	assert first != other


#============================================
@pytest.mark.parametrize("jitter_fraction", (0.0, 1.0))
def test_stratified_jitter_endpoints_stay_in_their_exact_strata(
	jitter_fraction: float,
) -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(5, 4)
	sites = colorbynumber.voronoi_geometry.generate_stratified_jitter_sites(
		domain, 20260722, jitter_fraction
	)
	stratum_width = domain.width / domain.columns
	stratum_height = domain.height / domain.rows
	membership = []
	for site in sites:
		row, column = divmod(site.identifier, domain.columns)
		inside_x = column * stratum_width <= site.x < (column + 1) * stratum_width
		inside_y = row * stratum_height <= site.y < (row + 1) * stratum_height
		membership.append(inside_x and inside_y)
	assert len(sites) == domain.site_count
	assert all(membership)


#============================================
def test_zero_stratified_jitter_is_the_centered_grid() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	jittered = colorbynumber.voronoi_geometry.generate_stratified_jitter_sites(
		domain, 20260722, 0.0
	)
	grid = colorbynumber.voronoi_geometry.generate_square_grid_sites(domain)
	assert jittered == grid


#============================================
def test_stratified_jitter_replays_without_numpy_global_state() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	numpy.random.seed(17)
	first = colorbynumber.voronoi_geometry.generate_stratified_jitter_sites(
		domain, 20260722, 1.0
	)
	numpy.random.seed(29)
	replay = colorbynumber.voronoi_geometry.generate_stratified_jitter_sites(
		domain, 20260722, 1.0
	)
	other = colorbynumber.voronoi_geometry.generate_stratified_jitter_sites(
		domain, 20260723, 1.0
	)
	assert first == replay
	assert first != other


#============================================
@pytest.mark.parametrize("jitter_fraction", (-0.01, 1.01, math.nan, math.inf, True))
def test_stratified_jitter_rejects_invalid_fraction(jitter_fraction: object) -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(2, 2)
	with pytest.raises(colorbynumber.voronoi_geometry.GeometryError, match="jitter fraction"):
		colorbynumber.voronoi_geometry.generate_stratified_jitter_sites(
			domain, 1, jitter_fraction
		)


#============================================
@pytest.mark.parametrize("seed", (-1, True))
def test_stratified_jitter_rejects_invalid_seed(seed: object) -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(2, 2)
	with pytest.raises(colorbynumber.voronoi_geometry.GeometryError, match="seed"):
		colorbynumber.voronoi_geometry.generate_stratified_jitter_sites(
			domain, seed, 0.5
		)


#============================================
def test_stratified_jitter_cells_match_independent_half_plane_oracle() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	sites = colorbynumber.voronoi_geometry.generate_stratified_jitter_sites(
		domain, 20260722, 0.5
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	maximum_difference = _maximum_oracle_cell_difference(
		domain,
		sites,
		result.partition.cells,
	)
	assert maximum_difference <= domain.area_tolerance


#============================================
def test_hard_core_generator_enforces_count_distance_and_domain() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	ratio = 0.7
	sites = colorbynumber.voronoi_geometry.generate_hard_core_sites(
		domain, 20260722, ratio, 1200
	)
	requested_squared = (ratio * domain.nominal_spacing) ** 2
	pair_distances_squared = (
		(first.x - second.x) ** 2 + (first.y - second.y) ** 2
		for first_index, first in enumerate(sites)
		for second in sites[first_index + 1:]
	)
	inside_domain = all(
		0.0 <= site.x <= domain.width and 0.0 <= site.y <= domain.height
		for site in sites
	)
	assert len(sites) == domain.site_count and inside_domain
	assert min(pair_distances_squared) >= requested_squared


#============================================
def test_hard_core_generator_replays_without_numpy_global_state() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	numpy.random.seed(17)
	first = colorbynumber.voronoi_geometry.generate_hard_core_sites(
		domain, 20260722, 0.5, 1200
	)
	numpy.random.seed(29)
	replay = colorbynumber.voronoi_geometry.generate_hard_core_sites(
		domain, 20260722, 0.5, 1200
	)
	other = colorbynumber.voronoi_geometry.generate_hard_core_sites(
		domain, 20260723, 0.5, 1200
	)
	assert first == replay
	assert first != other


#============================================
def test_hard_core_generator_fails_explicitly_at_same_seed_and_budget() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	with pytest.raises(colorbynumber.voronoi_geometry.HardCoreGenerationError) as first:
		colorbynumber.voronoi_geometry.generate_hard_core_sites(
			domain, 20260722, 5.0, domain.site_count
		)
	with pytest.raises(colorbynumber.voronoi_geometry.HardCoreGenerationError) as replay:
		colorbynumber.voronoi_geometry.generate_hard_core_sites(
			domain, 20260722, 5.0, domain.site_count
		)
	assert str(first.value) == str(replay.value)
	assert "accepted=" in str(first.value) and "policy=" in str(first.value)


#============================================
@pytest.mark.parametrize(
	"seed,ratio,budget,error_text",
	(
		(-1, 0.5, 12, "seed"),
		(True, 0.5, 12, "seed"),
		(1, 0.0, 12, "ratio"),
		(1, math.inf, 12, "ratio"),
		(1, 0.5, True, "budget"),
		(1, 0.5, 11, "site count"),
	),
)
def test_hard_core_generator_rejects_invalid_parameters(
	seed: object,
	ratio: object,
	budget: object,
	error_text: str,
) -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	with pytest.raises(colorbynumber.voronoi_geometry.GeometryError, match=error_text):
		colorbynumber.voronoi_geometry.generate_hard_core_sites(
			domain, seed, ratio, budget
		)


#============================================
def test_hard_core_rejects_squared_distance_underflow_before_rng(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	def unexpected_rng(seed: int) -> None:
		raise RuntimeError("The RNG boundary was reached")

	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	minimum_positive_distance = math.nextafter(0.0, math.inf)
	ratio = minimum_positive_distance / domain.nominal_spacing
	monkeypatch.setattr(
		colorbynumber.voronoi_geometry.numpy.random,
		"default_rng",
		unexpected_rng,
	)
	with pytest.raises(colorbynumber.voronoi_geometry.GeometryError, match="squared"):
		colorbynumber.voronoi_geometry.generate_hard_core_sites(
			domain, 1, ratio, domain.site_count
		)


#============================================
def test_hard_core_rejects_unrepresentable_maximum_bin_coordinate() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	maximum_finite = math.nextafter(math.inf, 0.0)
	wide_domain = dataclasses.replace(domain, width=math.sqrt(maximum_finite))
	minimum_distance = math.sqrt(math.nextafter(0.0, math.inf))
	ratio = minimum_distance / domain.nominal_spacing
	with pytest.raises(colorbynumber.voronoi_geometry.GeometryError, match="bin coordinate"):
		colorbynumber.voronoi_geometry.generate_hard_core_sites(
			wide_domain, 1, ratio, wide_domain.site_count
		)


#============================================
def test_hard_core_cells_match_independent_half_plane_oracle() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	sites = colorbynumber.voronoi_geometry.generate_hard_core_sites(
		domain, 20260722, 0.7, 1200
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	maximum_difference = _maximum_oracle_cell_difference(
		domain,
		sites,
		result.partition.cells,
	)
	assert maximum_difference <= domain.area_tolerance


#============================================
def test_bounded_lloyd_replays_exactly() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	sites = colorbynumber.voronoi_geometry.generate_hard_core_sites(
		domain, 20260722, 0.7, 1200
	)
	first = colorbynumber.voronoi_geometry.relax_bounded_lloyd_once(
		domain, sites, 0.5
	)
	replay = colorbynumber.voronoi_geometry.relax_bounded_lloyd_once(
		domain, sites, 0.5
	)
	assert first == replay


#============================================
@pytest.mark.parametrize("alpha", (-0.01, 1.01, math.nan, True))
def test_bounded_lloyd_rejects_invalid_alpha(alpha: object) -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(2, 1)
	sites = colorbynumber.voronoi_geometry.generate_square_grid_sites(domain)
	with pytest.raises(colorbynumber.voronoi_geometry.GeometryError, match="Lloyd alpha"):
		colorbynumber.voronoi_geometry.relax_bounded_lloyd_once(domain, sites, alpha)


#============================================
def test_bounded_lloyd_preserves_site_identity_count_and_domain() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	sites = colorbynumber.voronoi_geometry.generate_uniform_sites(domain, 71)
	moved = colorbynumber.voronoi_geometry.relax_bounded_lloyd_once(domain, sites, 0.5)
	identifiers = tuple(site.identifier for site in moved)
	inside_domain = all(
		0.0 <= site.x <= domain.width and 0.0 <= site.y <= domain.height
		for site in moved
	)
	assert identifiers == tuple(site.identifier for site in sites)
	assert len(moved) == domain.site_count and inside_domain


#============================================
def test_bounded_lloyd_moves_two_sites_to_independently_known_centroids() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(2, 1)
	y = domain.height / 2.0
	sites = (
		colorbynumber.voronoi_geometry.Site(0, 0.2, y),
		colorbynumber.voronoi_geometry.Site(1, 1.2, y),
	)
	moved = colorbynumber.voronoi_geometry.relax_bounded_lloyd_once(domain, sites, 0.5)
	bisector_x = 0.7
	expected = (
		(0.5 * 0.2 + 0.5 * bisector_x / 2.0, y),
		(0.5 * 1.2 + 0.5 * (bisector_x + domain.width) / 2.0, y),
	)
	actual_x = tuple(site.x for site in moved)
	actual_y = tuple(site.y for site in moved)
	assert actual_x == pytest.approx(tuple(point[0] for point in expected))
	assert actual_y == pytest.approx(tuple(point[1] for point in expected))


#============================================
def test_bounded_lloyd_checkpoint_matches_independent_partition_oracle() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	sites = colorbynumber.voronoi_geometry.generate_hard_core_sites(
		domain, 20260722, 0.7, 1200
	)
	moved = colorbynumber.voronoi_geometry.relax_bounded_lloyd_once(
		domain, sites, 0.5
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, moved)
	maximum_difference = _maximum_oracle_cell_difference(
		domain,
		moved,
		result.partition.cells,
	)
	assert maximum_difference <= domain.area_tolerance


#============================================
@pytest.mark.parametrize(
	"sites,error_text",
	(
		(
			(
				colorbynumber.voronoi_geometry.Site(0, 0.5, 0.5),
				colorbynumber.voronoi_geometry.Site(1, 0.5, 0.5),
			),
			"Duplicate",
		),
		(
			(
				colorbynumber.voronoi_geometry.Site(0, 0.5, 0.5),
				colorbynumber.voronoi_geometry.Site(1, math.nan, 0.5),
			),
			"nonfinite",
		),
		(
			(
				colorbynumber.voronoi_geometry.Site(0, 0.5, 0.5),
				colorbynumber.voronoi_geometry.Site(1, 2.0, 0.5),
			),
			"outside",
		),
	),
)
def test_invalid_sites_are_rejected(
	sites: tuple[colorbynumber.voronoi_geometry.Site, ...],
	error_text: str,
) -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(2, 1)
	with pytest.raises(colorbynumber.voronoi_geometry.GeometryError, match=error_text):
		colorbynumber.voronoi_geometry.validate_sites(domain, sites)


#============================================
@pytest.mark.parametrize("separation_scale", (0.5, 1.0))
def test_sites_at_or_below_duplicate_tolerance_are_rejected(
	separation_scale: float,
) -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(2, 1)
	sites = (
		colorbynumber.voronoi_geometry.Site(0, 0.5, 0.5),
		colorbynumber.voronoi_geometry.Site(
			1,
			0.5 + separation_scale * domain.coordinate_tolerance,
			0.5,
		),
	)
	with pytest.raises(colorbynumber.voronoi_geometry.GeometryError, match="near-duplicate"):
		colorbynumber.voronoi_geometry.validate_sites(domain, sites)


#============================================
def test_two_sites_just_above_duplicate_tolerance_cover_domain() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(2, 1)
	separation = 1.01 * domain.coordinate_tolerance
	sites = (
		colorbynumber.voronoi_geometry.Site(0, 0.7, 0.4),
		colorbynumber.voronoi_geometry.Site(1, 0.7 + separation, 0.4),
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	polygons = [shapely.geometry.Polygon(cell.vertices) for cell in result.partition.cells]
	assert shapely.union_all(polygons).area == pytest.approx(1.0)
	assert sum(polygon.area for polygon in polygons) == pytest.approx(1.0)


#============================================
def test_collinear_sites_just_above_duplicate_tolerance_cover_domain() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(3, 1)
	separation = 1.01 * domain.coordinate_tolerance
	sites = tuple(
		colorbynumber.voronoi_geometry.Site(identifier, 0.8 + identifier * separation, 0.3)
		for identifier in range(3)
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	polygons = [shapely.geometry.Polygon(cell.vertices) for cell in result.partition.cells]
	assert shapely.union_all(polygons).area == pytest.approx(1.0)
	assert sum(polygon.area for polygon in polygons) == pytest.approx(1.0)


#============================================
def test_boundary_adjacent_two_site_partition_preserves_thin_cell() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(2, 1)
	separation = 1.01 * domain.coordinate_tolerance
	sites = (
		colorbynumber.voronoi_geometry.Site(0, 0.0, 0.5),
		colorbynumber.voronoi_geometry.Site(1, separation, 0.5),
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	polygons = tuple(
		shapely.geometry.Polygon(cell.vertices) for cell in result.partition.cells
	)
	assert polygons[0].bounds[2] == pytest.approx(separation / 2.0)
	assert shapely.union_all(polygons).area == pytest.approx(1.0)


#============================================
def test_boundary_adjacent_collinear_partition_preserves_thin_cells() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(3, 1)
	separation = 1.01 * domain.coordinate_tolerance
	sites = tuple(
		colorbynumber.voronoi_geometry.Site(identifier, identifier * separation, 0.5)
		for identifier in range(3)
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	polygons = tuple(
		shapely.geometry.Polygon(cell.vertices) for cell in result.partition.cells
	)
	boundaries = (polygons[0].bounds[2], polygons[1].bounds[2])
	assert boundaries == pytest.approx((separation / 2.0, 1.5 * separation))
	assert shapely.union_all(polygons).area == pytest.approx(1.0)


#============================================
def test_canonical_polygon_order_is_stable() -> None:
	coordinates = ((1.0, 1.0), (1.0, 0.0), (0.5, 0.0), (0.0, 0.0), (0.0, 1.0))
	canonical = colorbynumber.voronoi_geometry.canonicalize_polygon(coordinates)
	assert canonical == ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))


#============================================
def test_canonical_polygon_preserves_positive_thin_rectangle() -> None:
	coordinates = ((0.0, 0.0), (5e-13, 0.0), (5e-13, 1.0), (0.0, 1.0))
	canonical = colorbynumber.voronoi_geometry.canonicalize_polygon(coordinates)
	assert canonical == coordinates


#============================================
def test_canonical_polygon_keeps_one_near_duplicate_across_ring_seam() -> None:
	coordinates = (
		(0.0, 0.0),
		(0.0, 1.0),
		(1.0, 1.0),
		(1.0, 0.0),
		(1e-15, 0.0),
		(0.0, 0.0),
	)
	canonical = colorbynumber.voronoi_geometry.canonicalize_polygon(coordinates)
	assert canonical == ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))


#============================================
def test_one_site_cell_is_the_domain() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(1, 1)
	sites = (colorbynumber.voronoi_geometry.Site(0, 0.5, 0.5),)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	assert result.partition.cells[0].vertices == (
		(0.0, 0.0),
		(1.0, 0.0),
		(1.0, 1.0),
		(0.0, 1.0),
	)


#============================================
def test_two_site_cells_meet_at_analytical_bisector() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(2, 1)
	sites = (
		colorbynumber.voronoi_geometry.Site(0, 0.2, 0.5),
		colorbynumber.voronoi_geometry.Site(1, 1.2, 0.5),
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	polygons = [shapely.geometry.Polygon(cell.vertices) for cell in result.partition.cells]
	assert (polygons[0].bounds[2], polygons[1].bounds[0]) == pytest.approx((0.7, 0.7))
	assert shapely.union_all(polygons).area == pytest.approx(1.0)


#============================================
def test_collinear_cells_follow_ordered_midpoint_bisectors() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(3, 1)
	sites = (
		colorbynumber.voronoi_geometry.Site(0, 0.2, 0.4),
		colorbynumber.voronoi_geometry.Site(1, 0.8, 0.4),
		colorbynumber.voronoi_geometry.Site(2, 1.5, 0.4),
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	polygons = [shapely.geometry.Polygon(cell.vertices) for cell in result.partition.cells]
	boundaries = (polygons[0].bounds[2], polygons[1].bounds[0], polygons[1].bounds[2])
	assert boundaries == pytest.approx((0.5, 0.5, 1.15))


#============================================
def test_cocircular_boundary_sites_form_equal_corner_cells() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(2, 2)
	sites = (
		colorbynumber.voronoi_geometry.Site(0, 0.0, 0.0),
		colorbynumber.voronoi_geometry.Site(1, domain.width, 0.0),
		colorbynumber.voronoi_geometry.Site(2, domain.width, domain.height),
		colorbynumber.voronoi_geometry.Site(3, 0.0, domain.height),
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	areas = tuple(
		shapely.geometry.Polygon(cell.vertices).area for cell in result.partition.cells
	)
	sides = tuple(cell.boundary_sides for cell in result.partition.cells)
	assert areas == pytest.approx((0.25, 0.25, 0.25, 0.25))
	assert sides == (
		("left", "bottom"),
		("right", "bottom"),
		("right", "top"),
		("left", "top"),
	)


#============================================
def test_general_constructor_matches_independent_half_plane_oracle() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(3, 2)
	coordinates = (
		(0.12, 0.14),
		(0.72, 0.19),
		(1.15, 0.08),
		(0.25, 0.63),
		(0.81, 0.71),
		(1.13, 0.55),
	)
	sites = tuple(
		colorbynumber.voronoi_geometry.Site(identifier, x, y)
		for identifier, (x, y) in enumerate(coordinates)
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	maximum_difference = _maximum_oracle_cell_difference(
		domain,
		sites,
		result.partition.cells,
	)
	assert result.partition.constructor_family == "shapely-geos-voronoi"
	assert maximum_difference <= domain.area_tolerance


#============================================
def test_sampled_points_confirm_nearest_site_ownership() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(3, 2)
	sites = colorbynumber.voronoi_geometry.generate_uniform_sites(domain, 71)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	samples = ((0.1, 0.1), (0.4, 0.2), (0.9, 0.5), (1.1, 0.7), (0.3, 0.75))
	owned = []
	for x, y in samples:
		identifier = colorbynumber.voronoi_geometry.nearest_site_identifier(
			sites, x, y, domain.coordinate_tolerance
		)
		polygon = shapely.geometry.Polygon(result.partition.cells[identifier].vertices)
		owned.append(polygon.covers(shapely.geometry.Point(x, y)))
	assert all(owned)


#============================================
def test_validated_partition_covers_domain_and_owns_every_site() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	sites = colorbynumber.voronoi_geometry.generate_uniform_sites(domain, 17)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	polygons = [shapely.geometry.Polygon(cell.vertices) for cell in result.partition.cells]
	coverage_error = colorbynumber.voronoi_geometry.domain_polygon(domain).difference(
		shapely.union_all(polygons)
	).area
	owners_are_covered = all(
		polygon.covers(shapely.geometry.Point(site.x, site.y))
		for site, polygon in zip(result.partition.sites, polygons, strict=True)
	)
	assert coverage_error <= domain.area_tolerance
	assert owners_are_covered


#============================================
def test_validation_rejects_invalid_cell_area() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(1, 1)
	sites = (colorbynumber.voronoi_geometry.Site(0, 0.5, 0.5),)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	bad_cell = dataclasses.replace(
		result.partition.cells[0], vertices=((0.0, 0.0), (0.5, 0.0), (1.0, 0.0))
	)
	bad_partition = dataclasses.replace(result.partition, cells=(bad_cell,))
	with pytest.raises(colorbynumber.voronoi_geometry.GeometryError, match="invalid area"):
		colorbynumber.voronoi_geometry.validate_partition(bad_partition)


#============================================
def test_validation_accepts_positive_cell_smaller_than_aggregate_area_tolerance() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(2, 1)
	split = 1.1 * domain.coordinate_tolerance
	sites = (
		colorbynumber.voronoi_geometry.Site(0, split / 2.0, domain.height / 2.0),
		colorbynumber.voronoi_geometry.Site(
			1, (split + domain.width) / 2.0, domain.height / 2.0
		),
	)
	cells = (
		colorbynumber.voronoi_geometry.Cell(
			0,
			((0.0, 0.0), (split, 0.0), (split, domain.height), (0.0, domain.height)),
			("left", "bottom", "top"),
			"boundary",
			"corner",
		),
		colorbynumber.voronoi_geometry.Cell(
			1,
			(
				(split, 0.0),
				(domain.width, 0.0),
				(domain.width, domain.height),
				(split, domain.height),
			),
			("right", "bottom", "top"),
			"boundary",
			"corner",
		),
	)
	partition = colorbynumber.voronoi_geometry.Partition(
		domain, sites, cells, "analytical-test-control"
	)
	tiny_area = shapely.geometry.Polygon(cells[0].vertices).area
	assert 0.0 < tiny_area < domain.area_tolerance
	colorbynumber.voronoi_geometry.validate_partition(partition)


#============================================
def test_validation_rejects_thin_spike_beyond_coordinate_tolerance() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(1, 1)
	sites = (colorbynumber.voronoi_geometry.Site(0, 0.5, 0.5),)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	excursion = 2.0 * domain.coordinate_tolerance
	bad_cell = dataclasses.replace(
		result.partition.cells[0],
		vertices=(
			(0.0, 0.0),
			(1.0, 0.0),
			(1.0, 0.49),
			(1.0 + excursion, 0.5),
			(1.0, 0.51),
			(1.0, 1.0),
			(0.0, 1.0),
		),
	)
	bad_partition = dataclasses.replace(result.partition, cells=(bad_cell,))
	bad_polygon = shapely.geometry.Polygon(bad_cell.vertices)
	outside_area = bad_polygon.difference(
		colorbynumber.voronoi_geometry.domain_polygon(domain)
	).area
	assert outside_area < domain.area_tolerance
	with pytest.raises(colorbynumber.voronoi_geometry.GeometryError, match="domain bounds"):
		colorbynumber.voronoi_geometry.validate_partition(bad_partition)


#============================================
def test_validation_rejects_invalid_cell_topology() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(1, 1)
	sites = (colorbynumber.voronoi_geometry.Site(0, 0.5, 0.5),)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	bad_cell = dataclasses.replace(
		result.partition.cells[0],
		vertices=((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.5, -0.5)),
	)
	bad_partition = dataclasses.replace(result.partition, cells=(bad_cell,))
	with pytest.raises(colorbynumber.voronoi_geometry.GeometryError, match="invalid topology"):
		colorbynumber.voronoi_geometry.validate_partition(bad_partition)


#============================================
def test_general_constructor_reports_ordered_voronoi_capability(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(3, 2)
	sites = colorbynumber.voronoi_geometry.generate_uniform_sites(domain, 19)
	monkeypatch.setattr(shapely, "geos_version", (3, 11, 9))
	with pytest.raises(colorbynumber.voronoi_geometry.GeometryError, match="GEOS 3.12"):
		colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
