"""Command-line parsing and pipeline orchestration."""

# Standard Library
import pathlib
import argparse

# local repo modules
import colorbynumber.constants
import colorbynumber.csv_writer
import colorbynumber.color_matcher
import colorbynumber.image_sampler
import colorbynumber.palette_loader
import colorbynumber.pdf_writer
import colorbynumber.preview_writer
import colorbynumber.summary_writer


#============================================
def parse_args() -> argparse.Namespace:
	"""Parse command-line arguments.

	Returns:
		The parsed command-line arguments.
	"""
	parser = argparse.ArgumentParser(
		description="Make a 43 by 30 code-only color-by-number diagram from an image."
	)
	parser.add_argument(
		"-i", "--input", dest="input_file", type=pathlib.Path, required=True,
		help="Input portrait image",
	)
	parser.add_argument(
		"-o", "--output", dest="output_file", type=pathlib.Path,
		default=colorbynumber.constants.DEFAULT_OUTPUT,
		help="Output PDF file (default: output/pdf/color_by_number.pdf)",
	)
	parser.add_argument(
		"-p", "--palette", dest="palette_file", type=pathlib.Path,
		default=colorbynumber.constants.DEFAULT_PALETTE,
		help="Marker palette YAML file (default: palettes/aoartix_48.yml)",
	)
	parser.add_argument(
		"-f", "--fit", dest="fit_mode", choices=("crop", "contain"), default="crop",
		help="Fit the image by center cropping or adding a border (default: crop)",
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
		"marker preview": parent / f"{stem}_marker_preview.png",
		"source preview": parent / f"{stem}_source_preview.png",
		"assignments": parent / f"{stem}_assignments.csv",
		"legend": parent / f"{stem}_legend.csv",
		"summary": parent / f"{stem}_summary.txt",
	}
	return paths


#============================================
def generate_outputs(args: argparse.Namespace) -> dict[str, pathlib.Path]:
	"""Run the complete image-to-diagram pipeline.

	Args:
		args: Parsed command-line arguments.

	Returns:
		A mapping from output labels to generated paths.
	"""
	palette = colorbynumber.palette_loader.load_palette(args.palette_file)
	image = colorbynumber.image_sampler.load_rgb_image(args.input_file)
	source_grid = colorbynumber.image_sampler.sample_image_grid(image, args.fit_mode)
	indices, errors = colorbynumber.color_matcher.assign_marker_colors(source_grid, palette)
	marker_grid = colorbynumber.color_matcher.palette_grid_rgb(indices, palette)
	paths = build_output_paths(args.output_file)
	args.output_file.parent.mkdir(parents=True, exist_ok=True)

	colorbynumber.pdf_writer.write_pdf(indices, palette, paths["diagram"])
	colorbynumber.preview_writer.write_preview(marker_grid, paths["marker preview"])
	colorbynumber.preview_writer.write_preview(source_grid, paths["source preview"])
	colorbynumber.csv_writer.write_assignments_csv(indices, palette, paths["assignments"])
	colorbynumber.csv_writer.write_legend_csv(indices, palette, paths["legend"])
	colorbynumber.summary_writer.write_summary(
		args.input_file,
		args.palette_file,
		args.fit_mode,
		errors,
		paths["summary"],
	)
	return paths


#============================================
def main() -> None:
	"""Generate the diagram and report its output paths."""
	args = parse_args()
	paths = generate_outputs(args)
	columns = colorbynumber.constants.GRID_COLUMNS
	rows = colorbynumber.constants.GRID_ROWS
	print(f"Created a {columns} x {rows} color-by-number diagram:")
	for label, path in paths.items():
		print(f"  {label}: {path}")
