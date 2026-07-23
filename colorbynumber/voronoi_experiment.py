"""Metrics, configuration digests, and artifacts for Voronoi experiments."""

# Standard Library
import json
import math
import time
import hashlib
import pathlib
import platform
import dataclasses

# PIP3 modules
import numpy
import shapely

# local repo modules
import colorbynumber.voronoi_metrics
import colorbynumber.voronoi_geometry


CONFIGURATION_SCHEMA_VERSION = 6
ARTIFACT_SCHEMA_VERSION = 4


#============================================
@dataclasses.dataclass(frozen=True)
class SiteGenerationResult:
	"""Raw generated sites and the disjoint generation-phase duration."""

	sites: tuple[colorbynumber.voronoi_geometry.Site, ...]
	generation_seconds: float


#============================================
def generate_sites(
	domain: colorbynumber.voronoi_geometry.Domain,
	generator_family: str,
	seed: int | None,
	*,
	jitter_fraction: float | None = None,
	hard_core_minimum_distance_ratio: float | None = None,
	hard_core_attempt_budget: int | None = None,
) -> SiteGenerationResult:
	"""Generate raw experiment sites and time only that generator boundary.

	Args:
		domain: Normalized experiment domain.
		generator_family: Grid, uniform, stratified-jitter, or hard-core family.
		seed: Replay seed for stochastic sites, or None for the grid control.
		jitter_fraction: Fraction of each stratum spanned by jitter.
		hard_core_minimum_distance_ratio: Minimum center distance divided by spacing.
		hard_core_attempt_budget: Total uniform-candidate draw budget.

	Returns:
		Raw sites plus their single-run generation duration.

	Raises:
		ValueError: The generator family and seed combination is invalid.
	"""
	generation_start = time.perf_counter()
	if generator_family == "grid":
		if seed is not None:
			raise ValueError("The grid control requires seed None")
		_require_unused_generator_parameters(
			jitter_fraction,
			hard_core_minimum_distance_ratio,
			hard_core_attempt_budget,
		)
		sites = colorbynumber.voronoi_geometry.generate_square_grid_sites(domain)
	elif generator_family == "uniform":
		if seed is None:
			raise ValueError("The uniform generator requires a replay seed")
		_require_unused_generator_parameters(
			jitter_fraction,
			hard_core_minimum_distance_ratio,
			hard_core_attempt_budget,
		)
		sites = colorbynumber.voronoi_geometry.generate_uniform_sites(domain, seed)
	elif generator_family == "stratified-jitter":
		if seed is None:
			raise ValueError("The stratified-jitter generator requires a replay seed")
		if jitter_fraction is None:
			raise ValueError("The stratified-jitter generator requires jitter_fraction")
		if hard_core_minimum_distance_ratio is not None or hard_core_attempt_budget is not None:
			raise ValueError("Stratified jitter does not accept hard-core parameters")
		sites = colorbynumber.voronoi_geometry.generate_stratified_jitter_sites(
			domain,
			seed,
			jitter_fraction,
		)
	elif generator_family == "hard-core":
		if seed is None:
			raise ValueError("The hard-core generator requires a replay seed")
		if hard_core_minimum_distance_ratio is None or hard_core_attempt_budget is None:
			raise ValueError("The hard-core generator requires distance ratio and attempt budget")
		if jitter_fraction is not None:
			raise ValueError("Hard-core generation does not accept jitter_fraction")
		sites = colorbynumber.voronoi_geometry.generate_hard_core_sites(
			domain,
			seed,
			hard_core_minimum_distance_ratio,
			hard_core_attempt_budget,
		)
	else:
		raise ValueError(f"Unsupported experiment generator family: {generator_family!r}")
	generation_seconds = time.perf_counter() - generation_start
	result = SiteGenerationResult(
		sites=sites,
		generation_seconds=generation_seconds,
	)
	return result


#============================================
def _require_unused_generator_parameters(
	jitter_fraction: float | None,
	hard_core_minimum_distance_ratio: float | None,
	hard_core_attempt_budget: int | None,
) -> None:
	"""Reject generator parameters that do not apply to grid or uniform controls."""
	parameters = (
		jitter_fraction,
		hard_core_minimum_distance_ratio,
		hard_core_attempt_budget,
	)
	if any(parameter is not None for parameter in parameters):
		raise ValueError("Grid and uniform generators do not accept candidate parameters")


#============================================
def _generator_configuration_parameters(
	domain: colorbynumber.voronoi_geometry.Domain,
	generator_family: str,
	seed: int | None,
	jitter_fraction: float | None,
	hard_core_minimum_distance_ratio: float | None,
	hard_core_attempt_budget: int | None,
) -> dict[str, object]:
	"""Build complete generator-specific configuration fields."""
	parameters: dict[str, object] = {
		"hard_core_attempt_budget": None,
		"hard_core_attempt_policy": None,
		"hard_core_distance": None,
		"hard_core_minimum_distance_ratio": None,
		"jitter_fraction": None,
	}
	if generator_family == "grid":
		if seed is not None:
			raise ValueError("The grid control configuration requires seed None")
	elif seed is None or isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
		raise ValueError("Stochastic generator configurations require a nonnegative seed")
	if generator_family in ("grid", "uniform"):
		_require_unused_generator_parameters(
			jitter_fraction,
			hard_core_minimum_distance_ratio,
			hard_core_attempt_budget,
		)
	elif generator_family == "stratified-jitter":
		if jitter_fraction is None:
			raise ValueError("Stratified-jitter configuration requires jitter_fraction")
		if isinstance(jitter_fraction, bool):
			raise ValueError("The stratified jitter fraction must be a finite number")
		if hard_core_minimum_distance_ratio is not None or hard_core_attempt_budget is not None:
			raise ValueError("Stratified-jitter configuration rejects hard-core parameters")
		jitter_value = float(jitter_fraction)
		if not math.isfinite(jitter_value) or not 0.0 <= jitter_value <= 1.0:
			raise ValueError("The stratified jitter fraction must be between 0 and 1")
		parameters["jitter_fraction"] = jitter_value
	elif generator_family == "hard-core":
		if hard_core_minimum_distance_ratio is None or hard_core_attempt_budget is None:
			raise ValueError("Hard-core configuration requires distance ratio and attempt budget")
		if jitter_fraction is not None:
			raise ValueError("Hard-core configuration rejects jitter_fraction")
		if (
			isinstance(hard_core_attempt_budget, bool)
			or not isinstance(hard_core_attempt_budget, int)
			or hard_core_attempt_budget < domain.site_count
		):
			raise ValueError("The hard-core attempt budget must be at least the site count")
		hard_core_distance, _distance_squared, _maximum_bin_coordinate = (
			colorbynumber.voronoi_geometry.hard_core_distance_parameters(
				domain,
				hard_core_minimum_distance_ratio,
			)
		)
		ratio = float(hard_core_minimum_distance_ratio)
		parameters["hard_core_attempt_budget"] = hard_core_attempt_budget
		parameters["hard_core_attempt_policy"] = (
			colorbynumber.voronoi_geometry.HARD_CORE_ATTEMPT_POLICY
		)
		parameters["hard_core_distance"] = hard_core_distance
		parameters["hard_core_minimum_distance_ratio"] = ratio
	else:
		raise ValueError(f"Unsupported experiment generator family: {generator_family!r}")
	return parameters


#============================================
def _canonical_value(value: object) -> object:
	"""Convert configuration values to the canonical JSON value grammar."""
	if value is None or isinstance(value, (bool, str, int)):
		return value
	if isinstance(value, float):
		if not math.isfinite(value):
			raise ValueError("Canonical configuration floats must be finite")
		return value.hex()
	if isinstance(value, dict):
		converted: dict[str, object] = {}
		for key, item in value.items():
			if not isinstance(key, str):
				raise ValueError("Canonical configuration keys must be strings")
			converted[key] = _canonical_value(item)
		return converted
	if isinstance(value, (list, tuple)):
		return [_canonical_value(item) for item in value]
	raise ValueError(f"Unsupported canonical configuration value: {type(value).__name__}")


#============================================
def canonical_configuration(configuration: dict[str, object]) -> str:
	"""Serialize a complete configuration as canonical ASCII JSON.

	Args:
		configuration: Complete behavior-changing experiment inputs.

	Returns:
		Canonical compact JSON with exact hexadecimal float strings.
	"""
	canonical_value = _canonical_value(configuration)
	text = json.dumps(
		canonical_value,
		sort_keys=True,
		separators=(",", ":"),
		ensure_ascii=True,
		allow_nan=False,
	)
	return text


#============================================
def configuration_digest(configuration: dict[str, object]) -> str:
	"""Return the full lowercase SHA-256 configuration digest."""
	canonical_text = canonical_configuration(configuration)
	digest = hashlib.sha256(canonical_text.encode("ascii")).hexdigest()
	return digest


#============================================
def dependency_versions() -> dict[str, str]:
	"""Return exact supported dependency versions recorded in artifacts."""
	versions = {
		"geos": shapely.geos_version_string,
		"numpy": numpy.__version__,
		"python": platform.python_version(),
		"shapely": shapely.__version__,
	}
	return versions


#============================================
def build_configuration(
	partition: colorbynumber.voronoi_geometry.Partition,
	generator_family: str,
	seed: int | None,
	stage: str,
	*,
	jitter_fraction: float | None = None,
	hard_core_minimum_distance_ratio: float | None = None,
	hard_core_attempt_budget: int | None = None,
	relaxation_schedule: tuple[float, ...] = (),
) -> dict[str, object]:
	"""Build a complete configuration for one experiment candidate.

	Args:
		partition: Constructed bounded partition.
		generator_family: Stable site-generator family name.
		seed: Replay seed, or None for the deterministic square grid.
		stage: Human-readable experiment stage slug.
		jitter_fraction: Fraction of each stratum spanned by jitter.
		hard_core_minimum_distance_ratio: Minimum center distance divided by spacing.
		hard_core_attempt_budget: Total uniform-candidate draw budget.
		relaxation_schedule: Ordered movement alpha for every completed iteration.

	Returns:
		A complete configuration ready for canonical serialization.
	"""
	domain = partition.domain
	generator_parameters = _generator_configuration_parameters(
		domain,
		generator_family,
		seed,
		jitter_fraction,
		hard_core_minimum_distance_ratio,
		hard_core_attempt_budget,
	)
	validated_schedule = tuple(
		colorbynumber.voronoi_geometry.validate_lloyd_alpha(alpha)
		for alpha in relaxation_schedule
	)
	relaxation_step = len(validated_schedule) if validated_schedule else None
	configuration: dict[str, object] = {
		"artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
		"boundary_force": None,
		"boundary_policy": "closed-rectangle-clip",
		"configuration_schema_version": CONFIGURATION_SCHEMA_VERSION,
		"constructor_family": partition.constructor_family,
		"dependency_versions": dependency_versions(),
		"generator_family": generator_family,
		"geometry_implementation_version": (
			colorbynumber.voronoi_geometry.VORONOI_GEOMETRY_IMPLEMENTATION_VERSION
		),
		"ghost_site_policy": None,
		"relative_tolerance": colorbynumber.voronoi_geometry.RELATIVE_TOLERANCE,
		"relaxation_schedule": list(validated_schedule),
		"relaxation_step": relaxation_step,
		"resolved_dimensions": {
			"columns": domain.columns,
			"rows": domain.rows,
		},
		"seed": seed,
		"site_count": domain.site_count,
		"stage": stage,
		"tolerance_policy_version": (
			colorbynumber.voronoi_geometry.TOLERANCE_POLICY_VERSION
		),
	}
	configuration.update(generator_parameters)
	return configuration


#============================================
def artifact_filename(
	configuration: dict[str, object],
	kind: str,
	extension: str,
) -> str:
	"""Return a collision-safe readable artifact filename."""
	dimensions = configuration["resolved_dimensions"]
	columns = dimensions["columns"]
	rows = dimensions["rows"]
	algorithm = configuration["generator_family"]
	site_count = configuration["site_count"]
	seed = configuration["seed"]
	stage = configuration["stage"]
	seed_text = "none" if seed is None else str(seed)
	digest = configuration_digest(configuration)
	filename = (
		f"{algorithm}_c{columns}_r{rows}_n{site_count}_seed{seed_text}_stage-{stage}"
		f"_cfg-{digest}_{kind}.{extension}"
	)
	return filename


#============================================
def _partition_record(
	result: colorbynumber.voronoi_geometry.ConstructionResult,
	configuration: dict[str, object],
	evaluation: colorbynumber.voronoi_metrics.PartitionEvaluation,
) -> dict[str, object]:
	"""Build the stable JSON record for one baseline control."""
	partition = result.partition
	domain = partition.domain
	record: dict[str, object] = {
		"artifact_schema_version": ARTIFACT_SCHEMA_VERSION,
		"canonical_configuration": canonical_configuration(configuration),
		"cells": [
			{
				"boundary_class": cell.boundary_class,
				"boundary_sides": list(cell.boundary_sides),
				"boundary_subtype": cell.boundary_subtype,
				"site_identifier": cell.site_identifier,
				"vertices": [list(vertex) for vertex in cell.vertices],
			}
			for cell in partition.cells
		],
		"configuration": configuration,
		"configuration_digest": configuration_digest(configuration),
		"domain": {
			"area_tolerance": domain.area_tolerance,
			"coordinate_tolerance": domain.coordinate_tolerance,
			"height": domain.height,
			"nominal_spacing": domain.nominal_spacing,
			"width": domain.width,
		},
		"quality_metrics": evaluation.quality_metrics,
		"sites": [
			{"identifier": site.identifier, "x": site.x, "y": site.y}
			for site in partition.sites
		],
		"timing_metadata": evaluation.timing_metadata,
	}
	return record


#============================================
def write_json_artifact(
	output_directory: pathlib.Path,
	result: colorbynumber.voronoi_geometry.ConstructionResult,
	configuration: dict[str, object],
	evaluation: colorbynumber.voronoi_metrics.PartitionEvaluation,
) -> pathlib.Path:
	"""Write one stable-schema JSON geometry evaluation artifact."""
	output_directory.mkdir(parents=True, exist_ok=True)
	filename = artifact_filename(configuration, "evaluation", "json")
	path = output_directory / filename
	record = _partition_record(result, configuration, evaluation)
	text = json.dumps(record, sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False)
	path.write_text(text + "\n", encoding="ascii")
	return path


#============================================
def _svg_path(vertices: tuple[tuple[float, float], ...]) -> str:
	"""Return a stable SVG path command for canonical vertices."""
	commands = [f"M {vertices[0][0]:.17g} {vertices[0][1]:.17g}"]
	commands.extend(f"L {x:.17g} {y:.17g}" for x, y in vertices[1:])
	commands.append("Z")
	path_data = " ".join(commands)
	return path_data


#============================================
def write_diagnostic_svg(
	output_directory: pathlib.Path,
	result: colorbynumber.voronoi_geometry.ConstructionResult,
	configuration: dict[str, object],
) -> pathlib.Path:
	"""Write an inspectable SVG with sites and boundary classes."""
	output_directory.mkdir(parents=True, exist_ok=True)
	filename = artifact_filename(configuration, "diagnostic", "svg")
	path = output_directory / filename
	partition = result.partition
	domain = partition.domain
	stroke_width = domain.nominal_spacing * 0.035
	site_radius = domain.nominal_spacing * 0.055
	lines = [
		'<?xml version="1.0" encoding="UTF-8"?>',
		(
			f'<svg xmlns="http://www.w3.org/2000/svg" '
			f'viewBox="0 0 {domain.width:.17g} {domain.height:.17g}">'
		),
		(
			f'<g transform="translate(0 {domain.height:.17g}) scale(1 -1)" '
			f'stroke="#334455" stroke-width="{stroke_width:.17g}">'
		),
	]
	for cell in partition.cells:
		if cell.boundary_subtype == "corner":
			fill = "#e07b39"
		elif cell.boundary_class == "boundary":
			fill = "#f4c27a"
		else:
			fill = "#dcecf7"
		lines.append(f'<path d="{_svg_path(cell.vertices)}" fill="{fill}"/>')
	lines.append('</g>')
	lines.append(
		f'<g transform="translate(0 {domain.height:.17g}) scale(1 -1)" fill="#17212b">'
	)
	for site in partition.sites:
		lines.append(
			f'<circle cx="{site.x:.17g}" cy="{site.y:.17g}" r="{site_radius:.17g}"/>'
		)
	lines.extend(("</g>", "</svg>"))
	path.write_text("\n".join(lines) + "\n", encoding="ascii")
	return path
