"""Image loading, orientation, fitting, and fixed-grid sampling."""

# Standard Library
import pathlib

# PIP3 modules
import numpy
import PIL.Image
import PIL.ImageOps

# local repo modules
import colorbynumber.constants


#============================================
def load_rgb_image(image_path: pathlib.Path) -> PIL.Image.Image:
	"""Load an image, apply EXIF orientation, and flatten transparency to white.

	Args:
		image_path: Input image file.

	Returns:
		An RGB Pillow image.

	Raises:
		FileNotFoundError: The input image does not exist.
	"""
	if not image_path.is_file():
		raise FileNotFoundError(f"Input image does not exist: {image_path}")
	with PIL.Image.open(image_path) as loaded_image:
		oriented_image = PIL.ImageOps.exif_transpose(loaded_image)
		if "A" in oriented_image.getbands():
			rgba_image = oriented_image.convert("RGBA")
			background = PIL.Image.new("RGBA", rgba_image.size, (255, 255, 255, 255))
			background.alpha_composite(rgba_image)
			rgb_image = background.convert("RGB")
		else:
			rgb_image = oriented_image.convert("RGB")
	return rgb_image


#============================================
def sample_image_grid(image: PIL.Image.Image, fit_mode: str) -> numpy.ndarray:
	"""Resample an image into exactly one RGB value per output square.

	Args:
		image: Source RGB image.
		fit_mode: Either crop or contain.

	Returns:
		A GRID_ROWS by GRID_COLUMNS RGB array.
	"""
	target_size = (colorbynumber.constants.GRID_COLUMNS, colorbynumber.constants.GRID_ROWS)
	if fit_mode == "crop":
		grid_image = PIL.ImageOps.fit(
			image,
			target_size,
			method=PIL.Image.Resampling.LANCZOS,
			centering=(0.5, 0.5),
		)
	elif fit_mode == "contain":
		grid_image = PIL.ImageOps.pad(
			image,
			target_size,
			method=PIL.Image.Resampling.LANCZOS,
			color=(255, 255, 255),
			centering=(0.5, 0.5),
		)
	else:
		raise ValueError(f"Unsupported fit mode: {fit_mode}")
	rgb_grid = numpy.asarray(grid_image, dtype=numpy.uint8)
	return rgb_grid
