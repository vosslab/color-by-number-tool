# Geometry model

## Purpose

This document defines the Voronoi geometry model. It is the design source of truth for coordinate
conventions, numeric policy, valid inputs, degeneracy handling, deterministic site movement,
polygon sampling ownership, and validation. The square command remains the default and retains its
rectangular array and implicit square geometry instead of adopting this model.

## Task profile

- Dimension: 2D.
- Operation: construct a static bounded partition, then query cell geometry for measurement,
  sampling, labeling, and rendering.
- Numeric model: approximate IEEE 754 double-precision coordinates.
- Execution model: deterministic batch processing.
- Scale: `N = columns * rows`, normally thousands of sites.
- Initial target and default control: 86 by 60, or 5,160 sites.
- Expected construction cost: an `O(N log N)` library Voronoi construction at normal sizes.
- Correctness strategy: compare small general-position cases with an independently implemented
  analytical half-plane clipper, use a trusted polygon library for topology and boolean checks,
  and use brute-force raster ownership as a supplemental check.

The model retains the existing positive grid-size parser and adds a numerical-conditioning gate
after orientation resolution. Runtime and memory policy belongs to the calling coordinator rather
than the site and partition representation.

## Current geometry inventory

### Primitives and ownership

- [../colorbynumber/pdf_writer.py](../colorbynumber/pdf_writer.py) owns the immutable `PageLayout`
  record in PDF points.
- [../colorbynumber/image_sampler.py](../colorbynumber/image_sampler.py) represents source samples
  as a `rows x columns x 3` NumPy array.
- [../colorbynumber/color_matcher.py](../colorbynumber/color_matcher.py) represents assignments and
  errors as rectangular NumPy arrays.
- [../colorbynumber/voronoi_geometry.py](../colorbynumber/voronoi_geometry.py) owns the
  domain, site, cell, partition, canonical-ring, and tolerance primitives.

### Existing algorithms

- [../colorbynumber/orientation.py](../colorbynumber/orientation.py) parses landscape
  `COLUMNSxROWS`, resolves page orientation, and swaps the pair for portrait output.
- [../colorbynumber/image_sampler.py](../colorbynumber/image_sampler.py) crops or contains the
  source and resamples it to one RGB triplet per square.
- [../colorbynumber/pdf_writer.py](../colorbynumber/pdf_writer.py) and
  [../colorbynumber/grid_only_pdf_writer.py](../colorbynumber/grid_only_pdf_writer.py) calculate one
  scalar cell size and draw axis-aligned grid lines.
- [../colorbynumber/color_matcher.py](../colorbynumber/color_matcher.py) uses four-neighbor array
  adjacency for local detail enhancement.
- [../colorbynumber/voronoi_geometry.py](../colorbynumber/voronoi_geometry.py) implements analytical
  degeneracy support, the exact grid control, general Shapely/GEOS construction, and validation.

### Serialization and input

- [../colorbynumber/cli.py](../colorbynumber/cli.py) owns CLI parsing and derives companion artifact
  paths from the requested PDF stem.
- [../colorbynumber/csv_writer.py](../colorbynumber/csv_writer.py) serializes assignments by
  one-based row and column. It has no polygon schema.
- [../colorbynumber/summary_writer.py](../colorbynumber/summary_writer.py) records rectangular grid
  dimensions and assignment counts. It has no seed or geometry metadata.
- [../colorbynumber/voronoi_experiment.py](../colorbynumber/voronoi_experiment.py) writes
  deterministic JSON records and SVG diagnostics for geometry maintenance.

### Prototype sampling and output

- [../colorbynumber/pdf_writer.py](../colorbynumber/pdf_writer.py) draws the marker-key worksheet.
- [../colorbynumber/grid_only_pdf_writer.py](../colorbynumber/grid_only_pdf_writer.py) draws aligned
  blank and numbered artwork pages.
- [../colorbynumber/preview_writer.py](../colorbynumber/preview_writer.py) enlarges the rectangular
  RGB grid with nearest-neighbor sampling.
- The Voronoi prototype starts with hard-core-accepted deterministic uniform x/y candidates and
  applies two alpha-`0.50` bounded Lloyd movements before constructing its settled partition.
- Polygon sampling assigns each fitted-raster pixel center to one ordered clipped cell, averages
  owned RGB values, and falls back to the pixel center nearest a site's location only when that
  polygon owns no sampled center.
- Strong color matching reuses the square thresholds but derives local dark-detail neighbors from
  shared polygon edges. Point-only corner contact is not adjacency.
- Preview and PDF writers consume stable site-ordered polygon assignments. Palette ownership is
  always `cell.site_identifier`; identifiers remain polygon identifiers rather than row-and-column
  coordinates.
- Each numbered-code anchor starts at the Shapely area centroid of its authoritative printable
  polygon. The writer transforms that polygon into PDF points and measures the actual ReportLab
  code width, ascent, and descent before placing the label.
- Every measured glyph box includes a preferred `0.25`-point inward padding. If the exact centroid
  box fails, the writer constructs every positive-area feasible center component by subtracting
  the axis-aligned padded-box dilation of the polygon complement; a deterministic interior point
  from each component is revalidated in the original polygon. The configuration-space construction
  handles concavities and holes without changing region geometry or relying on sampled anchors.
- If a region is too small for the complete padded box, the code uses the polygon's
  maximum-clearance interior point and PDF generation continues. Voronoi summaries record that
  best-effort placement alongside shifted-label count, total and maximum shift in points, and
  overlap pairs from the resolved boxes.

### Tests

- [../tests/test_color_by_number.py](../tests/test_color_by_number.py) covers grid parsing,
  orientation swaps, square PDF geometry, source-grid shape, page counts, and code fitting.
- [../tests/test_markdown_links.py](../tests/test_markdown_links.py) checks local documentation
  links.
- [../tests/test_ascii_compliance.py](../tests/test_ascii_compliance.py) checks text encoding.
- [../tests/test_voronoi_geometry.py](../tests/test_voronoi_geometry.py) contains inline geometry
  fixtures and an independent test-only analytical half-plane oracle.

## Count and aspect contract

The existing `-g COLUMNSxROWS` pair is a shared configuration and count convention, not a shared
layout representation. Let the entered landscape pair be `(C, R)`:

- The site count is always `N = C * R`.
- Landscape resolves to `columns = C` and `rows = R`.
- Portrait resolves to `columns = R` and `rows = C`.
- The portrait swap preserves `N` exactly.
- The square pipeline continues to interpret the resolved pair as rectangular array dimensions.
- Voronoi cells have stable site identifiers, not row and column indices.
- The resolved pair still defines the artwork aspect ratio even though it does not define polygon
  rows or columns.

Examples:

| Grid input | Site count | Landscape | Portrait |
| --- | ---: | --- | --- |
| `43x30` | 1,290 | 43 by 30 | 30 by 43 |
| `86x60` | 5,160 | 86 by 60 | 60 by 86 |
| `100x75` | 7,500 | 100 by 75 | 75 by 100 |

This interpretation preserves the existing CLI meaning and permits density comparisons without
introducing a second site-count option.

## Coordinate frame

### Normalized geometry

Geometry uses a unit-area Cartesian rectangle. For resolved `columns` and `rows`, define:

```text
aspect = columns / rows
width  = sqrt(aspect)
height = 1 / sqrt(aspect)
domain = [0, width] x [0, height]
```

The domain area is exactly 1 in the mathematical model, and `width / height` equals the resolved
artwork aspect ratio. The origin is the bottom-left corner. The positive x-axis points right and
the positive y-axis points up. Coordinates have normalized length units rather than pixels or PDF
points.

The Voronoi geometry API receives resolved positive `-g` dimensions and constructs this
domain internally. It does not accept a caller-supplied rectangle, area, or coordinate scale.
Arbitrary tiny or large external domains are outside the input contract; numerical stress cases
vary numerically representable aspect ratios and site spacing inside this unit-area domain.

Normalizing area makes distances and cell areas comparable across portrait and landscape while a
uniform output transform preserves aspect ratio. It also makes the nominal equal-area spacing
`s = sqrt(1 / N)` independent of orientation.

### Raster and PDF transforms

Raster images use a top-left origin, so normalized raster position `(u, v)` maps to geometry as:

```text
x = u * width
y = (1 - v) * height
```

PDF pages already use a bottom-left origin. A writer applies one uniform scale and a translation
from the normalized domain into its calculated grid rectangle. The transform never stretches one
axis independently. Crop and contain behavior continues to use the resolved artwork aspect ratio
before polygon sampling.

## Geometry primitives

### Domain

The domain is the one closed, axis-aligned, unit-area rectangle derived from the resolved positive
grid dimensions. Its sides are named `left`, `right`, `bottom`, and `top` in the geometry frame.

### Site

A site contains:

- a stable zero-based integer identifier;
- finite double-precision `x` and `y` coordinates;
- coordinates inside or on the closed domain.

Site identifiers follow generator output order and do not change during clipping, relaxation, or
serialization. Algorithms and writers order cells by site identifier rather than library traversal
order.

### Polygon and cell

A polygon is a simple closed region represented by an open vertex ring: the first vertex is not
repeated at the end. Exterior vertices use counterclockwise winding in the Cartesian geometry
frame. A clipped Voronoi cell is expected to be convex and have no holes.

A cell contains one site identifier and one polygon. The closed cell includes its boundary, while
cell interiors are disjoint. Shared edges therefore belong to both adjacent cell closures without
creating an area overlap. When a discrete sampling operation lands exactly on a shared edge, the
lowest site identifier wins the tie.

For deterministic serialization, vertices are counterclockwise and begin at the lexicographically
smallest canonical vertex. Exact consecutive duplicates, an exact repeated closing vertex, and an
exactly collinear vertex lying between its neighbors are removed during explicit canonicalization.
Coordinate tolerance is not a polygon-simplification distance, so positive thin cells retain their
topology and dimensions.

## Bounded Voronoi contract

For site `i`, its bounded cell is:

```text
cell_i = {p in domain : distance(p, site_i) <= distance(p, site_j) for every j}
```

Construction clips every unbounded Voronoi region to the normalized rectangle. A successful result
has exactly one nonempty cell per site. Each cell contains or touches its generating site, every
cell lies in the domain, cell interiors do not overlap, and the union of cells covers the domain.

The analytical construction for site `i` starts with the domain polygon and clips it against the
closed perpendicular-bisector half-plane in which `site_i` is no farther than every other site.
This independently implemented `O(N^2)` path is the small-case oracle for a selected general
constructor. If the selected general constructor also uses half-plane clipping, its small-case
oracle must be a second implementation or an equivalent independent mechanism. The analytical path
is also the required constructor for `N = 1`, `N = 2`, and fully collinear site sets, so those
mathematically valid bounded partitions do not depend on a library's unbounded Voronoi
preconditions.

Shapely is a declared runtime dependency for bounded polygon construction, clipping, topology, and
boolean validation. The general constructor requires Shapely 2.1 or newer and GEOS 3.12 or newer,
because stable site ownership uses `voronoi_polygons(ordered=True)`. The constructor checks this
capability and reports an explicit geometry error when it is unavailable. SciPy and scikit-image
remain undeclared. Shapely-backed construction and validation retain the independently implemented
analytical half-plane oracle, so one library is never the sole correctness authority.

The exact centered square-grid control uses its known analytical rectangular cells. It is an
experiment-only comparison control, not an integration with the production square pipeline. This
avoids making a cocircular equality control depend on a GEOS tie choice while preserving the same
bounded Voronoi definition. General-position and uniform-random partitions use the Shapely/GEOS
constructor.

The `100x75` audit reproduced the previously reported half-cell gap only after canonicalization;
the raw GEOS polygons had zero gap and nominal cell areas. A repeated closure plus a nearby
collinear vertex at the ring seam caused the old tolerance simplifier to remove both seam
representatives and turn one square into a triangle. Exact closure removal followed by proven
collinearity removal preserves the corner, and the bypassed general Shapely path also covers the
domain exactly. The exact grid constructor remains a proactive, deterministic control path rather
than a retry or repair.

### Raw distribution generators

The stratified-jitter comparator divides the domain into the resolved `C x R` rectangular strata
and emits exactly one site per stratum in row-major order. Its dimensionless jitter fraction `f`
scales independent x and y displacement from the stratum center. `f = 0` reproduces the exact
centered grid and `f = 1` spans the full stratum. The closed valid interval is `[0, 1]`; invalid
values fail instead of being clamped.

The direct Euclidean hard-core generator uses deterministic uniform dart throwing and an owned
square-bin neighbor index. Its requested center distance is `d = ratio * s`, where
`s = sqrt(1/N)`. Bins are one requested distance wide, so a candidate needs only its own and the
eight neighboring bins for an exact rejection query. Stable accepted-site order follows uniform
candidate traversal order.

Before creating its random-number generator, the hard-core path requires `d`, `d * d`, and
`max(width, height) / d` to be finite and strictly positive. Configuration construction uses the
same validation. This rejects positive subnormal ratios whose requested distance or squared
distance underflows, and distances whose maximum required square-bin coordinate overflows, before
`math.floor` or random candidate generation can run.

The `total-uniform-candidate-draws-v1` attempt policy counts every drawn candidate against one
explicit budget. Reaching the budget before exactly `N` acceptances raises a deterministic
hard-core generation error with the accepted count, target, seed, ratio, budget, and policy. The
generator performs no retry, repair, joggle, or seed change. The prototype supplies its configured
attempt budget explicitly, so its result is reproducible from its seed and parameters.

Geometry implementation version 5 owns these raw-generator semantics. Configuration schema 5
records the jitter fraction, hard-core `d/s`, absolute `d`, attempt budget, and attempt policy.

### Partial point relaxation

One bounded Lloyd iteration is a point-distribution operation over the settled bounded-partition
plumbing. It constructs and validates the current clipped partition, computes each convex cell's
centroid, and moves site `i` by:

```text
new_site_i = (1 - alpha) * site_i + alpha * centroid_i
```

The finite movement fraction `alpha` lies in the closed interval `[0, 1]`. The result preserves site
identifiers and order, remains in the closed domain, and passes the same site validation as every
other generator output. A caller constructs the moved checkpoint separately before measuring or
serializing it, so current-partition construction and checkpoint construction retain explicit
validation boundaries.

Geometry implementation version 6 owns this movement rule. Configuration schema 6 stores the full
ordered list of movement fractions already applied and derives the current cumulative step from
that list. The raw hard-core distance and budget fields describe the starting generator; they do not
claim that centroid movement preserves the original minimum distance. Artifact schema 4 remains
current because the evaluation record shape is unchanged.

## Boundary classification

Each cell records the set of domain sides that its polygon touches within the centralized geometry
tolerance. Its primary class and subtype are:

- `interior`: touches no domain side;
- `boundary`: touches one or more domain sides;
- `edge` subtype: a boundary cell that does not contain a domain corner;
- `corner` subtype: a boundary cell that contains a domain corner.

The complete side set remains available for diagnostics, including unusual cells that touch
opposite or more than two sides. Boundary-band density is a separate metric based on site distance
to the domain boundary; it does not change the topological class.

## Numeric tolerance

All geometry code uses one centralized tolerance policy. The future geometry module owns one
dimensionless relative tolerance constant:

```text
relative_tolerance = 1e-10
domain_area = 1
nominal_spacing = sqrt(domain_area / N)
coordinate_roundoff_floor = 8 * math.ulp(max(width, height))
coordinate_tolerance = max(
    relative_tolerance * nominal_spacing,
    coordinate_roundoff_floor,
)
area_roundoff_floor = 8 * math.ulp(domain_area)
area_tolerance = max(
    relative_tolerance * domain_area,
    area_roundoff_floor,
)
```

Coordinate comparisons, boundary contact, point containment, and duplicate-site detection derive
from `coordinate_tolerance`. Area conservation, overlap area, and uncovered area derive from
`area_tolerance`. Squared-distance comparisons derive their threshold from the same coordinate
tolerance. Individual algorithms do not introduce local epsilon values.

The analytical half-plane predicate evaluates the algebraic residual against exact zero. That
residual has squared-length units, so comparing it with a coordinate tolerance would be
dimensionally invalid and would make two complementary cells overlap. It uses the midpoint form of
the bisector equation to avoid cancellation between nearly equal squared site coordinates.

The factor of eight budgets several rounded coordinate or area operations without scaling the
relative term by the domain's long side. Because `domain_area` is always 1, the area tolerance does
not grow with site count, perimeter, or aspect ratio. The coordinate tolerance follows nominal cell
spacing until representable coordinate magnitude requires the ULP floor. A measured oracle failure
can revise this policy in one place.

## Valid inputs

A Voronoi request is valid when:

- the entered grid dimensions pass the existing positive landscape-pair validation;
- orientation resolves to landscape or portrait;
- `N` equals the product of the entered dimensions;
- the domain is constructed from that resolved pair by the unit-area formula;
- `2 * coordinate_tolerance < min(width, height, nominal_spacing)`;
- every generated coordinate is finite and lies in the closed domain;
- site identifiers are unique and contiguous;
- sites are unique beyond the coordinate tolerance.

The strict conditioning check keeps two coordinate-tolerance bands disjoint within both the short
domain side and nominal spacing. Parser-valid requests that fail it raise a numeric-conditioning
error reporting the resolved dimensions, tolerance, short side, and nominal spacing. Ordinary
`43x30`, `86x60`, and `100x75` requests pass, as does the representable stress pair
`1000000000000x1`. The parser-valid `10000000000000000x1` fixture fails the conditioning check.
These examples specify a representability boundary rather than a fixed maximum aspect ratio. Custom
domain rectangles and coordinate scales remain invalid inputs. The production square layout keeps
the existing positive `-g` behavior unchanged. Voronoi `N = 1`, `N = 2`, and collinear cases
remain valid when they pass the same conditioning and site contracts.

## Degeneracy policy

- Duplicate or near-duplicate sites are rejected with both site identifiers; cells are never
  silently dropped or merged.
- Nonfinite or out-of-domain sites are rejected; coordinates are never silently clamped.
- One-site, two-site, and fully collinear site sets use analytical half-plane clipping and produce
  their mathematically valid bounded partitions.
- Cocircular sites are valid. Equivalent Delaunay tie choices are accepted when canonical cells,
  topology, and area agree within tolerance.
- Sites exactly on the domain boundary are valid, though stochastic generators normally produce
  interior sites.
- Empty, nonfinite-area, zero-area, self-intersecting, disconnected, or holed cell output is
  invalid.
- A library precision or topology failure is reported as a geometry error. Low-level geometry
  errors do not claim candidate or seed context that the geometry layer does not own.
- Deterministic canonicalization removes exact repeated closure and consecutive duplicate vertices,
  plus exactly collinear vertices proven to lie between their neighbors. It does not use coordinate
  tolerance to simplify a ring and never removes a cell.

This policy follows the repository principle **Fix the design, not the symptom**: invalid geometry
becomes evidence for changing the generator or constructor instead of being hidden by a fallback.

## Determinism and naming

Every stochastic generator receives an explicit nonnegative integer seed and creates its own local
random-number generator. It does not read or modify global random state. The generator family is
recorded with the seed so replay does not depend on a library default changing.

Explicit seeds are a generator, test, artifact-metadata, and maintainer-input interface. A future
user-facing organic mode generates its seed internally and records it for diagnostics and replay;
the production CLI does not expose a seed flag.

The experiment records a fixed seed set before candidate renderings are reviewed and applies the
same seeds to every stochastic candidate for which they are meaningful.

The same resolved dimensions, algorithm, parameters, seed, and supported dependency versions must
produce equivalent canonical sites, cells, quality metrics, and SVG geometry within the geometry
tolerance. Wall-clock timings are explicitly single-run observations and may vary. Timing metadata
records five disjoint phases: raw site generation, mandatory site validation once at construction
entry, cell construction, partition validation, and quality measurement. A stochastic generator
returns its first seeded output unchanged; construction rejects invalid or near-duplicate sites
instead of silently generating a replacement. Square-grid controls use `seed_none`.

For relaxed checkpoints, these five fields cover the raw starting-generator call and the final
checkpoint construction and evaluation. They do not claim to measure the cumulative intermediate
relaxation cost.

Experimental artifact names use lowercase ASCII and this stable pattern:

```text
{readable_prefix}_cfg-{digest}_{kind}.{extension}
readable_prefix = {algorithm}_c{columns}_r{rows}_n{site_count}_seed{seed}_stage-{stage}
```

`stage` is a readable lowercase slug such as `initial`, `hardcore-d0p25s`, or
`lloyd-step003-a0p50`; it is not the uniqueness mechanism. `kind` distinguishes coordinates,
metrics, geometry diagnostics, and comparison boards.

`digest` is the full lowercase SHA-256 hexadecimal digest of a canonical ASCII JSON configuration.
Configuration keys are sorted by ASCII code point, JSON separators contain no optional whitespace,
integers use minimal decimal form, and finite double-precision values are JSON strings containing
their exact hexadecimal encoding. The configuration includes every behavior-changing input:
configuration schema, artifact schema, owned Voronoi geometry implementation version, constructor
and generator family, resolved dimensions, seed, stratified-jitter fraction, hard-core distance and
distance ratio, hard-core attempt budget and policy, boundary policy, complete relaxation schedule
and current step, tolerance-policy version, dependency versions, and all other candidate parameters.
Optional parameters appear explicitly as `null`.

The Voronoi geometry implementation version is independent of the application release version. It
increments whenever a geometry semantic, canonical geometry output, or quality-metric definition
changes, so old and new behavior cannot silently share artifact names.

This grammar prevents two hard-core distances or progressive relaxation stages from sharing an
artifact name while preserving readable dimensions, seed, and stage. Examples of extensions include
`json` for geometry evaluations, `svg` for geometry diagnostics, and `png` for raster comparison
boards. Artifacts live under the ignored `output/voronoi_experiment/` directory. Each evaluation
record stores deterministic geometry and quality metrics separately from single-run timing metadata.
The artifact and configuration schema versions change when record semantics change, and the owned
geometry implementation version changes when canonical geometry semantics change, so old and new
records cannot share a configuration digest. Each record also stores the canonical configuration
text and exact dependency versions.

## Validation contract

Every successful construction passes these checks:

- Cell count and site count both equal `N`.
- Every cell polygon is finite, simple, nonempty, positive-area, and valid. Positive cells may be
  smaller than the aggregate area tolerance.
- Every cell's coordinate bounds stay inside the domain within the coordinate tolerance, independent
  of how little area an excursion contributes.
- Every cell has outside-domain area no greater than the separate area tolerance.
- Every cell contains or touches its generating site within the coordinate tolerance.
- Cell interiors have no overlap area above the area tolerance.
- The cell union leaves no uncovered domain area above the area tolerance.
- The sum of cell areas agrees with the domain area within the area tolerance.
- Boundary side sets agree with an independent polygon-boundary query.

Small general-position fixtures compare every selected-constructor cell with the independently
implemented analytical half-plane clipping oracle. The construction and this oracle do not share
polygon clipping code. Shapely independently checks topology, union, intersection, containment, and
area, but it is never the construction's sole correctness oracle. A brute-force nearest-site raster
supplements these analytical and polygon checks with sampled ownership evidence, but it is not the
topology oracle. One-site, two-site, and collinear fixtures use the analytical construction path and
still receive the independent Shapely checks.

Validation reports the failed invariant and the site identifier when available. Candidate names,
resolved dimensions, and seeds belong to experiment orchestration rather than every low-level
geometry error. Validation never reports a partial partition as successful.

## Pipeline boundary

The square path continues to use rectangular NumPy arrays, row and column assignment semantics,
square sampling, four-neighbor enhancement, and its existing CSV, summary, preview, and PDF
writers. Its PDF coordinates are physical points with the print contract documented in
[VISION_PIPELINE.md](VISION_PIPELINE.md), and it remains the default behavior.

The polygon path uses normalized ordered sites and polygons. It owns polygon-area sampling,
site-identifier assignments, polygon-specific label placement and diagnostics, and dedicated
preview and PDF semantics. Its strong enhancement uses shared-edge adjacency rather than
rectangular four-neighbor logic.

A future CLI may choose between the square and Voronoi coordinators, but the two paths retain
separate data models and writers. The architecture does not introduce a generic `Layout` interface
and does not coerce polygons into a grid. Reuse is limited to low-level, representation-independent
utilities demonstrated by their interfaces, such as input loading and EXIF correction, palette
definitions, color-distance and nearest-match primitives, page constants and orientation
conventions, and dependency or repository-path helpers. Fit transforms may become shared only
after evidence shows that their interfaces do not encode square sampling. This geometry contract
does not change the CLI, file formats, or current square-grid behavior. Shapely is already declared
for the bounded polygon construction and topology work defined here.
