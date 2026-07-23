"""Behavioral tests for the prototype polygon sampling and writers."""

# Standard Library
import pathlib

# PIP3 modules
import numpy
import PIL.Image
import pypdf
import pytest
import reportlab.pdfbase.pdfmetrics
import shapely

# local repo modules
import colorbynumber.constants
import colorbynumber.label_placement
import colorbynumber.marker_color
import colorbynumber.render_regions
import colorbynumber.voronoi_geometry
import colorbynumber.voronoi_pdf_writer
import colorbynumber.voronoi_preview_writer
import colorbynumber.voronoi_prototype


#============================================
def _partition(columns: int, rows: int) -> colorbynumber.voronoi_geometry.Partition:
	"""Return a small exact control partition for one test."""
	domain = colorbynumber.voronoi_geometry.create_domain(columns, rows)
	sites = colorbynumber.voronoi_geometry.generate_square_grid_sites(domain)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	return result.partition


#============================================
def _palette() -> list[colorbynumber.marker_color.MarkerColor]:
	"""Return a compact distinct palette for user-visible prototype behavior."""
	palette = [
		colorbynumber.marker_color.MarkerColor("R", "red", (255, 0, 0)),
		colorbynumber.marker_color.MarkerColor("B", "blue", (0, 0, 255)),
	]
	return palette


#============================================
def _asymmetric_one_cell_partition() -> colorbynumber.voronoi_geometry.Partition:
	"""Return one valid clipped cell whose site is not its area centroid."""
	domain = colorbynumber.voronoi_geometry.create_domain(1, 1)
	sites = (colorbynumber.voronoi_geometry.Site(0, 0.01, 0.01),)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	return result.partition


#============================================
def _centered_code_box(
	anchor: tuple[float, float],
	code: str,
	font_size: float,
	layout: colorbynumber.voronoi_pdf_writer.VoronoiPageLayout,
) -> shapely.Polygon:
	"""Return an independently measured centered Helvetica code box in domain units."""
	width_points = reportlab.pdfbase.pdfmetrics.stringWidth(code, "Helvetica", font_size)
	ascent = reportlab.pdfbase.pdfmetrics.getAscent("Helvetica") * font_size / 1000.0
	descent = reportlab.pdfbase.pdfmetrics.getDescent("Helvetica") * font_size / 1000.0
	anchor_x, anchor_y = anchor
	center_y = layout.polygon_y + anchor_y * layout.scale
	baseline = center_y - (ascent + descent) / 2.0
	minimum_x = anchor_x - width_points / (2.0 * layout.scale)
	maximum_x = anchor_x + width_points / (2.0 * layout.scale)
	minimum_y = (baseline + descent - layout.polygon_y) / layout.scale
	maximum_y = (baseline + ascent - layout.polygon_y) / layout.scale
	return shapely.box(minimum_x, minimum_y, maximum_x, maximum_y)


#============================================
def _numbered_code_position(
	pdf_path: pathlib.Path,
	code: str,
) -> tuple[float, float, float]:
	"""Return the numbered-page text matrix for one visible marker code."""
	positions: list[tuple[float, float, float]] = []

	def record_position(
		text: str,
		_user_matrix: list[float],
		text_matrix: list[float],
		_font_dictionary: object,
		font_size: float,
	) -> None:
		"""Collect the requested code's PDF position."""
		if text.strip() == code:
			positions.append((text_matrix[4], text_matrix[5], font_size))

	pypdf.PdfReader(pdf_path).pages[1].extract_text(visitor_text=record_position)
	if len(positions) != 1:
		raise ValueError(f"Expected one numbered {code!r} label, found {len(positions)}")
	return positions[0]


#============================================
def _numbered_code_count(pdf_path: pathlib.Path, code: str) -> int:
	"""Return the exact numbered-page PDF text count for one marker code."""
	count = 0

	def count_code(
		text: str,
		_user_matrix: list[float],
		_text_matrix: list[float],
		_font_dictionary: object,
		_font_size: float,
	) -> None:
		"""Count one complete matching text token."""
		nonlocal count
		if text.strip() == code:
			count += 1

	pypdf.PdfReader(pdf_path).pages[1].extract_text(visitor_text=count_code)
	return count


#============================================
def test_selected_distribution_replays_and_ownership_follows_site_order() -> None:
	first = colorbynumber.voronoi_prototype.build_selected_partition(3, 2, 1701)
	replay = colorbynumber.voronoi_prototype.build_selected_partition(3, 2, 1701)
	ownership, seam_count = colorbynumber.voronoi_prototype.rasterize_partition_ownership(
		first,
		9,
		6,
	)
	assert first == replay
	assert seam_count == 0 and set(numpy.unique(ownership)) == set(range(6))


#============================================
def test_fit_source_raster_crop_and_contain_have_the_requested_canvas() -> None:
	image = PIL.Image.new("RGB", (6, 2), (12, 34, 56))
	cropped = colorbynumber.voronoi_prototype.fit_source_raster(image, "crop", 2, 2, 3)
	contained = colorbynumber.voronoi_prototype.fit_source_raster(image, "contain", 2, 2, 3)
	assert cropped.size == contained.size == (6, 6)
	assert contained.getpixel((3, 0)) == (255, 255, 255)


#============================================
def test_polygon_sampling_averages_owned_pixel_centers() -> None:
	partition = _partition(2, 1)
	image = PIL.Image.fromarray(
		numpy.array([[[10, 0, 0], [30, 0, 0], [100, 0, 0], [140, 0, 0]]], dtype=numpy.uint8),
		mode="RGB",
	)
	sample = colorbynumber.voronoi_prototype.sample_partition_rgb(partition, image)
	assert numpy.allclose(sample.polygon_rgb, ((20.0, 0.0, 0.0), (120.0, 0.0, 0.0)))


#============================================
def test_shared_edge_pixel_center_uses_lower_site_identifier() -> None:
	partition = _partition(2, 1)
	ownership, seam_count = colorbynumber.voronoi_prototype.rasterize_partition_ownership(
		partition,
		3,
		1,
	)
	assert ownership.tolist() == [[0, 0, 1]] and seam_count == 0


#============================================
@pytest.mark.parametrize(("width", "height"), ((True, 1), (1, 1.5)))
def test_ownership_raster_rejects_boolean_and_noninteger_dimensions(
	width: int | float,
	height: int | float,
) -> None:
	partition = _partition(2, 1)
	with pytest.raises(ValueError, match="integer"):
		colorbynumber.voronoi_prototype.rasterize_partition_ownership(
			partition,
			width,
			height,
		)


#============================================
def test_polygon_sampling_falls_back_to_nearest_site_pixel_without_a_center() -> None:
	partition = _partition(2, 1)
	image = PIL.Image.new("RGB", (1, 1), (25, 50, 75))
	sample = colorbynumber.voronoi_prototype.sample_partition_rgb(partition, image)
	assert sample.polygon_fallback_identifiers == (1,)
	assert sample.polygon_rgb[1].tolist() == [25.0, 50.0, 75.0]


#============================================
def test_adjacency_keeps_shared_edges_and_excludes_corner_only_contacts() -> None:
	adjacency = colorbynumber.voronoi_prototype.polygon_adjacency(_partition(2, 2))
	assert adjacency[0] == (1, 2)
	assert 3 not in adjacency[0]


#============================================
def test_polygon_palette_matching_uses_polygon_neighbors_and_one_dimensional_indices() -> None:
	partition = _partition(2, 1)
	indices, errors = colorbynumber.voronoi_prototype.assign_polygon_palette(
		partition,
		numpy.array(((250, 0, 0), (0, 0, 250)), dtype=numpy.uint8),
		_palette(),
		"none",
	)
	assert indices.tolist() == [0, 1]
	assert errors.shape == (2,)


#============================================
def test_strong_polygon_matching_uses_shared_edges_not_diagonal_contacts() -> None:
	partition = _partition(2, 2)
	polygon_rgb = numpy.array(
		((60, 10, 30), (60, 10, 30), (60, 10, 30), (255, 255, 255)),
		dtype=numpy.uint8,
	)
	palette = [
		colorbynumber.marker_color.MarkerColor("D", "dark", (0, 0, 0)),
		colorbynumber.marker_color.MarkerColor("W", "warm", (120, 0, 70)),
	]
	none_indices, _none_errors = colorbynumber.voronoi_prototype.assign_polygon_palette(
		partition,
		polygon_rgb,
		palette,
		"none",
	)
	strong_indices, _strong_errors = colorbynumber.voronoi_prototype.assign_polygon_palette(
		partition,
		polygon_rgb,
		palette,
		"strong",
	)
	assert (none_indices.tolist(), strong_indices.tolist()) == ([0, 0, 0, 1], [0, 1, 1, 1])


#============================================
def test_palette_expansion_rejects_invalid_assignments_and_reconstructs_owned_pixels() -> None:
	palette = _palette()
	with pytest.raises(ValueError, match="available colors"):
		colorbynumber.voronoi_prototype.palette_rgb_values(numpy.array((2,)), palette)
	reconstructed = colorbynumber.voronoi_prototype.reconstruct_polygon_raster(
		numpy.array(((0, 1), (1, 0)), dtype=numpy.int32),
		numpy.array((0, 1)),
		palette,
	)
	assert reconstructed.tolist() == [[[255, 0, 0], [0, 0, 255]], [[0, 0, 255], [255, 0, 0]]]


#============================================
def test_palette_expansion_rejects_boolean_palette_indices() -> None:
	with pytest.raises(ValueError, match="integer"):
		colorbynumber.voronoi_prototype.palette_rgb_values(
			numpy.array((True, False)),
			_palette(),
		)


#============================================
@pytest.mark.parametrize(
	"assignments",
	(numpy.array((0.0, 1.0)), numpy.array((True, False))),
)
def test_pdf_rejects_noninteger_palette_assignments(
	assignments: numpy.ndarray,
	tmp_path: pathlib.Path,
) -> None:
	"""Reject palette arrays that cannot safely identify PDF marker codes."""
	with pytest.raises(ValueError, match="integer"):
		colorbynumber.render_regions.build_voronoi_regions(
			_partition(2, 1), assignments, False
		)


#============================================
def test_pixel_weighted_reconstruction_error_reports_exact_and_changed_rasters() -> None:
	source = numpy.array([[[0, 0, 0], [255, 255, 255]]], dtype=numpy.uint8)
	mean_error, maximum_error = colorbynumber.voronoi_prototype.pixel_weighted_reconstruction_error(
		source,
		numpy.array([[[0, 0, 0], [0, 0, 0]]], dtype=numpy.uint8),
	)
	assert mean_error > 0.0 and maximum_error > mean_error


#============================================
def test_preview_writer_draws_border_and_orders_comparison_panels(tmp_path: pathlib.Path) -> None:
	partition = _partition(2, 1)
	source = numpy.full((8, 16, 3), (200, 0, 0), dtype=numpy.uint8)
	square = numpy.full((8, 16, 3), (0, 200, 0), dtype=numpy.uint8)
	voronoi = numpy.full((8, 16, 3), (0, 0, 200), dtype=numpy.uint8)
	preview_path = tmp_path / "preview.png"
	comparison_path = tmp_path / "comparison.png"
	regions = colorbynumber.render_regions.build_voronoi_regions(
		partition, numpy.array((0, 0), dtype=numpy.int64), False
	)
	colorbynumber.voronoi_preview_writer.write_polygon_preview(
		voronoi, partition.domain, preview_path, regions
	)
	colorbynumber.voronoi_preview_writer.write_comparison(
		source, square, voronoi, partition, comparison_path
	)
	preview = PIL.Image.open(preview_path)
	comparison = PIL.Image.open(comparison_path)
	assert preview.getpixel((0, 0)) == (42, 42, 42)
	assert [comparison.getpixel((x, 32)) for x in (4, 20, 36)] == [
		(200, 0, 0),
		(0, 200, 0),
		(0, 0, 200),
	]


#============================================
def test_merged_preview_removes_same_color_internal_edge(tmp_path: pathlib.Path) -> None:
	"""A merged preview keeps the outer border without drawing its removed shared edge."""
	partition = _partition(2, 1)
	image = numpy.full((8, 16, 3), (0, 0, 200), dtype=numpy.uint8)
	regions = colorbynumber.render_regions.build_voronoi_regions(
		partition, numpy.array((0, 0), dtype=numpy.int64), True
	)
	output_path = tmp_path / "merged_preview.png"
	colorbynumber.voronoi_preview_writer.write_polygon_preview(
		image, partition.domain, output_path, regions
	)
	with PIL.Image.open(output_path) as preview:
		assert preview.getpixel((0, 0)) == (42, 42, 42)
		assert preview.getpixel((8, 4)) == (0, 0, 200)


#============================================
def test_centroid_labels_keep_an_asymmetric_clipped_cell_code_inside() -> None:
	"""Use a displaced generator where its cell centroid avoids a site-edge label."""
	partition = _asymmetric_one_cell_partition()
	layout = colorbynumber.voronoi_pdf_writer.calculate_layout(
		colorbynumber.constants.LANDSCAPE_ORIENTATION,
		partition.domain,
	)
	diagnostics = colorbynumber.voronoi_pdf_writer.analyze_labels(
		partition.domain,
		[colorbynumber.marker_color.MarkerColor("WIDE", "wide", (1, 2, 3))],
		layout,
		colorbynumber.render_regions.build_voronoi_regions(
			partition, numpy.array((0,), dtype=numpy.int64), False
		),
	)
	site_box = _centered_code_box((0.01, 0.01), "WIDE", diagnostics.font_size_points, layout)
	domain = colorbynumber.voronoi_geometry.domain_polygon(partition.domain)
	assert diagnostics.shifted_label_count == 0
	assert diagnostics.best_effort_label_count == 0
	assert not domain.covers(site_box)


#============================================
def test_numbered_page_places_asymmetric_cell_code_at_area_centroid(tmp_path: pathlib.Path) -> None:
	"""Read the PDF text matrix to verify the visible code is centroid-centered."""
	partition = _asymmetric_one_cell_partition()
	palette = [colorbynumber.marker_color.MarkerColor("WIDE", "wide", (1, 2, 3))]
	output_path = tmp_path / "centroid.pdf"
	colorbynumber.voronoi_pdf_writer.write_pdf(
		partition.domain,
		palette,
		colorbynumber.constants.LANDSCAPE_ORIENTATION,
		output_path,
		colorbynumber.render_regions.build_voronoi_regions(
			partition, numpy.array((0,), dtype=numpy.int64), False
		),
	)
	text_x, text_y, font_size = _numbered_code_position(output_path, "WIDE")
	layout = colorbynumber.voronoi_pdf_writer.calculate_layout(
		colorbynumber.constants.LANDSCAPE_ORIENTATION,
		partition.domain,
	)
	cell_centroid = colorbynumber.voronoi_geometry.domain_polygon(partition.domain).centroid
	code_width = reportlab.pdfbase.pdfmetrics.stringWidth("WIDE", "Helvetica", font_size)
	expected_center_x = layout.polygon_x + cell_centroid.x * layout.scale
	expected_center_y = layout.polygon_y + cell_centroid.y * layout.scale
	font_ascent = reportlab.pdfbase.pdfmetrics.getAscent("Helvetica") * font_size / 1000.0
	font_descent = reportlab.pdfbase.pdfmetrics.getDescent("Helvetica") * font_size / 1000.0
	expected_baseline = expected_center_y - (font_ascent + font_descent) / 2.0
	assert numpy.allclose(
		(text_x + code_width / 2.0, text_y),
		(expected_center_x, expected_baseline),
		atol=0.01,
	)
	actual_anchor = (text_x + code_width / 2.0, expected_center_y)
	actual_box = colorbynumber.label_placement.text_box(
		actual_anchor, "WIDE", "Helvetica", font_size
	)
	physical_domain = colorbynumber.voronoi_pdf_writer._region_polygon_pdf(
		layout, colorbynumber.voronoi_geometry.domain_polygon(partition.domain)
	)
	assert physical_domain.contains_properly(
		colorbynumber.label_placement.padded_text_box(actual_box, 0.25)
	)


#============================================
def test_voronoi_pdf_uses_one_code_per_resolved_render_region(tmp_path: pathlib.Path) -> None:
	"""All three pages remain present while the numbered page follows regions exactly."""
	partition = _partition(2, 1)
	code = "MERGE-CHECK-42"
	palette = [colorbynumber.marker_color.MarkerColor(code, "red", (255, 0, 0))]
	indices = numpy.array((0, 0), dtype=numpy.int64)
	merged_path = tmp_path / "merged.pdf"
	unmerged_path = tmp_path / "unmerged.pdf"
	merged = colorbynumber.render_regions.build_voronoi_regions(partition, indices, True)
	unmerged = colorbynumber.render_regions.build_voronoi_regions(partition, indices, False)
	colorbynumber.voronoi_pdf_writer.write_pdf(
		partition.domain, palette, "landscape", merged_path, merged
	)
	colorbynumber.voronoi_pdf_writer.write_pdf(
		partition.domain, palette, "landscape", unmerged_path, unmerged
	)
	merged_reader = pypdf.PdfReader(merged_path)
	unmerged_reader = pypdf.PdfReader(unmerged_path)
	assert (len(merged_reader.pages), len(unmerged_reader.pages)) == (3, 3)
	assert _numbered_code_count(merged_path, code) == len(merged)
	assert _numbered_code_count(unmerged_path, code) == len(unmerged)
