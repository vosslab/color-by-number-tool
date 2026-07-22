"""Crisp PNG preview writing."""

# Standard Library
import pathlib

# PIP3 modules
import numpy
import PIL.Image

# local repo modules
import colorbynumber.constants


#============================================
def write_preview(rgb_grid: numpy.ndarray, output_path: pathlib.Path) -> None:
	"""Write a nearest-neighbor preview that keeps every square visually crisp.

	Args:
		rgb_grid: RGB value for every square.
		output_path: Destination PNG path.
	"""
	image = PIL.Image.fromarray(rgb_grid.astype(numpy.uint8), mode="RGB")
	preview_size = (
		colorbynumber.constants.GRID_COLUMNS * colorbynumber.constants.PREVIEW_CELL_PIXELS,
		colorbynumber.constants.GRID_ROWS * colorbynumber.constants.PREVIEW_CELL_PIXELS,
	)
	preview = image.resize(preview_size, resample=PIL.Image.Resampling.NEAREST)
	preview.save(output_path)
