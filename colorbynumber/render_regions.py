"""Output-only same-color polygon merging for printable color-by-number regions."""

# Standard Library
import dataclasses
import math

# PIP3 modules
import numpy
import shapely

# local repo modules
import colorbynumber.voronoi_geometry


#============================================
@dataclasses.dataclass(frozen=True)
class RenderRegion:
	"""One connected printable region with a single palette assignment."""

	palette_index: int
	member_identifiers: tuple[int, ...]
	polygon: shapely.Polygon

	def __post_init__(self) -> None:
		"""Reject malformed intrinsic printable-region values."""
		_validate_region_values(self)


#============================================
def _validate_region_values(region: RenderRegion) -> None:
	"""Validate one region independently of its output palette."""
	if isinstance(region.palette_index, bool) or not isinstance(region.palette_index, int):
		raise ValueError("Region palette index must be a nonnegative integer")
	if region.palette_index < 0:
		raise ValueError("Region palette index must be a nonnegative integer")
	if not isinstance(region.member_identifiers, tuple) or not region.member_identifiers:
		raise ValueError("Region members must be a nonempty tuple")
	if any(
		isinstance(member, bool) or not isinstance(member, int)
		for member in region.member_identifiers
	):
		raise ValueError("Region members must be nonnegative integers")
	if any(member < 0 for member in region.member_identifiers):
		raise ValueError("Region members must be nonnegative integers")
	if len(set(region.member_identifiers)) != len(region.member_identifiers):
		raise ValueError("Region members must not repeat")
	if not isinstance(region.polygon, shapely.Polygon):
		raise ValueError("Region geometry must be a polygon")
	if region.polygon.is_empty or not region.polygon.is_valid:
		raise ValueError("Region geometry must be a nonempty valid polygon")


#============================================
def validate_region_geometries(regions: tuple[RenderRegion, ...]) -> None:
	"""Validate one complete concrete printable-region tuple."""
	if not isinstance(regions, tuple) or not regions:
		raise ValueError("Rendered regions must be a nonempty tuple")
	members: list[int] = []
	for region in regions:
		if not isinstance(region, RenderRegion):
			raise ValueError("Rendered regions must contain RenderRegion values")
		_validate_region_values(region)
		members.extend(region.member_identifiers)
	if len(set(members)) != len(members):
		raise ValueError("Rendered region members must not repeat across regions")


#============================================
def validate_regions(regions: tuple[RenderRegion, ...], palette_size: int) -> None:
	"""Validate printable regions against one output palette."""
	if isinstance(palette_size, bool) or not isinstance(palette_size, int) or palette_size <= 0:
		raise ValueError("Region palette size must be a positive integer")
	validate_region_geometries(regions)
	if any(region.palette_index >= palette_size for region in regions):
		raise ValueError("Region palette index is outside the available palette")


#============================================
def _polygon_parts(geometry: shapely.Geometry) -> list[shapely.Polygon]:
	"""Return nonempty polygon members from a union result in stable geometry order."""
	if isinstance(geometry, shapely.Polygon):
		parts = [geometry]
	elif isinstance(geometry, shapely.MultiPolygon):
		parts = list(geometry.geoms)
	else:
		raise ValueError("Merged regions must be polygonal")
	if not parts or any(part.is_empty or not part.is_valid for part in parts):
		raise ValueError("Merged regions must be nonempty valid polygons")
	return parts


#============================================
def build_regions(
	polygons: list[shapely.Polygon],
	indices: numpy.ndarray,
	merge_regions: bool,
) -> tuple[RenderRegion, ...]:
	"""Merge exact-color polygon coverages into stable connected render regions.

	The caller supplies polygons in authoritative assignment order.  Coverage union
	merges positive-length shared boundaries while point-only contacts remain
	separate polygon members.
	"""
	if indices.ndim != 1 or len(polygons) != indices.size:
		raise ValueError("Regions require one polygon for every one-dimensional assignment")
	if not numpy.issubdtype(indices.dtype, numpy.integer):
		raise ValueError("Regions require integer palette assignments")
	if numpy.any(indices < 0):
		raise ValueError("Regions require nonnegative palette assignments")
	if not polygons or any(not polygon.is_valid or polygon.is_empty for polygon in polygons):
		raise ValueError("Regions require nonempty valid polygon inputs")
	if not merge_regions:
		regions = tuple(
			RenderRegion(int(indices[identifier]), (identifier,), polygon)
			for identifier, polygon in enumerate(polygons)
		)
		validate_region_geometries(regions)
		return regions
	regions: list[RenderRegion] = []
	all_member_identifiers: list[int] = []
	for palette_index in sorted(int(index) for index in numpy.unique(indices)):
		member_ids = tuple(int(identifier) for identifier in numpy.flatnonzero(indices == palette_index))
		member_polygons = [polygons[identifier] for identifier in member_ids]
		union = shapely.union_all(member_polygons)
		if not math.isclose(
			sum(polygon.area for polygon in member_polygons),
			union.area,
			rel_tol=1.0e-10,
			abs_tol=1.0e-12,
		):
			raise ValueError("Merged regions must preserve total assigned area")
		for polygon in _polygon_parts(union):
			members = tuple(
				identifier for identifier in member_ids
				if polygon.covers(polygons[identifier])
			)
			if not members:
				raise ValueError("Merged region lost its assignment members")
			regions.append(RenderRegion(palette_index, members, polygon))
			all_member_identifiers.extend(members)
	if sorted(all_member_identifiers) != list(range(indices.size)):
		raise ValueError("Merged regions must retain every assignment exactly once")
	regions.sort(key=lambda region: region.member_identifiers[0])
	result = tuple(regions)
	validate_region_geometries(result)
	return result


#============================================
def build_square_regions(
	indices: numpy.ndarray,
	merge_regions: bool,
) -> tuple[RenderRegion, ...]:
	"""Build printable regions from row-major square assignments."""
	if indices.ndim != 2 or indices.size == 0:
		raise ValueError("Square regions require a nonempty two-dimensional assignment grid")
	rows, columns = indices.shape
	polygons = [
		shapely.box(column, rows - row - 1, column + 1, rows - row)
		for row in range(rows)
		for column in range(columns)
	]
	return build_regions(polygons, indices.reshape(-1), merge_regions)


#============================================
def build_voronoi_regions(
	partition: colorbynumber.voronoi_geometry.Partition,
	indices: numpy.ndarray,
	merge_regions: bool,
) -> tuple[RenderRegion, ...]:
	"""Build printable regions from authoritative site-ordered Voronoi cells."""
	polygons = [shapely.Polygon(cell.vertices) for cell in partition.cells]
	return build_regions(polygons, indices, merge_regions)
