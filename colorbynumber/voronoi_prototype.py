"""Prototype-only Voronoi image sampling and comparison data flow."""

# Standard Library
import math
import dataclasses

# PIP3 modules
import numpy
import shapely
import PIL.Image
import PIL.ImageOps

# local repo modules
import colorbynumber.color_matcher
import colorbynumber.color_metrics
import colorbynumber.image_sampler
import colorbynumber.marker_color
import colorbynumber.voronoi_geometry


HARD_CORE_DISTANCE_RATIO = 0.70
HARD_CORE_ATTEMPT_MULTIPLIER = 100
LLOYD_ALPHA = 0.50
LLOYD_STEP_COUNT = 2
DEFAULT_RASTER_SCALE = 8


#============================================
@dataclasses.dataclass(frozen=True)
class PolygonRasterSample:
	"""Area samples and deterministic raster ownership in site order."""

	fitted_rgb: numpy.ndarray
	ownership: numpy.ndarray
	polygon_rgb: numpy.ndarray
	pixel_counts: numpy.ndarray
	polygon_fallback_identifiers: tuple[int, ...]
	seam_fallback_pixel_count: int


#============================================
@dataclasses.dataclass(frozen=True)
class SquareControl:
	"""Unchanged square-pipeline assignments expanded onto the comparison raster."""

	indices: numpy.ndarray
	reconstruction_rgb: numpy.ndarray


#============================================
def build_selected_partition(
	columns: int,
	rows: int,
	seed: int,
) -> colorbynumber.voronoi_geometry.Partition:
	"""Build the selected hard-core plus two-step Lloyd prototype partition.

	Args:
		columns: Resolved domain columns.
		rows: Resolved domain rows.
		seed: Internal deterministic replay seed.

	Returns:
		A validated bounded partition in stable site order.
	"""
	domain = colorbynumber.voronoi_geometry.create_domain(columns, rows)
	attempt_budget = HARD_CORE_ATTEMPT_MULTIPLIER * domain.site_count
	sites = colorbynumber.voronoi_geometry.generate_hard_core_sites(
		domain,
		seed,
		HARD_CORE_DISTANCE_RATIO,
		attempt_budget,
	)
	for _step in range(LLOYD_STEP_COUNT):
		sites = colorbynumber.voronoi_geometry.relax_bounded_lloyd_once(
			domain,
			sites,
			LLOYD_ALPHA,
		)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	return result.partition


#============================================
def fit_source_raster(
	image: PIL.Image.Image,
	fit_mode: str,
	columns: int,
	rows: int,
	raster_scale: int = DEFAULT_RASTER_SCALE,
) -> PIL.Image.Image:
	"""Fit a source to a higher-resolution polygon sampling raster.

	The crop, contain, centering, white-border, and Lanczos policies match the
	production square sampler. The target retains ``raster_scale`` pixel centers
	per nominal square-grid axis, rather than becoming a square-cell array.

	Args:
		image: EXIF-corrected RGB source image.
		fit_mode: Crop or contain.
		columns: Resolved count/aspect columns.
		rows: Resolved count/aspect rows.
		raster_scale: Raster pixels per nominal grid axis.

	Returns:
		The fitted RGB comparison raster.

	Raises:
		ValueError: Dimensions, scale, or fit mode are invalid.
	"""
	if isinstance(columns, bool) or isinstance(rows, bool):
		raise ValueError("Raster dimensions must be positive integers")
	if not isinstance(columns, int) or not isinstance(rows, int):
		raise ValueError("Raster dimensions must be positive integers")
	if columns <= 0 or rows <= 0:
		raise ValueError("Raster dimensions must be greater than zero")
	if isinstance(raster_scale, bool) or not isinstance(raster_scale, int):
		raise ValueError("Raster scale must be a positive integer")
	if raster_scale <= 0:
		raise ValueError("Raster scale must be a positive integer")
	target_size = (columns * raster_scale, rows * raster_scale)
	if fit_mode == "crop":
		fitted = PIL.ImageOps.fit(
			image,
			target_size,
			method=PIL.Image.Resampling.LANCZOS,
			centering=(0.5, 0.5),
		)
	elif fit_mode == "contain":
		fitted = PIL.ImageOps.pad(
			image,
			target_size,
			method=PIL.Image.Resampling.LANCZOS,
			color=(255, 255, 255),
			centering=(0.5, 0.5),
		)
	else:
		raise ValueError(f"Unsupported fit mode: {fit_mode}")
	rgb_image = fitted.convert("RGB")
	return rgb_image


#============================================
def _pixel_center_coordinates(
	domain: colorbynumber.voronoi_geometry.Domain,
	width: int,
	height: int,
) -> tuple[numpy.ndarray, numpy.ndarray]:
	"""Return domain coordinates for raster pixel centers."""
	x_step = domain.width / width
	y_step = domain.height / height
	x_coordinates = (numpy.arange(width, dtype=numpy.float64) + 0.5) * x_step
	y_coordinates = domain.height - (
		(numpy.arange(height, dtype=numpy.float64) + 0.5) * y_step
	)
	return x_coordinates, y_coordinates


#============================================
def _assign_seam_fallbacks(
	partition: colorbynumber.voronoi_geometry.Partition,
	ownership: numpy.ndarray,
	x_coordinates: numpy.ndarray,
	y_coordinates: numpy.ndarray,
) -> int:
	"""Assign any numerical seam pixels by the documented nearest-site tie rule."""
	missing_rows, missing_columns = numpy.nonzero(ownership < 0)
	for row, column in zip(missing_rows, missing_columns, strict=True):
		identifier = colorbynumber.voronoi_geometry.nearest_site_identifier(
			partition.sites,
			float(x_coordinates[column]),
			float(y_coordinates[row]),
			partition.domain.coordinate_tolerance,
		)
		ownership[row, column] = identifier
	missing_count = int(missing_rows.size)
	return missing_count


#============================================
def rasterize_partition_ownership(
	partition: colorbynumber.voronoi_geometry.Partition,
	width: int,
	height: int,
) -> tuple[numpy.ndarray, int]:
	"""Assign every raster pixel center to one ordered clipped polygon.

	Cells are traversed in site order. Inclusive polygon coverage claims only an
	unclaimed center, so an exact shared-edge center belongs to the lower site
	identifier. Any center left by a numerical seam uses the geometry module's
	nearest-site rule with the same identifier tie break.

	Args:
		partition: Validated stable ordered sites and cells.
		width: Raster width in pixels.
		height: Raster height in pixels.

	Returns:
		The site-identifier ownership raster and seam fallback count.

	Raises:
		ValueError: Raster dimensions are invalid.
	"""
	if isinstance(width, (bool, numpy.bool_)) or isinstance(height, (bool, numpy.bool_)):
		raise ValueError("Ownership raster dimensions must be positive integers")
	if not isinstance(width, (int, numpy.integer)) or not isinstance(height, (int, numpy.integer)):
		raise ValueError("Ownership raster dimensions must be positive integers")
	if width <= 0 or height <= 0:
		raise ValueError("Ownership raster dimensions must be greater than zero")
	x_coordinates, y_coordinates = _pixel_center_coordinates(
		partition.domain,
		width,
		height,
	)
	ownership = numpy.full((height, width), -1, dtype=numpy.int32)
	tolerance = partition.domain.coordinate_tolerance
	for cell in partition.cells:
		polygon = shapely.Polygon(cell.vertices)
		minimum_x, minimum_y, maximum_x, maximum_y = polygon.bounds
		column_indices = numpy.flatnonzero(
			(x_coordinates >= minimum_x - tolerance)
			& (x_coordinates <= maximum_x + tolerance)
		)
		row_indices = numpy.flatnonzero(
			(y_coordinates >= minimum_y - tolerance)
			& (y_coordinates <= maximum_y + tolerance)
		)
		if column_indices.size == 0 or row_indices.size == 0:
			continue
		x_values, y_values = numpy.meshgrid(
			x_coordinates[column_indices],
			y_coordinates[row_indices],
		)
		covered = shapely.intersects_xy(polygon, x_values, y_values)
		current = ownership[numpy.ix_(row_indices, column_indices)]
		claim = covered & (current < 0)
		current[claim] = cell.site_identifier
		ownership[numpy.ix_(row_indices, column_indices)] = current
	seam_fallback_count = _assign_seam_fallbacks(
		partition,
		ownership,
		x_coordinates,
		y_coordinates,
	)
	return ownership, seam_fallback_count


#============================================
def _fallback_pixel_rgb(
	partition: colorbynumber.voronoi_geometry.Partition,
	site: colorbynumber.voronoi_geometry.Site,
	rgb: numpy.ndarray,
) -> numpy.ndarray:
	"""Return the fitted-raster pixel whose center is nearest one site."""
	height, width = rgb.shape[:2]
	column_value = site.x * width / partition.domain.width - 0.5
	row_value = (partition.domain.height - site.y) * height / partition.domain.height - 0.5
	column = math.floor(column_value + 0.5)
	row = math.floor(row_value + 0.5)
	column = min(max(column, 0), width - 1)
	row = min(max(row, 0), height - 1)
	color = rgb[row, column].astype(numpy.float64)
	return color


#============================================
def sample_partition_rgb(
	partition: colorbynumber.voronoi_geometry.Partition,
	fitted_image: PIL.Image.Image,
) -> PolygonRasterSample:
	"""Average all owned source pixel centers for each clipped polygon.

	Every fitted-raster pixel center has equal weight. A polygon with no covered
	pixel center samples the fitted pixel center nearest its owned site; fallback
	identifiers are retained for diagnostics.

	Args:
		partition: Validated partition in stable site order.
		fitted_image: Fitted RGB source raster.

	Returns:
		Ordered polygon RGB values and complete raster ownership evidence.
	"""
	rgb = numpy.asarray(fitted_image.convert("RGB"), dtype=numpy.uint8)
	height, width = rgb.shape[:2]
	ownership, seam_fallback_count = rasterize_partition_ownership(
		partition,
		width,
		height,
	)
	flat_ownership = ownership.reshape(-1)
	flat_rgb = rgb.reshape(-1, 3).astype(numpy.float64)
	pixel_counts = numpy.bincount(
		flat_ownership,
		minlength=partition.domain.site_count,
	).astype(numpy.int64)
	channel_sums = numpy.zeros((partition.domain.site_count, 3), dtype=numpy.float64)
	for channel in range(3):
		channel_sums[:, channel] = numpy.bincount(
			flat_ownership,
			weights=flat_rgb[:, channel],
			minlength=partition.domain.site_count,
		)
	polygon_rgb = numpy.zeros((partition.domain.site_count, 3), dtype=numpy.float64)
	covered = pixel_counts > 0
	polygon_rgb[covered] = channel_sums[covered] / pixel_counts[covered, numpy.newaxis]
	fallback_identifiers: list[int] = []
	for site in partition.sites:
		if pixel_counts[site.identifier] != 0:
			continue
		polygon_rgb[site.identifier] = _fallback_pixel_rgb(partition, site, rgb)
		fallback_identifiers.append(site.identifier)
	sample = PolygonRasterSample(
		fitted_rgb=rgb,
		ownership=ownership,
		polygon_rgb=polygon_rgb,
		pixel_counts=pixel_counts,
		polygon_fallback_identifiers=tuple(fallback_identifiers),
		seam_fallback_pixel_count=seam_fallback_count,
	)
	return sample


#============================================
def polygon_adjacency(
	partition: colorbynumber.voronoi_geometry.Partition,
) -> tuple[tuple[int, ...], ...]:
	"""Return deterministic shared-edge neighbors in stable site order.

	Point-only corner contact is excluded. The coordinate tolerance is used as a
	minimum shared-boundary length, matching the existing normalized geometry
	contract without adding a second epsilon.
	"""
	polygons = numpy.asarray(
		[shapely.Polygon(cell.vertices) for cell in partition.cells],
		dtype=object,
	)
	query_pairs = shapely.STRtree(polygons).query(polygons, predicate="touches")
	neighbor_sets = [set() for _cell in partition.cells]
	for first, second in zip(query_pairs[0], query_pairs[1], strict=True):
		first_identifier = int(first)
		second_identifier = int(second)
		if first_identifier >= second_identifier:
			continue
		shared = polygons[first_identifier].boundary.intersection(
			polygons[second_identifier].boundary
		)
		if shared.length <= partition.domain.coordinate_tolerance:
			continue
		neighbor_sets[first_identifier].add(second_identifier)
		neighbor_sets[second_identifier].add(first_identifier)
	adjacency = tuple(tuple(sorted(neighbors)) for neighbors in neighbor_sets)
	return adjacency


#============================================
def _polygon_dark_detail_mask(
	source_lab: numpy.ndarray,
	adjacency: tuple[tuple[int, ...], ...],
) -> numpy.ndarray:
	"""Apply square strong thresholds to shared-edge polygon neighborhoods."""
	lightness = source_lab[:, 0]
	chroma = numpy.hypot(source_lab[:, 1], source_lab[:, 2])
	maximum_neighbor_difference = numpy.zeros(lightness.shape, dtype=numpy.float64)
	for identifier, neighbors in enumerate(adjacency):
		if not neighbors:
			continue
		neighbor_lab = source_lab[numpy.asarray(neighbors, dtype=numpy.int64)]
		difference = neighbor_lab - source_lab[identifier]
		distances = numpy.sqrt(numpy.sum(difference**2, axis=-1))
		maximum_neighbor_difference[identifier] = numpy.max(distances)
	mask = (
		(lightness < colorbynumber.color_matcher.DARK_DETAIL_LIGHTNESS_LIMIT)
		& (chroma > colorbynumber.color_matcher.DARK_DETAIL_CHROMA_MINIMUM)
		& (
			maximum_neighbor_difference
			> colorbynumber.color_matcher.DARK_DETAIL_DIFFERENCE_MINIMUM
		)
	)
	return mask


#============================================
def _enhance_polygon_lab(
	partition: colorbynumber.voronoi_geometry.Partition,
	source_lab: numpy.ndarray,
	enhancement: str,
) -> numpy.ndarray:
	"""Apply square preset transforms with shared-edge polygon adjacency."""
	if enhancement not in colorbynumber.color_matcher.ENHANCEMENT_SETTINGS:
		raise ValueError(f"Unsupported color enhancement: {enhancement}")
	shadow_gamma, warm_chroma_scale = colorbynumber.color_matcher.ENHANCEMENT_SETTINGS[
		enhancement
	]
	matching_lab = source_lab.copy()
	if shadow_gamma is not None:
		adjacency = polygon_adjacency(partition)
		mask = _polygon_dark_detail_mask(source_lab, adjacency)
		lightness = source_lab[:, 0]
		normalized = numpy.clip(
			lightness / colorbynumber.color_matcher.DARK_DETAIL_LIGHTNESS_LIMIT,
			0.0,
			1.0,
		)
		expanded = (
			colorbynumber.color_matcher.DARK_DETAIL_LIGHTNESS_LIMIT
			* normalized**shadow_gamma
		)
		matching_lab[:, 0] = numpy.where(mask, expanded, lightness)
	lightness = source_lab[:, 0]
	chroma = numpy.hypot(source_lab[:, 1], source_lab[:, 2])
	hue = numpy.degrees(numpy.arctan2(source_lab[:, 2], source_lab[:, 1])) % 360.0
	warm_mask = (
		(lightness >= colorbynumber.color_matcher.WARM_TONE_LIGHTNESS_MINIMUM)
		& (lightness <= colorbynumber.color_matcher.WARM_TONE_LIGHTNESS_MAXIMUM)
		& (chroma > colorbynumber.color_matcher.WARM_TONE_CHROMA_MINIMUM)
		& (hue >= colorbynumber.color_matcher.WARM_TONE_HUE_MINIMUM)
		& (hue <= colorbynumber.color_matcher.WARM_TONE_HUE_MAXIMUM)
	)
	for channel in (1, 2):
		scaled_channel = numpy.clip(
			matching_lab[:, channel] * warm_chroma_scale,
			-128.0,
			127.0,
		)
		matching_lab[:, channel] = numpy.where(
			warm_mask,
			scaled_channel,
			matching_lab[:, channel],
		)
	return matching_lab


#============================================
def assign_polygon_palette(
	partition: colorbynumber.voronoi_geometry.Partition,
	polygon_rgb: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
	enhancement: str = colorbynumber.color_matcher.STRONG_ENHANCEMENT,
) -> tuple[numpy.ndarray, numpy.ndarray]:
	"""Match polygon samples with square-equivalent enhancement thresholds.

	Args:
		partition: Ordered polygons used for shared-edge dark-detail adjacency.
		polygon_rgb: Ordered RGB samples shaped as polygons by three channels.
		palette: Ordered marker colors.
		enhancement: None, balanced, or strong preset.

	Returns:
		One-dimensional palette indices and Delta E 76 errors.

	Raises:
		ValueError: Polygon samples do not have vector RGB shape.
	"""
	if polygon_rgb.ndim != 2 or polygon_rgb.shape[1] != 3:
		raise ValueError("Polygon RGB samples must have shape (polygon_count, 3)")
	if polygon_rgb.shape[0] != partition.domain.site_count:
		raise ValueError("Polygon RGB samples must follow stable site order")
	palette_rgb = numpy.array([marker.rgb for marker in palette], dtype=numpy.uint8)
	source_lab = colorbynumber.color_metrics.rgb_to_lab(polygon_rgb)
	palette_lab = colorbynumber.color_metrics.rgb_to_lab(palette_rgb)
	matching_lab = _enhance_polygon_lab(partition, source_lab, enhancement)
	distances = colorbynumber.color_metrics.delta_e_76_distances(matching_lab, palette_lab)
	indices = numpy.argmin(distances, axis=-1)
	errors = colorbynumber.color_metrics.delta_e_76_errors(
		source_lab,
		palette_lab,
		indices,
	)
	return indices, errors


#============================================
def palette_rgb_values(
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
) -> numpy.ndarray:
	"""Return ordered RGB values for one-dimensional palette assignments."""
	if indices.ndim != 1:
		raise ValueError("Polygon palette indices must be one-dimensional")
	if indices.size == 0:
		raise ValueError("Polygon palette indices must not be empty")
	if not numpy.issubdtype(indices.dtype, numpy.integer):
		raise ValueError("Polygon palette indices must be integers")
	if numpy.any(indices < 0) or numpy.any(indices >= len(palette)):
		raise ValueError("Polygon palette indices must identify available colors")
	palette_rgb = numpy.array([marker.rgb for marker in palette], dtype=numpy.uint8)
	selected_rgb = palette_rgb[indices]
	return selected_rgb


#============================================
def reconstruct_polygon_raster(
	ownership: numpy.ndarray,
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
) -> numpy.ndarray:
	"""Expand ordered polygon assignments onto their owned comparison pixels."""
	selected_rgb = palette_rgb_values(indices, palette)
	if ownership.ndim != 2 or ownership.size == 0:
		raise ValueError("Polygon ownership must be a nonempty two-dimensional raster")
	if numpy.any(ownership < 0) or numpy.any(ownership >= selected_rgb.shape[0]):
		raise ValueError("Polygon ownership must contain valid site identifiers")
	reconstruction = selected_rgb[ownership]
	return reconstruction


#============================================
def build_square_control(
	image: PIL.Image.Image,
	fit_mode: str,
	columns: int,
	rows: int,
	raster_scale: int,
	palette: list[colorbynumber.marker_color.MarkerColor],
	enhancement: str = colorbynumber.color_matcher.STRONG_ENHANCEMENT,
) -> SquareControl:
	"""Run the unchanged square sampler and matcher as a comparison control."""
	if isinstance(raster_scale, bool) or not isinstance(raster_scale, int):
		raise ValueError("Raster scale must be a positive integer")
	if raster_scale <= 0:
		raise ValueError("Raster scale must be a positive integer")
	source_grid = colorbynumber.image_sampler.sample_image_grid(
		image,
		fit_mode,
		columns,
		rows,
	)
	indices, _errors = colorbynumber.color_matcher.assign_marker_colors(
		source_grid,
		palette,
		enhancement,
	)
	marker_grid = colorbynumber.color_matcher.palette_grid_rgb(indices, palette)
	reconstruction = numpy.repeat(marker_grid, raster_scale, axis=0)
	reconstruction = numpy.repeat(reconstruction, raster_scale, axis=1)
	control = SquareControl(indices=indices, reconstruction_rgb=reconstruction)
	return control


#============================================
def pixel_weighted_reconstruction_error(
	source_rgb: numpy.ndarray,
	reconstruction_rgb: numpy.ndarray,
) -> tuple[float, float]:
	"""Return mean and maximum Delta E 76 over equal-weight raster centers."""
	if source_rgb.ndim != 3 or reconstruction_rgb.ndim != 3:
		raise ValueError("Source and reconstruction RGB rasters must have the same shape")
	if source_rgb.shape != reconstruction_rgb.shape or source_rgb.shape[2] != 3:
		raise ValueError("Source and reconstruction RGB rasters must have the same shape")
	if source_rgb.size == 0:
		raise ValueError("Reconstruction error rasters must not be empty")
	source_lab = colorbynumber.color_metrics.rgb_to_lab(source_rgb)
	reconstruction_lab = colorbynumber.color_metrics.rgb_to_lab(reconstruction_rgb)
	difference = source_lab - reconstruction_lab
	errors = numpy.sqrt(numpy.sum(difference**2, axis=-1))
	mean_error = float(numpy.mean(errors))
	maximum_error = float(numpy.max(errors))
	return mean_error, maximum_error
