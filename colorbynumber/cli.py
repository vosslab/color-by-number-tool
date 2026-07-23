"""Command-line parsing and dispatch for square and Voronoi output pipelines."""

# Standard Library
import argparse
import pathlib

# local repo modules
import colorbynumber.constants
import colorbynumber.csv_writer
import colorbynumber.color_matcher
import colorbynumber.grid_only_pdf_writer
import colorbynumber.image_sampler
import colorbynumber.orientation
import colorbynumber.palette_loader
import colorbynumber.pdf_writer
import colorbynumber.preview_writer
import colorbynumber.repo_paths
import colorbynumber.summary_writer
import colorbynumber.voronoi_pipeline


#============================================
def parse_args() -> argparse.Namespace:
	"""Parse command-line arguments.

	Returns:
		The parsed command-line arguments.
	"""
	default_grid = colorbynumber.constants.DEFAULT_GRID_SIZE
	default_grid_text = f"{default_grid[0]}x{default_grid[1]}"
	parser = argparse.ArgumentParser(
		description="Make an orientation-matched, code-only color-by-number diagram."
	)
	parser.add_argument(
		"-i", "--input", dest="input_file", type=pathlib.Path, required=True,
		help="Input image",
	)
	parser.add_argument(
		"-o", "--output", dest="output_file", type=pathlib.Path,
		default=colorbynumber.constants.DEFAULT_OUTPUT,
		help="Output PDF file (default: output/pdf/color_by_number.pdf)",
	)
	parser.add_argument(
		"-p", "--palette", dest="palette_file", type=pathlib.Path,
		default=colorbynumber.repo_paths.get_default_palette_path(),
		help="Marker palette YAML file (default: palettes/aoartix_48.yml)",
	)
	parser.add_argument(
		"-f", "--fit", dest="fit_mode", choices=("crop", "contain"), default="crop",
		help="Fit the image by center cropping or adding a border (default: crop)",
	)
	parser.add_argument(
		"--layout", choices=("square", "voronoi"), default="square",
		help=(
			"Output layout: square uses the existing default; voronoi uses organic polygons "
			"(default: square)"
		),
	)
	parser.add_argument(
		"-g", "--grid", dest="grid_size", type=colorbynumber.orientation.parse_grid_size,
		default=default_grid, metavar="COLUMNSxROWS",
		help=(
			"Landscape grid dimensions; portrait swaps them "
			f"(default: {default_grid_text})"
		),
	)
	parser.add_argument(
		"-e", "--enhancement", dest="enhancement",
		choices=(
			colorbynumber.color_matcher.NO_ENHANCEMENT,
			colorbynumber.color_matcher.BALANCED_ENHANCEMENT,
			colorbynumber.color_matcher.STRONG_ENHANCEMENT,
		),
		default=colorbynumber.color_matcher.STRONG_ENHANCEMENT,
		help="Color-detail treatment: none, balanced, or strong (default: strong)",
	)
	orientation_group = parser.add_mutually_exclusive_group()
	orientation_group.add_argument(
		"-L", "--landscape", dest="page_orientation", action="store_const",
		const=colorbynumber.constants.LANDSCAPE_ORIENTATION,
		help="Force a landscape page",
	)
	orientation_group.add_argument(
		"-P", "--portrait", dest="page_orientation", action="store_const",
		const=colorbynumber.constants.PORTRAIT_ORIENTATION,
		help="Force a portrait page and rotate the grid dimensions",
	)
	parser.set_defaults(
		page_orientation=colorbynumber.constants.AUTO_ORIENTATION,
	)
	args = parser.parse_args()
	return args


#============================================
def build_output_paths(output_file: pathlib.Path) -> dict[str, pathlib.Path]:
	"""Derive every companion artifact path from the requested PDF path.

	Args:
		output_file: Requested single-page PDF file.

	Returns:
		A mapping from output labels to generated paths.

	Raises:
		ValueError: The output filename does not end in .pdf.
	"""
	if output_file.suffix.lower() != ".pdf":
		raise ValueError("Output filename must end in .pdf")
	parent = output_file.parent
	stem = output_file.stem
	paths = {
		"diagram": output_file,
		"artwork pages": parent / f"{stem}_grid_only.pdf",
		"marker preview": parent / f"{stem}_marker_preview.png",
		"source preview": parent / f"{stem}_source_preview.png",
		"assignments": parent / f"{stem}_assignments.csv",
		"legend": parent / f"{stem}_legend.csv",
		"summary": parent / f"{stem}_summary.txt",
	}
	return paths


#============================================
def generate_outputs(
	args: argparse.Namespace,
) -> tuple[dict[str, pathlib.Path], str, tuple[int, int]]:
	"""Run the unchanged square image-to-diagram pipeline.

	Args:
		args: Parsed command-line arguments.

	Returns:
		Output paths, resolved orientation, and grid dimensions.
	"""
	palette = colorbynumber.palette_loader.load_palette(args.palette_file)
	image = colorbynumber.image_sampler.load_rgb_image(args.input_file)
	page_orientation = colorbynumber.orientation.resolve_page_orientation(
		image.width,
		image.height,
		args.page_orientation,
	)
	columns, rows = colorbynumber.orientation.grid_dimensions(
		page_orientation,
		args.grid_size,
	)
	source_grid = colorbynumber.image_sampler.sample_image_grid(
		image,
		args.fit_mode,
		columns,
		rows,
	)
	indices, errors = colorbynumber.color_matcher.assign_marker_colors(
		source_grid,
		palette,
		args.enhancement,
	)
	marker_grid = colorbynumber.color_matcher.palette_grid_rgb(indices, palette)
	paths = build_output_paths(args.output_file)
	args.output_file.parent.mkdir(parents=True, exist_ok=True)

	colorbynumber.pdf_writer.write_pdf(
		indices,
		palette,
		page_orientation,
		paths["diagram"],
	)
	colorbynumber.grid_only_pdf_writer.write_pdf(
		indices,
		palette,
		page_orientation,
		paths["artwork pages"],
	)
	colorbynumber.preview_writer.write_preview(marker_grid, paths["marker preview"])
	colorbynumber.preview_writer.write_preview(source_grid, paths["source preview"])
	colorbynumber.csv_writer.write_assignments_csv(indices, palette, paths["assignments"])
	colorbynumber.csv_writer.write_legend_csv(indices, palette, paths["legend"])
	colorbynumber.summary_writer.write_summary(
		args.input_file,
		args.palette_file,
		args.fit_mode,
		page_orientation,
		args.enhancement,
		errors,
		paths["summary"],
	)
	dimensions = (columns, rows)
	return paths, page_orientation, dimensions


#============================================
def main() -> None:
	"""Generate the selected diagram layout and report its output paths."""
	args = parse_args()
	if args.layout == "square":
		paths, page_orientation, dimensions = generate_outputs(args)
		internal_seed = None
	elif args.layout == "voronoi":
		result = colorbynumber.voronoi_pipeline.generate_outputs(args)
		paths = result.paths
		page_orientation = result.page_orientation
		dimensions = result.dimensions
		internal_seed = result.seed
	else:
		raise ValueError(f"Unsupported layout: {args.layout}")
	columns, rows = dimensions
	print(
		f"Created {columns} x {rows} {page_orientation} {args.layout} color-by-number diagram:"
	)
	for label, path in paths.items():
		print(f"  {label}: {path}")
	if internal_seed is not None:
		print(f"  internal seed: {internal_seed}")
