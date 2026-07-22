"""Crisp PNG preview writing."""

# Standard Library
import pathlib

# PIP3 modules
import numpy
import PIL.Image

PREVIEW_CELL_PIXELS = 24


#============================================
def write_preview(rgb_grid: numpy.ndarray, output_path: pathlib.Path) -> None:
	"""Write a nearest-neighbor preview that keeps every square visually crisp.

	Args:
		rgb_grid: RGB value for every square.
		output_path: Destination PNG path.
	"""
	image = PIL.Image.fromarray(rgb_grid.astype(numpy.uint8), mode="RGB")
	rows, columns = rgb_grid.shape[:2]
	preview_size = (
		columns * PREVIEW_CELL_PIXELS,
		rows * PREVIEW_CELL_PIXELS,
	)
	preview = image.resize(preview_size, resample=PIL.Image.Resampling.NEAREST)
	preview.save(output_path)
