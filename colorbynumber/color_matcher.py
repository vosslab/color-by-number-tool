"""Perceptual marker matching with selective dark-detail preservation."""

# PIP3 modules
import numpy

# local repo modules
import colorbynumber.color_metrics
import colorbynumber.marker_color


DARK_DETAIL_LIGHTNESS_LIMIT = 45.0
DARK_DETAIL_CHROMA_MINIMUM = 5.0
DARK_DETAIL_DIFFERENCE_MINIMUM = 3.0
WARM_TONE_LIGHTNESS_MINIMUM = 45.0
WARM_TONE_LIGHTNESS_MAXIMUM = 92.0
WARM_TONE_CHROMA_MINIMUM = 8.0
WARM_TONE_HUE_MINIMUM = 15.0
WARM_TONE_HUE_MAXIMUM = 80.0
WARM_CHROMA_SCALE = 1.15
NO_ENHANCEMENT = "none"
BALANCED_ENHANCEMENT = "balanced"
STRONG_ENHANCEMENT = "strong"
ENHANCEMENT_SETTINGS = {
	NO_ENHANCEMENT: (None, 1.0),
	BALANCED_ENHANCEMENT: (0.65, WARM_CHROMA_SCALE),
	STRONG_ENHANCEMENT: (0.50, WARM_CHROMA_SCALE),
}


#============================================
def build_dark_detail_mask(grid_lab: numpy.ndarray) -> numpy.ndarray:
	"""Locate dark, chromatic cells whose local source detail needs separation.

	Args:
		grid_lab: Source Lab value for every square.

	Returns:
		A boolean mask selecting locally changing dark-color cells.
	"""
	lightness = grid_lab[:, :, 0]
	chroma = numpy.hypot(grid_lab[:, :, 1], grid_lab[:, :, 2])
	maximum_neighbor_difference = numpy.zeros(lightness.shape, dtype=numpy.float64)
	neighbor_pairs = (
		(grid_lab[1:, :, :], grid_lab[:-1, :, :], (slice(1, None), slice(None))),
		(grid_lab[:-1, :, :], grid_lab[1:, :, :], (slice(None, -1), slice(None))),
		(grid_lab[:, 1:, :], grid_lab[:, :-1, :], (slice(None), slice(1, None))),
		(grid_lab[:, :-1, :], grid_lab[:, 1:, :], (slice(None), slice(None, -1))),
	)
	for current, neighbor, target_slice in neighbor_pairs:
		difference = numpy.sqrt(numpy.sum((current - neighbor) ** 2, axis=-1))
		maximum_neighbor_difference[target_slice] = numpy.maximum(
			maximum_neighbor_difference[target_slice],
			difference,
		)
	mask = (
		(lightness < DARK_DETAIL_LIGHTNESS_LIMIT)
		& (chroma > DARK_DETAIL_CHROMA_MINIMUM)
		& (maximum_neighbor_difference > DARK_DETAIL_DIFFERENCE_MINIMUM)
	)
	return mask


#============================================
def expand_dark_details(
	grid_lab: numpy.ndarray,
	gamma: float,
) -> numpy.ndarray:
	"""Lift shadow separation in dark, chromatic, locally detailed cells.

	Args:
		grid_lab: Source Lab value for every square.
		gamma: Shadow-curve exponent between zero and one.

	Returns:
		A copy of the Lab grid with selected lightness values expanded.

	Raises:
		ValueError: Gamma is not strictly between zero and one.
	"""
	if not 0.0 < gamma < 1.0:
		raise ValueError("Dark-detail gamma must be between zero and one")
	mask = build_dark_detail_mask(grid_lab)
	expanded_lab = grid_lab.copy()
	lightness = expanded_lab[:, :, 0]
	normalized = numpy.clip(
		lightness / DARK_DETAIL_LIGHTNESS_LIMIT,
		0.0,
		1.0,
	)
	expanded_lightness = DARK_DETAIL_LIGHTNESS_LIMIT * normalized**gamma
	expanded_lab[:, :, 0] = numpy.where(mask, expanded_lightness, lightness)
	return expanded_lab


#============================================
def build_warm_tone_mask(grid_lab: numpy.ndarray) -> numpy.ndarray:
	"""Locate moderately bright chromatic colors in the warm hue arc.

	Args:
		grid_lab: Original source Lab value for every square.

	Returns:
		A boolean mask selecting warm midtone and highlight cells.
	"""
	lightness = grid_lab[:, :, 0]
	chroma = numpy.hypot(grid_lab[:, :, 1], grid_lab[:, :, 2])
	hue = numpy.degrees(numpy.arctan2(grid_lab[:, :, 2], grid_lab[:, :, 1])) % 360.0
	mask = (
		(lightness >= WARM_TONE_LIGHTNESS_MINIMUM)
		& (lightness <= WARM_TONE_LIGHTNESS_MAXIMUM)
		& (chroma > WARM_TONE_CHROMA_MINIMUM)
		& (hue >= WARM_TONE_HUE_MINIMUM)
		& (hue <= WARM_TONE_HUE_MAXIMUM)
	)
	return mask


#============================================
def expand_warm_chroma(
	matching_lab: numpy.ndarray,
	source_lab: numpy.ndarray,
	scale: float,
) -> numpy.ndarray:
	"""Increase chroma in source-selected warm midtones and highlights.

	Args:
		matching_lab: Lab values already prepared for palette matching.
		source_lab: Original Lab values used to select warm cells.
		scale: Positive multiplier for the a and b channels.

	Returns:
		A copy of the matching grid with selected chroma expanded.

	Raises:
		ValueError: Scale is not positive.
	"""
	if scale <= 0.0:
		raise ValueError("Warm-chroma scale must be greater than zero")
	mask = build_warm_tone_mask(source_lab)
	expanded_lab = matching_lab.copy()
	for channel in (1, 2):
		scaled_channel = numpy.clip(
			expanded_lab[:, :, channel] * scale,
			-128.0,
			127.0,
		)
		expanded_lab[:, :, channel] = numpy.where(
			mask,
			scaled_channel,
			expanded_lab[:, :, channel],
		)
	return expanded_lab


#============================================
def assign_marker_colors(
	rgb_grid: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
	enhancement: str = STRONG_ENHANCEMENT,
) -> tuple[numpy.ndarray, numpy.ndarray]:
	"""Assign one nearest marker to every square.

	Args:
		rgb_grid: Source RGB value for every square.
		palette: Available marker colors.
		enhancement: None, balanced, or strong tested color enhancement.

	Returns:
		The palette index and original-source Delta E 76 error for every square.

	Raises:
		ValueError: The enhancement preset is unsupported.
	"""
	if enhancement not in ENHANCEMENT_SETTINGS:
		raise ValueError(f"Unsupported color enhancement: {enhancement}")
	palette_rgb = numpy.array([marker.rgb for marker in palette], dtype=numpy.uint8)
	source_lab = colorbynumber.color_metrics.rgb_to_lab(rgb_grid)
	palette_lab = colorbynumber.color_metrics.rgb_to_lab(palette_rgb)
	shadow_gamma, warm_chroma_scale = ENHANCEMENT_SETTINGS[enhancement]
	matching_lab = source_lab
	if shadow_gamma is not None:
		matching_lab = expand_dark_details(source_lab, shadow_gamma)
	matching_lab = expand_warm_chroma(
		matching_lab,
		source_lab,
		warm_chroma_scale,
	)
	distances = colorbynumber.color_metrics.delta_e_76_distances(
		matching_lab,
		palette_lab,
	)
	indices = numpy.argmin(distances, axis=-1)
	errors = colorbynumber.color_metrics.delta_e_76_errors(
		source_lab,
		palette_lab,
		indices,
	)
	return indices, errors


#============================================
def palette_grid_rgb(
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
) -> numpy.ndarray:
	"""Build an RGB grid from palette indices.

	Args:
		indices: Palette index for each square.
		palette: Available marker colors.

	Returns:
		An RGB array containing the selected marker colors.
	"""
	palette_rgb = numpy.array([marker.rgb for marker in palette], dtype=numpy.uint8)
	rgb_grid = palette_rgb[indices]
	return rgb_grid
