"""Single-page Letter worksheet and color-key PDF writing."""

# Standard Library
import dataclasses
import math
import pathlib

# PIP3 modules
import numpy
import reportlab.lib.colors
import reportlab.lib.pagesizes
import reportlab.pdfbase.pdfmetrics
import reportlab.pdfgen.canvas
import shapely
import shapely.affinity

# local repo modules
import colorbynumber.constants
import colorbynumber.label_placement
import colorbynumber.marker_color
import colorbynumber.render_regions


POINTS_PER_INCH = 72.0
PAGE_MARGIN = 0.65 * POINTS_PER_INCH
KEY_GAP = 0.25 * POINTS_PER_INCH
KEY_WIDTH = 1.7 * POINTS_PER_INCH
KEY_COLUMNS = 2
KEY_HEADER_HEIGHT = 14.0
CODE_FONT_NAME = "Helvetica-Bold"
MAX_CODE_FONT_SIZE = 5.4
CODE_WIDTH_FRACTION = 0.78


@dataclasses.dataclass(frozen=True)
class PageLayout:
	"""Computed printable positions in PDF points."""

	page_width: float
	page_height: float
	page_orientation: str
	columns: int
	rows: int
	margin: float
	grid_x: float
	grid_y: float
	grid_width: float
	grid_height: float
	cell_size: float
	key_x: float
	key_width: float


#============================================
def calculate_layout(
	page_orientation: str,
	columns: int,
	rows: int,
) -> PageLayout:
	"""Calculate a Letter layout with square cells and a side key.

	Args:
		page_orientation: Resolved landscape or portrait orientation.
		columns: Number of grid columns.
		rows: Number of grid rows.

	Returns:
		The physical page, grid, and key dimensions in PDF points.

	Raises:
		ValueError: The page orientation is not supported.
	"""
	if page_orientation == colorbynumber.constants.LANDSCAPE_ORIENTATION:
		page_size = reportlab.lib.pagesizes.landscape(reportlab.lib.pagesizes.letter)
	elif page_orientation == colorbynumber.constants.PORTRAIT_ORIENTATION:
		page_size = reportlab.lib.pagesizes.portrait(reportlab.lib.pagesizes.letter)
	else:
		raise ValueError(f"Unsupported page orientation: {page_orientation}")
	page_width, page_height = page_size
	content_width = page_width - 2.0 * PAGE_MARGIN
	content_height = page_height - 2.0 * PAGE_MARGIN
	grid_available_width = content_width - KEY_GAP - KEY_WIDTH
	cell_size = min(
		grid_available_width / columns,
		content_height / rows,
	)
	grid_width = cell_size * columns
	grid_height = cell_size * rows
	grid_x = PAGE_MARGIN
	grid_y = PAGE_MARGIN + (content_height - grid_height) / 2.0
	key_x = grid_x + grid_width + KEY_GAP
	layout = PageLayout(
		page_width=page_width,
		page_height=page_height,
		page_orientation=page_orientation,
		columns=columns,
		rows=rows,
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
def calculate_code_font_size(
	layout: PageLayout,
	palette: list[colorbynumber.marker_color.MarkerColor],
) -> float:
	"""Return one readable font size that fits every marker code.

	Args:
		layout: Computed page layout.
		palette: Available marker colors.

	Returns:
		The largest permitted common font size that fits every code.
	"""
	maximum_width = max(
		reportlab.pdfbase.pdfmetrics.stringWidth(
			marker.code,
			CODE_FONT_NAME,
			MAX_CODE_FONT_SIZE,
		)
		for marker in palette
	)
	available_width = layout.cell_size * CODE_WIDTH_FRACTION
	if maximum_width > available_width:
		font_size = MAX_CODE_FONT_SIZE * available_width / maximum_width
	else:
		font_size = MAX_CODE_FONT_SIZE
	return font_size


#============================================
def draw_header(
	pdf: reportlab.pdfgen.canvas.Canvas,
	layout: PageLayout,
) -> None:
	"""Draw the compact worksheet title and grid contract.

	Args:
		pdf: ReportLab canvas for the output page.
		layout: Computed page layout.
	"""
	title_y = layout.page_height - layout.margin - 12.0
	pdf.setFillColor(reportlab.lib.colors.black)
	pdf.setFont("Helvetica-Bold", 11.0)
	pdf.drawString(
		layout.grid_x,
		title_y,
		f"{layout.columns} x {layout.rows} COLOR BY NUMBER",
	)
	pdf.setFont("Helvetica", 6.5)
	pdf.drawString(
		layout.grid_x,
		title_y - 10.0,
		"One marker code per printable region. Shapes are intentionally unfilled.",
	)
	header_y = title_y - 3.0
	pdf.setFillColor(reportlab.lib.colors.black)
	pdf.rect(
		layout.key_x,
		header_y,
		layout.key_width,
		KEY_HEADER_HEIGHT,
		stroke=0,
		fill=1,
	)
	pdf.setFillColor(reportlab.lib.colors.white)
	pdf.setFont("Helvetica-Bold", 7.2)
	key_title_baseline = colorbynumber.label_placement.centered_text_baseline(
		header_y + KEY_HEADER_HEIGHT / 2.0,
		"Helvetica-Bold",
		7.2,
	)
	pdf.drawCentredString(
		layout.key_x + layout.key_width / 2.0,
		key_title_baseline,
		"MARKER KEY",
	)


#============================================
def _region_path(
	pdf: reportlab.pdfgen.canvas.Canvas,
	layout: PageLayout,
	polygon: shapely.Polygon,
) -> reportlab.pdfgen.pathobject.PDFPathObject:
	"""Map a normalized square-grid polygon, including holes, to a PDF path."""
	path = pdf.beginPath()
	for ring in (polygon.exterior, *polygon.interiors):
		coordinates = list(ring.coords)
		first_x, first_y = coordinates[0]
		path.moveTo(
			layout.grid_x + first_x * layout.cell_size,
			layout.grid_y + first_y * layout.cell_size,
		)
		for x, y in coordinates[1:]:
			path.lineTo(layout.grid_x + x * layout.cell_size, layout.grid_y + y * layout.cell_size)
		path.close()
	return path


#============================================
def _region_polygon_pdf(
	layout: PageLayout,
	polygon: shapely.Polygon,
) -> shapely.Polygon:
	"""Transform one normalized square region into physical PDF-point coordinates."""
	scaled = shapely.affinity.scale(
		polygon,
		xfact=layout.cell_size,
		yfact=layout.cell_size,
		origin=(0.0, 0.0),
	)
	pdf_polygon = shapely.affinity.translate(scaled, xoff=layout.grid_x, yoff=layout.grid_y)
	return pdf_polygon


#============================================
def resolve_code_placements(
	layout: PageLayout,
	palette: list[colorbynumber.marker_color.MarkerColor],
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
) -> tuple[colorbynumber.label_placement.LabelPlacement, ...]:
	"""Resolve every square-region code once in shared physical PDF coordinates."""
	font_size = calculate_code_font_size(layout, palette)
	placements = tuple(
		colorbynumber.label_placement.place_label(
			_region_polygon_pdf(layout, region.polygon),
			palette[region.palette_index].code,
			CODE_FONT_NAME,
			font_size,
			region.member_identifiers,
		)
		for region in regions
	)
	return placements


#============================================
def draw_code_regions(
	pdf: reportlab.pdfgen.canvas.Canvas,
	layout: PageLayout,
	palette: list[colorbynumber.marker_color.MarkerColor],
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
) -> None:
	"""Draw one outlined, numbered printable shape for each region."""
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
	pdf.setLineWidth(0.3)
	for region in regions:
		pdf.drawPath(
			_region_path(pdf, layout, region.polygon),
			stroke=1,
			fill=1,
			fillMode=0,
		)
	pdf.setLineWidth(0.7)
	pdf.rect(
		layout.grid_x,
		layout.grid_y,
		layout.grid_width,
		layout.grid_height,
		stroke=1,
		fill=0,
	)
	font_size = calculate_code_font_size(layout, palette)
	placements = resolve_code_placements(layout, palette, regions)
	pdf.setFillColor(reportlab.lib.colors.black)
	pdf.setFont(CODE_FONT_NAME, font_size)
	for region, placement in zip(regions, placements, strict=True):
		baseline = colorbynumber.label_placement.centered_text_baseline(
			placement.anchor[1], CODE_FONT_NAME, font_size
		)
		pdf.drawCentredString(
			placement.anchor[0],
			baseline,
			palette[region.palette_index].code,
		)


#============================================
def draw_blank_regions(
	pdf: reportlab.pdfgen.canvas.Canvas,
	layout: PageLayout,
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
	line_gray: float = 0.72,
) -> None:
	"""Draw a code-free printable-region worksheet page."""
	pdf.setFillColor(reportlab.lib.colors.white)
	pdf.rect(
		layout.grid_x,
		layout.grid_y,
		layout.grid_width,
		layout.grid_height,
		stroke=0,
		fill=1,
	)
	pdf.setStrokeColorRGB(line_gray, line_gray, line_gray)
	pdf.setLineWidth(0.3)
	for region in regions:
		pdf.drawPath(
			_region_path(pdf, layout, region.polygon),
			stroke=1,
			fill=1,
			fillMode=0,
		)
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
def draw_color_key(
	pdf: reportlab.pdfgen.canvas.Canvas,
	layout: PageLayout,
	palette: list[colorbynumber.marker_color.MarkerColor],
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
) -> None:
	"""Draw colored key swatches for marker codes used by the worksheet.

	Args:
		pdf: ReportLab canvas for the output page.
		layout: Computed page layout.
		palette: Available marker colors.
		regions: Concrete printable regions counted by marker code.
	"""
	counts = numpy.bincount([region.palette_index for region in regions], minlength=len(palette))
	used_entries = [
		(marker, int(count))
		for marker, count in zip(palette, counts, strict=True)
		if count > 0
	]
	rows_per_column = math.ceil(len(used_entries) / KEY_COLUMNS)
	item_height = min(22.0, layout.grid_height / rows_per_column)
	column_width = layout.key_width / KEY_COLUMNS
	swatch_size = min(11.0, item_height - 4.0)
	for index, (marker, count) in enumerate(used_entries):
		column = index // rows_per_column
		row = index % rows_per_column
		x_position = layout.key_x + column * column_width
		y_top = layout.grid_y + layout.grid_height - row * item_height
		y_center = y_top - item_height / 2.0
		swatch_y = y_center - swatch_size / 2.0
		red, green, blue = marker.rgb
		pdf.setFillColorRGB(red / 255.0, green / 255.0, blue / 255.0)
		pdf.setStrokeColor(reportlab.lib.colors.black)
		pdf.setLineWidth(0.3)
		pdf.rect(x_position, swatch_y, swatch_size, swatch_size, stroke=1, fill=1)
		pdf.setFillColor(reportlab.lib.colors.black)
		text_x = x_position + swatch_size + 2.5
		pdf.setFont("Helvetica-Bold", 5.4)
		pdf.drawString(text_x, y_center + 0.5, f"{marker.code}  x{count}")
		pdf.setFont("Helvetica", 4.3)
		pdf.setFillColorRGB(0.25, 0.25, 0.25)
		pdf.drawString(text_x, y_center - 5.2, marker.name)


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
		(
			f"Print {layout.page_orientation} at actual size. "
			"Key colors use chart RGB and approximate physical ink."
		),
	)


#============================================
def write_pdf(
	palette: list[colorbynumber.marker_color.MarkerColor],
	page_orientation: str,
	columns: int,
	rows: int,
	output_path: pathlib.Path,
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
) -> None:
	"""Write the complete single-page Letter PDF from concrete render regions.

	Args:
		palette: Available marker colors.
		page_orientation: Resolved landscape or portrait orientation.
		columns: Number of square columns.
		rows: Number of square rows.
		output_path: Destination PDF path.
		regions: Concrete printable regions derived from square assignments.
	"""
	layout = calculate_layout(page_orientation, columns, rows)
	colorbynumber.render_regions.validate_regions(regions, len(palette))
	page_size = (layout.page_width, layout.page_height)
	pdf = reportlab.pdfgen.canvas.Canvas(str(output_path), pagesize=page_size)
	pdf.setTitle(f"{columns} x {rows} color-by-number worksheet")
	pdf.setAuthor("color-by-number-tool")
	pdf.setSubject("Printable marker-code grid with an Aoartix marker key")
	pdf.setCreator("color-by-number-tool")
	draw_header(pdf, layout)
	draw_code_regions(pdf, layout, palette, regions)
	draw_color_key(pdf, layout, palette, regions)
	draw_footer(pdf, layout)
	pdf.showPage()
	pdf.save()
