"""Page-orientation selection and configurable grid dimensions."""

# Standard Library
import re

# local repo modules
import colorbynumber.constants


#============================================
def validate_grid_size(grid_size: tuple[int, int]) -> tuple[int, int]:
	"""Validate landscape columns and rows.

	Args:
		grid_size: Landscape columns and rows.

	Returns:
		The validated landscape grid size.

	Raises:
		ValueError: A dimension is non-positive or the first dimension is shorter.
	"""
	columns, rows = grid_size
	if columns <= 0 or rows <= 0:
		raise ValueError("Grid dimensions must be greater than zero")
	if columns < rows:
		raise ValueError("Grid size must list the longer landscape dimension first")
	validated_size = (columns, rows)
	return validated_size


#============================================
def parse_grid_size(value: str) -> tuple[int, int]:
	"""Parse a CLI grid size written as landscape columns by rows.

	Args:
		value: Grid size in COLUMNSxROWS form.

	Returns:
		Validated landscape columns and rows.

	Raises:
		ValueError: The value is not a valid positive landscape grid size.
	"""
	match = re.fullmatch(r"([1-9][0-9]*)[xX]([1-9][0-9]*)", value.strip())
	if match is None:
		raise ValueError("Grid size must use positive COLUMNSxROWS form, such as 86x60")
	grid_size = (int(match.group(1)), int(match.group(2)))
	validated_size = validate_grid_size(grid_size)
	return validated_size


#============================================
def resolve_page_orientation(
	image_width: int,
	image_height: int,
	requested_orientation: str,
) -> str:
	"""Resolve automatic or overridden page orientation.

	Args:
		image_width: EXIF-corrected source width in pixels.
		image_height: EXIF-corrected source height in pixels.
		requested_orientation: Auto, landscape, or portrait.

	Returns:
		The resolved landscape or portrait orientation.

	Raises:
		ValueError: Image dimensions or the requested orientation are invalid.
	"""
	if image_width <= 0 or image_height <= 0:
		raise ValueError("Image dimensions must be greater than zero")
	valid_orientations = {
		colorbynumber.constants.AUTO_ORIENTATION,
		colorbynumber.constants.LANDSCAPE_ORIENTATION,
		colorbynumber.constants.PORTRAIT_ORIENTATION,
	}
	if requested_orientation not in valid_orientations:
		raise ValueError(f"Unsupported page orientation: {requested_orientation}")
	if requested_orientation == colorbynumber.constants.AUTO_ORIENTATION:
		if image_height > image_width:
			orientation = colorbynumber.constants.PORTRAIT_ORIENTATION
		else:
			orientation = colorbynumber.constants.LANDSCAPE_ORIENTATION
	else:
		orientation = requested_orientation
	return orientation


#============================================
def grid_dimensions(
	page_orientation: str,
	landscape_grid_size: tuple[int, int],
) -> tuple[int, int]:
	"""Return columns and rows for the selected page orientation.

	Args:
		page_orientation: Resolved landscape or portrait orientation.
		landscape_grid_size: Columns and rows when the page is landscape.

	Returns:
		Grid columns and rows.

	Raises:
		ValueError: The page orientation is not supported.
	"""
	landscape_columns, landscape_rows = validate_grid_size(landscape_grid_size)
	if page_orientation == colorbynumber.constants.LANDSCAPE_ORIENTATION:
		columns = landscape_columns
		rows = landscape_rows
	elif page_orientation == colorbynumber.constants.PORTRAIT_ORIENTATION:
		columns = landscape_rows
		rows = landscape_columns
	else:
		raise ValueError(f"Unsupported page orientation: {page_orientation}")
	dimensions = (columns, rows)
	return dimensions
