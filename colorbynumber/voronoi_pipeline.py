"""Dedicated bounded-Voronoi production-output coordinator."""

# Standard Library
import argparse
import dataclasses
import pathlib
import secrets

# PIP3 modules
import numpy

# local repo modules
import colorbynumber.image_sampler
import colorbynumber.orientation
import colorbynumber.palette_loader
import colorbynumber.voronoi_csv_writer
import colorbynumber.voronoi_pdf_writer
import colorbynumber.voronoi_preview_writer
import colorbynumber.voronoi_prototype
import colorbynumber.voronoi_summary_writer


#============================================
@dataclasses.dataclass(frozen=True)
class VoronoiPipelineResult:
	"""Recorded outputs from one independently generated Voronoi worksheet."""

	paths: dict[str, pathlib.Path]
	page_orientation: str
	dimensions: tuple[int, int]
	seed: int
	label_diagnostics: colorbynumber.voronoi_pdf_writer.LabelDiagnostics


#============================================
def build_output_paths(output_file: pathlib.Path) -> dict[str, pathlib.Path]:
	"""Derive polygon-specific output paths from one requested PDF path.

	Args:
		output_file: Requested bounded-Voronoi PDF path.

	Returns:
		Paths for the diagram and its polygon-specific companion artifacts.

	Raises:
		ValueError: The requested output does not have a PDF suffix.
	"""
	if output_file.suffix.lower() != ".pdf":
		raise ValueError("Output filename must end in .pdf")
	parent = output_file.parent
	stem = output_file.stem
	paths = {
		"diagram": output_file,
		"polygon preview": parent / f"{stem}_polygon_preview.png",
		"source preview": parent / f"{stem}_source_preview.png",
		"assignments": parent / f"{stem}_polygon_assignments.csv",
		"legend": parent / f"{stem}_legend.csv",
		"summary": parent / f"{stem}_summary.txt",
	}
	return paths


#============================================
def _resolve_seed(seed: int | None) -> int:
	"""Return one nonnegative internal seed suitable for recording and replay."""
	if seed is None:
		return secrets.randbits(63)
	if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
		raise ValueError("Voronoi seed must be a nonnegative integer")
	return seed


#============================================
def _write_summary(
	args: argparse.Namespace,
	page_orientation: str,
	dimensions: tuple[int, int],
	seed: int,
	errors: numpy.ndarray,
	sample: colorbynumber.voronoi_prototype.PolygonRasterSample,
	label_diagnostics: colorbynumber.voronoi_pdf_writer.LabelDiagnostics,
	output_path: pathlib.Path,
) -> None:
	"""Write polygon-specific run metadata and color-assignment diagnostics."""
	if errors.ndim != 1 or errors.size == 0:
		raise ValueError("Polygon assignment errors must be a nonempty one-dimensional array")
	columns, rows = dimensions
	summary = colorbynumber.voronoi_summary_writer.VoronoiRunSummary(
		input_path=args.input_file,
		palette_path=args.palette_file,
		fit_mode=args.fit_mode,
		page_orientation=page_orientation,
		enhancement=args.enhancement,
		columns=columns,
		rows=rows,
		seed=seed,
		mean_delta_e_76=float(numpy.mean(errors)),
		maximum_delta_e_76=float(numpy.max(errors)),
		seam_fallback_pixel_count=sample.seam_fallback_pixel_count,
		polygon_fallback_count=len(sample.polygon_fallback_identifiers),
		label_font_size_points=label_diagnostics.font_size_points,
		labels_outside_owned_cell_count=label_diagnostics.outside_owned_cell_count,
		label_overlap_pair_count=label_diagnostics.overlap_pair_count,
	)
	colorbynumber.voronoi_summary_writer.write_summary(summary, output_path)


#============================================
def generate_outputs(
	args: argparse.Namespace,
	seed: int | None = None,
) -> VoronoiPipelineResult:
	"""Create the complete independent bounded-Voronoi output family.

	The generated seed is deliberately internal to the user interface and is
	recorded in the polygon-specific summary for maintainer replay.

	Args:
		args: Parsed input, palette, fit, orientation, grid, and enhancement options.
		seed: Optional internal deterministic seed for tests and maintainers.

	Returns:
		The artifact paths, resolved count/aspect, replay seed, and label evidence.
	"""
	palette = colorbynumber.palette_loader.load_palette(args.palette_file)
	image = colorbynumber.image_sampler.load_rgb_image(args.input_file)
	page_orientation = colorbynumber.orientation.resolve_page_orientation(
		image.width,
		image.height,
		args.page_orientation,
	)
	dimensions = colorbynumber.orientation.grid_dimensions(
		page_orientation,
		args.grid_size,
	)
	columns, rows = dimensions
	resolved_seed = _resolve_seed(seed)
	partition = colorbynumber.voronoi_prototype.build_selected_partition(
		columns,
		rows,
		resolved_seed,
	)
	fitted_image = colorbynumber.voronoi_prototype.fit_source_raster(
		image,
		args.fit_mode,
		columns,
		rows,
	)
	sample = colorbynumber.voronoi_prototype.sample_partition_rgb(partition, fitted_image)
	indices, errors = colorbynumber.voronoi_prototype.assign_polygon_palette(
		partition,
		sample.polygon_rgb,
		palette,
		args.enhancement,
	)
	reconstruction_rgb = colorbynumber.voronoi_prototype.reconstruct_polygon_raster(
		sample.ownership,
		indices,
		palette,
	)
	paths = build_output_paths(args.output_file)
	args.output_file.parent.mkdir(parents=True, exist_ok=True)
	label_diagnostics = colorbynumber.voronoi_pdf_writer.write_pdf(
		partition,
		indices,
		palette,
		page_orientation,
		paths["diagram"],
	)
	colorbynumber.voronoi_preview_writer.write_polygon_preview(
		reconstruction_rgb,
		partition,
		paths["polygon preview"],
	)
	colorbynumber.voronoi_preview_writer.write_polygon_preview(
		sample.fitted_rgb,
		partition,
		paths["source preview"],
	)
	colorbynumber.voronoi_csv_writer.write_assignments_csv(
		partition,
		sample.polygon_rgb,
		indices,
		errors,
		palette,
		paths["assignments"],
	)
	colorbynumber.voronoi_csv_writer.write_legend_csv(
		indices,
		palette,
		paths["legend"],
	)
	_write_summary(
		args,
		page_orientation,
		dimensions,
		resolved_seed,
		errors,
		sample,
		label_diagnostics,
		paths["summary"],
	)
	result = VoronoiPipelineResult(
		paths=paths,
		page_orientation=page_orientation,
		dimensions=dimensions,
		seed=resolved_seed,
		label_diagnostics=label_diagnostics,
	)
	return result
