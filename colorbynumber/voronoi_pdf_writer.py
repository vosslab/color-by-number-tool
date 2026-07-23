"""Prototype-only bounded-polygon Letter PDF writing."""

# Standard Library
import dataclasses
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
	"""Measured label-placement and overlap evidence for the numbered page."""

	font_size_points: float
	shifted_label_count: int
	best_effort_label_count: int
	total_shift_points: float
	maximum_shift_points: float
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
	domain: colorbynumber.voronoi_geometry.Domain,
	layout: VoronoiPageLayout,
) -> float:
	"""Choose one conservative common size from nominal polygon spacing."""
	nominal_points = domain.nominal_spacing * layout.scale
	font_size = min(MAXIMUM_CODE_FONT_SIZE, CODE_SIZE_FRACTION * nominal_points)
	return font_size


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
def _polygon_path(
	pdf: reportlab.pdfgen.canvas.Canvas,
	layout: VoronoiPageLayout,
	polygon: shapely.Polygon,
) -> reportlab.pdfgen.pathobject.PDFPathObject:
	"""Build one closed even-odd path from a Shapely polygon and its holes."""
	path = pdf.beginPath()
	for ring in (polygon.exterior, *polygon.interiors):
		coordinates = list(ring.coords)
		first_x, first_y = _pdf_vertex(layout, coordinates[0])
		path.moveTo(first_x, first_y)
		for vertex in coordinates[1:]:
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
	layout: VoronoiPageLayout,
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
) -> None:
	"""Draw white polygons with the square control's light-gray line policy."""
	pdf.setFillColor(reportlab.lib.colors.white)
	pdf.setStrokeColorRGB(BLANK_LINE_GRAY, BLANK_LINE_GRAY, BLANK_LINE_GRAY)
	pdf.setLineWidth(CELL_LINE_WIDTH)
	for region in regions:
		pdf.drawPath(_polygon_path(pdf, layout, region.polygon), stroke=1, fill=1, fillMode=0)
	border_color = reportlab.lib.colors.Color(
		BLANK_LINE_GRAY,
		BLANK_LINE_GRAY,
		BLANK_LINE_GRAY,
	)
	_draw_outer_border(pdf, layout, border_color)


#============================================
def _label_baseline(y_center: float, font_size: float) -> float:
	"""Return a baseline that centers Helvetica vertically on a label anchor."""
	baseline = colorbynumber.label_placement.centered_text_baseline(
		y_center, CODE_FONT_NAME, font_size
	)
	return baseline


#============================================
def _region_polygon_pdf(
	layout: VoronoiPageLayout,
	polygon: shapely.Polygon,
) -> shapely.Polygon:
	"""Transform one normalized printable region into physical PDF-point coordinates."""
	scaled = shapely.affinity.scale(
		polygon,
		xfact=layout.scale,
		yfact=layout.scale,
		origin=(0.0, 0.0),
	)
	pdf_polygon = shapely.affinity.translate(
		scaled,
		xoff=layout.polygon_x,
		yoff=layout.polygon_y,
	)
	return pdf_polygon


#============================================
def resolve_label_placements(
	domain: colorbynumber.voronoi_geometry.Domain,
	palette: list[colorbynumber.marker_color.MarkerColor],
	layout: VoronoiPageLayout,
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
) -> tuple[colorbynumber.label_placement.LabelPlacement, ...]:
	"""Resolve all Voronoi labels once for shared diagnostics and PDF drawing."""
	font_size = calculate_code_font_size(domain, layout)
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
def analyze_labels(
	domain: colorbynumber.voronoi_geometry.Domain,
	palette: list[colorbynumber.marker_color.MarkerColor],
	layout: VoronoiPageLayout,
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
) -> LabelDiagnostics:
	"""Resolve labels and measure their shifts plus final text-box overlap."""
	font_size = calculate_code_font_size(domain, layout)
	placements = resolve_label_placements(domain, palette, layout, regions)
	diagnostics = analyze_resolved_labels(font_size, placements)
	return diagnostics


#============================================
def analyze_resolved_labels(
	font_size: float,
	placements: tuple[colorbynumber.label_placement.LabelPlacement, ...],
) -> LabelDiagnostics:
	"""Measure diagnostics from the exact placements used by the numbered PDF page."""
	boxes = [placement.text_box for placement in placements]
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
		shifted_label_count=sum(not placement.used_centroid for placement in placements),
		best_effort_label_count=sum(
			placement.used_best_effort for placement in placements
		),
		total_shift_points=sum(placement.shift_distance_points for placement in placements),
		maximum_shift_points=max(
			(placement.shift_distance_points for placement in placements), default=0.0
		),
		overlap_pair_count=overlap_count,
	)
	return diagnostics


#============================================
def draw_numbered_page(
	pdf: reportlab.pdfgen.canvas.Canvas,
	domain: colorbynumber.voronoi_geometry.Domain,
	palette: list[colorbynumber.marker_color.MarkerColor],
	layout: VoronoiPageLayout,
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
	placements: tuple[colorbynumber.label_placement.LabelPlacement, ...],
) -> None:
	"""Draw black printable-region edges and the already-resolved codes."""
	pdf.setFillColor(reportlab.lib.colors.white)
	pdf.setStrokeColor(reportlab.lib.colors.black)
	pdf.setLineWidth(CELL_LINE_WIDTH)
	for region in regions:
		pdf.drawPath(_polygon_path(pdf, layout, region.polygon), stroke=1, fill=1, fillMode=0)
	_draw_outer_border(pdf, layout, reportlab.lib.colors.black)
	font_size = calculate_code_font_size(domain, layout)
	pdf.setFillColor(reportlab.lib.colors.black)
	pdf.setFont(CODE_FONT_NAME, font_size)
	for region, placement in zip(regions, placements, strict=True):
		marker = palette[region.palette_index]
		baseline = _label_baseline(placement.anchor[1], font_size)
		pdf.drawCentredString(placement.anchor[0], baseline, marker.code)


#============================================
def draw_reference_page(
	pdf: reportlab.pdfgen.canvas.Canvas,
	palette: list[colorbynumber.marker_color.MarkerColor],
	layout: VoronoiPageLayout,
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
) -> None:
	"""Draw the assigned palette color inside every printable region."""
	pdf.setStrokeColorRGB(0.25, 0.25, 0.25)
	pdf.setLineWidth(CELL_LINE_WIDTH)
	for region in regions:
		marker = palette[region.palette_index]
		red, green, blue = marker.rgb
		pdf.setFillColorRGB(red / 255.0, green / 255.0, blue / 255.0)
		pdf.drawPath(_polygon_path(pdf, layout, region.polygon), stroke=1, fill=1, fillMode=0)
	_draw_outer_border(pdf, layout, reportlab.lib.colors.black)


#============================================
def write_pdf(
	domain: colorbynumber.voronoi_geometry.Domain,
	palette: list[colorbynumber.marker_color.MarkerColor],
	page_orientation: str,
	output_path: pathlib.Path,
	regions: tuple[colorbynumber.render_regions.RenderRegion, ...],
) -> LabelDiagnostics:
	"""Write blank, numbered, and palette-reference printable-region pages.

	Args:
		domain: Normalized Voronoi domain.
		palette: Available marker colors.
		page_orientation: Resolved landscape or portrait orientation.
		output_path: Destination PDF path.
		regions: Concrete printable regions derived from Voronoi assignments.

	Returns:
		Measured label-fit diagnostics for the numbered page.
	"""
	colorbynumber.render_regions.validate_regions(regions, len(palette))
	layout = calculate_layout(page_orientation, domain)
	placements = resolve_label_placements(domain, palette, layout, regions)
	font_size = calculate_code_font_size(domain, layout)
	diagnostics = analyze_resolved_labels(font_size, placements)
	output_path.parent.mkdir(parents=True, exist_ok=True)
	page_size = (layout.page_width, layout.page_height)
	pdf = reportlab.pdfgen.canvas.Canvas(str(output_path), pagesize=page_size)
	pdf.setTitle("Voronoi color-by-number prototype pages")
	pdf.setAuthor("color-by-number-tool")
	pdf.setSubject("Blank, numbered, and palette-reference bounded polygons")
	pdf.setCreator("color-by-number-tool")
	draw_blank_page(pdf, layout, regions)
	pdf.showPage()
	draw_numbered_page(pdf, domain, palette, layout, regions, placements)
	pdf.showPage()
	draw_reference_page(pdf, palette, layout, regions)
	pdf.showPage()
	pdf.save()
	return diagnostics
