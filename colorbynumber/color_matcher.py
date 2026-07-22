"""Perceptual marker-color matching in CIE L*a*b* space."""

# PIP3 modules
import numpy

# local repo modules
import colorbynumber.marker_color


#============================================
def rgb_to_lab(rgb: numpy.ndarray) -> numpy.ndarray:
	"""Convert sRGB values to CIE L*a*b* using the D65 white point.

	Args:
		rgb: Array whose final dimension contains red, green, and blue.

	Returns:
		An array of the same shape containing CIE L*a*b* values.
	"""
	srgb = rgb.astype(numpy.float64) / 255.0
	linear = numpy.where(
		srgb <= 0.04045,
		srgb / 12.92,
		((srgb + 0.055) / 1.055) ** 2.4,
	)
	matrix = numpy.array([
		[0.4124564, 0.3575761, 0.1804375],
		[0.2126729, 0.7151522, 0.0721750],
		[0.0193339, 0.1191920, 0.9503041],
	])
	xyz = linear @ matrix.T
	xyz = xyz / numpy.array([0.95047, 1.0, 1.08883])
	delta = 6.0 / 29.0
	transformed = numpy.where(
		xyz > delta**3,
		numpy.cbrt(xyz),
		xyz / (3.0 * delta**2) + 4.0 / 29.0,
	)
	l_channel = 116.0 * transformed[..., 1] - 16.0
	a_channel = 500.0 * (transformed[..., 0] - transformed[..., 1])
	b_channel = 200.0 * (transformed[..., 1] - transformed[..., 2])
	lab = numpy.stack((l_channel, a_channel, b_channel), axis=-1)
	return lab


#============================================
def assign_marker_colors(
	rgb_grid: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
) -> tuple[numpy.ndarray, numpy.ndarray]:
	"""Assign the perceptually nearest marker to every grid square.

	Args:
		rgb_grid: Source RGB value for every square.
		palette: Available marker colors.

	Returns:
		The palette index and Delta E 76 error for every square.
	"""
	palette_rgb = numpy.array([marker.rgb for marker in palette], dtype=numpy.uint8)
	grid_lab = rgb_to_lab(rgb_grid)
	palette_lab = rgb_to_lab(palette_rgb)
	difference = (
		grid_lab[:, :, numpy.newaxis, :]
		- palette_lab[numpy.newaxis, numpy.newaxis, :, :]
	)
	distances = numpy.sqrt(numpy.sum(difference**2, axis=-1))
	indices = numpy.argmin(distances, axis=-1)
	errors = numpy.take_along_axis(distances, indices[:, :, numpy.newaxis], axis=-1)
	errors = errors[:, :, 0]
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
