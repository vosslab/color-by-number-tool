"""Full-page, grid-only Letter PDF writing."""

# Standard Library
import pathlib

# PIP3 modules
import numpy
import reportlab.lib.colors
import reportlab.lib.pagesizes
import reportlab.pdfgen.canvas

# local repo modules
import colorbynumber.constants
import colorbynumber.marker_color
import colorbynumber.pdf_writer


GRID_ONLY_MARGIN = 0.6 * colorbynumber.pdf_writer.POINTS_PER_INCH
BLANK_GRID_GRAY = 0.72


#============================================
def calculate_layout(
	page_orientation: str,
	columns: int,
	rows: int,
) -> colorbynumber.pdf_writer.PageLayout:
	"""Calculate the largest centered square grid inside 0.6-inch margins.

	Args:
		page_orientation: Resolved landscape or portrait orientation.
		columns: Number of grid columns.
		rows: Number of grid rows.

	Returns:
		The full-page grid dimensions in PDF points.

	Raises:
		ValueError: The orientation or grid dimensions are invalid.
	"""
	if columns <= 0 or rows <= 0:
		raise ValueError("Grid dimensions must be greater than zero")
	if page_orientation == colorbynumber.constants.LANDSCAPE_ORIENTATION:
		page_size = reportlab.lib.pagesizes.landscape(reportlab.lib.pagesizes.letter)
	elif page_orientation == colorbynumber.constants.PORTRAIT_ORIENTATION:
		page_size = reportlab.lib.pagesizes.portrait(reportlab.lib.pagesizes.letter)
	else:
		raise ValueError(f"Unsupported page orientation: {page_orientation}")
	page_width, page_height = page_size
	available_width = page_width - 2.0 * GRID_ONLY_MARGIN
	available_height = page_height - 2.0 * GRID_ONLY_MARGIN
	cell_size = min(available_width / columns, available_height / rows)
	grid_width = cell_size * columns
	grid_height = cell_size * rows
	grid_x = (page_width - grid_width) / 2.0
	grid_y = (page_height - grid_height) / 2.0
	layout = colorbynumber.pdf_writer.PageLayout(
		page_width=page_width,
		page_height=page_height,
		page_orientation=page_orientation,
		columns=columns,
		rows=rows,
		margin=GRID_ONLY_MARGIN,
		grid_x=grid_x,
		grid_y=grid_y,
		grid_width=grid_width,
		grid_height=grid_height,
		cell_size=cell_size,
		key_x=page_width,
		key_width=0.0,
	)
	return layout


#============================================
def draw_blank_grid(
	pdf: reportlab.pdfgen.canvas.Canvas,
	layout: colorbynumber.pdf_writer.PageLayout,
) -> None:
	"""Draw a light-gray grid with no marker codes.

	Args:
		pdf: ReportLab canvas for the output page.
		layout: Computed full-page grid layout.
	"""
	pdf.setFillColor(reportlab.lib.colors.white)
	pdf.rect(
		layout.grid_x,
		layout.grid_y,
		layout.grid_width,
		layout.grid_height,
		stroke=0,
		fill=1,
	)
	pdf.setStrokeColorRGB(BLANK_GRID_GRAY, BLANK_GRID_GRAY, BLANK_GRID_GRAY)
	pdf.setLineWidth(0.3)
	for column in range(layout.columns + 1):
		x_position = layout.grid_x + column * layout.cell_size
		pdf.line(x_position, layout.grid_y, x_position, layout.grid_y + layout.grid_height)
	for row in range(layout.rows + 1):
		y_position = layout.grid_y + row * layout.cell_size
		pdf.line(layout.grid_x, y_position, layout.grid_x + layout.grid_width, y_position)
	pdf.setLineWidth(0.7)
	pdf.rect(
		layout.grid_x,
		layout.grid_y,
		layout.grid_width,
		layout.grid_height,
		stroke=1,
		fill=0,
	)


#============================================
def write_pdf(
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
	page_orientation: str,
	output_path: pathlib.Path,
) -> None:
	"""Write aligned blank-artwork and numbered-reference Letter pages.

	Args:
		indices: Palette index for every grid square.
		palette: Available marker colors.
		page_orientation: Resolved landscape or portrait orientation.
		output_path: Destination PDF path.
	"""
	rows, columns = indices.shape
	layout = calculate_layout(page_orientation, columns, rows)
	page_size = (layout.page_width, layout.page_height)
	pdf = reportlab.pdfgen.canvas.Canvas(str(output_path), pagesize=page_size)
	pdf.setTitle(f"{columns} x {rows} color-by-number artwork pages")
	pdf.setAuthor("color-by-number-tool")
	pdf.setSubject("Aligned blank artwork grid and numbered marker-code reference")
	pdf.setCreator("color-by-number-tool")
	draw_blank_grid(pdf, layout)
	pdf.showPage()
	colorbynumber.pdf_writer.draw_code_grid(pdf, layout, indices, palette)
	pdf.showPage()
	pdf.save()
