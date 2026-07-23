"""Behavioral tests for the separate production Voronoi output pipeline."""

# Standard Library
import argparse
import csv
import pathlib
import sys
import types

# PIP3 modules
import numpy
import PIL.Image
import pypdf
import pytest

# local repo modules
import colorbynumber.cli
import colorbynumber.voronoi_pipeline


#============================================
def _arguments(tmp_path: pathlib.Path, output_name: str) -> argparse.Namespace:
	"""Write a compact source and palette, then return valid Voronoi options."""
	tmp_path.mkdir(parents=True, exist_ok=True)
	input_path = tmp_path / "source.png"
	palette_path = tmp_path / "palette.yml"
	image = PIL.Image.fromarray(
		numpy.array(
			[
				[(255, 0, 0), (0, 255, 0), (0, 0, 255)],
				[(255, 255, 0), (0, 255, 255), (255, 0, 255)],
			],
			dtype=numpy.uint8,
		),
		mode="RGB",
	)
	image.save(input_path)
	palette_path.write_text(
		"""colors:
- code: R
  name: red
  rgb: [255, 0, 0]
- code: B
  name: blue
  rgb: [0, 0, 255]
""",
		encoding="utf-8",
	)
	args = argparse.Namespace(
		input_file=input_path,
		output_file=tmp_path / output_name,
		palette_file=palette_path,
		fit_mode="crop",
		page_orientation="auto",
		grid_size=(3, 2),
		enhancement="none",
	)
	return args


#============================================
def _generate_small_output(tmp_path: pathlib.Path) -> colorbynumber.voronoi_pipeline.VoronoiPipelineResult:
	"""Generate one deterministic compact artifact family for pipeline tests."""
	result = colorbynumber.voronoi_pipeline.generate_outputs(
		_arguments(tmp_path, "worksheet.pdf"),
		seed=1701,
	)
	return result


#============================================
def test_build_output_paths_names_polygon_artifacts_next_to_requested_pdf(
	tmp_path: pathlib.Path,
) -> None:
	"""Keep polygon artifacts distinct from the square-grid companion names."""
	paths = colorbynumber.voronoi_pipeline.build_output_paths(tmp_path / "face.pdf")
	assert paths["polygon preview"] == tmp_path / "face_polygon_preview.png"
	assert paths["assignments"] == tmp_path / "face_polygon_assignments.csv"


#============================================
def test_voronoi_pipeline_writes_complete_meaningful_artifacts(
	tmp_path: pathlib.Path,
) -> None:
	"""Create a resolved polygon worksheet and nonempty companion artifacts."""
	result = _generate_small_output(tmp_path)
	assert (result.dimensions, result.page_orientation, result.seed) == (
		(3, 2), "landscape", 1701,
	)
	assert all(path.is_file() and path.stat().st_size > 0 for path in result.paths.values())


#============================================
def test_voronoi_pipeline_reopens_pdf_and_preview_artifacts(
	tmp_path: pathlib.Path,
) -> None:
	"""Keep the generated PDF and both PNG previews readable by their consumers."""
	result = _generate_small_output(tmp_path)
	reader = pypdf.PdfReader(result.paths["diagram"])
	with PIL.Image.open(result.paths["source preview"]) as source_preview:
		with PIL.Image.open(result.paths["polygon preview"]) as polygon_preview:
			source_preview.load()
			polygon_preview.load()
	assert reader.metadata.title == "Voronoi color-by-number prototype pages"
	assert source_preview.mode == polygon_preview.mode == "RGB" and source_preview.size == polygon_preview.size


#============================================
def test_voronoi_pipeline_records_site_order_and_internal_seed(
	tmp_path: pathlib.Path,
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Retain generated seed replay data and stable zero-based polygon order."""
	monkeypatch.setattr(colorbynumber.voronoi_pipeline.secrets, "randbits", lambda _bits: 2468)
	result = colorbynumber.voronoi_pipeline.generate_outputs(_arguments(tmp_path, "generated.pdf"))
	with result.paths["assignments"].open("r", encoding="utf-8", newline="") as handle:
		rows = list(csv.DictReader(handle))
	summary = result.paths["summary"].read_text(encoding="utf-8")
	assert [int(row["site_identifier"]) for row in rows] == list(range(6))
	assert (
		result.seed == 2468
		and "Layout: voronoi" in summary
		and "Internal generated/replay seed: 2468" in summary
	)


#============================================
def test_voronoi_pipeline_replays_explicit_seed_geometry_and_preview(
	tmp_path: pathlib.Path,
) -> None:
	"""A maintainer replay seed preserves spatial assignments and rendered polygons."""
	first = colorbynumber.voronoi_pipeline.generate_outputs(
		_arguments(tmp_path / "first", "worksheet.pdf"),
		seed=610,
	)
	second = colorbynumber.voronoi_pipeline.generate_outputs(
		_arguments(tmp_path / "second", "worksheet.pdf"),
		seed=610,
	)
	assert first.paths["assignments"].read_bytes() == second.paths["assignments"].read_bytes()
	with PIL.Image.open(first.paths["polygon preview"]) as first_preview:
		with PIL.Image.open(second.paths["polygon preview"]) as second_preview:
			assert numpy.array_equal(numpy.asarray(first_preview), numpy.asarray(second_preview))


#============================================
def test_cli_parser_defaults_square_and_accepts_voronoi(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Expose organic polygons as an opt-in while retaining the square default."""
	monkeypatch.setattr(sys, "argv", ("color_by_number.py", "-i", "source.png"))
	default_args = colorbynumber.cli.parse_args()
	monkeypatch.setattr(
		sys,
		"argv",
		("color_by_number.py", "-i", "source.png", "--layout", "voronoi"),
	)
	voronoi_args = colorbynumber.cli.parse_args()
	assert default_args.layout == "square"
	assert voronoi_args.layout == "voronoi"


#============================================
def test_cli_dispatches_each_layout_to_its_separate_coordinator(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Choose coordinators by public layout without opening an input image."""
	paths = {"diagram": pathlib.Path("worksheet.pdf")}
	square_calls: list[str] = []
	voronoi_calls: list[str] = []

	def fake_square(
		args: argparse.Namespace,
	) -> tuple[dict[str, pathlib.Path], str, tuple[int, int]]:
		"""Record square dispatch without producing artifacts."""
		square_calls.append(args.layout)
		return paths, "landscape", (3, 2)

	def fake_voronoi(args: argparse.Namespace) -> types.SimpleNamespace:
		"""Record Voronoi dispatch without producing artifacts."""
		voronoi_calls.append(args.layout)
		return types.SimpleNamespace(
			paths=paths,
			page_orientation="landscape",
			dimensions=(3, 2),
			seed=99,
		)

	monkeypatch.setattr(colorbynumber.cli, "generate_outputs", fake_square)
	monkeypatch.setattr(
		colorbynumber.voronoi_pipeline,
		"generate_outputs",
		fake_voronoi,
	)
	monkeypatch.setattr(sys, "argv", ("color_by_number.py", "-i", "source.png"))
	colorbynumber.cli.main()
	monkeypatch.setattr(
		sys,
		"argv",
		("color_by_number.py", "-i", "source.png", "--layout", "voronoi"),
	)
	colorbynumber.cli.main()
	assert square_calls == ["square"]
	assert voronoi_calls == ["voronoi"]
