"""Exercise the default square CLI path and verify its complete output family."""

# Standard Library
import pathlib
import sys
import tempfile

# PIP3 modules
import pypdf

# Make the shared test helper importable before resolving the repository root.
TESTS_DIRECTORY = pathlib.Path(__file__).resolve().parents[1]
if str(TESTS_DIRECTORY) not in sys.path:
	sys.path.insert(0, str(TESTS_DIRECTORY))

# local test modules
import file_utils

# Resolve and expose the repository root before importing its package modules.
REPO_ROOT = pathlib.Path(file_utils.get_repo_root())
if str(REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(REPO_ROOT))

# local repo modules
import colorbynumber.cli
import colorbynumber.repo_paths


#============================================
def _verify_output_family(paths: dict[str, pathlib.Path]) -> None:
	"""Fail clearly when the square CLI omits or corrupts an expected artifact.

	Args:
		paths: Generated output paths from the square coordinator.

	Raises:
		RuntimeError: A required artifact is missing, empty, or has the wrong page count.
	"""
	for label, path in paths.items():
		if not path.is_file() or path.stat().st_size == 0:
			raise RuntimeError(f"Missing or empty {label} output: {path}")
	if len(pypdf.PdfReader(paths["diagram"]).pages) != 1:
		raise RuntimeError("The square marker-key PDF must contain one page")
	if len(pypdf.PdfReader(paths["artwork pages"]).pages) != 2:
		raise RuntimeError("The square artwork PDF must contain blank and numbered pages")


#============================================
def main() -> None:
	"""Run the normal unmerged square CLI against the tracked chart and palette."""
	input_path = REPO_ROOT / "palettes" / "marker_image_set.jpg"
	palette_path = colorbynumber.repo_paths.get_default_palette_path()
	if not input_path.is_file():
		raise RuntimeError(f"Missing tracked E2E input image: {input_path}")
	if not palette_path.is_file():
		raise RuntimeError(f"Missing tracked E2E palette: {palette_path}")
	with tempfile.TemporaryDirectory(prefix="color_by_number_square_e2e_") as temporary_directory:
		output_path = pathlib.Path(temporary_directory) / "worksheet.pdf"
		original_argv = sys.argv
		sys.argv = [
			"color_by_number.py",
			"--input",
			str(input_path),
			"--palette",
			str(palette_path),
			"--output",
			str(output_path),
			"--grid",
			"2x1",
			"--enhancement",
			"none",
		]
		try:
			colorbynumber.cli.main()
		finally:
			sys.argv = original_argv
		paths = colorbynumber.cli.build_output_paths(output_path)
		_verify_output_family(paths)


if __name__ == "__main__":
	main()
