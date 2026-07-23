"""Behavioral contracts for the separate bounded-Voronoi output writers."""

# Standard Library
import csv
import pathlib

# PIP3 modules
import numpy
import pytest

# local repo modules
import colorbynumber.marker_color
import colorbynumber.render_regions
import colorbynumber.voronoi_pdf_writer
import colorbynumber.voronoi_csv_writer
import colorbynumber.voronoi_geometry
import colorbynumber.voronoi_summary_writer


#============================================
def _partition() -> colorbynumber.voronoi_geometry.Partition:
	"""Return a small real partition with stable site order."""
	domain = colorbynumber.voronoi_geometry.create_domain(2, 1)
	sites = colorbynumber.voronoi_geometry.generate_square_grid_sites(domain)
	return colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites).partition


#============================================
def _palette() -> list[colorbynumber.marker_color.MarkerColor]:
	"""Return a compact palette whose entries make row order visible."""
	return [
		colorbynumber.marker_color.MarkerColor("R", "red", (255, 0, 0)),
		colorbynumber.marker_color.MarkerColor("B", "blue", (0, 0, 255)),
		colorbynumber.marker_color.MarkerColor("Y", "yellow", (255, 255, 0)),
	]


#============================================
def _summary(**changes: object) -> colorbynumber.voronoi_summary_writer.VoronoiRunSummary:
	"""Build one valid resolved run summary, with explicit invalid-value overrides."""
	values: dict[str, object] = {
		"input_path": pathlib.Path("source.png"),
		"palette_path": pathlib.Path("palette.yml"),
		"fit_mode": "crop",
		"page_orientation": "landscape",
		"enhancement": "strong",
		"columns": 3,
		"rows": 2,
		"seed": 901,
		"mean_delta_e_76": 4.25,
		"maximum_delta_e_76": 12.5,
		"seam_fallback_pixel_count": 1,
		"polygon_fallback_count": 2,
		"label_font_size_points": 5.5,
		"shifted_label_count": 3,
		"best_effort_label_count": 0,
		"total_label_shift_points": 9.5,
		"maximum_label_shift_points": 4.5,
		"label_overlap_pair_count": 4,
		"merge_regions": False,
		"rendered_region_count": 6,
	}
	values.update(changes)
	return colorbynumber.voronoi_summary_writer.VoronoiRunSummary(**values)  # type: ignore[arg-type]


#============================================
def test_assignment_csv_keeps_stable_site_order(tmp_path: pathlib.Path) -> None:
	partition = _partition()
	output_path = tmp_path / "assignments.csv"
	colorbynumber.voronoi_csv_writer.write_assignments_csv(
		partition,
		numpy.array(((12.5, 34.0, 56.25), (210.0, 190.0, 170.0))),
		numpy.array((1, 0), dtype=numpy.int64),
		numpy.array((1.25, 9.5)),
		_palette(),
		output_path,
	)
	with output_path.open(newline="", encoding="utf-8") as handle:
		rows = list(csv.DictReader(handle))
	assert [row["site_identifier"] for row in rows] == ["0", "1"]


#============================================
def test_assignment_csv_records_the_chosen_marker_for_each_site(tmp_path: pathlib.Path) -> None:
	output_path = tmp_path / "assignments.csv"
	colorbynumber.voronoi_csv_writer.write_assignments_csv(
		_partition(),
		numpy.array(((12.5, 34.0, 56.25), (210.0, 190.0, 170.0))),
		numpy.array((1, 0), dtype=numpy.int64),
		numpy.array((1.25, 9.5)),
		_palette(),
		output_path,
	)
	with output_path.open(newline="", encoding="utf-8") as handle:
		rows = list(csv.DictReader(handle))
	assert (rows[0]["code"], rows[0]["color_name"]) == ("B", "blue")


#============================================
def test_legend_csv_records_an_unused_palette_color(tmp_path: pathlib.Path) -> None:
	output_path = tmp_path / "legend.csv"
	partition = _partition()
	indices = numpy.array((1, 1), dtype=numpy.int64)
	colorbynumber.voronoi_csv_writer.write_legend_csv(
		_palette(),
		output_path,
		colorbynumber.render_regions.build_voronoi_regions(partition, indices, False),
	)
	with output_path.open(newline="", encoding="utf-8") as handle:
		rows = {row["code"]: row for row in csv.DictReader(handle)}
	assert rows["R"]["polygon_count"] == "0"


#============================================
def test_legend_csv_records_a_used_palette_color(tmp_path: pathlib.Path) -> None:
	output_path = tmp_path / "legend.csv"
	partition = _partition()
	indices = numpy.array((1, 1), dtype=numpy.int64)
	colorbynumber.voronoi_csv_writer.write_legend_csv(
		_palette(),
		output_path,
		colorbynumber.render_regions.build_voronoi_regions(partition, indices, False),
	)
	with output_path.open(newline="", encoding="utf-8") as handle:
		rows = {row["code"]: row for row in csv.DictReader(handle)}
	assert rows["B"]["polygon_count"] == "2"


#============================================
def test_legend_csv_records_base_and_rendered_region_counts(tmp_path: pathlib.Path) -> None:
	"""Legend preserves assignments while recording the printable region reduction."""
	partition = _partition()
	indices = numpy.array((1, 1), dtype=numpy.int64)
	regions = colorbynumber.render_regions.build_voronoi_regions(partition, indices, True)
	output_path = tmp_path / "legend.csv"
	colorbynumber.voronoi_csv_writer.write_legend_csv(_palette(), output_path, regions)
	with output_path.open(newline="", encoding="utf-8") as handle:
		rows = {row["code"]: row for row in csv.DictReader(handle)}
	assert (rows["B"]["polygon_count"], rows["B"]["region_count"]) == ("2", "1")


#============================================
@pytest.mark.parametrize(
	("polygon_rgb", "indices", "errors", "message"),
	[
		(numpy.array(((1.0, 2.0), (3.0, 4.0))), numpy.array((0, 1)), numpy.array((1.0, 2.0)), "RGB"),
		(
			numpy.array(((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))),
			numpy.array((0.0, 1.0)),
			numpy.array((1.0, 2.0)),
			"integers",
		),
		(
			numpy.array(((1.0, 2.0, 3.0), (4.0, 5.0, 6.0))),
			numpy.array((0, 3)),
			numpy.array((1.0, 2.0)),
			"available colors",
		),
	],
)
def test_assignment_csv_rejects_invalid_shape_type_and_palette_bounds(
	tmp_path: pathlib.Path,
	polygon_rgb: numpy.ndarray,
	indices: numpy.ndarray,
	errors: numpy.ndarray,
	message: str,
) -> None:
	with pytest.raises(ValueError, match=message):
		colorbynumber.voronoi_csv_writer.write_assignments_csv(
			_partition(), polygon_rgb, indices, errors, _palette(), tmp_path / "bad.csv"
		)


#============================================
def test_summary_records_resolved_site_dimensions(tmp_path: pathlib.Path) -> None:
	output_path = tmp_path / "summary.txt"
	colorbynumber.voronoi_summary_writer.write_summary(
		_summary(columns=7, rows=4), output_path
	)
	text = output_path.read_text(encoding="utf-8")
	assert "Grid-derived sites: 7 columns x 4 rows" in text


#============================================
def test_summary_records_resolved_polygon_count(tmp_path: pathlib.Path) -> None:
	output_path = tmp_path / "summary.txt"
	colorbynumber.voronoi_summary_writer.write_summary(
		_summary(columns=7, rows=4), output_path
	)
	text = output_path.read_text(encoding="utf-8")
	assert "Voronoi polygons: N=28 (7 * 4)" in text


#============================================
def test_summary_records_rendered_region_reduction(tmp_path: pathlib.Path) -> None:
	output_path = tmp_path / "summary.txt"
	colorbynumber.voronoi_summary_writer.write_summary(
		_summary(
			columns=2,
			rows=1,
			merge_regions=True,
			rendered_region_count=1,
			shifted_label_count=1,
			total_label_shift_points=1.0,
			maximum_label_shift_points=1.0,
		),
		output_path,
	)
	text = output_path.read_text(encoding="utf-8")
	assert "Merge same-color regions: enabled" in text
	assert "Rendered regions: 1 (reduction: 1)" in text


#============================================
def test_summary_records_internal_replay_seed(tmp_path: pathlib.Path) -> None:
	output_path = tmp_path / "summary.txt"
	colorbynumber.voronoi_summary_writer.write_summary(_summary(seed=31415), output_path)
	text = output_path.read_text(encoding="utf-8")
	assert "Internal generated/replay seed: 31415" in text


#============================================
def test_summary_formats_color_error_measurements(tmp_path: pathlib.Path) -> None:
	output_path = tmp_path / "summary.txt"
	colorbynumber.voronoi_summary_writer.write_summary(
		_summary(mean_delta_e_76=3.125, maximum_delta_e_76=9.875), output_path
	)
	text = output_path.read_text(encoding="utf-8")
	assert "Mean Delta E 76: 3.125" in text
	assert "Maximum Delta E 76: 9.875" in text


#============================================
@pytest.mark.parametrize(
	("changes", "expected_line"),
	[
		({"seam_fallback_pixel_count": 6}, "Numerical seam fallback pixels: 6"),
		({"polygon_fallback_count": 8}, "Zero-pixel polygon fallbacks: 8"),
		(
			{
				"shifted_label_count": 0,
				"total_label_shift_points": 0.0,
				"maximum_label_shift_points": 0.0,
			},
			"Shifted labels: 0",
		),
		({"shifted_label_count": 5}, "Shifted labels: 5"),
		({"best_effort_label_count": 2}, "Best-effort labels: 2"),
		({"total_label_shift_points": 12.25}, "Total label shift (points): 12.250"),
		({"maximum_label_shift_points": 4.25}, "Maximum label shift (points): 4.250"),
		({"label_overlap_pair_count": 12}, "Label overlap pairs: 12"),
	],
)
def test_summary_records_diagnostic_counts(
	tmp_path: pathlib.Path,
	changes: dict[str, object],
	expected_line: str,
) -> None:
	output_path = tmp_path / "summary.txt"
	colorbynumber.voronoi_summary_writer.write_summary(_summary(**changes), output_path)
	assert expected_line in output_path.read_text(encoding="utf-8")


#============================================
@pytest.mark.parametrize(
	("changes", "message"),
	[
		({"columns": True}, "positive integer"),
		({"mean_delta_e_76": float("inf")}, "finite number"),
		({"polygon_fallback_count": -1}, "nonnegative integer"),
		({"best_effort_label_count": -1}, "nonnegative integer"),
	],
)
def test_summary_rejects_invalid_resolved_values(
	changes: dict[str, object],
	message: str,
) -> None:
	with pytest.raises(ValueError, match=message):
		_summary(**changes)


#============================================
@pytest.mark.parametrize(
	("changes", "message"),
	[
		({"mean_delta_e_76": -0.25}, "nonnegative"),
		({"maximum_delta_e_76": -0.25}, "nonnegative"),
		(
			{"mean_delta_e_76": 4.5, "maximum_delta_e_76": 4.25},
			"maximum Delta E 76.*mean Delta E 76",
		),
	],
)
def test_summary_rejects_invalid_color_error_measurements(
	changes: dict[str, object],
	message: str,
) -> None:
	with pytest.raises(ValueError, match=message):
		_summary(**changes)


#============================================
@pytest.mark.parametrize(
	("changes", "message"),
	[
		({"shifted_label_count": 7}, "shifted label count exceeds rendered region count"),
		(
			{"best_effort_label_count": 7},
			"best-effort label count exceeds rendered region count",
		),
		(
			{
				"shifted_label_count": 0,
				"total_label_shift_points": 1.0,
				"maximum_label_shift_points": 0.0,
			},
			"zero shifted labels require zero total and maximum label shift",
		),
		(
			{
				"shifted_label_count": 0,
				"total_label_shift_points": 0.0,
				"maximum_label_shift_points": 1.0,
			},
			"zero shifted labels require zero total and maximum label shift",
		),
		(
			{
				"shifted_label_count": 1,
				"total_label_shift_points": 0.0,
				"maximum_label_shift_points": 0.0,
			},
			"shifted labels require positive total and maximum label shift",
		),
		(
			{
				"shifted_label_count": 1,
				"total_label_shift_points": 1.0,
				"maximum_label_shift_points": 0.0,
			},
			"shifted labels require positive total and maximum label shift",
		),
		(
			{
				"shifted_label_count": 1,
				"total_label_shift_points": 1.0,
				"maximum_label_shift_points": 2.0,
			},
			"maximum label shift exceeds total label shift",
		),
	],
)
def test_summary_rejects_incoherent_label_shift_diagnostics(
	changes: dict[str, object],
	message: str,
) -> None:
	"""Reject impossible relationships among contained-label shift diagnostics."""
	with pytest.raises(ValueError, match=message):
		_summary(**changes)
