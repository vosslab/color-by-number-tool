# Plan: Evaluate organic Voronoi worksheet layouts

## Context

The square grid is a valid production layout and remains the control.
The proposed option replaces squares with bounded Voronoi polygons generated from sites that look
random while producing cells of roughly equal area.

Those goals compete.
Uniform randomness creates close pairs and large holes, while aggressive equal-area relaxation tends
to converge toward a visible hexagonal lattice.
The work should find an evidence-supported compromise rather than assume one algorithm already does
everything needed.

The default 86 by 60 landscape or 60 by 86 portrait layout contains 5,160 cells.
A current 60 by 86 Kimi control produced a mean Delta E 76 of 15.276 and a maximum of 42.087 with
strong enhancement.
These values establish a reproducible image baseline, not an acceptance threshold for polygonal
layouts.

Every experiment derives its site count from the existing `-g COLUMNSxROWS` value, with
`N = columns * rows` before or after the current portrait dimension swap. Thus `43x30` requests
1,290 sites, the default `86x60` requests 5,160, and `100x75` requests 7,500. The pair remains the
backward-compatible density and target-aspect input even though Voronoi cells have no row and column
indices. This is a shared configuration and count convention, not a shared layout representation.

Output creation uses two deliberately separate, representation-incompatible paths. The current
square path keeps rectangular NumPy arrays and its existing sampling, matching, enhancement, and
writers. The Voronoi path owns ordered sites and polygons, area sampling, assignments, centroid
label placement, diagnostics, formats, renderers, and its coordinator. The `--layout` choice
dispatches to one path without a generic layout interface or polygon-to-grid coercion.

## Objectives

- Find a reproducible bounded point layout with an organic appearance, low cell-area variation,
  adequate edge coverage, and enough interior clearance for marker codes.
- Compare plausible algorithms using common seeds, geometry, images, metrics, and rendered boards.
- Preserve the current square grid as the default and control while the option is unproven.
- Record a design decision only after geometry and worksheet experiments identify a stable Pareto
  improvement.
- Produce a focused implementation plan after algorithm selection.

## Design philosophy

The experiment will separate observations, hypotheses, and decisions.
Each candidate changes one important mechanism at a time so that a result can be attributed to that
mechanism.

The first comparison concerns geometry only.
Image sampling, palette matching, enhancement, labels, and PDF composition follow after a short list
of layouts survives the geometry screen.

No single weighted score will hide a tradeoff.
Candidates will be compared on a Pareto frontier and with side-by-side renderings.
If no organic candidate is convincingly better for the intended effect, the correct result is to
retain only the square grid.

## Scope

- Define a normalized rectangular domain and use the shared site-count convention.
- Generate, clip, validate, and measure bounded Voronoi partitions.
- Compare grid, random, stratified, hard-core, and partially relaxed site layouts.
- Measure both center/interior behavior and boundary behavior.
- Validate a geometry short list on representative images and printable worksheets.
- Record the evidence, selected parameters, rejected alternatives, and implementation handoff.

## Non-goals

- Replacing or changing the existing square-grid default during experimentation.
- Making site density depend on image content in the first version.
- Reproducing Inkscape's overlap-removal implementation inside the application.
- Adding final CLI, CSV, preview, or PDF behavior before the layout is selected.
- Adopting weighted or capacity-constrained Voronoi cells unless simpler candidates fail for a
  measured reason.
- Reworking color enhancement while comparing layouts.

## Current state summary

The production square pipeline represents samples, assignments, and errors as rectangular NumPy
arrays. Square resampling, color matching, four-neighbor enhancement, row and column CSV output,
PNG previews, summary metrics, and both PDF writers retain those semantics and remain the default.

A production Voronoi pipeline owns an ordered site-and-polygon model, polygon-area sampling,
site-identifier assignments, centroid-based polygon labels, dedicated CSV and summary semantics,
polygon previews, and polygon PDF rendering. Strong enhancement derives adjacency from shared
Voronoi edges rather than rectangular four-neighbor positions.

The CLI dispatches `--layout square` (the default) and `--layout voronoi` to separate
coordinators. Their data models and writers remain separate: there is no generic `Layout` interface
and no polygon-to-grid coercion. The paths reuse only demonstrated representation-independent
utilities: input loading and EXIF correction, palette definitions, color-distance and nearest-match
primitives, page constants and orientation conventions, and dependency or repository-path helpers.

Shapely is a declared runtime dependency for bounded polygon construction, clipping, topology, and
boolean operations. Stable owner ordering requires Shapely 2.1 or newer with GEOS 3.12 or newer and
the `voronoi_polygons(ordered=True)` capability. SciPy and scikit-image remain undeclared. The
independently implemented analytical half-plane clipper remains the small-case oracle, so Shapely
never validates itself as the sole correctness authority.

## Milestone 2A result

The raw site-distribution screen is complete and recorded in
[../decisions/voronoi_milestone_2a_distribution_screen.md](../decisions/voronoi_milestone_2a_distribution_screen.md).
It used the precommitted seeds `20260722`, `20260723`, and `20260724` at `43x30`, promoted distinct
regions to `86x60`, and checked the survivors at `100x75`.

The screen treats area CV, area p90/p10, exact covering radius, hard-core requested-distance
verification, boundary/interior median area, and equal-scale visuals as primary evidence.
Nearest-neighbor CV, nearest-neighbor minimum/median, and boundary-band density remain secondary
diagnostics and did not select candidates. No composite score or numeric randomness proxy was used.
The decision record retains a complete alternatives ledger with tested scales, strengths, failure
modes, current disposition, and explicit reconsideration conditions. It also preserves the
withdrawn early metric-only elimination of hard-core `0.50` and jitter `1.00` as a methodological
negative result.

Hard-core `d/s = 0.85` produced no 1,290-site sample or evaluation for any fixed seed under the
declared `100N` total-candidate budget, bracketing this generator and policy above successful
`0.70` without disproving geometric feasibility. Three equal-scale boards show `0.50` as the more
disordered hard-core comparator and `0.70` as the more even organic starting point across the fixed
seeds. Stratified jitter `0.50` remains the equality/grid-signature comparator; its visible rows
and columns prevent its strong area metrics from being treated as evidence of organic appearance.

The bounded Lloyd checkpoint screen is complete and recorded in
`docs/active_plans/decisions/voronoi_milestone_2b_partial_lloyd_screen.md`.
At `43x30`, the fixed alpha-`0.50` checkpoints `1`, `2`, and `4` all improve the recorded area and
covering measurements from the hard-core `0.70` start. Three equal-scale fixed-seed boards show
step `2` as the good-enough point-spacing knee: it removes the most visible raw holes while
retaining more irregularity than step `4`. Step `4` remains a documented equality-first
alternative rather than the selected screen result.

Milestone 2 point-distribution screening is complete. Hard-core `0.50` and jitter `0.50` remain
unchanged visual anchors. Boundary correction, local unclumping, image behavior, print behavior,
and production integration remain outside this screen.

The handoff stays adaptable through deterministic generator contracts, separate construction,
validation, measurement, and rendering stages, complete versioned configurations, and preserved
negative results with revisit triggers. This stage separation does not create a generic layout
abstraction: square and Voronoi representations remain separate and share only proven
representation-independent utilities.

## The circle proposal

Equal circles are a useful way to express a minimum site separation.
For circles of diameter `d`, exact circle non-overlap is equivalent to requiring a Euclidean
center-to-center distance of at least `d`.
That is a hard-core point process, closely related to Poisson-disk sampling.

Let `s = sqrt(A / N)`, where `A` is domain area and `N` is the site count.
The previous square grid has cell side `s` in an equal-area square-domain analogy.
A circle diameter of `0.25s` only prevents very close pairs; it does not constrain large empty
regions and is unlikely by itself to make Voronoi areas similar.
The experiment should start at that proposed value, then increase `d / s` through a feasibility and
appearance search rather than promote 25 percent to a fixed design constant.

Inkscape Remove Overlaps is not the preferred mechanism for this job.
It separates axis-aligned bounding rectangles while minimizing movement, so equal circle objects are
treated through their square bounds.
That supplies a minimum separation with horizontal and vertical bias, but it does not fill holes,
equalize Voronoi areas, or manage a containing boundary.
Direct Euclidean hard-core sampling is simpler and matches the intended circle model exactly.

## Hypotheses

### H1: Uniform random baseline

Independent uniform sites will look random but produce close pairs, large holes, high Voronoi-area
variation, and unreliable label clearance.
They are a negative control rather than a likely design.

### H2: Stratified jitter grid signature

One randomly displaced site per square stratum should improve area equality and boundary coverage,
but row, column, or fourfold patterns may remain visible.
This candidate directly tests the concern that sites starting near grid positions will still look
like a distorted grid.

### H3: Hard-core spacing limits

Poisson-disk sampling should provide isotropic minimum separation and a more natural blue-noise
appearance than overlap removal.
Its minimum-distance parameter will reduce clumping, but Voronoi-area variation and boundary bias
may remain.

### H4: Limited Lloyd compromise

Starting with Poisson-disk sites and moving each site partway toward the centroid of its clipped
Voronoi cell should reduce cell-area variation and large holes.
Early iterations may retain organic irregularity; full convergence is expected to become too
crystalline.
The selected stopping point should be the measured knee before order increases faster than useful
equality improves.

### H5: Local unclumping comparator

Local push-pull relaxation may create a pleasant distribution while preserving more disorder than
Lloyd relaxation.
It should be implemented only if the first comparisons leave a meaningful gap, because it lacks a
global area objective and explicit boundary behavior.

### H6: Evidence-led boundary correction

Clipping cells to the worksheet domain and using bounded centroids may already provide acceptable
edge behavior.
Mirrored sites, ghost sites, or a boundary force should be compared only if edge-cell area, site
density, or label clearance differs materially from the interior.

### H7: Capacity constraint escalation

If partial Lloyd relaxation becomes visibly ordered before areas are sufficiently balanced, a
capacity-constrained Voronoi or power-diagram method may separate area control from site order.
Its complexity is justified only by that measured failure.

## Measurements

### Geometry

- Cell-area coefficient of variation and the 90th-to-10th percentile area ratio.
- Nearest-neighbor distance coefficient of variation and minimum-to-median ratio.
- Exact bounded covering radius, computed as the maximum generating-site-to-owned-cell-vertex
  distance, which detects large holes that a minimum-distance constraint misses.
- Boundary-cell median area divided by interior-cell median area.
- Boundary-band site density divided by interior site density.
- Low-percentile label clearance using the radius of a largest inscribed label region.
- Fourfold and sixfold directional order, supported by pair-correlation or spectral plots when the
  simpler measurements disagree with the rendering.
- Five disjoint timings at the default 5,160 sites, with scaling checks at 1,290 and 7,500 sites:
  raw generation, mandatory site validation once at construction entry, construction, partition
  validation, and quality measurement.

### Image and worksheet

- Pixel- or area-weighted Delta E between the source and the palette reconstruction.
- Edge-weighted reconstruction error so smoother averages cannot hide lost facial or object edges.
- Color-code stability across seeds for visually important regions.
- Legibility and clipping of codes in low-clearance cells.
- Alignment of blank and reference artwork pages.
- Full-page renderings plus center, corner, and long-edge crops.

These measurements remain separate.
The experiment will not invent a composite score before their practical tradeoffs are visible.

## Experiment controls and fixtures

All stochastic candidates will use recorded seeds and the same resolved grid input, domain, site
count, clipping method, and measurement code.
Several seeds will characterize stability; one attractive seed will not establish a result.

The geometry board will include:

- an analytical square-cell construction as the equality and runtime control, used only for
  experimental comparison rather than production square-pipeline integration;
- independent uniform random sites as the clumping control;
- stratified jitter as the grid-signature control;
- direct Poisson-disk sites over a searched minimum-distance range;
- Poisson-disk sites after progressive bounded Lloyd relaxation;
- optional local unclumping only if the preceding results justify it.

The worksheet board will use:

- `kimi-face.png` for recognizable facial structure and dark hair;
- the included marker-chart image for a landscape and sharp-region case;
- a generated corner, border, thin-line, and high-contrast fixture for boundary and edge failures.

The first image comparison will keep palette, fit, and enhancement settings fixed.
Polygon colors will be based on cell-area sampling or a verified supersampled approximation, rather
than a single pixel at the site.

## Milestone plan

### Milestone 1: Geometry contract and baseline

Dependencies: none.

Work:

- Normalize the rectangular domain while retaining the target page aspect ratio.
- Define bounded Voronoi clipping, site ownership, boundary classification, and degeneracy policy.
- Record the grid and uniform-random controls at the default 5,160 sites, then confirm the same
  contract at 1,290 and 7,500 sites.
- Define deterministic seed handling and collision-safe artifact naming from a canonical
  full-configuration digest.
- Gate parser-valid experimental dimensions with the centralized nominal-spacing and ULP-aware
  conditioning policy while leaving production square behavior unchanged.
- Support one-site, two-site, and collinear bounded partitions with analytical half-plane clipping.
- Compare small general-position partitions with an independently implemented analytical
  half-plane clipping oracle; retain raster nearest-site ownership as a supplemental check.

Exit evidence:

- Every finite polygon is valid, lies inside the domain, owns its site, and participates in a
  gap-free, overlap-free partition within numeric tolerance.
- Total polygon area agrees with domain area.
- The selected general constructor and independent analytical oracle agree on small fixtures.
- One-site, two-site, and collinear fixtures produce their valid bounded partitions.
- `43x30`, `86x60`, `100x75`, and the representable `1000000000000x1` stress pair pass
  conditioning. The parser-accepted `10000000000000000x1` fixture reports a clear conditioning
  error.
- Baseline sites, cells, quality metrics, and SVG geometry are reproducible. Generation, site
  validation, construction, partition validation, and quality measurement are recorded as disjoint
  single-run observations and are allowed to vary. Uniform generation returns its first seeded
  output; construction rejects invalid output rather than replacing it.

Parallel-plan ready: no.
The Voronoi geometry contract and evaluator should stabilize before candidate work branches.

### Milestone 2: Site-distribution screening

Dependencies: milestone 1.

Status: complete. The selected experimental checkpoint is two cumulative alpha-`0.50` bounded
centroid movements from the hard-core `d/s = 0.70` start at `43x30`.

Work:

- Evaluate stratified jitter, direct hard-core sampling, and partial bounded Lloyd relaxation.
- Search hard-core distance relative to `s` by bracketing feasibility and visible order, beginning
  with the proposed `0.25s` observation point.
- Capture metrics after progressive relaxation rather than assuming an iteration count.
- Eliminate dominated candidates and retain distinct Pareto choices when the tradeoff is real.
- Add local unclumping only if it tests an unresolved question in the frontier.

Exit evidence:

- A point-distribution board makes equality, holes, boundary behavior, and lattice signatures
  judgeable.
- Metrics across recorded seeds show whether each result is stable.
- The short list and rejected candidates have written reasons tied to observations.

Parallel-plan ready: no.
Candidate selection depends on one shared evaluator and deliberately sequential hypothesis updates.

### Milestone 3: Image and print validation

Dependencies: milestone 2 short list.

Status: complete. The prototype evidence is recorded in
[voronoi_milestone_3_image_print_prototype.md](../decisions/voronoi_milestone_3_image_print_prototype.md).
The selected distribution produces intended polygon previews with zero ownership and sampling
fallbacks. Centroid labels are accepted as the good-enough production anchor after the earlier
site-centered labels failed. A single-page `60x86` worksheet remains a known readability limit;
the supported default `86x60` presentation passed the real CLI smoke.

Work:

- Build one end-to-end Voronoi prototype path around ordered sites and polygons without routing its
  data through the production square coordinator or rectangular arrays.
- Sample source color over each polygon and match it with the unchanged palette definitions and
  color-distance primitives where their interfaces remain representation-independent.
- Render Kimi, marker-chart, and synthetic-edge comparisons with enhancement disabled first.
- Measure reconstruction and edge error against the square-grid control.
- Test polygon-specific code placement and diagnostics, cell outlines, page margins, previews, and
  blank/reference alignment through prototype Voronoi writers.
- Evaluate enhancement only after the base comparison. If it is supported, use Delaunay or
  shared-edge adjacency and keep the square four-neighbor implementation unchanged.

Exit evidence:

- The leading layout preserves recognizable structure; the prototype establishes that result.
- The earlier site-centered label diagnostics remain recorded as negative evidence; centroid labels
  provide the accepted good-enough production anchor.
- Boundary crops do not reveal systematic under-coverage or oversized edge cells.
- Runtime and memory are compatible with the existing interactive workflow, or the cost is
  explicitly accepted.

Parallel-plan ready: no.
The short list is intentionally small and uses one end-to-end prototype path.

### Milestone 4: Decision and implementation handoff

Dependencies: milestone 3.

Status: complete. The selected hard-core `0.70` start with two cumulative alpha-`0.50` bounded
Lloyd movements is implemented as the optional Voronoi path. `--layout voronoi` dispatches to its
dedicated coordinator and writers, while square output remains the default. The production path
records its internally generated seed for replay without exposing a user seed flag. The real CLI
smoke passed. No further point-distribution work is required for this feature.

Work:

- Select the nondominated candidate that best supports the intended organic style.
- Record parameter meanings, seed behavior, boundary policy, dependencies, and rejected
  alternatives.
- Implement the dedicated Voronoi coordinator, ordered site-and-polygon data model, area sampler,
  shared-edge enhancement, centroid labels, diagnostics, output writers, and tests.
- Provide `--layout voronoi` alongside the unchanged default `--layout square` without merging
  their models or writers.
- Define polygon-specific CSV, summary, preview, and PDF semantics while preserving current square
  formats and default behavior.
- Reuse only evidence-proven low-level utilities; each pipeline owns uncertain interfaces until
  their representation independence is demonstrated.

Exit evidence:

- The decision traces from fixtures and measurements to the selected design.
- The optional production path passes its real CLI smoke and the test suite.
- The implementation contains no unresolved geometry assumption that the experiment could have
  answered.

Parallel-plan ready: no.
The implementation handoff is complete.

## Decision tree

1. If direct hard-core sampling is random-looking and sufficiently balanced, select the simplest
   stable parameter region and stop.
2. If it retains holes or high area variation, add progressive bounded Lloyd relaxation and stop at
   the Pareto knee before visible order dominates.
3. If equality remains inadequate before crystallization, test a capacity-constrained Voronoi or
   power-diagram prototype.
4. If only boundary metrics fail, compare bounded relaxation with mirrored or ghost-site handling;
   do not change the interior algorithm first.
5. If labels fail at a newly requested density, compare a lower cell count or a multi-page format
   before distorting the selected point distribution.
6. If image reconstruction loses important edges, determine whether polygon sampling or uniform site
   density is responsible before changing point spacing.
7. If no candidate improves the intended visual character without unacceptable geometry or print
   costs, keep the square grid as the only production layout.

## Verification

### Geometry invariants

- Sites are finite, unique within tolerance, and inside the bounded domain.
- Polygons are finite, nonempty, valid, and clipped to the domain.
- Each polygon contains or touches its generating site within tolerance.
- Polygon interiors do not overlap and their union covers the domain.
- The sum of polygon areas agrees with domain area within a scale-aware tolerance.
- Fixed seeds reproduce equivalent sites, cells, quality metrics, and SVG geometry. Timing metadata
  records five disjoint single-run observations rather than deterministic output. The raw generator
  interval ends before construction performs its one mandatory site-validation pass.

### Numerical and degeneracy checks

- Exercise duplicate, nearly duplicate, one-site, two-site, collinear, boundary, and corner
  fixtures in domains constructed from valid resolved `-g` dimensions, including positive thin
  cells formed by close boundary-adjacent two-site and three-site sets.
- Stress parser-accepted and numerically representable aspect ratios and small valid site spacing
  inside the normalized unit-area domain, including `1000000000000x1`. Reject the parser-accepted
  `10000000000000000x1` fixture with a clear numeric-conditioning error when two tolerance bands no
  longer fit within the short side and nominal spacing.
- Compare small general-position cases with an independently implemented analytical half-plane
  clipping oracle and use a brute-force nearest-site raster only as supplemental ownership evidence.
- Validate topology and polygon booleans with declared Shapely while the independent analytical
  half-plane implementation remains the small-case correctness oracle.
- Use double precision and normalized coordinates. Derive centralized coordinate tolerance from
  nominal spacing plus a coordinate-magnitude ULP floor, and area tolerance from unit area plus its
  ULP floor, without aspect, perimeter, or site-count growth.
- Report rejected geometry and topology-preserving canonicalization rather than silently dropping
  cells.

### Visual checks

- Render sites, Voronoi edges, boundary classification, and label-clearance warnings as optional
  diagnostic layers.
- Compare candidates at the same physical scale and line weight.
- Inspect the full page and fixed center, edge, and corner crops.
- Review several recorded seeds without choosing the seed after seeing the final image.

### Repository checks after implementation begins

- Run focused geometry, sampling, and pipeline tests through `source source_me.sh && python3`.
- Run the complete test suite before accepting a production change.
- Render both PDF orientations and inspect rasterized pages, including the `60x86` readability
  boundary when changing printable density.
- Keep experimental artifacts under an ignored output directory and commit only durable plans,
  decisions, fixtures, and tests.

## Risk register

| Risk | Evidence to watch | Response |
| --- | --- | --- |
| Lloyd crystallization | Sixfold order rises | Stop earlier or test capacity constraints |
| Hard-core infeasibility | Count is not reached or runtime spikes | Bracket feasible distance |
| Sparse or oversized edge cells | Boundary/interior metrics diverge | Test mirrors or ghosts |
| Unreadable tiny polygons | Label-clearance tail fails | Improve labels or reduce cell count |
| Polygon sampling blurs edges | Edge error rises | Test sampling before adaptive density |
| Extra library weight | SciPy or scikit-image seems necessary | Require measured evidence |
| Weak reproducibility | Seeds or traversal change output | Fix seed and ordering contracts |
| Pipeline boundary leaks | Polygon data reaches square models | Restore Voronoi ownership |
| Premature utility sharing | A helper encodes squares | Keep it separate until proven independent |

## Resolved decisions

- The square grid remains the default and the experimental control.
- Equal-circle overlap is modeled directly as Euclidean minimum separation, not through Inkscape's
  axis-aligned rectangle solver.
- The proposed `0.25s` circle diameter is an experiment point, not a chosen production value.
- Geometry selection precedes changes to palette matching, enhancement, and output architecture.
- Square and Voronoi output creation use separate coordinators, data models, assignment semantics,
  and writers. `--layout` selects one pipeline without a generic `Layout` interface or
  polygon-to-grid coercion.
- The square pipeline retains rectangular NumPy arrays, row and column assignments, square
  sampling, four-neighbor enhancement, and all current CSV, summary, preview, and PDF behavior.
- The Voronoi pipeline owns ordered sites and polygons, polygon-area sampling, site-identifier
  assignments, centroid-based labels and diagnostics, dedicated output semantics, and shared-edge
  adjacency for strong enhancement.
- `-g COLUMNSxROWS` remains a shared configuration and count convention with `N = C * R`; it does
  not define a shared layout model. The analytical square cells remain an experiment-only control.
- Low-level utilities are shared only after their interfaces prove representation independence.
- Boundary behavior and visual randomness are measured explicitly rather than inferred from average
  cell area.
- The first polygon image comparison uses area-aware cell sampling.
- Shapely is the declared runtime library for bounded polygon construction and topology operations;
  an owned analytical half-plane implementation remains the independent small-case oracle.
- SciPy and scikit-image remain undeclared dependencies.
- Explicit replay seeds remain internal to generators, tests, artifact metadata, and maintainer
  inputs. The user-facing organic mode generates and records its seed without a production seed
  flag.

## Reconsideration triggers

- Revisit printable density only when a requested page size or grid makes centroid labels
  unreadable; the known single-page `60x86` limit calls for lower density or pagination first.
- Revisit point distribution only if image, boundary, or print evidence shows a material failure of
  the selected two-step bounded Lloyd result. Preserve the negative results in the Milestone 2
  decision records rather than rerunning an unbounded parameter search.
- Revisit additional presets only when a concrete user workflow needs both a more random and a more
  equal visual result.
- Revisit SciPy only when a measured production requirement cannot be met with Shapely; SciPy and
  scikit-image remain undeclared dependencies.
