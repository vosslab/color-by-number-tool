"""Deterministic text summaries for one bounded-Voronoi conversion run."""

# Standard Library
import dataclasses
import math
import numbers
import pathlib

# local repo modules
import colorbynumber.voronoi_geometry
import colorbynumber.voronoi_prototype


#============================================
@dataclasses.dataclass(frozen=True)
class VoronoiRunSummary:
	"""The resolved inputs, outputs, and diagnostics for one Voronoi run."""

	input_path: pathlib.Path
	palette_path: pathlib.Path
	fit_mode: str
	page_orientation: str
	enhancement: str
	columns: int
	rows: int
	seed: int
	mean_delta_e_76: float
	maximum_delta_e_76: float
	seam_fallback_pixel_count: int
	polygon_fallback_count: int
	label_font_size_points: float
	shifted_label_count: int
	best_effort_label_count: int
	total_label_shift_points: float
	maximum_label_shift_points: float
	label_overlap_pair_count: int
	merge_regions: bool
	rendered_region_count: int

	def __post_init__(self) -> None:
		"""Reject malformed summary values before a durable output is written."""
		if isinstance(self.columns, bool) or not isinstance(self.columns, int):
			raise ValueError("Voronoi summary columns must be a positive integer")
		if isinstance(self.rows, bool) or not isinstance(self.rows, int):
			raise ValueError("Voronoi summary rows must be a positive integer")
		if self.columns <= 0 or self.rows <= 0:
			raise ValueError("Voronoi summary dimensions must be greater than zero")
		if isinstance(self.seed, bool) or not isinstance(self.seed, int):
			raise ValueError("Voronoi summary seed must be an integer")
		_validate_finite_metric("mean Delta E 76", self.mean_delta_e_76)
		_validate_finite_metric("maximum Delta E 76", self.maximum_delta_e_76)
		_validate_nonnegative_metric("mean Delta E 76", self.mean_delta_e_76)
		_validate_nonnegative_metric("maximum Delta E 76", self.maximum_delta_e_76)
		if self.maximum_delta_e_76 < self.mean_delta_e_76:
			raise ValueError(
				"Voronoi summary maximum Delta E 76 must be at least mean Delta E 76"
			)
		_validate_finite_metric("label font size", self.label_font_size_points)
		if self.label_font_size_points <= 0.0:
			raise ValueError("Voronoi summary label font size must be greater than zero")
		_validate_nonnegative_count(
			"seam fallback pixel count",
			self.seam_fallback_pixel_count,
		)
		_validate_nonnegative_count("polygon fallback count", self.polygon_fallback_count)
		_validate_nonnegative_count("shifted label count", self.shifted_label_count)
		_validate_nonnegative_count(
			"best-effort label count",
			self.best_effort_label_count,
		)
		_validate_finite_metric("total label shift", self.total_label_shift_points)
		_validate_nonnegative_metric("total label shift", self.total_label_shift_points)
		_validate_finite_metric("maximum label shift", self.maximum_label_shift_points)
		_validate_nonnegative_metric("maximum label shift", self.maximum_label_shift_points)
		_validate_nonnegative_count("label overlap pair count", self.label_overlap_pair_count)
		_validate_nonnegative_count("rendered region count", self.rendered_region_count)
		if self.rendered_region_count == 0:
			raise ValueError("Voronoi summary rendered region count must be greater than zero")
		if self.rendered_region_count > self.columns * self.rows:
			raise ValueError("Voronoi summary rendered region count exceeds the site count")
		if self.shifted_label_count > self.rendered_region_count:
			raise ValueError("Voronoi summary shifted label count exceeds rendered region count")
		if self.best_effort_label_count > self.rendered_region_count:
			raise ValueError("Voronoi summary best-effort label count exceeds rendered region count")
		if self.shifted_label_count == 0:
			if self.total_label_shift_points != 0.0 or self.maximum_label_shift_points != 0.0:
				raise ValueError(
					"Voronoi summary zero shifted labels require zero total and maximum label shift"
				)
		else:
			if self.total_label_shift_points <= 0.0 or self.maximum_label_shift_points <= 0.0:
				raise ValueError(
					"Voronoi summary shifted labels require positive total and maximum label shift"
				)
		if self.maximum_label_shift_points > self.total_label_shift_points:
			raise ValueError("Voronoi summary maximum label shift exceeds total label shift")


#============================================
def _validate_finite_metric(label: str, value: float) -> None:
	"""Require one real finite measurement in a generated summary."""
	if isinstance(value, bool) or not isinstance(value, numbers.Real):
		raise ValueError(f"Voronoi summary {label} must be a finite number")
	if not math.isfinite(value):
		raise ValueError(f"Voronoi summary {label} must be a finite number")


#============================================
def _validate_nonnegative_metric(label: str, value: float) -> None:
	"""Require one finite measurement that cannot be negative."""
	if value < 0.0:
		raise ValueError(f"Voronoi summary {label} must be nonnegative")


#============================================
def _validate_nonnegative_count(label: str, value: int) -> None:
	"""Require one nonnegative integer diagnostic count."""
	if isinstance(value, bool) or not isinstance(value, int):
		raise ValueError(f"Voronoi summary {label} must be a nonnegative integer")
	if value < 0:
		raise ValueError(f"Voronoi summary {label} must be a nonnegative integer")


#============================================
def write_summary(summary: VoronoiRunSummary, output_path: pathlib.Path) -> None:
	"""Write one clear, stable UTF-8 summary for a bounded-Voronoi conversion.

	Args:
		summary: Validated resolved conversion inputs and diagnostics.
		output_path: Destination text file.
	"""
	site_count = summary.columns * summary.rows
	rendered_region_count = summary.rendered_region_count
	attempt_budget = (
		colorbynumber.voronoi_prototype.HARD_CORE_ATTEMPT_MULTIPLIER * site_count
	)
	lines = [
		"Layout: voronoi",
		f"Input image: {summary.input_path}",
		f"Palette: {summary.palette_path}",
		f"Grid-derived sites: {summary.columns} columns x {summary.rows} rows",
		(
			"Voronoi polygons: "
			f"N={site_count} ({summary.columns} * {summary.rows})"
		),
		f"Merge same-color regions: {'enabled' if summary.merge_regions else 'disabled'}",
		f"Rendered regions: {rendered_region_count} (reduction: {site_count - rendered_region_count})",
		f"Fit mode: {summary.fit_mode}",
		f"Page orientation: {summary.page_orientation}",
		f"Color enhancement: {summary.enhancement}",
		"Distribution: hard-core Euclidean point spacing, then bounded Lloyd relaxation",
		(
			"Hard-core minimum distance (d/s): "
			f"{colorbynumber.voronoi_prototype.HARD_CORE_DISTANCE_RATIO:.2f}"
		),
		(
			"Hard-core candidate budget: "
			f"{colorbynumber.voronoi_prototype.HARD_CORE_ATTEMPT_MULTIPLIER}N "
			f"({attempt_budget} total uniform candidates)"
		),
		(
			"Hard-core exhaustion policy: fail the run without retry or repair "
			f"({colorbynumber.voronoi_geometry.HARD_CORE_ATTEMPT_POLICY})"
		),
		(
			"Bounded Lloyd relaxation: "
			f"{colorbynumber.voronoi_prototype.LLOYD_STEP_COUNT} rounds at alpha "
			f"{colorbynumber.voronoi_prototype.LLOYD_ALPHA:.2f}"
		),
		f"Internal generated/replay seed: {summary.seed}",
		"Polygon sampling: average fitted-raster pixel centers owned by each polygon",
		"Zero-pixel polygon policy: sample the fitted pixel center nearest its owned site",
		"Numerical seam policy: assign an unowned pixel to its nearest site",
		"Matching metric: CIE Delta E 76",
		f"Mean Delta E 76: {summary.mean_delta_e_76:.3f}",
		f"Maximum Delta E 76: {summary.maximum_delta_e_76:.3f}",
		f"Numerical seam fallback pixels: {summary.seam_fallback_pixel_count}",
		f"Zero-pixel polygon fallbacks: {summary.polygon_fallback_count}",
		f"Label font size (points): {summary.label_font_size_points:.3f}",
		f"Shifted labels: {summary.shifted_label_count}",
		f"Best-effort labels: {summary.best_effort_label_count}",
		f"Total label shift (points): {summary.total_label_shift_points:.3f}",
		f"Maximum label shift (points): {summary.maximum_label_shift_points:.3f}",
		f"Label overlap pairs: {summary.label_overlap_pair_count}",
	]
	text = "\n".join(lines) + "\n"
	output_path.write_text(text, encoding="utf-8")
