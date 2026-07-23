"""Metrics and reproducibility tests for the bounded Voronoi baseline."""

# Standard Library
import json
import math
import hashlib
import pathlib

# PIP3 modules
import numpy
import pytest

# local repo modules
import colorbynumber.voronoi_metrics
import colorbynumber.voronoi_geometry
import colorbynumber.voronoi_experiment


#============================================
def _small_grid_result() -> colorbynumber.voronoi_geometry.ConstructionResult:
	"""Build a small deterministic grid control for focused evaluator tests."""
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	sites = colorbynumber.voronoi_geometry.generate_square_grid_sites(domain)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	return result


#============================================
def _uniform_configuration(seed: int) -> dict[str, object]:
	"""Build one real uniform candidate configuration."""
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	sites = colorbynumber.voronoi_geometry.generate_uniform_sites(domain, seed)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	configuration = colorbynumber.voronoi_experiment.build_configuration(
		result.partition,
		"uniform",
		seed,
		"uniform-control",
	)
	return configuration


#============================================
def _jitter_configuration(jitter_fraction: float) -> dict[str, object]:
	"""Build one real stratified-jitter candidate configuration."""
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	sites = colorbynumber.voronoi_geometry.generate_stratified_jitter_sites(
		domain,
		20260722,
		jitter_fraction,
	)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	stage_fraction = int(round(100.0 * jitter_fraction))
	configuration = colorbynumber.voronoi_experiment.build_configuration(
		result.partition,
		"stratified-jitter",
		20260722,
		f"jitter-f{stage_fraction:03d}",
		jitter_fraction=jitter_fraction,
	)
	return configuration


#============================================
def _hard_core_configuration(
	minimum_distance_ratio: float,
	attempt_budget: int,
	relaxation_schedule: tuple[float, ...] = (),
) -> dict[str, object]:
	"""Build one real hard-core candidate configuration."""
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	sites = colorbynumber.voronoi_geometry.generate_hard_core_sites(
		domain,
		20260722,
		minimum_distance_ratio,
		attempt_budget,
	)
	for alpha in relaxation_schedule:
		sites = colorbynumber.voronoi_geometry.relax_bounded_lloyd_once(
			domain, sites, alpha
		)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	distance_percent = int(round(100.0 * minimum_distance_ratio))
	configuration = colorbynumber.voronoi_experiment.build_configuration(
		result.partition,
		"hard-core",
		20260722,
		f"hardcore-d{distance_percent:03d}s",
		hard_core_minimum_distance_ratio=minimum_distance_ratio,
		hard_core_attempt_budget=attempt_budget,
		relaxation_schedule=relaxation_schedule,
	)
	return configuration


#============================================
def test_canonical_configuration_has_exact_stable_float_encoding() -> None:
	first = {"z": 0.25, "a": {"optional": None, "steps": [1, 0.5]}}
	second = {"a": {"steps": [1, 0.5], "optional": None}, "z": 0.25}
	first_text = colorbynumber.voronoi_experiment.canonical_configuration(first)
	second_text = colorbynumber.voronoi_experiment.canonical_configuration(second)
	assert first_text == second_text
	assert '"0x1.0000000000000p-2"' in first_text


#============================================
def test_canonical_configuration_rejects_nonfinite_float() -> None:
	with pytest.raises(ValueError, match="finite"):
		colorbynumber.voronoi_experiment.canonical_configuration({"distance": math.inf})


#============================================
def test_configuration_digest_matches_independent_sha256() -> None:
	configuration = _uniform_configuration(17)
	canonical = colorbynumber.voronoi_experiment.canonical_configuration(configuration)
	expected = hashlib.sha256(canonical.encode("ascii")).hexdigest()
	assert colorbynumber.voronoi_experiment.configuration_digest(configuration) == expected


#============================================
def test_configuration_digest_changes_with_behavior_input() -> None:
	first = _uniform_configuration(17)
	second = _uniform_configuration(18)
	assert colorbynumber.voronoi_experiment.configuration_digest(first) != (
		colorbynumber.voronoi_experiment.configuration_digest(second)
	)


#============================================
def test_stratified_configuration_digest_distinguishes_jitter_fraction() -> None:
	first = _jitter_configuration(0.5)
	second = _jitter_configuration(1.0)
	assert colorbynumber.voronoi_experiment.configuration_digest(first) != (
		colorbynumber.voronoi_experiment.configuration_digest(second)
	)


#============================================
def test_hard_core_configuration_digest_distinguishes_attempt_budget() -> None:
	first = _hard_core_configuration(0.5, 1200)
	second = _hard_core_configuration(0.5, 2400)
	assert colorbynumber.voronoi_experiment.configuration_digest(first) != (
		colorbynumber.voronoi_experiment.configuration_digest(second)
	)


#============================================
def test_hard_core_configuration_digest_distinguishes_distance_ratio() -> None:
	first = _hard_core_configuration(0.5, 1200)
	second = _hard_core_configuration(0.7, 1200)
	assert colorbynumber.voronoi_experiment.configuration_digest(first) != (
		colorbynumber.voronoi_experiment.configuration_digest(second)
	)


#============================================
@pytest.mark.parametrize(
	"first_schedule,second_schedule",
	(
		((0.5,), (0.5, 0.5)),
		((0.5,), (0.25,)),
	),
	ids=("cumulative-count", "movement-alpha"),
)
def test_relaxation_configuration_digest_distinguishes_complete_schedule(
	first_schedule: tuple[float, ...],
	second_schedule: tuple[float, ...],
) -> None:
	first = _hard_core_configuration(0.7, 1200, first_schedule)
	second = _hard_core_configuration(0.7, 1200, second_schedule)
	assert colorbynumber.voronoi_experiment.configuration_digest(first) != (
		colorbynumber.voronoi_experiment.configuration_digest(second)
	)


#============================================
def test_hard_core_configuration_digest_distinguishes_attempt_policy(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	first = _hard_core_configuration(0.5, 1200)
	monkeypatch.setattr(
		colorbynumber.voronoi_geometry,
		"HARD_CORE_ATTEMPT_POLICY",
		"total-uniform-candidate-draws-test",
	)
	second = _hard_core_configuration(0.5, 1200)
	assert colorbynumber.voronoi_experiment.configuration_digest(first) != (
		colorbynumber.voronoi_experiment.configuration_digest(second)
	)


#============================================
def test_hard_core_configuration_rejects_squared_distance_underflow() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	configuration = _hard_core_configuration(0.5, 1200)
	minimum_positive_distance = math.nextafter(0.0, math.inf)
	ratio = minimum_positive_distance / domain.nominal_spacing
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(
		domain,
		colorbynumber.voronoi_geometry.generate_hard_core_sites(
			domain,
			20260722,
			0.5,
			1200,
		),
	)
	with pytest.raises(ValueError, match="squared"):
		colorbynumber.voronoi_experiment.build_configuration(
			result.partition,
			"hard-core",
			20260722,
			configuration["stage"],
			hard_core_minimum_distance_ratio=ratio,
			hard_core_attempt_budget=1200,
		)


#============================================
def test_generation_dispatch_preserves_candidate_parameters() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	jitter = colorbynumber.voronoi_experiment.generate_sites(
		domain,
		"stratified-jitter",
		20260722,
		jitter_fraction=0.5,
	)
	hard_core = colorbynumber.voronoi_experiment.generate_sites(
		domain,
		"hard-core",
		20260722,
		hard_core_minimum_distance_ratio=0.7,
		hard_core_attempt_budget=1200,
	)
	assert jitter.sites == colorbynumber.voronoi_geometry.generate_stratified_jitter_sites(
		domain, 20260722, 0.5
	)
	assert hard_core.sites == colorbynumber.voronoi_geometry.generate_hard_core_sites(
		domain, 20260722, 0.7, 1200
	)


#============================================
def test_generation_dispatch_rejects_incomplete_candidate_parameters() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	with pytest.raises(ValueError, match="distance ratio and attempt budget"):
		colorbynumber.voronoi_experiment.generate_sites(
			domain,
			"hard-core",
			20260722,
			hard_core_minimum_distance_ratio=0.7,
		)


#============================================
def test_artifact_name_contains_complete_configuration_digest() -> None:
	result = _small_grid_result()
	configuration = colorbynumber.voronoi_experiment.build_configuration(
		result.partition, "grid", None, "initial"
	)
	digest = colorbynumber.voronoi_experiment.configuration_digest(configuration)
	filename = colorbynumber.voronoi_experiment.artifact_filename(
		configuration, "diagnostic", "svg"
	)
	assert filename.endswith(f"cfg-{digest}_diagnostic.svg")


#============================================
def test_grid_metrics_preserve_equal_area_and_spacing_controls() -> None:
	result = _small_grid_result()
	metrics = colorbynumber.voronoi_metrics.evaluate_partition(
		result, 0.0
	).quality_metrics
	assert metrics["area_p90_to_p10_ratio"] == pytest.approx(1.0)
	assert metrics["nearest_neighbor_minimum_to_median_ratio"] == pytest.approx(1.0)


#============================================
def test_uniform_metrics_show_more_area_variation_than_grid() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	grid_result = _small_grid_result()
	uniform_sites = colorbynumber.voronoi_geometry.generate_uniform_sites(domain, 17)
	uniform_result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(
		domain, uniform_sites
	)
	grid_metrics = colorbynumber.voronoi_metrics.evaluate_partition(
		grid_result, 0.0
	).quality_metrics
	uniform_metrics = colorbynumber.voronoi_metrics.evaluate_partition(
		uniform_result, 0.0
	).quality_metrics
	assert uniform_metrics["area_coefficient_of_variation"] > (
		grid_metrics["area_coefficient_of_variation"]
	)


#============================================
def test_exact_covering_radius_matches_centered_unit_square() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(1, 1)
	sites = (colorbynumber.voronoi_geometry.Site(0, 0.5, 0.5),)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	radius = colorbynumber.voronoi_metrics.exact_bounded_covering_radius(
		result.partition
	)
	assert radius == pytest.approx(math.sqrt(0.5))


#============================================
def test_exact_covering_radius_matches_square_grid_control() -> None:
	result = _small_grid_result()
	radius = colorbynumber.voronoi_metrics.exact_bounded_covering_radius(
		result.partition
	)
	assert radius == pytest.approx(1.0 / math.sqrt(24.0))


#============================================
def test_one_site_has_no_defined_nearest_neighbor_metrics() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(1, 1)
	sites = (colorbynumber.voronoi_geometry.Site(0, 0.5, 0.5),)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	quality = colorbynumber.voronoi_metrics.evaluate_partition(result, 0.0).quality_metrics
	assert quality["nearest_neighbor_median"] is None
	assert quality["nearest_neighbor_coefficient_of_variation"] is None


#============================================
def test_one_site_still_reports_area_and_boundary_behavior() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(1, 1)
	sites = (colorbynumber.voronoi_geometry.Site(0, 0.5, 0.5),)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(domain, sites)
	evaluation = colorbynumber.voronoi_metrics.evaluate_partition(result, 0.0)
	assert evaluation.quality_metrics["area_p90_to_p10_ratio"] == pytest.approx(1.0)
	assert evaluation.quality_metrics["boundary_to_interior_median_area_ratio"] is None


#============================================
def test_phase_timings_use_explicit_boundaries(monkeypatch: pytest.MonkeyPatch) -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(1, 1)
	clock_values = iter(
		(10.0, 12.0, 20.0, 25.0, 30.0, 37.0, 40.0, 44.0, 50.0, 59.0)
	)
	monkeypatch.setattr(
		colorbynumber.voronoi_experiment.time,
		"perf_counter",
		lambda: next(clock_values),
	)
	generation = colorbynumber.voronoi_experiment.generate_sites(domain, "grid", None)
	result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(
		domain, generation.sites
	)
	evaluation = colorbynumber.voronoi_metrics.evaluate_partition(
		result, generation.generation_seconds
	)
	timings = evaluation.timing_metadata
	actual = (
		timings["generation_seconds"],
		timings["site_validation_seconds"],
		timings["construction_seconds"],
		timings["partition_validation_seconds"],
		timings["quality_measurement_seconds"],
	)
	assert actual == pytest.approx((2.0, 5.0, 7.0, 4.0, 9.0))


#============================================
def test_uniform_invalid_output_is_rejected_during_construction(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	class DuplicateRandomGenerator:
		def random(self, shape: tuple[int, int]) -> numpy.ndarray:
			return numpy.zeros(shape)

	def duplicate_rng(seed: int) -> DuplicateRandomGenerator:
		return DuplicateRandomGenerator()

	domain = colorbynumber.voronoi_geometry.create_domain(2, 1)
	monkeypatch.setattr(
		colorbynumber.voronoi_geometry.numpy.random,
		"default_rng",
		duplicate_rng,
	)
	generation = colorbynumber.voronoi_experiment.generate_sites(
		domain, "uniform", 20260722
	)
	with pytest.raises(
		colorbynumber.voronoi_geometry.GeometryError,
		match="Duplicate or near-duplicate sites",
	):
		colorbynumber.voronoi_geometry.construct_bounded_voronoi(
			domain, generation.sites
		)


#============================================
def test_fresh_fixed_seed_runs_reproduce_geometry_and_quality() -> None:
	domain = colorbynumber.voronoi_geometry.create_domain(4, 3)
	first_sites = colorbynumber.voronoi_geometry.generate_uniform_sites(domain, 23)
	first_result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(
		domain, first_sites
	)
	first_quality = colorbynumber.voronoi_metrics.evaluate_partition(
		first_result, 0.0
	).quality_metrics
	second_sites = colorbynumber.voronoi_geometry.generate_uniform_sites(domain, 23)
	second_result = colorbynumber.voronoi_geometry.construct_bounded_voronoi(
		domain, second_sites
	)
	second_quality = colorbynumber.voronoi_metrics.evaluate_partition(
		second_result, 0.0
	).quality_metrics
	assert (first_result.partition.sites, first_result.partition.cells) == (
		second_result.partition.sites,
		second_result.partition.cells,
	)
	assert first_quality == second_quality


#============================================
@pytest.mark.parametrize(
	"owner,version_name",
	(
		(colorbynumber.voronoi_experiment, "CONFIGURATION_SCHEMA_VERSION"),
		(colorbynumber.voronoi_experiment, "ARTIFACT_SCHEMA_VERSION"),
		(colorbynumber.voronoi_geometry, "VORONOI_GEOMETRY_IMPLEMENTATION_VERSION"),
	),
	ids=("configuration-schema", "artifact-schema", "geometry-implementation"),
)
def test_configuration_digest_covers_owned_versions(
	monkeypatch: pytest.MonkeyPatch,
	owner: object,
	version_name: str,
) -> None:
	result = _small_grid_result()
	first = colorbynumber.voronoi_experiment.build_configuration(
		result.partition, "grid", None, "initial"
	)
	monkeypatch.setattr(owner, version_name, getattr(owner, version_name) + 1)
	second = colorbynumber.voronoi_experiment.build_configuration(
		result.partition, "grid", None, "initial"
	)
	assert colorbynumber.voronoi_experiment.configuration_digest(first) != (
		colorbynumber.voronoi_experiment.configuration_digest(second)
	)


#============================================
def test_json_artifact_separates_quality_metrics_from_timing_metadata(
	tmp_path: pathlib.Path,
) -> None:
	result = _small_grid_result()
	configuration = colorbynumber.voronoi_experiment.build_configuration(
		result.partition, "grid", None, "initial"
	)
	evaluation = colorbynumber.voronoi_metrics.evaluate_partition(result, 0.0)
	path = colorbynumber.voronoi_experiment.write_json_artifact(
		tmp_path, result, configuration, evaluation
	)
	record = json.loads(path.read_text(encoding="ascii"))
	assert record["quality_metrics"] == evaluation.quality_metrics
	assert record["timing_metadata"] == evaluation.timing_metadata


#============================================
def test_svg_artifact_is_byte_stable(tmp_path: pathlib.Path) -> None:
	result = _small_grid_result()
	configuration = colorbynumber.voronoi_experiment.build_configuration(
		result.partition, "grid", None, "initial"
	)
	first_path = colorbynumber.voronoi_experiment.write_diagnostic_svg(
		tmp_path / "first", result, configuration
	)
	second_path = colorbynumber.voronoi_experiment.write_diagnostic_svg(
		tmp_path / "second", result, configuration
	)
	assert first_path.read_bytes() == second_path.read_bytes()
