"""Shared fixed dimensions and default paths."""

# Standard Library
import pathlib


DEFAULT_GRID_SIZE = (86, 60)
AUTO_ORIENTATION = "auto"
LANDSCAPE_ORIENTATION = "landscape"
PORTRAIT_ORIENTATION = "portrait"
DEFAULT_PALETTE_RELATIVE = pathlib.Path("palettes") / "aoartix_48.yml"
DEFAULT_OUTPUT = pathlib.Path("output") / "pdf" / "color_by_number.pdf"
