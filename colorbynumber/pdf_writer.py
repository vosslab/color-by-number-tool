"""Single-page landscape Letter worksheet and color-key PDF writing."""

# Standard Library
import math
import pathlib
import dataclasses

# PIP3 modules
import numpy
import reportlab.pdfgen.canvas
import reportlab.lib.pagesizes
import reportlab.lib.colors

# local repo modules
import colorbynumber.constants
import colorbynumber.marker_color


POINTS_PER_INCH = 72.0
PAGE_MARGIN = 0.65 * POINTS_PER_INCH
KEY_GAP = 0.25 * POINTS_PER_INCH
KEY_WIDTH = 1.5 * POINTS_PER_INCH
KEY_COLUMNS = 2


@dataclasses.dataclass(frozen=True)
class PageLayout:
	"""Computed printable positions in PDF points."""

	page_width: float
	page_height: float
	margin: float
	grid_x: float
	grid_y: float
	grid_width: float
	grid_height: float
	cell_size: float
	key_x: float
	key_width: float


#============================================
def calculate_layout() -> PageLayout:
	"""Calculate a landscape Letter layout with square cells and a side key.

	Returns:
		The physical page, grid, and key dimensions in PDF points.
	"""
	page_width, page_height = reportlab.lib.pagesizes.landscape(
		reportlab.lib.pagesizes.letter
	)
	content_width = page_width - 2.0 * PAGE_MARGIN
	content_height = page_height - 2.0 * PAGE_MARGIN
	grid_available_width = content_width - KEY_GAP - KEY_WIDTH
	cell_size = min(
		grid_available_width / colorbynumber.constants.GRID_COLUMNS,
		content_height / colorbynumber.constants.GRID_ROWS,
	)
	grid_width = cell_size * colorbynumber.constants.GRID_COLUMNS
	grid_height = cell_size * colorbynumber.constants.GRID_ROWS
	grid_x = PAGE_MARGIN
	grid_y = PAGE_MARGIN + (content_height - grid_height) / 2.0
	key_x = grid_x + grid_width + KEY_GAP
	layout = PageLayout(
		page_width=page_width,
		page_height=page_height,
		margin=PAGE_MARGIN,
		grid_x=grid_x,
		grid_y=grid_y,
		grid_width=grid_width,
		grid_height=grid_height,
		cell_size=cell_size,
		key_x=key_x,
		key_width=KEY_WIDTH,
	)
	return layout


#============================================
def draw_header(pdf: reportlab.pdfgen.canvas.Canvas, layout: PageLayout) -> None:
	"""Draw the compact worksheet title and grid contract.

	Args:
		pdf: ReportLab canvas for the output page.
		layout: Computed page layout.
	"""
	title_y = layout.page_height - layout.margin - 12.0
	pdf.setFillColor(reportlab.lib.colors.black)
	pdf.setFont("Helvetica-Bold", 11.0)
	pdf.drawString(layout.grid_x, title_y, "43 x 30 COLOR BY NUMBER")
	pdf.setFont("Helvetica", 6.5)
	pdf.drawString(
		layout.grid_x,
		title_y - 10.0,
		"One marker code per square. Grid boxes are intentionally unfilled.",
	)
	pdf.setFont("Helvetica-Bold", 8.0)
	pdf.drawCentredString(
		layout.key_x + layout.key_width / 2.0,
		title_y,
		"COLOR KEY",
	)


#============================================
def draw_code_grid(
	pdf: reportlab.pdfgen.canvas.Canvas,
	layout: PageLayout,
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
) -> None:
	"""Draw the white 43 by 30 grid and one black code per cell.

	Args:
		pdf: ReportLab canvas for the output page.
		layout: Computed page layout.
		indices: Palette index for every grid square.
		palette: Available marker colors.
	"""
	columns = colorbynumber.constants.GRID_COLUMNS
	rows = colorbynumber.constants.GRID_ROWS
	pdf.setFillColor(reportlab.lib.colors.white)
	pdf.rect(
		layout.grid_x,
		layout.grid_y,
		layout.grid_width,
		layout.grid_height,
		stroke=0,
		fill=1,
	)
	pdf.setStrokeColor(reportlab.lib.colors.black)
	pdf.setLineWidth(0.35)
	for column in range(columns + 1):
		x_position = layout.grid_x + column * layout.cell_size
		pdf.line(x_position, layout.grid_y, x_position, layout.grid_y + layout.grid_height)
	for row in range(rows + 1):
		y_position = layout.grid_y + row * layout.cell_size
		pdf.line(layout.grid_x, y_position, layout.grid_x + layout.grid_width, y_position)

	font_size = min(5.2, layout.cell_size * 0.40)
	pdf.setFillColor(reportlab.lib.colors.black)
	pdf.setFont("Helvetica", font_size)
	baseline_offset = font_size * 0.35
	for row in range(rows):
		for column in range(columns):
			marker = palette[int(indices[row, column])]
			x_center = layout.grid_x + (column + 0.5) * layout.cell_size
			y_center = layout.grid_y + layout.grid_height - (row + 0.5) * layout.cell_size
			pdf.drawCentredString(x_center, y_center - baseline_offset, marker.code)


#============================================
def draw_color_key(
	pdf: reportlab.pdfgen.canvas.Canvas,
	layout: PageLayout,
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
) -> None:
	"""Draw colored key swatches for marker codes used by the worksheet.

	Args:
		pdf: ReportLab canvas for the output page.
		layout: Computed page layout.
		indices: Palette index for every grid square.
		palette: Available marker colors.
	"""
	counts = numpy.bincount(indices.reshape(-1), minlength=len(palette))
	used_entries = [
		(marker, int(count))
		for marker, count in zip(palette, counts, strict=True)
		if count > 0
	]
	rows_per_column = math.ceil(len(used_entries) / KEY_COLUMNS)
	item_height = min(18.0, layout.grid_height / rows_per_column)
	column_width = layout.key_width / KEY_COLUMNS
	swatch_size = min(10.0, item_height - 3.0)
	pdf.setFont("Helvetica", 5.4)
	for index, (marker, count) in enumerate(used_entries):
		column = index // rows_per_column
		row = index % rows_per_column
		x_position = layout.key_x + column * column_width
		y_top = layout.grid_y + layout.grid_height - row * item_height
		swatch_y = y_top - swatch_size
		red, green, blue = marker.rgb
		pdf.setFillColorRGB(red / 255.0, green / 255.0, blue / 255.0)
		pdf.setStrokeColor(reportlab.lib.colors.black)
		pdf.setLineWidth(0.3)
		pdf.rect(x_position, swatch_y, swatch_size, swatch_size, stroke=1, fill=1)
		pdf.setFillColor(reportlab.lib.colors.black)
		label = f"{marker.code} x{count}"
		pdf.drawString(x_position + swatch_size + 2.5, swatch_y + 2.0, label)


#============================================
def draw_footer(pdf: reportlab.pdfgen.canvas.Canvas, layout: PageLayout) -> None:
	"""Draw print and palette-accuracy guidance below the grid.

	Args:
		pdf: ReportLab canvas for the output page.
		layout: Computed page layout.
	"""
	footer_y = layout.margin + 12.0
	pdf.setFillColor(reportlab.lib.colors.black)
	pdf.setFont("Helvetica", 6.0)
	pdf.drawString(
		layout.grid_x,
		footer_y,
		"Print landscape at actual size. Key colors use chart RGB and approximate physical ink.",
	)


#============================================
def write_pdf(
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
	output_path: pathlib.Path,
) -> None:
	"""Write the complete single-page Letter PDF.

	Args:
		indices: Palette index for every grid square.
		palette: Available marker colors.
		output_path: Destination PDF path.
	"""
	layout = calculate_layout()
	page_size = (layout.page_width, layout.page_height)
	pdf = reportlab.pdfgen.canvas.Canvas(str(output_path), pagesize=page_size)
	draw_header(pdf, layout)
	draw_code_grid(pdf, layout, indices, palette)
	draw_color_key(pdf, layout, indices, palette)
	draw_footer(pdf, layout)
	pdf.showPage()
	pdf.save()
