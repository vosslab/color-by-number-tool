"""Separate measurements for bounded Voronoi experiment partitions."""

# Standard Library
import math
import time
import dataclasses

# PIP3 modules
import numpy
import shapely
import shapely.geometry

# local repo modules
import colorbynumber.voronoi_geometry


#============================================
@dataclasses.dataclass(frozen=True)
class PartitionEvaluation:
	"""Deterministic quality metrics and separate single-run timing metadata."""

	quality_metrics: dict[str, float | None]
	timing_metadata: dict[str, float]


#============================================
def _coefficient_of_variation(values: numpy.ndarray) -> float:
	"""Return population standard deviation divided by mean."""
	coefficient = float(numpy.std(values) / numpy.mean(values))
	return coefficient


#============================================
def _nearest_neighbor_distances(
	partition: colorbynumber.voronoi_geometry.Partition,
) -> numpy.ndarray:
	"""Return one nearest-neighbor distance per site using a spatial index."""
	if len(partition.sites) == 1:
		return numpy.array([], dtype=float)
	coordinates = numpy.array([(site.x, site.y) for site in partition.sites])
	points = shapely.points(coordinates)
	tree = shapely.STRtree(points)
	nearest = tree.query_nearest(
		points,
		exclusive=True,
		all_matches=False,
		return_distance=True,
	)
	distances = numpy.asarray(nearest[1], dtype=float)
	return distances


#============================================
def exact_bounded_covering_radius(
	partition: colorbynumber.voronoi_geometry.Partition,
) -> float:
	"""Return the exact covering radius of bounded convex Voronoi cells.

	The farthest point in each convex cell from its generating site is a vertex,
	so this scans every owned cell vertex once.
	"""
	maximum_squared_distance = 0.0
	for site, cell in zip(partition.sites, partition.cells, strict=True):
		for x, y in cell.vertices:
			dx = x - site.x
			dy = y - site.y
			distance_squared = dx * dx + dy * dy
			maximum_squared_distance = max(maximum_squared_distance, distance_squared)
	radius = math.sqrt(maximum_squared_distance)
	return radius


#============================================
def _boundary_area_ratio(
	partition: colorbynumber.voronoi_geometry.Partition,
	areas: numpy.ndarray,
) -> float | None:
	"""Return boundary-cell median area divided by interior-cell median area."""
	boundary_areas = numpy.array(
		[
			areas[cell.site_identifier]
			for cell in partition.cells
			if cell.boundary_class == "boundary"
		]
	)
	interior_areas = numpy.array(
		[
			areas[cell.site_identifier]
			for cell in partition.cells
			if cell.boundary_class == "interior"
		]
	)
	if boundary_areas.size == 0 or interior_areas.size == 0:
		return None
	ratio = float(numpy.median(boundary_areas) / numpy.median(interior_areas))
	return ratio


#============================================
def _boundary_band_density_ratio(
	partition: colorbynumber.voronoi_geometry.Partition,
) -> float | None:
	"""Compare site density within one nominal spacing of the boundary to the interior."""
	domain = partition.domain
	band_width = domain.nominal_spacing
	interior_width = max(0.0, domain.width - 2.0 * band_width)
	interior_height = max(0.0, domain.height - 2.0 * band_width)
	interior_area = interior_width * interior_height
	band_area = 1.0 - interior_area
	if interior_area == 0.0 or band_area == 0.0:
		return None
	boundary_count = sum(
		1
		for site in partition.sites
		if min(site.x, domain.width - site.x, site.y, domain.height - site.y)
		<= band_width
	)
	interior_count = domain.site_count - boundary_count
	if interior_count == 0:
		return None
	boundary_density = boundary_count / band_area
	interior_density = interior_count / interior_area
	ratio = boundary_density / interior_density
	return ratio


#============================================
def evaluate_partition(
	result: colorbynumber.voronoi_geometry.ConstructionResult,
	generation_seconds: float,
) -> PartitionEvaluation:
	"""Measure deterministic quality and separate single-run timing metadata.

	Args:
		result: Constructed and validated partition with timings.
		generation_seconds: Site-generation wall time.

	Returns:
		Quality metrics and wall-clock metadata without a composite score.
	"""
	quality_measurement_start = time.perf_counter()
	partition = result.partition
	polygons = [shapely.geometry.Polygon(cell.vertices) for cell in partition.cells]
	areas = numpy.array([polygon.area for polygon in polygons])
	nearest_distances = _nearest_neighbor_distances(partition)
	percentile_10, percentile_90 = numpy.percentile(areas, (10.0, 90.0))
	covering_radius = exact_bounded_covering_radius(partition)
	boundary_area_ratio = _boundary_area_ratio(partition, areas)
	boundary_density_ratio = _boundary_band_density_ratio(partition)
	if nearest_distances.size == 0:
		nearest_coefficient = None
		nearest_median = None
		nearest_minimum = None
		nearest_minimum_to_median = None
	else:
		nearest_coefficient = _coefficient_of_variation(nearest_distances)
		nearest_median = float(numpy.median(nearest_distances))
		nearest_minimum = float(numpy.min(nearest_distances))
		nearest_minimum_to_median = nearest_minimum / nearest_median
	quality_metrics: dict[str, float | None] = {
		"area_coefficient_of_variation": _coefficient_of_variation(areas),
		"area_p90_to_p10_ratio": float(percentile_90 / percentile_10),
		"boundary_band_density_ratio": boundary_density_ratio,
		"boundary_to_interior_median_area_ratio": boundary_area_ratio,
		"exact_bounded_covering_radius": covering_radius,
		"nearest_neighbor_coefficient_of_variation": nearest_coefficient,
		"nearest_neighbor_median": nearest_median,
		"nearest_neighbor_minimum": nearest_minimum,
		"nearest_neighbor_minimum_to_median_ratio": nearest_minimum_to_median,
	}
	quality_measurement_seconds = time.perf_counter() - quality_measurement_start
	timing_metadata = {
		"generation_seconds": generation_seconds,
		"site_validation_seconds": result.site_validation_seconds,
		"construction_seconds": result.construction_seconds,
		"partition_validation_seconds": result.partition_validation_seconds,
		"quality_measurement_seconds": quality_measurement_seconds,
	}
	evaluation = PartitionEvaluation(
		quality_metrics=quality_metrics,
		timing_metadata=timing_metadata,
	)
	return evaluation
