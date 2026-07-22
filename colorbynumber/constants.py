"""Shared fixed dimensions and default paths."""

# Standard Library
import pathlib


GRID_COLUMNS = 43
GRID_ROWS = 30
PREVIEW_CELL_PIXELS = 24
REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_PALETTE = REPO_ROOT / "palettes" / "aoartix_48.yml"
DEFAULT_OUTPUT = pathlib.Path("output") / "pdf" / "color_by_number.pdf"
