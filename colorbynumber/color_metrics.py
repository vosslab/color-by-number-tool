"""CIE Lab conversion and Delta E 76 measurement."""

# PIP3 modules
import numpy


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
def delta_e_76_distances(
	lab_values: numpy.ndarray,
	palette_lab: numpy.ndarray,
) -> numpy.ndarray:
	"""Measure each Lab value against every palette entry.

	Args:
		lab_values: Lab values with a final three-channel dimension.
		palette_lab: Palette Lab values shaped as colors by three channels.

	Returns:
		Delta E 76 distances with one trailing palette dimension.
	"""
	difference = lab_values[..., numpy.newaxis, :] - palette_lab
	distances = numpy.sqrt(numpy.sum(difference**2, axis=-1))
	return distances


#============================================
def delta_e_76_errors(
	grid_lab: numpy.ndarray,
	palette_lab: numpy.ndarray,
	indices: numpy.ndarray,
) -> numpy.ndarray:
	"""Measure actual Delta E 76 error for selected palette indices.

	Args:
		grid_lab: Source Lab value for every square.
		palette_lab: Palette Lab values.
		indices: Selected palette index for every square.

	Returns:
		Delta E 76 error for every square.
	"""
	selected_lab = palette_lab[indices]
	difference = grid_lab - selected_lab
	errors = numpy.sqrt(numpy.sum(difference**2, axis=-1))
	return errors
