# Code architecture

## Overview

The project is a Python 3.12 command-line application that converts one image into either a
square grid or an optional Voronoi polygon layout of marker assignments. Each production path
assigns one palette entry with CIE Delta E 76 matching and writes printable and machine-readable
artifacts.

The executable [../color_by_number.py](../color_by_number.py) is a small entry-point shim. Runtime
behavior lives in the [../colorbynumber/](../colorbynumber/) package. The
[../colorbynumber/cli.py](../colorbynumber/cli.py) dispatcher selects the square coordinator by
default or the dedicated Voronoi coordinator through `--layout voronoi`. Voronoi owns its own site,
polygon, sampling, matching, preview, CSV, summary, and PDF contracts. It is intentionally not
represented as a rectangular grid or a generic layout abstraction.

## Pipeline boundaries

Output creation has two deliberately separate, representation-incompatible paths:

- The production square path owns rectangular NumPy sample, assignment, and error arrays;
  row-and-column semantics; square sampling; four-neighbor enhancement; and the existing CSV,
  summary, preview, and PDF writers. It remains the default.
- The optional Voronoi path owns ordered sites and partition polygons, polygon-area samples,
  one-dimensional site-identifier assignments, polygon-centroid label anchors, and dedicated
  polygon CSV, summary, preview, and PDF writers. Its strong enhancement uses shared polygon edges
  for adjacency. It generates and records an internal seed for the bounded site distribution.

Each pipeline keeps its own coordinator, data model, and writers. The design has no generic
`Layout` interface and does not coerce polygons into a rectangular grid. The shared
`-g COLUMNSxROWS` input provides a count and aspect convention with `N = C * R`; it does not
provide a common cell representation.

Reuse is limited to low-level utilities whose interfaces are demonstrated to be
representation-independent. Candidates include image loading and EXIF correction, palette
definitions, color-distance and nearest-match primitives, page constants and orientation
conventions, and dependency or repository-path helpers. A fit transform may become shared after
its interface is shown not to encode square sampling. This boundary does not promise reuse merely
because both pipelines process the same source image.

## Major components

### Command orchestration

- [../colorbynumber/cli.py](../colorbynumber/cli.py) defines the CLI, resolves companion output
  paths, and calls every processing and writing stage.
- [../colorbynumber/constants.py](../colorbynumber/constants.py) stores default grid dimensions,
  orientation names, and default paths.
- [../colorbynumber/repo_paths.py](../colorbynumber/repo_paths.py) resolves the repository root with
  `git rev-parse --show-toplevel` for shipped palette data.

### Image and grid preparation

- [../colorbynumber/image_sampler.py](../colorbynumber/image_sampler.py) applies EXIF orientation,
  flattens transparency onto white, and uses Pillow to crop or contain the image at the grid size.
- [../colorbynumber/orientation.py](../colorbynumber/orientation.py) validates `COLUMNSxROWS`, chooses
  page orientation from the corrected image, and swaps grid axes for portrait output.

### Voronoi geometry and output path

- [../colorbynumber/voronoi_geometry.py](../colorbynumber/voronoi_geometry.py) owns the unit-area
  domain, centralized tolerance and canonicalization policy, raw deterministic grid, uniform,
	stratified-jitter, and hard-core site generators, bounded construction with one mandatory
	site-validation pass, boundary classification, and partition validation. Hard-core generation
	owns its uniform spatial-bin index, explicit total-candidate attempt policy, and shared numeric
	preflight for its distance, squared distance, and maximum required bin coordinate. The same module
	also owns one deterministic bounded-centroid movement step for point-distribution experiments.
- [../colorbynumber/voronoi_metrics.py](../colorbynumber/voronoi_metrics.py) owns separate area,
  spacing, exact bounded covering-radius, and boundary quality metrics, and packages the five
  disjoint single-run phase timings without a composite score.
- [../colorbynumber/voronoi_experiment.py](../colorbynumber/voronoi_experiment.py) owns canonical
  raw site-generation timing, generator-parameter dispatch, canonical full-configuration
  serialization, SHA-256 artifact naming, stable JSON records, and SVG diagnostics. Configuration
	schema 6 distinguishes raw-generator inputs and the complete cumulative relaxation schedule while
	artifact schema 4 retains the established evaluation shape.
- The centered square-grid control has an exact analytical rectangular constructor. One-site,
  two-site, and collinear partitions use analytical half-plane clipping; general-position and
  uniform partitions use Shapely/GEOS followed by explicit domain clipping.
- The `colorbynumber.voronoi_pipeline` module is the dedicated optional-output coordinator. It
  resolves an internal seed, creates the bounded site distribution, builds the ordered partition,
  samples and matches polygons, and calls only Voronoi writers.
- [../colorbynumber/voronoi_prototype.py](../colorbynumber/voronoi_prototype.py) owns bounded-site
  construction and image data flow. It accepts deterministic uniform x/y candidate draws through
  the hard-core acceptance rule, applies two alpha-`0.50` bounded Lloyd movements, constructs the
  settled clipped partition, averages owned fitted-raster pixel centers per polygon, assigns a
  palette code, and reconstructs a palette-colored raster.
- [../colorbynumber/voronoi_preview_writer.py](../colorbynumber/voronoi_preview_writer.py) draws
  polygon boundaries on palette-colored previews and writes equal-scale comparison panels.
- [../colorbynumber/voronoi_pdf_writer.py](../colorbynumber/voronoi_pdf_writer.py) writes blank,
  numbered, and palette-reference Letter pages from ordered polygon assignments, placing codes at
  the area centroid of their owned polygons.
- [../colorbynumber/voronoi_csv_writer.py](../colorbynumber/voronoi_csv_writer.py) writes
  site-ordered polygon assignments and palette usage.
- [../colorbynumber/voronoi_summary_writer.py](../colorbynumber/voronoi_summary_writer.py) records
  resolved Voronoi inputs, the internal seed, color error, and label diagnostics.

### Palette matching

- [../colorbynumber/marker_color.py](../colorbynumber/marker_color.py) defines the immutable marker
  code, name, and RGB record.
- [../colorbynumber/palette_loader.py](../colorbynumber/palette_loader.py) loads and validates the
  YAML palette, including unique codes and three bounded RGB channels.
- [../colorbynumber/color_metrics.py](../colorbynumber/color_metrics.py) converts sRGB to CIE Lab
  under D65 and measures Delta E 76 distances.
- [../colorbynumber/color_matcher.py](../colorbynumber/color_matcher.py) optionally expands local
  shadow detail and warm chroma, then assigns the nearest palette entry to each cell.
- [../palettes/aoartix_48.yml](../palettes/aoartix_48.yml) is the default 48-marker data source.

### Output writers

- [../colorbynumber/pdf_writer.py](../colorbynumber/pdf_writer.py) uses ReportLab to draw the
  single-page Letter worksheet with square numbered cells and a colored marker key.
- [../colorbynumber/grid_only_pdf_writer.py](../colorbynumber/grid_only_pdf_writer.py) uses the same
  ReportLab grid renderer for two aligned Letter pages: a gray blank grid and a black numbered grid.
- [../colorbynumber/preview_writer.py](../colorbynumber/preview_writer.py) writes nearest-neighbor PNG
  previews so each sampled cell remains crisp.
- [../colorbynumber/csv_writer.py](../colorbynumber/csv_writer.py) writes per-cell assignments and
  palette usage counts.
- [../colorbynumber/summary_writer.py](../colorbynumber/summary_writer.py) records input settings,
  grid invariants, and Delta E error measurements.
- [../colorbynumber/voronoi_preview_writer.py](../colorbynumber/voronoi_preview_writer.py) and
  [../colorbynumber/voronoi_pdf_writer.py](../colorbynumber/voronoi_pdf_writer.py), plus
  [../colorbynumber/voronoi_csv_writer.py](../colorbynumber/voronoi_csv_writer.py) and
  [../colorbynumber/voronoi_summary_writer.py](../colorbynumber/voronoi_summary_writer.py), own
  the polygon outputs. They do not adapt square writers.

## Production square data flow

1. [../colorbynumber/cli.py](../colorbynumber/cli.py) parses the input, output, palette, fit, grid,
   enhancement, and orientation options.
2. The palette loader validates YAML into ordered marker records while the image sampler loads an
   EXIF-corrected RGB image.
3. The orientation module chooses Letter orientation and final grid dimensions.
4. Pillow resamples the fitted image to a NumPy array with one RGB triplet per cell.
5. The matcher converts source and palette values to Lab, applies the selected enhancement, and
   produces a palette-index grid plus original-source Delta E errors.
6. The index grid drives both ReportLab PDFs, the marker preview, two CSV files, and the summary.
7. The sampled RGB grid independently drives the source preview.

The index grid is the central invariant between renderers: every writer reads the same row and
column assignment, so each cell keeps one marker code across PDF, PNG, and CSV outputs.

## Optional Voronoi data flow

1. The CLI dispatches `--layout voronoi` to the dedicated Voronoi coordinator; the square path
   remains the default.
2. The coordinator generates and records its internal seed, then creates a normalized domain from
   the resolved `-g` count and aspect convention.
3. It accepts deterministic uniform x/y candidate draws only when they satisfy the hard-core
   minimum distance, then applies two bounded Lloyd movements with alpha `0.50`.
4. It constructs the settled clipped Voronoi partition in stable site order.
5. It fits the source image at a higher-resolution raster and assigns every pixel center to one
   polygon. Shared-edge centers use the lowest site identifier; numerical seam pixels use the
   nearest-site rule with the same tie break.
6. It averages each polygon's owned pixel-center RGB values. A polygon with no owned center uses
   the fitted pixel nearest its site, retaining the fallback identifier for diagnostics.
7. It applies the square strong-preset thresholds to polygon samples, using shared-edge polygon
   neighbors for dark-detail comparison, then assigns one nearest palette color per site.
8. One-dimensional ordered assignments drive the dedicated polygon CSV, summary, preview, and PDF
   writers. PDF code anchors use each polygon's area centroid.

The stable identifier is the Voronoi path's cross-writer invariant. It is not a row-and-column
index, and it is never converted into a fake grid.

## Testing and verification

- [../tests/test_color_by_number.py](../tests/test_color_by_number.py) verifies perceptual matching,
  enhancement selectivity, grid parsing, orientation, square-cell geometry, page counts, and codes.
- [../tests/test_voronoi_geometry.py](../tests/test_voronoi_geometry.py) checks conditioning,
  degeneracies, topology, ownership, and cell-by-cell agreement with an independent half-plane
  oracle.
- [../tests/test_voronoi_experiment.py](../tests/test_voronoi_experiment.py) checks deterministic
  geometry and quality metrics, exact analytical controls, canonical digests, construction-time
  rejection of invalid generator output, and controlled-clock phase boundaries.
- [../tests/test_markdown_links.py](../tests/test_markdown_links.py) validates local documentation
  links, while [../tests/test_ascii_compliance.py](../tests/test_ascii_compliance.py) checks encoding.
- [../pip_requirements-dev.txt](../pip_requirements-dev.txt) includes `pypdf` for PDF page-size and
  page-count assertions.
- The repository verification command is `source source_me.sh && python3 -m pytest tests/`.

## Extension points

- Add a marker set as a compatible YAML file under [../palettes/](../palettes/) and select it with
  the palette CLI option; no matching-code change is required.
- Add a tested enhancement preset in
  [../colorbynumber/color_matcher.py](../colorbynumber/color_matcher.py) and expose its name through
  [../colorbynumber/cli.py](../colorbynumber/cli.py).
- Add a square-pipeline companion artifact as a dedicated writer module, then register its path and
  call in [../colorbynumber/cli.py](../colorbynumber/cli.py).
- Keep square printable geometry in the two existing PDF writer modules and reuse their
  `PageLayout` record when square pages must align.
- Keep the Voronoi coordinator separate from the square coordinator. It may share
  representation-independent utilities without changing square arrays or output semantics.

## Known gaps

- Verify the default palette against photographed marker swatches on the final paper before treating
  chart-derived RGB values as physical color measurements.
