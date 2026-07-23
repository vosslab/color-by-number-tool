# Standard Library
import csv
import math
import pathlib

# PIP3 modules
import numpy
import PIL.Image
import pypdf
import pytest
import reportlab.pdfbase.pdfmetrics

# local repo modules
import colorbynumber.constants
import colorbynumber.color_matcher
import colorbynumber.csv_writer
import colorbynumber.grid_only_pdf_writer
import colorbynumber.image_sampler
import colorbynumber.label_placement
import colorbynumber.marker_color
import colorbynumber.orientation
import colorbynumber.palette_loader
import colorbynumber.pdf_writer
import colorbynumber.render_regions
import colorbynumber.repo_paths
import colorbynumber.summary_writer


def test_assign_marker_colors_uses_perceptual_nearest_color() -> None:
	palette = [
		colorbynumber.marker_color.MarkerColor("120", "Black", (0, 0, 0)),
		colorbynumber.marker_color.MarkerColor("131", "Paper White", (255, 255, 255)),
	]
	rgb_grid = numpy.array([[[8, 8, 8], [248, 248, 248]]], dtype=numpy.uint8)
	indices, errors = colorbynumber.color_matcher.assign_marker_colors(rgb_grid, palette)
	assert indices.tolist() == [[0, 1]]
	assert numpy.all(errors < 3.0)


def test_shadow_detail_reduces_black_assignments_in_dark_brown_texture() -> None:
	palette = [
		colorbynumber.marker_color.MarkerColor("120", "Black", (14, 14, 14)),
		colorbynumber.marker_color.MarkerColor("98", "Brown", (123, 101, 103)),
	]
	rgb_grid = numpy.empty((10, 10, 3), dtype=numpy.uint8)
	for row in range(10):
		for column in range(10):
			value = 50 + (row + column) % 3 * 8
			rgb_grid[row, column] = (value, value - 25, value - 35)
	plain_indices, plain_errors = colorbynumber.color_matcher.assign_marker_colors(
		rgb_grid, palette, colorbynumber.color_matcher.NO_ENHANCEMENT,
	)
	detail_indices, detail_errors = colorbynumber.color_matcher.assign_marker_colors(
		rgb_grid, palette, colorbynumber.color_matcher.STRONG_ENHANCEMENT,
	)
	plain_black = int(numpy.sum(plain_indices == 0))
	detail_black = int(numpy.sum(detail_indices == 0))
	assert detail_black < plain_black
	assert plain_errors.shape == detail_errors.shape == (10, 10)


def test_detail_mask_excludes_flat_chromatic_regions() -> None:
	flat_lab = numpy.full((4, 4, 3), (30.0, 12.0, 8.0), dtype=numpy.float64)
	mask = colorbynumber.color_matcher.build_dark_detail_mask(flat_lab)
	assert not numpy.any(mask)


def test_dark_detail_expansion_lifts_only_selected_shadows() -> None:
	grid_lab = numpy.array([
		[[20.0, 12.0, 8.0], [35.0, 12.0, 8.0]],
		[[20.0, 12.0, 8.0], [35.0, 12.0, 8.0]],
	])
	expanded = colorbynumber.color_matcher.expand_dark_details(grid_lab, 0.6)
	assert numpy.all(expanded[:, 0, 0] > grid_lab[:, 0, 0])
	assert numpy.all(expanded[:, 1, 0] > grid_lab[:, 1, 0])
	assert numpy.array_equal(expanded[:, :, 1:], grid_lab[:, :, 1:])


def test_warm_chroma_expansion_excludes_dark_and_cool_colors() -> None:
	source_lab = numpy.array([[
		[60.0, 20.0, 20.0],
		[30.0, 20.0, 20.0],
		[60.0, -20.0, -20.0],
	]])
	expanded = colorbynumber.color_matcher.expand_warm_chroma(
		source_lab,
		source_lab,
		1.15,
	)
	assert numpy.all(numpy.abs(expanded[0, 0, 1:]) > numpy.abs(source_lab[0, 0, 1:]))
	assert numpy.array_equal(expanded[0, 1:], source_lab[0, 1:])


def test_sample_image_grid_has_required_layout() -> None:
	image = PIL.Image.new("RGB", (86, 60), (20, 40, 60))
	rgb_grid = colorbynumber.image_sampler.sample_image_grid(image, "crop", 17, 11)
	assert rgb_grid.shape == (11, 17, 3)
	assert numpy.all(rgb_grid == (20, 40, 60))


def test_grid_size_parser_accepts_columns_by_rows() -> None:
	grid_size = colorbynumber.orientation.parse_grid_size("86x60")
	assert grid_size == (86, 60)


def test_grid_dimensions_rotate_for_portrait() -> None:
	landscape = colorbynumber.orientation.grid_dimensions("landscape", (86, 60))
	portrait = colorbynumber.orientation.grid_dimensions("portrait", (86, 60))
	assert landscape == (86, 60)
	assert portrait == (60, 86)


@pytest.mark.parametrize("value", ("86", "0x60", "60x86"))
def test_grid_size_parser_rejects_invalid_layouts(value: str) -> None:
	with pytest.raises(ValueError):
		colorbynumber.orientation.parse_grid_size(value)


def test_auto_orientation_tracks_source_aspect_ratio() -> None:
	auto = colorbynumber.constants.AUTO_ORIENTATION
	portrait = colorbynumber.orientation.resolve_page_orientation(100, 200, auto)
	landscape = colorbynumber.orientation.resolve_page_orientation(200, 100, auto)
	square = colorbynumber.orientation.resolve_page_orientation(100, 100, auto)
	assert portrait == colorbynumber.constants.PORTRAIT_ORIENTATION
	assert landscape == colorbynumber.constants.LANDSCAPE_ORIENTATION
	assert square == colorbynumber.constants.LANDSCAPE_ORIENTATION


def test_orientation_flags_override_source_aspect_ratio() -> None:
	portrait = colorbynumber.constants.PORTRAIT_ORIENTATION
	landscape = colorbynumber.constants.LANDSCAPE_ORIENTATION
	forced_portrait = colorbynumber.orientation.resolve_page_orientation(200, 100, portrait)
	forced_landscape = colorbynumber.orientation.resolve_page_orientation(100, 200, landscape)
	assert forced_portrait == portrait
	assert forced_landscape == landscape


@pytest.mark.parametrize(
	("page_orientation", "columns", "rows"),
	(("landscape", 86, 60), ("portrait", 60, 86)),
)
def test_pdf_layout_has_safe_margins_and_square_cells(
	page_orientation: str,
	columns: int,
	rows: int,
) -> None:
	layout = colorbynumber.pdf_writer.calculate_layout(page_orientation, columns, rows)
	width_per_cell = layout.grid_width / columns
	height_per_cell = layout.grid_height / rows
	assert layout.margin > 0.6 * colorbynumber.pdf_writer.POINTS_PER_INCH
	assert math.isclose(width_per_cell, height_per_cell)


def test_code_font_size_fits_longest_palette_code() -> None:
	layout = colorbynumber.pdf_writer.calculate_layout("landscape", 86, 60)
	palette = [
		colorbynumber.marker_color.MarkerColor("LONG-CODE", "Example", (0, 0, 0)),
	]
	font_size = colorbynumber.pdf_writer.calculate_code_font_size(layout, palette)
	code_width = reportlab.pdfbase.pdfmetrics.stringWidth(
		palette[0].code,
		colorbynumber.pdf_writer.CODE_FONT_NAME,
		font_size,
	)
	maximum_width = layout.cell_size * colorbynumber.pdf_writer.CODE_WIDTH_FRACTION
	assert code_width <= maximum_width


@pytest.mark.parametrize(
	("page_orientation", "columns", "rows"),
	(("landscape", 86, 60), ("portrait", 60, 86)),
)
def test_grid_only_layout_maximizes_grid_inside_margins(
	page_orientation: str,
	columns: int,
	rows: int,
) -> None:
	layout = colorbynumber.grid_only_pdf_writer.calculate_layout(
		page_orientation,
		columns,
		rows,
	)
	margins = (
		layout.grid_x,
		layout.page_width - layout.grid_x - layout.grid_width,
		layout.grid_y,
		layout.page_height - layout.grid_y - layout.grid_height,
	)
	minimum_margin = colorbynumber.grid_only_pdf_writer.GRID_ONLY_MARGIN
	assert math.isclose(min(margins), minimum_margin)
	assert math.isclose(margins[0], margins[1]) and math.isclose(margins[2], margins[3])


def test_grid_only_writer_makes_blank_and_numbered_pages(tmp_path: pathlib.Path) -> None:
	indices = numpy.zeros((2, 3), dtype=numpy.int64)
	palette = [colorbynumber.marker_color.MarkerColor("120", "Black", (14, 14, 14))]
	output_path = tmp_path / "artwork.pdf"
	colorbynumber.grid_only_pdf_writer.write_pdf(
		palette,
		"landscape",
		3,
		2,
		output_path,
		colorbynumber.render_regions.build_square_regions(indices, False),
	)
	reader = pypdf.PdfReader(output_path)
	assert reader.get_num_pages() == 2
	assert not reader.pages[0].extract_text() and "120" in reader.pages[1].extract_text()


#============================================
def test_square_pdf_writes_a_strictly_contained_code_box(tmp_path: pathlib.Path) -> None:
	palette = [colorbynumber.marker_color.MarkerColor("WIDE", "wide", (14, 14, 14))]
	regions = colorbynumber.render_regions.build_square_regions(
		numpy.array(((0,),), dtype=numpy.int64), False
	)
	output_path = tmp_path / "contained.pdf"
	colorbynumber.pdf_writer.write_pdf(palette, "landscape", 1, 1, output_path, regions)
	positions: list[tuple[float, float, float]] = []

	def record_position(
		text: str,
		_user_matrix: list[float],
		text_matrix: list[float],
		_font_dictionary: object,
		font_size: float,
	) -> None:
		"""Collect the worksheet code rather than the marker-key text."""
		if text.strip() == "WIDE":
			positions.append((text_matrix[4], text_matrix[5], font_size))

	pypdf.PdfReader(output_path).pages[0].extract_text(visitor_text=record_position)
	text_x, baseline, font_size = positions[0]
	code_width = reportlab.pdfbase.pdfmetrics.stringWidth("WIDE", "Helvetica-Bold", font_size)
	ascent = reportlab.pdfbase.pdfmetrics.getAscent("Helvetica-Bold") * font_size / 1000.0
	descent = reportlab.pdfbase.pdfmetrics.getDescent("Helvetica-Bold") * font_size / 1000.0
	anchor = (text_x + code_width / 2.0, baseline + (ascent + descent) / 2.0)
	actual_box = colorbynumber.label_placement.text_box(
		anchor, "WIDE", "Helvetica-Bold", font_size
	)
	layout = colorbynumber.pdf_writer.calculate_layout("landscape", 1, 1)
	physical_region = colorbynumber.pdf_writer._region_polygon_pdf(layout, regions[0].polygon)
	assert physical_region.contains_properly(
		colorbynumber.label_placement.padded_text_box(actual_box, 0.25)
	)


#============================================
def test_merged_square_pdfs_use_one_code_for_one_connected_region(tmp_path: pathlib.Path) -> None:
	"""Merged square output reduces a uniform four-cell assignment to one printed code."""
	indices = numpy.zeros((2, 2), dtype=numpy.int64)
	palette = [colorbynumber.marker_color.MarkerColor("120", "Black", (14, 14, 14))]
	key_path = tmp_path / "key.pdf"
	artwork_path = tmp_path / "artwork.pdf"
	regions = colorbynumber.render_regions.build_square_regions(indices, True)
	colorbynumber.pdf_writer.write_pdf(palette, "landscape", 2, 2, key_path, regions)
	colorbynumber.grid_only_pdf_writer.write_pdf(
		palette, "landscape", 2, 2, artwork_path, regions
	)
	key_reader = pypdf.PdfReader(key_path)
	artwork_reader = pypdf.PdfReader(artwork_path)
	assert key_reader.pages[0].extract_text().count("120") == 2
	assert (
		not artwork_reader.pages[0].extract_text()
		and artwork_reader.pages[1].extract_text().count("120") == 1
	)


#============================================
def test_square_legend_records_base_and_rendered_region_counts(tmp_path: pathlib.Path) -> None:
	indices = numpy.zeros((1, 2), dtype=numpy.int64)
	palette = [colorbynumber.marker_color.MarkerColor("120", "Black", (14, 14, 14))]
	regions = colorbynumber.render_regions.build_square_regions(indices, True)
	output_path = tmp_path / "legend.csv"
	colorbynumber.csv_writer.write_legend_csv(palette, output_path, regions)
	with output_path.open(newline="", encoding="utf-8") as handle:
		row = next(csv.DictReader(handle))
	assert (row["square_count"], row["region_count"]) == ("2", "1")


#============================================
def test_square_summary_records_region_reduction(tmp_path: pathlib.Path) -> None:
	output_path = tmp_path / "summary.txt"
	colorbynumber.summary_writer.write_summary(
		pathlib.Path("source.png"),
		pathlib.Path("palette.yml"),
		"crop",
		"landscape",
		"none",
		numpy.zeros((1, 2)),
		output_path,
		True,
		1,
	)
	text = output_path.read_text(encoding="utf-8")
	assert "Merge same-color regions: enabled" in text
	assert "Square assignments: 2" in text and "Rendered regions: 1 (reduction: 1)" in text


@pytest.mark.parametrize(
	("page_orientation", "grid_shape", "page_size"),
	(
		("landscape", (30, 43), (792.0, 612.0)),
		("portrait", (43, 30), (612.0, 792.0)),
	),
)
def test_pdf_writer_makes_one_letter_page(
	tmp_path: pathlib.Path,
	page_orientation: str,
	grid_shape: tuple[int, int],
	page_size: tuple[float, float],
) -> None:
	indices = numpy.zeros(grid_shape, dtype=numpy.int64)
	palette = [colorbynumber.marker_color.MarkerColor("120", "Black", (14, 14, 14))]
	output_path = tmp_path / f"{page_orientation}.pdf"
	colorbynumber.pdf_writer.write_pdf(
		palette,
		page_orientation,
		grid_shape[1],
		grid_shape[0],
		output_path,
		colorbynumber.render_regions.build_square_regions(indices, False),
	)
	reader = pypdf.PdfReader(output_path)
	page = reader.pages[0]
	actual_page_size = (float(page.mediabox.width), float(page.mediabox.height))
	assert reader.get_num_pages() == 1
	assert actual_page_size == page_size


def test_default_palette_preserves_alphanumeric_codes() -> None:
	palette_path = colorbynumber.repo_paths.get_default_palette_path()
	palette = colorbynumber.palette_loader.load_palette(palette_path)
	blue_grey = next(marker for marker in palette if marker.name == "Blue Grey")
	assert blue_grey.code == "BG7"
