# Standard Library
import math
import pathlib

# PIP3 modules
import numpy
import PIL.Image
import pypdf

# local repo modules
import colorbynumber.constants
import colorbynumber.color_matcher
import colorbynumber.image_sampler
import colorbynumber.marker_color
import colorbynumber.palette_loader
import colorbynumber.pdf_writer


def test_assign_marker_colors_uses_perceptual_nearest_color() -> None:
	palette = [
		colorbynumber.marker_color.MarkerColor("120", "Black", (0, 0, 0)),
		colorbynumber.marker_color.MarkerColor("131", "Paper White", (255, 255, 255)),
	]
	rgb_grid = numpy.array([[[8, 8, 8], [248, 248, 248]]], dtype=numpy.uint8)
	indices, errors = colorbynumber.color_matcher.assign_marker_colors(rgb_grid, palette)
	assert indices.tolist() == [[0, 1]]
	assert numpy.all(errors < 3.0)


def test_sample_image_grid_has_required_layout() -> None:
	image = PIL.Image.new("RGB", (86, 60), (20, 40, 60))
	rgb_grid = colorbynumber.image_sampler.sample_image_grid(image, "crop")
	assert rgb_grid.shape == (30, 43, 3)
	assert numpy.all(rgb_grid == (20, 40, 60))


def test_pdf_layout_has_safe_margins_and_square_cells() -> None:
	layout = colorbynumber.pdf_writer.calculate_layout()
	width_per_cell = layout.grid_width / colorbynumber.constants.GRID_COLUMNS
	height_per_cell = layout.grid_height / colorbynumber.constants.GRID_ROWS
	assert layout.margin > 0.6 * colorbynumber.pdf_writer.POINTS_PER_INCH
	assert math.isclose(width_per_cell, height_per_cell)


def test_pdf_writer_makes_one_landscape_letter_page(tmp_path: pathlib.Path) -> None:
	indices = numpy.zeros((30, 43), dtype=numpy.int64)
	palette = [colorbynumber.marker_color.MarkerColor("120", "Black", (14, 14, 14))]
	output_path = tmp_path / "worksheet.pdf"
	colorbynumber.pdf_writer.write_pdf(indices, palette, output_path)
	reader = pypdf.PdfReader(output_path)
	page = reader.pages[0]
	page_size = (float(page.mediabox.width), float(page.mediabox.height))
	assert reader.get_num_pages() == 1
	assert page_size == (792.0, 612.0)


def test_default_palette_preserves_alphanumeric_codes() -> None:
	palette = colorbynumber.palette_loader.load_palette(colorbynumber.constants.DEFAULT_PALETTE)
	blue_grey = next(marker for marker in palette if marker.name == "Blue Grey")
	assert blue_grey.code == "BG7"
