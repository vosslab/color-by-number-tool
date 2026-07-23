"""Bounded Voronoi geometry for maintainer experiments."""

# Standard Library
import math
import time
import inspect
import dataclasses

# PIP3 modules
import numpy
import shapely
import shapely.geometry


RELATIVE_TOLERANCE = 1e-10
TOLERANCE_POLICY_VERSION = "unit-area-v1"
VORONOI_GEOMETRY_IMPLEMENTATION_VERSION = 6
ORDERED_VORONOI_MINIMUM_GEOS_VERSION = (3, 12, 0)
BOUNDARY_SIDE_ORDER = ("left", "right", "bottom", "top")
HARD_CORE_ATTEMPT_POLICY = "total-uniform-candidate-draws-v1"


#============================================
class GeometryError(ValueError):
	"""Report an invalid experimental geometry request or partition."""


#============================================
class NumericConditioningError(GeometryError):
	"""Report dimensions that cannot support the numeric tolerance contract."""


#============================================
class HardCoreGenerationError(GeometryError):
	"""Report deterministic exhaustion before a hard-core layout reaches its target."""


#============================================
@dataclasses.dataclass(frozen=True)
class Domain:
	"""Unit-area rectangular geometry derived from resolved grid dimensions."""

	columns: int
	rows: int
	site_count: int
	width: float
	height: float
	nominal_spacing: float
	coordinate_tolerance: float
	area_tolerance: float


#============================================
@dataclasses.dataclass(frozen=True)
class Site:
	"""One ordered Voronoi generating site."""

	identifier: int
	x: float
	y: float


#============================================
@dataclasses.dataclass(frozen=True)
class Cell:
	"""One canonical bounded Voronoi cell."""

	site_identifier: int
	vertices: tuple[tuple[float, float], ...]
	boundary_sides: tuple[str, ...]
	boundary_class: str
	boundary_subtype: str | None


#============================================
@dataclasses.dataclass(frozen=True)
class Partition:
	"""A validated bounded partition in stable site order."""

	domain: Domain
	sites: tuple[Site, ...]
	cells: tuple[Cell, ...]
	constructor_family: str


#============================================
@dataclasses.dataclass(frozen=True)
class ConstructionResult:
	"""A partition plus separately measured construction-phase timings."""

	partition: Partition
	site_validation_seconds: float
	construction_seconds: float
	partition_validation_seconds: float


#============================================
def _conditioning_error(
	columns: int,
	rows: int,
	tolerance: float | None,
	short_side: float | None,
	nominal_spacing: float | None,
) -> NumericConditioningError:
	"""Build the stable numeric-conditioning error.

	Args:
		columns: Resolved column count.
		rows: Resolved row count.
		tolerance: Computed coordinate tolerance when available.
		short_side: Computed short domain side when available.
		nominal_spacing: Computed nominal spacing when available.

	Returns:
		The numeric-conditioning exception.
	"""
	message = (
		"Experimental Voronoi numeric conditioning failed for resolved dimensions "
		f"{columns}x{rows}: coordinate_tolerance={tolerance!r}, "
		f"short_side={short_side!r}, nominal_spacing={nominal_spacing!r}"
	)
	error = NumericConditioningError(message)
	return error


#============================================
def create_domain(columns: int, rows: int) -> Domain:
	"""Create the normalized unit-area domain and centralized tolerances.

	Args:
		columns: Positive resolved column count.
		rows: Positive resolved row count.

	Returns:
		The conditioned unit-area domain.

	Raises:
		GeometryError: Dimensions are not positive integers.
		NumericConditioningError: Float conversion or conditioning fails.
	"""
	if isinstance(columns, bool) or isinstance(rows, bool):
		raise GeometryError("Resolved dimensions must be positive integers")
	if not isinstance(columns, int) or not isinstance(rows, int):
		raise GeometryError("Resolved dimensions must be positive integers")
	if columns <= 0 or rows <= 0:
		raise GeometryError("Resolved dimensions must be greater than zero")

	site_count = columns * rows
	try:
		aspect = columns / rows
	except OverflowError as error:
		raise _conditioning_error(columns, rows, None, None, None) from error
	try:
		width = math.sqrt(aspect)
		nominal_spacing = 1.0 / math.sqrt(site_count)
	except OverflowError as error:
		raise _conditioning_error(columns, rows, None, None, None) from error
	if width == 0.0 or not math.isfinite(width) or nominal_spacing == 0.0:
		raise _conditioning_error(columns, rows, None, None, nominal_spacing)
	height = 1.0 / width
	coordinate_floor = 8.0 * math.ulp(max(width, height))
	coordinate_tolerance = max(
		RELATIVE_TOLERANCE * nominal_spacing,
		coordinate_floor,
	)
	area_tolerance = max(RELATIVE_TOLERANCE, 8.0 * math.ulp(1.0))
	short_side = min(width, height)
	condition_limit = min(short_side, nominal_spacing)
	if not math.isfinite(height) or not math.isfinite(coordinate_tolerance):
		raise _conditioning_error(
			columns, rows, coordinate_tolerance, short_side, nominal_spacing
		)
	if 2.0 * coordinate_tolerance >= condition_limit:
		raise _conditioning_error(
			columns, rows, coordinate_tolerance, short_side, nominal_spacing
		)
	domain = Domain(
		columns=columns,
		rows=rows,
		site_count=site_count,
		width=width,
		height=height,
		nominal_spacing=nominal_spacing,
		coordinate_tolerance=coordinate_tolerance,
		area_tolerance=area_tolerance,
	)
	return domain


#============================================
def domain_polygon(domain: Domain) -> shapely.Polygon:
	"""Return the Shapely polygon for a domain.

	Args:
		domain: Normalized domain.

	Returns:
		The closed rectangular polygon.
	"""
	polygon = shapely.geometry.box(0.0, 0.0, domain.width, domain.height)
	return polygon


#============================================
def _distance_squared(first: tuple[float, float], second: tuple[float, float]) -> float:
	"""Return squared Euclidean distance between two coordinates."""
	dx = first[0] - second[0]
	dy = first[1] - second[1]
	distance = dx * dx + dy * dy
	return distance


#============================================
def _signed_area(vertices: list[tuple[float, float]]) -> float:
	"""Return twice the signed polygon area."""
	origin_x, origin_y = vertices[0]
	terms = []
	for index in range(1, len(vertices) - 1):
		first_x = vertices[index][0] - origin_x
		first_y = vertices[index][1] - origin_y
		second_x = vertices[index + 1][0] - origin_x
		second_y = vertices[index + 1][1] - origin_y
		terms.append(first_x * second_y - second_x * first_y)
	total = math.fsum(terms)
	return total


#============================================
def _is_redundant_vertex(
	previous: tuple[float, float],
	current: tuple[float, float],
	following: tuple[float, float],
) -> bool:
	"""Return whether a vertex is exactly duplicate or provably collinear."""
	if current == previous or current == following:
		return True
	first_x = current[0] - previous[0]
	first_y = current[1] - previous[1]
	second_x = following[0] - previous[0]
	second_y = following[1] - previous[1]
	cross = second_x * first_y - second_y * first_x
	if cross != 0.0:
		return False
	within_x = min(previous[0], following[0]) <= current[0] <= max(
		previous[0], following[0]
	)
	within_y = min(previous[1], following[1]) <= current[1] <= max(
		previous[1], following[1]
	)
	redundant = within_x and within_y
	return redundant


#============================================
def canonicalize_polygon(
	coordinates: object,
) -> tuple[tuple[float, float], ...]:
	"""Canonicalize an open polygon ring without changing its topology.

	Args:
		coordinates: Iterable coordinate pairs.

	Returns:
		A counterclockwise open ring beginning at its smallest vertex.

	Raises:
		GeometryError: The canonical result is not a positive-area polygon.
	"""
	vertices = [(float(point[0]), float(point[1])) for point in coordinates]
	if any(not math.isfinite(value) for vertex in vertices for value in vertex):
		raise GeometryError("Canonical polygon has nonfinite coordinates")
	if len(vertices) > 1 and vertices[0] == vertices[-1]:
		vertices.pop()
	deduplicated: list[tuple[float, float]] = []
	for vertex in vertices:
		if not deduplicated or vertex != deduplicated[-1]:
			deduplicated.append(vertex)
	if len(deduplicated) > 1 and deduplicated[0] == deduplicated[-1]:
		deduplicated.pop()
	vertices = deduplicated
	changed = True
	while changed and len(vertices) >= 3:
		changed = False
		kept: list[tuple[float, float]] = []
		for index, vertex in enumerate(vertices):
			previous = vertices[index - 1]
			following = vertices[(index + 1) % len(vertices)]
			if _is_redundant_vertex(previous, vertex, following):
				changed = True
			else:
				kept.append(vertex)
		vertices = kept
	if len(vertices) < 3:
		raise GeometryError("Canonical polygon has fewer than three vertices")
	signed_area = _signed_area(vertices)
	if signed_area == 0.0 or not math.isfinite(signed_area):
		raise GeometryError("Canonical polygon has invalid area")
	if signed_area < 0.0:
		vertices.reverse()
	start_index = min(range(len(vertices)), key=lambda index: vertices[index])
	ordered = vertices[start_index:] + vertices[:start_index]
	canonical = tuple(ordered)
	return canonical


#============================================
def validate_sites(domain: Domain, sites: tuple[Site, ...]) -> tuple[Site, ...]:
	"""Validate site identifiers, coordinates, bounds, and separation.

	Args:
		domain: Normalized domain.
		sites: Sites in identifier order.

	Returns:
		The validated sites unchanged.

	Raises:
		GeometryError: A site violates the geometry contract.
	"""
	if len(sites) != domain.site_count:
		raise GeometryError(
			f"Site count {len(sites)} does not equal dimensions product {domain.site_count}"
		)
	for expected_identifier, site in enumerate(sites):
		if site.identifier != expected_identifier:
			raise GeometryError("Site identifiers must be unique, contiguous, and ordered")
		if not math.isfinite(site.x) or not math.isfinite(site.y):
			raise GeometryError(f"Site {site.identifier} has nonfinite coordinates")
		if site.x < 0.0 or site.x > domain.width:
			raise GeometryError(f"Site {site.identifier} lies outside the domain")
		if site.y < 0.0 or site.y > domain.height:
			raise GeometryError(f"Site {site.identifier} lies outside the domain")

	points = [shapely.geometry.Point(site.x, site.y) for site in sites]
	tree = shapely.STRtree(points)
	pairs = tree.query(
		points,
		predicate="dwithin",
		distance=domain.coordinate_tolerance,
	)
	for first, second in zip(pairs[0], pairs[1], strict=True):
		first_identifier = int(first)
		second_identifier = int(second)
		if first_identifier < second_identifier:
			raise GeometryError(
				"Duplicate or near-duplicate sites: "
				f"{first_identifier} and {second_identifier}"
			)
	return sites


#============================================
def generate_square_grid_sites(domain: Domain) -> tuple[Site, ...]:
	"""Generate one raw deterministic site per resolved square-grid cell."""
	sites: list[Site] = []
	identifier = 0
	for row in range(domain.rows):
		y = (row + 0.5) * domain.height / domain.rows
		for column in range(domain.columns):
			x = (column + 0.5) * domain.width / domain.columns
			sites.append(Site(identifier, x, y))
			identifier += 1
	generated_sites = tuple(sites)
	return generated_sites


#============================================
def generate_uniform_sites(domain: Domain, seed: int) -> tuple[Site, ...]:
	"""Generate raw independent uniform sites from a local NumPy generator.

	Args:
		domain: Normalized domain.
		seed: Explicit nonnegative replay seed.

	Returns:
		Unvalidated sites in generation order.

	Raises:
		GeometryError: The seed is invalid.
	"""
	_validate_experiment_seed(seed)
	random_generator = numpy.random.default_rng(seed)
	coordinates = random_generator.random((domain.site_count, 2))
	sites = tuple(
		Site(identifier, float(point[0] * domain.width), float(point[1] * domain.height))
		for identifier, point in enumerate(coordinates)
	)
	return sites


#============================================
def _validate_experiment_seed(seed: int) -> None:
	"""Validate one explicit maintainer replay seed."""
	if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
		raise GeometryError("The experimental seed must be a nonnegative integer")


#============================================
def generate_stratified_jitter_sites(
	domain: Domain,
	seed: int,
	jitter_fraction: float,
) -> tuple[Site, ...]:
	"""Generate one raw site per rectangular stratum with bounded jitter.

	The dimensionless ``jitter_fraction`` scales displacement from each stratum
	center independently on both axes. Zero preserves the centered grid and one
	allows the full stratum width and height. Values outside ``[0, 1]`` are
	rejected rather than clamped.

	Args:
		domain: Normalized domain partitioned into ``columns * rows`` strata.
		seed: Explicit nonnegative replay seed.
		jitter_fraction: Fraction of each stratum spanned by the jitter interval.

	Returns:
		Unvalidated sites in deterministic row-major stratum order.

	Raises:
		GeometryError: The seed or jitter fraction is invalid.
	"""
	_validate_experiment_seed(seed)
	if isinstance(jitter_fraction, bool) or not isinstance(jitter_fraction, (int, float)):
		raise GeometryError("The stratified jitter fraction must be a finite number")
	jitter_value = float(jitter_fraction)
	if not math.isfinite(jitter_value) or not 0.0 <= jitter_value <= 1.0:
		raise GeometryError("The stratified jitter fraction must be between 0 and 1")
	random_generator = numpy.random.default_rng(seed)
	coordinates = random_generator.random((domain.site_count, 2))
	stratum_width = domain.width / domain.columns
	stratum_height = domain.height / domain.rows
	sites: list[Site] = []
	for identifier, point in enumerate(coordinates):
		row, column = divmod(identifier, domain.columns)
		center_x = (column + 0.5) * domain.width / domain.columns
		center_y = (row + 0.5) * domain.height / domain.rows
		x_offset = jitter_value * (float(point[0]) - 0.5) * stratum_width
		y_offset = jitter_value * (float(point[1]) - 0.5) * stratum_height
		x = center_x + x_offset
		y = center_y + y_offset
		sites.append(Site(identifier, x, y))
	generated_sites = tuple(sites)
	return generated_sites


#============================================
def _hard_core_candidate_is_clear(
	candidate_x: float,
	candidate_y: float,
	minimum_distance_squared: float,
	bin_x: int,
	bin_y: int,
	bins: dict[tuple[int, int], list[Site]],
) -> bool:
	"""Return whether the candidate clears sites in its spatial-bin neighborhood."""
	for neighbor_y in range(bin_y - 1, bin_y + 2):
		for neighbor_x in range(bin_x - 1, bin_x + 2):
			for site in bins.get((neighbor_x, neighbor_y), []):
				dx = candidate_x - site.x
				dy = candidate_y - site.y
				if dx * dx + dy * dy < minimum_distance_squared:
					return False
	return True


#============================================
def hard_core_distance_parameters(
	domain: Domain,
	minimum_distance_ratio: float,
) -> tuple[float, float, float]:
	"""Return numerically usable hard-core distance and bin-index values.

	Args:
		domain: Normalized target domain.
		minimum_distance_ratio: Requested center distance divided by nominal spacing.

	Returns:
		The absolute distance, squared distance, and maximum bin coordinate.

	Raises:
		GeometryError: The ratio or a derived value is not finite and positive.
	"""
	if (
		isinstance(minimum_distance_ratio, bool)
		or not isinstance(minimum_distance_ratio, (int, float))
	):
		raise GeometryError("The hard-core minimum-distance ratio must be a finite number")
	try:
		ratio = float(minimum_distance_ratio)
	except OverflowError as error:
		raise GeometryError(
			"The hard-core minimum-distance ratio must be a finite number"
		) from error
	if not math.isfinite(ratio) or ratio <= 0.0:
		raise GeometryError("The hard-core minimum-distance ratio must be greater than zero")
	minimum_distance = ratio * domain.nominal_spacing
	if not math.isfinite(minimum_distance) or minimum_distance <= 0.0:
		raise GeometryError("The hard-core minimum distance is not numerically representable")
	minimum_distance_squared = minimum_distance * minimum_distance
	if not math.isfinite(minimum_distance_squared) or minimum_distance_squared <= 0.0:
		raise GeometryError(
			"The squared hard-core minimum distance is not numerically representable"
		)
	maximum_bin_coordinate = max(domain.width, domain.height) / minimum_distance
	if not math.isfinite(maximum_bin_coordinate) or maximum_bin_coordinate <= 0.0:
		raise GeometryError(
			"The hard-core maximum bin coordinate is not numerically representable"
		)
	parameters = (
		minimum_distance,
		minimum_distance_squared,
		maximum_bin_coordinate,
	)
	return parameters


#============================================
def generate_hard_core_sites(
	domain: Domain,
	seed: int,
	minimum_distance_ratio: float,
	attempt_budget: int,
) -> tuple[Site, ...]:
	"""Generate raw Euclidean hard-core sites by deterministic dart throwing.

	The minimum center distance is ``minimum_distance_ratio * nominal_spacing``.
	The owned neighbor index uses square bins one requested distance wide, so
	only the current and eight adjacent bins can contain a conflicting site.
	``HARD_CORE_ATTEMPT_POLICY`` defines the budget as the total number of
	uniform candidate draws. Exhaustion raises an explicit error and performs no
	retry, repair, joggle, or seed change.

	Args:
		domain: Normalized target domain.
		seed: Explicit nonnegative replay seed.
		minimum_distance_ratio: Requested center distance divided by nominal spacing.
		attempt_budget: Maximum total uniform candidate draws.

	Returns:
		Exactly ``domain.site_count`` unvalidated sites in acceptance order.

	Raises:
		GeometryError: A parameter is invalid.
		HardCoreGenerationError: The attempt budget is exhausted before exact count.
	"""
	_validate_experiment_seed(seed)
	if isinstance(attempt_budget, bool) or not isinstance(attempt_budget, int):
		raise GeometryError("The hard-core attempt budget must be an integer")
	if attempt_budget < domain.site_count:
		raise GeometryError("The hard-core attempt budget must be at least the site count")
	minimum_distance, minimum_distance_squared, _maximum_bin_coordinate = (
		hard_core_distance_parameters(domain, minimum_distance_ratio)
	)
	ratio = float(minimum_distance_ratio)
	random_generator = numpy.random.default_rng(seed)
	bins: dict[tuple[int, int], list[Site]] = {}
	sites: list[Site] = []
	for _attempt in range(attempt_budget):
		point = random_generator.random(2)
		candidate_x = float(point[0] * domain.width)
		candidate_y = float(point[1] * domain.height)
		bin_x = math.floor(candidate_x / minimum_distance)
		bin_y = math.floor(candidate_y / minimum_distance)
		if not _hard_core_candidate_is_clear(
			candidate_x,
			candidate_y,
			minimum_distance_squared,
			bin_x,
			bin_y,
			bins,
		):
			continue
		site = Site(len(sites), candidate_x, candidate_y)
		sites.append(site)
		bins.setdefault((bin_x, bin_y), []).append(site)
		if len(sites) == domain.site_count:
			generated_sites = tuple(sites)
			return generated_sites
	accepted_count = len(sites)
	message = (
		"Hard-core generation exhausted its deterministic attempt budget: "
		f"accepted={accepted_count}, target={domain.site_count}, "
		f"attempt_budget={attempt_budget}, minimum_distance_ratio={ratio!r}, "
		f"seed={seed}, policy={HARD_CORE_ATTEMPT_POLICY}"
	)
	raise HardCoreGenerationError(message)


#============================================
def _sites_are_collinear(domain: Domain, sites: tuple[Site, ...]) -> bool:
	"""Return whether all distinct sites lie on one line within policy."""
	if len(sites) <= 2:
		return True
	base = sites[0]
	farthest = max(
		sites[1:],
		key=lambda site: (site.x - base.x) ** 2 + (site.y - base.y) ** 2,
	)
	dx = farthest.x - base.x
	dy = farthest.y - base.y
	length = math.hypot(dx, dy)
	for site in sites[1:]:
		cross = abs(dx * (site.y - base.y) - dy * (site.x - base.x))
		if cross / length > domain.coordinate_tolerance:
			return False
	return True


#============================================
def _sites_are_centered_grid(domain: Domain, sites: tuple[Site, ...]) -> bool:
	"""Return whether sites are the exact ordered square-grid control."""
	if domain.columns == 1 or domain.rows == 1:
		return False
	for identifier, site in enumerate(sites):
		row, column = divmod(identifier, domain.columns)
		expected_x = (column + 0.5) * domain.width / domain.columns
		expected_y = (row + 0.5) * domain.height / domain.rows
		if site.x != expected_x:
			return False
		if site.y != expected_y:
			return False
	return True


#============================================
def _construct_centered_grid_vertices(
	domain: Domain,
) -> tuple[tuple[tuple[float, float], ...], ...]:
	"""Construct the exact analytical Voronoi cells of the grid control."""
	all_vertices: list[tuple[tuple[float, float], ...]] = []
	for identifier in range(domain.site_count):
		row, column = divmod(identifier, domain.columns)
		left = column * domain.width / domain.columns
		right = (column + 1) * domain.width / domain.columns
		bottom = row * domain.height / domain.rows
		top = (row + 1) * domain.height / domain.rows
		vertices = ((left, bottom), (right, bottom), (right, top), (left, top))
		canonical = canonicalize_polygon(vertices)
		all_vertices.append(canonical)
	return tuple(all_vertices)


#============================================
def _clip_half_plane(
	vertices: list[tuple[float, float]],
	owner: Site,
	other: Site,
) -> list[tuple[float, float]]:
	"""Clip a convex polygon to the owner's perpendicular-bisector half-plane."""
	normal_x = other.x - owner.x
	normal_y = other.y - owner.y
	midpoint_x = owner.x + 0.5 * normal_x
	midpoint_y = owner.y + 0.5 * normal_y
	clipped: list[tuple[float, float]] = []
	for index, start in enumerate(vertices):
		end = vertices[(index + 1) % len(vertices)]
		start_value = (
			normal_x * (start[0] - midpoint_x)
			+ normal_y * (start[1] - midpoint_y)
		)
		end_value = (
			normal_x * (end[0] - midpoint_x)
			+ normal_y * (end[1] - midpoint_y)
		)
		start_inside = start_value <= 0.0
		end_inside = end_value <= 0.0
		if start_inside:
			clipped.append(start)
		if start_inside != end_inside:
			fraction = start_value / (start_value - end_value)
			intersection = (
				start[0] + fraction * (end[0] - start[0]),
				start[1] + fraction * (end[1] - start[1]),
			)
			clipped.append(intersection)
	return clipped


#============================================
def _construct_analytical_vertices(
	domain: Domain,
	sites: tuple[Site, ...],
) -> tuple[tuple[tuple[float, float], ...], ...]:
	"""Construct bounded cells with the owned analytical clipping path."""
	rectangle = [
		(0.0, 0.0),
		(domain.width, 0.0),
		(domain.width, domain.height),
		(0.0, domain.height),
	]
	all_vertices: list[tuple[tuple[float, float], ...]] = []
	for owner in sites:
		vertices = rectangle.copy()
		for other in sites:
			if other.identifier != owner.identifier:
				vertices = _clip_half_plane(
					vertices,
					owner,
					other,
				)
			if not vertices:
				raise GeometryError(
					f"Analytical constructor produced empty cell for site {owner.identifier}"
				)
		canonical = canonicalize_polygon(vertices)
		all_vertices.append(canonical)
	return tuple(all_vertices)


#============================================
def _require_ordered_voronoi_capability() -> None:
	"""Require the Shapely and GEOS capability used for stable owner ordering."""
	if not hasattr(shapely, "voronoi_polygons"):
		raise GeometryError(
			"General Voronoi construction requires Shapely 2.1+ with "
			"voronoi_polygons(ordered=True) and GEOS 3.12+"
		)
	parameters = inspect.signature(shapely.voronoi_polygons).parameters
	geos_supported = shapely.geos_version >= ORDERED_VORONOI_MINIMUM_GEOS_VERSION
	if "ordered" not in parameters or not geos_supported:
		raise GeometryError(
			"General Voronoi construction requires Shapely 2.1+ with "
			"voronoi_polygons(ordered=True) and GEOS 3.12+; found "
			f"Shapely {shapely.__version__} with GEOS {shapely.geos_version_string}"
		)


#============================================
def _construct_shapely_vertices(
	domain: Domain,
	sites: tuple[Site, ...],
) -> tuple[tuple[tuple[float, float], ...], ...]:
	"""Construct ordinary bounded cells through Shapely and GEOS."""
	_require_ordered_voronoi_capability()
	points = shapely.geometry.MultiPoint([(site.x, site.y) for site in sites])
	regions = shapely.voronoi_polygons(
		points,
		extend_to=domain_polygon(domain),
		only_edges=False,
		ordered=True,
	)
	polygons = list(shapely.get_parts(regions))
	if len(polygons) != len(sites):
		raise GeometryError("GEOS did not return exactly one Voronoi cell per site")
	domain_shape = domain_polygon(domain)
	all_vertices: list[tuple[tuple[float, float], ...]] = []
	for site, polygon in zip(sites, polygons, strict=True):
		if polygon.geom_type != "Polygon":
			raise GeometryError(f"GEOS cell {site.identifier} is not a polygon")
		clipped_polygon = polygon.intersection(domain_shape)
		if clipped_polygon.geom_type != "Polygon" or clipped_polygon.is_empty:
			raise GeometryError(f"GEOS clipping invalidated cell {site.identifier}")
		coordinates = list(clipped_polygon.exterior.coords)
		canonical = canonicalize_polygon(coordinates)
		owner_point = shapely.geometry.Point(site.x, site.y)
		canonical_polygon = shapely.geometry.Polygon(canonical)
		if canonical_polygon.distance(owner_point) > domain.coordinate_tolerance:
			raise GeometryError(
				f"GEOS cell order does not preserve owner site {site.identifier}"
			)
		all_vertices.append(canonical)
	return tuple(all_vertices)


#============================================
def _boundary_sides_from_vertices(
	domain: Domain,
	vertices: tuple[tuple[float, float], ...],
) -> tuple[str, ...]:
	"""Classify domain-side contact from canonical vertex coordinates."""
	tolerance = domain.coordinate_tolerance
	contacts: set[str] = set()
	for x, y in vertices:
		if abs(x) <= tolerance:
			contacts.add("left")
		if abs(x - domain.width) <= tolerance:
			contacts.add("right")
		if abs(y) <= tolerance:
			contacts.add("bottom")
		if abs(y - domain.height) <= tolerance:
			contacts.add("top")
	ordered = tuple(side for side in BOUNDARY_SIDE_ORDER if side in contacts)
	return ordered


#============================================
def _cell_from_vertices(
	domain: Domain,
	site_identifier: int,
	vertices: tuple[tuple[float, float], ...],
) -> Cell:
	"""Build boundary metadata for canonical cell vertices."""
	sides = _boundary_sides_from_vertices(domain, vertices)
	if not sides:
		boundary_class = "interior"
		boundary_subtype = None
	else:
		boundary_class = "boundary"
		corners = (
			(0.0, 0.0),
			(domain.width, 0.0),
			(domain.width, domain.height),
			(0.0, domain.height),
		)
		tolerance_squared = domain.coordinate_tolerance ** 2
		has_corner = any(
			_distance_squared(vertex, corner) <= tolerance_squared
			for vertex in vertices
			for corner in corners
		)
		boundary_subtype = "corner" if has_corner else "edge"
	cell = Cell(
		site_identifier=site_identifier,
		vertices=vertices,
		boundary_sides=sides,
		boundary_class=boundary_class,
		boundary_subtype=boundary_subtype,
	)
	return cell


#============================================
def _independent_boundary_query(domain: Domain, polygon: shapely.Polygon) -> tuple[str, ...]:
	"""Query side contact with independent Shapely line distances."""
	lines = {
		"left": shapely.geometry.LineString(((0.0, 0.0), (0.0, domain.height))),
		"right": shapely.geometry.LineString(
			((domain.width, 0.0), (domain.width, domain.height))
		),
		"bottom": shapely.geometry.LineString(((0.0, 0.0), (domain.width, 0.0))),
		"top": shapely.geometry.LineString(
			((0.0, domain.height), (domain.width, domain.height))
		),
	}
	sides = tuple(
		side
		for side in BOUNDARY_SIDE_ORDER
		if polygon.distance(lines[side]) <= domain.coordinate_tolerance
	)
	return sides


#============================================
def validate_partition(partition: Partition) -> None:
	"""Validate all geometry, ownership, topology, and boundary invariants.

	Args:
		partition: Candidate bounded partition.

	Raises:
		GeometryError: Any contract invariant fails.
	"""
	domain = partition.domain
	if len(partition.cells) != domain.site_count:
		raise GeometryError("Partition cell count does not equal dimensions product")
	if len(partition.sites) != domain.site_count:
		raise GeometryError("Partition site count does not equal dimensions product")
	polygons: list[shapely.Polygon] = []
	for site, cell in zip(partition.sites, partition.cells, strict=True):
		if cell.site_identifier != site.identifier:
			raise GeometryError("Partition cells are not in stable site order")
		if any(
			not math.isfinite(value)
			for vertex in cell.vertices
			for value in vertex
		):
			raise GeometryError(f"Cell {site.identifier} has nonfinite coordinates")
		polygon = shapely.geometry.Polygon(cell.vertices)
		if polygon.is_empty:
			raise GeometryError(f"Cell {site.identifier} is empty")
		if not math.isfinite(polygon.area) or polygon.area <= 0.0:
			raise GeometryError(f"Cell {site.identifier} has invalid area {polygon.area!r}")
		if not polygon.is_valid or not polygon.is_simple:
			raise GeometryError(f"Cell {site.identifier} has invalid topology")
		if len(polygon.interiors) != 0:
			raise GeometryError(f"Cell {site.identifier} has a hole")
		min_x, min_y, max_x, max_y = polygon.bounds
		tolerance = domain.coordinate_tolerance
		if (
			min_x < -tolerance
			or min_y < -tolerance
			or max_x > domain.width + tolerance
			or max_y > domain.height + tolerance
		):
			raise GeometryError(f"Cell {site.identifier} lies outside the domain bounds")
		outside_area = polygon.difference(domain_polygon(domain)).area
		if outside_area > domain.area_tolerance:
			raise GeometryError(f"Cell {site.identifier} lies outside the domain")
		owner_point = shapely.geometry.Point(site.x, site.y)
		if polygon.distance(owner_point) > domain.coordinate_tolerance:
			raise GeometryError(f"Cell {site.identifier} does not own its site")
		queried_sides = _independent_boundary_query(domain, polygon)
		if queried_sides != cell.boundary_sides:
			raise GeometryError(f"Cell {site.identifier} boundary classification disagrees")
		polygons.append(polygon)

	union = shapely.union_all(polygons)
	domain_shape = domain_polygon(domain)
	uncovered_area = domain_shape.difference(union).area
	overlap_area = max(0.0, sum(polygon.area for polygon in polygons) - union.area)
	area_error = abs(sum(polygon.area for polygon in polygons) - 1.0)
	if uncovered_area > domain.area_tolerance:
		raise GeometryError(f"Partition leaves uncovered area {uncovered_area!r}")
	if overlap_area > domain.area_tolerance:
		raise GeometryError(f"Partition has overlap area {overlap_area!r}")
	if area_error > domain.area_tolerance:
		raise GeometryError(f"Partition area error is {area_error!r}")


#============================================
def construct_bounded_voronoi(
	domain: Domain,
	sites: tuple[Site, ...],
) -> ConstructionResult:
	"""Construct and validate a bounded partition in stable site order.

	Args:
		domain: Unit-area domain derived from resolved dimensions.
		sites: Ordered sites whose count equals the dimensions product.

	Returns:
		The validated partition and separate construction timings.
	"""
	site_validation_start = time.perf_counter()
	validated_sites = validate_sites(domain, sites)
	site_validation_seconds = time.perf_counter() - site_validation_start
	construction_start = time.perf_counter()
	if _sites_are_collinear(domain, validated_sites):
		all_vertices = _construct_analytical_vertices(domain, validated_sites)
		constructor_family = "analytical-half-plane"
	elif _sites_are_centered_grid(domain, validated_sites):
		all_vertices = _construct_centered_grid_vertices(domain)
		constructor_family = "analytical-square-grid"
	else:
		all_vertices = _construct_shapely_vertices(domain, validated_sites)
		constructor_family = "shapely-geos-voronoi"
	cells = tuple(
		_cell_from_vertices(domain, site.identifier, vertices)
		for site, vertices in zip(validated_sites, all_vertices, strict=True)
	)
	construction_seconds = time.perf_counter() - construction_start
	partition = Partition(
		domain=domain,
		sites=validated_sites,
		cells=cells,
		constructor_family=constructor_family,
	)
	partition_validation_start = time.perf_counter()
	validate_partition(partition)
	partition_validation_seconds = time.perf_counter() - partition_validation_start
	result = ConstructionResult(
		partition=partition,
		site_validation_seconds=site_validation_seconds,
		construction_seconds=construction_seconds,
		partition_validation_seconds=partition_validation_seconds,
	)
	return result


#============================================
def validate_lloyd_alpha(alpha: float) -> float:
	"""Return one finite bounded Lloyd movement fraction.

	Args:
		alpha: Fraction of the site-to-centroid displacement to apply.

	Returns:
		The validated double-precision movement fraction.

	Raises:
		GeometryError: Alpha is not a finite number in the closed unit interval.
	"""
	if isinstance(alpha, bool) or not isinstance(alpha, (int, float)):
		raise GeometryError("The bounded Lloyd alpha must be a finite number")
	alpha_value = float(alpha)
	if not math.isfinite(alpha_value) or not 0.0 <= alpha_value <= 1.0:
		raise GeometryError("The bounded Lloyd alpha must be between 0 and 1")
	return alpha_value


#============================================
def relax_bounded_lloyd_once(
	domain: Domain,
	sites: tuple[Site, ...],
	alpha: float,
) -> tuple[Site, ...]:
	"""Apply one deterministic bounded Lloyd movement iteration.

	The iteration constructs and validates the current clipped partition, then
	moves every site toward the centroid of its owned convex cell. The returned
	sites retain their identifiers and order. A caller constructs the returned
	partition as a separate stage when it needs checkpoint geometry or metrics.

	Args:
		domain: Normalized target domain.
		sites: Ordered source sites.
		alpha: Fraction of each site-to-centroid displacement to apply.

	Returns:
		Validated moved sites in unchanged identifier order.

	Raises:
		GeometryError: Alpha, source geometry, or moved sites violate the contract.
	"""
	alpha_value = validate_lloyd_alpha(alpha)
	source_result = construct_bounded_voronoi(domain, sites)
	moved_sites: list[Site] = []
	for site, cell in zip(
		source_result.partition.sites,
		source_result.partition.cells,
		strict=True,
	):
		centroid = shapely.geometry.Polygon(cell.vertices).centroid
		x = (1.0 - alpha_value) * site.x + alpha_value * centroid.x
		y = (1.0 - alpha_value) * site.y + alpha_value * centroid.y
		moved_sites.append(Site(site.identifier, x, y))
	validated_sites = validate_sites(domain, tuple(moved_sites))
	return validated_sites


#============================================
def nearest_site_identifier(
	sites: tuple[Site, ...],
	x: float,
	y: float,
	coordinate_tolerance: float,
) -> int:
	"""Return the nearest site, breaking sampled boundary ties by identifier.

	Args:
		sites: Ordered candidate sites.
		x: Sample x-coordinate.
		y: Sample y-coordinate.
		coordinate_tolerance: Shared domain coordinate tolerance.

	Returns:
		The lowest identifier among nearest sites within tolerance.
	"""
	best_identifier = sites[0].identifier
	best_distance = (x - sites[0].x) ** 2 + (y - sites[0].y) ** 2
	for site in sites[1:]:
		distance = (x - site.x) ** 2 + (y - site.y) ** 2
		distance_tolerance = coordinate_tolerance * (
			2.0 * math.sqrt(max(best_distance, distance)) + coordinate_tolerance
		)
		if distance < best_distance - distance_tolerance:
			best_identifier = site.identifier
			best_distance = distance
		elif abs(distance - best_distance) <= distance_tolerance:
			best_identifier = min(best_identifier, site.identifier)
	identifier = best_identifier
	return identifier
