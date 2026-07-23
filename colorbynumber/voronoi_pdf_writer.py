"""Prototype-only bounded-polygon Letter PDF writing."""

# Standard Library
import pathlib
import dataclasses

# PIP3 modules
import numpy
import shapely
import reportlab.lib.colors
import reportlab.lib.pagesizes
import reportlab.pdfbase.pdfmetrics
import reportlab.pdfgen.canvas

# local repo modules
import colorbynumber.constants
import colorbynumber.marker_color
import colorbynumber.voronoi_geometry


POINTS_PER_INCH = 72.0
PAGE_MARGIN = 0.6 * POINTS_PER_INCH
CELL_LINE_WIDTH = 0.3
OUTER_LINE_WIDTH = 0.7
BLANK_LINE_GRAY = 0.72
CODE_FONT_NAME = "Helvetica"
MAXIMUM_CODE_FONT_SIZE = 6.5
CODE_SIZE_FRACTION = 0.40


#============================================
@dataclasses.dataclass(frozen=True)
class VoronoiPageLayout:
	"""Prototype polygon placement in PDF points."""

	page_width: float
	page_height: float
	page_orientation: str
	polygon_x: float
	polygon_y: float
	polygon_width: float
	polygon_height: float
	scale: float


#============================================
@dataclasses.dataclass(frozen=True)
class LabelDiagnostics:
	"""Measured first-prototype polygon-centroid label fit limitations."""

	font_size_points: float
	outside_owned_cell_count: int
	overlap_pair_count: int


#============================================
def calculate_layout(
	page_orientation: str,
	domain: colorbynumber.voronoi_geometry.Domain,
) -> VoronoiPageLayout:
	"""Fit the normalized domain inside Letter pages with 0.6-inch margins."""
	if page_orientation == colorbynumber.constants.LANDSCAPE_ORIENTATION:
		page_size = reportlab.lib.pagesizes.landscape(reportlab.lib.pagesizes.letter)
	elif page_orientation == colorbynumber.constants.PORTRAIT_ORIENTATION:
		page_size = reportlab.lib.pagesizes.portrait(reportlab.lib.pagesizes.letter)
	else:
		raise ValueError(f"Unsupported page orientation: {page_orientation}")
	page_width, page_height = page_size
	available_width = page_width - 2.0 * PAGE_MARGIN
	available_height = page_height - 2.0 * PAGE_MARGIN
	scale = min(available_width / domain.width, available_height / domain.height)
	polygon_width = scale * domain.width
	polygon_height = scale * domain.height
	polygon_x = (page_width - polygon_width) / 2.0
	polygon_y = (page_height - polygon_height) / 2.0
	layout = VoronoiPageLayout(
		page_width=page_width,
		page_height=page_height,
		page_orientation=page_orientation,
		polygon_x=polygon_x,
		polygon_y=polygon_y,
		polygon_width=polygon_width,
		polygon_height=polygon_height,
		scale=scale,
	)
	return layout


#============================================
def calculate_code_font_size(
	partition: colorbynumber.voronoi_geometry.Partition,
	layout: VoronoiPageLayout,
) -> float:
	"""Choose one conservative common size from nominal polygon spacing."""
	nominal_points = partition.domain.nominal_spacing * layout.scale
	font_size = min(MAXIMUM_CODE_FONT_SIZE, CODE_SIZE_FRACTION * nominal_points)
	return font_size


#============================================
def _validate_assignments(
	partition: colorbynumber.voronoi_geometry.Partition,
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
) -> None:
	"""Validate one-dimensional site-ordered palette assignments."""
	if not isinstance(indices, numpy.ndarray):
		raise ValueError("Polygon palette assignments must be a NumPy array")
	if indices.ndim != 1 or indices.size == 0:
		raise ValueError("Polygon palette assignments must be a nonempty one-dimensional array")
	if not numpy.issubdtype(indices.dtype, numpy.integer):
		raise ValueError("Polygon palette assignments must be integers")
	if indices.size != partition.domain.site_count:
		raise ValueError("Polygon palette assignments must follow stable site order")
	if not palette:
		raise ValueError("Polygon palette must not be empty")
	if numpy.any(indices < 0) or numpy.any(indices >= len(palette)):
		raise ValueError("Polygon palette assignments must identify available colors")


#============================================
def _pdf_vertex(
	layout: VoronoiPageLayout,
	vertex: tuple[float, float],
) -> tuple[float, float]:
	"""Map one domain vertex to PDF coordinates."""
	x = layout.polygon_x + vertex[0] * layout.scale
	y = layout.polygon_y + vertex[1] * layout.scale
	point = (x, y)
	return point


#============================================
def _cell_path(
	pdf: reportlab.pdfgen.canvas.Canvas,
	layout: VoronoiPageLayout,
	cell: colorbynumber.voronoi_geometry.Cell,
) -> reportlab.pdfgen.pathobject.PDFPathObject:
	"""Build one closed ReportLab path from canonical open-ring vertices."""
	path = pdf.beginPath()
	first_x, first_y = _pdf_vertex(layout, cell.vertices[0])
	path.moveTo(first_x, first_y)
	for vertex in cell.vertices[1:]:
		x, y = _pdf_vertex(layout, vertex)
		path.lineTo(x, y)
	path.close()
	return path


#============================================
def _draw_outer_border(
	pdf: reportlab.pdfgen.canvas.Canvas,
	layout: VoronoiPageLayout,
	color: reportlab.lib.colors.Color,
) -> None:
	"""Draw the bounded-domain border at the square control's line weight."""
	pdf.setStrokeColor(color)
	pdf.setLineWidth(OUTER_LINE_WIDTH)
	pdf.rect(
		layout.polygon_x,
		layout.polygon_y,
		layout.polygon_width,
		layout.polygon_height,
		stroke=1,
		fill=0,
	)


#============================================
def draw_blank_page(
	pdf: reportlab.pdfgen.canvas.Canvas,
	partition: colorbynumber.voronoi_geometry.Partition,
	layout: VoronoiPageLayout,
) -> None:
	"""Draw white polygons with the square control's light-gray line policy."""
	pdf.setFillColor(reportlab.lib.colors.white)
	pdf.setStrokeColorRGB(BLANK_LINE_GRAY, BLANK_LINE_GRAY, BLANK_LINE_GRAY)
	pdf.setLineWidth(CELL_LINE_WIDTH)
	for cell in partition.cells:
		path = _cell_path(pdf, layout, cell)
		pdf.drawPath(path, stroke=1, fill=1)
	border_color = reportlab.lib.colors.Color(
		BLANK_LINE_GRAY,
		BLANK_LINE_GRAY,
		BLANK_LINE_GRAY,
	)
	_draw_outer_border(pdf, layout, border_color)


#============================================
def _label_baseline(y_center: float, font_size: float) -> float:
	"""Return a baseline that centers Helvetica vertically on a label anchor."""
	ascent = reportlab.pdfbase.pdfmetrics.getAscent(CODE_FONT_NAME) * font_size / 1000.0
	descent = reportlab.pdfbase.pdfmetrics.getDescent(CODE_FONT_NAME) * font_size / 1000.0
	baseline = y_center - (ascent + descent) / 2.0
	return baseline


#============================================
def _cell_centroid(
	cell: colorbynumber.voronoi_geometry.Cell,
) -> tuple[float, float]:
	"""Return the Shapely area centroid of one authoritative owned polygon."""
	polygon = shapely.Polygon(cell.vertices)
	centroid = polygon.centroid
	anchor = (centroid.x, centroid.y)
	return anchor


#============================================
def _label_box_domain(
	layout: VoronoiPageLayout,
	anchor: tuple[float, float],
	code: str,
	font_size: float,
) -> shapely.Polygon:
	"""Return one polygon-centroid text box in normalized domain units."""
	width_points = reportlab.pdfbase.pdfmetrics.stringWidth(
		code,
		CODE_FONT_NAME,
		font_size,
	)
	anchor_x, anchor_y = anchor
	y_center = layout.polygon_y + anchor_y * layout.scale
	baseline = _label_baseline(y_center, font_size)
	ascent = reportlab.pdfbase.pdfmetrics.getAscent(CODE_FONT_NAME) * font_size / 1000.0
	descent = reportlab.pdfbase.pdfmetrics.getDescent(CODE_FONT_NAME) * font_size / 1000.0
	minimum_x = anchor_x - width_points / (2.0 * layout.scale)
	maximum_x = anchor_x + width_points / (2.0 * layout.scale)
	minimum_y = (baseline + descent - layout.polygon_y) / layout.scale
	maximum_y = (baseline + ascent - layout.polygon_y) / layout.scale
	box = shapely.box(minimum_x, minimum_y, maximum_x, maximum_y)
	return box


#============================================
def analyze_labels(
	partition: colorbynumber.voronoi_geometry.Partition,
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
	layout: VoronoiPageLayout,
) -> LabelDiagnostics:
	"""Measure polygon-centroid code containment and text-box overlap."""
	_validate_assignments(partition, indices, palette)
	font_size = calculate_code_font_size(partition, layout)
	boxes: list[shapely.Polygon] = []
	outside_count = 0
	for cell in partition.cells:
		marker = palette[int(indices[cell.site_identifier])]
		anchor = _cell_centroid(cell)
		box = _label_box_domain(layout, anchor, marker.code, font_size)
		boxes.append(box)
		cell_polygon = shapely.Polygon(cell.vertices)
		covered = cell_polygon.buffer(partition.domain.coordinate_tolerance).covers(box)
		if not covered:
			outside_count += 1
	box_array = numpy.asarray(boxes, dtype=object)
	query_pairs = shapely.STRtree(box_array).query(box_array, predicate="intersects")
	overlap_count = 0
	for first, second in zip(query_pairs[0], query_pairs[1], strict=True):
		if first >= second:
			continue
		if boxes[int(first)].intersection(boxes[int(second)]).area > 0.0:
			overlap_count += 1
	diagnostics = LabelDiagnostics(
		font_size_points=font_size,
		outside_owned_cell_count=outside_count,
		overlap_pair_count=overlap_count,
	)
	return diagnostics


#============================================
def draw_numbered_page(
	pdf: reportlab.pdfgen.canvas.Canvas,
	partition: colorbynumber.voronoi_geometry.Partition,
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
	layout: VoronoiPageLayout,
) -> None:
	"""Draw black polygon edges and codes at owned-polygon area centroids."""
	pdf.setFillColor(reportlab.lib.colors.white)
	pdf.setStrokeColor(reportlab.lib.colors.black)
	pdf.setLineWidth(CELL_LINE_WIDTH)
	for cell in partition.cells:
		path = _cell_path(pdf, layout, cell)
		pdf.drawPath(path, stroke=1, fill=1)
	_draw_outer_border(pdf, layout, reportlab.lib.colors.black)
	font_size = calculate_code_font_size(partition, layout)
	pdf.setFillColor(reportlab.lib.colors.black)
	pdf.setFont(CODE_FONT_NAME, font_size)
	for cell in partition.cells:
		marker = palette[int(indices[cell.site_identifier])]
		anchor_x, anchor_y = _cell_centroid(cell)
		x_center = layout.polygon_x + anchor_x * layout.scale
		y_center = layout.polygon_y + anchor_y * layout.scale
		baseline = _label_baseline(y_center, font_size)
		pdf.drawCentredString(x_center, baseline, marker.code)


#============================================
def draw_reference_page(
	pdf: reportlab.pdfgen.canvas.Canvas,
	partition: colorbynumber.voronoi_geometry.Partition,
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
	layout: VoronoiPageLayout,
) -> None:
	"""Draw the assigned palette color inside every owned polygon."""
	pdf.setStrokeColorRGB(0.25, 0.25, 0.25)
	pdf.setLineWidth(CELL_LINE_WIDTH)
	for cell in partition.cells:
		marker = palette[int(indices[cell.site_identifier])]
		red, green, blue = marker.rgb
		pdf.setFillColorRGB(red / 255.0, green / 255.0, blue / 255.0)
		path = _cell_path(pdf, layout, cell)
		pdf.drawPath(path, stroke=1, fill=1)
	_draw_outer_border(pdf, layout, reportlab.lib.colors.black)


#============================================
def write_pdf(
	partition: colorbynumber.voronoi_geometry.Partition,
	indices: numpy.ndarray,
	palette: list[colorbynumber.marker_color.MarkerColor],
	page_orientation: str,
	output_path: pathlib.Path,
) -> LabelDiagnostics:
	"""Write blank, numbered, and palette-reference prototype polygon pages."""
	_validate_assignments(partition, indices, palette)
	layout = calculate_layout(page_orientation, partition.domain)
	diagnostics = analyze_labels(partition, indices, palette, layout)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	page_size = (layout.page_width, layout.page_height)
	pdf = reportlab.pdfgen.canvas.Canvas(str(output_path), pagesize=page_size)
	pdf.setTitle("Voronoi color-by-number prototype pages")
	pdf.setAuthor("color-by-number-tool")
	pdf.setSubject("Blank, numbered, and palette-reference bounded polygons")
	pdf.setCreator("color-by-number-tool")
	draw_blank_page(pdf, partition, layout)
	pdf.showPage()
	draw_numbered_page(pdf, partition, indices, palette, layout)
	pdf.showPage()
	draw_reference_page(pdf, partition, indices, palette, layout)
	pdf.showPage()
	pdf.save()
	return diagnostics
