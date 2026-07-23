## 2026-07-23

### Behavior or Interface Changes

- Changed impossible PDF label fits from a fatal error to a recorded best-effort placement. Labels
  still preserve the centroid or shift to a fully contained padded box whenever possible; regions
  too small for the full code now use their maximum-clearance interior point so PDF generation
  completes.

## 2026-07-22

### Additions and New Features

- Added a Python 3.12 converter that creates a strict 43 by 30 code-only PDF worksheet, source and
  marker previews, per-cell assignments, a marker legend, and color-distance metrics.
- Added opt-in `-m`/`--merge-regions` output merging for edge-adjacent same-color square and Voronoi
  shapes. PDFs, Voronoi boundary previews, legends, and summaries now report rendered regions while
  assignment CSVs preserve their original per-square or per-polygon audit rows.
- Added [REGION_PIPELINE.md](REGION_PIPELINE.md), a start-to-finish reference for the shared
  printable-region lifecycle and its source-to-output invariants.
- Added the 48-color Aoartix palette in YAML using median RGB values sampled from the supplied
  product chart, including numeric, grey-series, and blue-grey codes.
- Added focused unit tests and installation, usage, and vision-pipeline documentation.
- Split the implementation into dedicated modules for palette loading, image sampling, perceptual
  matching, PDF output, PNG previews, CSV output, and summary metrics while keeping the root command
  as a small executable entry point.
- Added explicit default argparse values for `palettes/aoartix_48.yml` and
  `output/pdf/color_by_number.pdf`; companion output names derive from the PDF stem.
- Changed the primary print artifact to one orientation-matched Letter page with 0.65-inch margins,
  a white square-cell grid on the left, and a two-column colored marker key on the right.
- Added automatic page orientation from EXIF-corrected source dimensions, using a 43 by 30 landscape
  grid for wide or square images and a 30 by 43 portrait grid for tall images.
- Added `-L`/`--landscape` and `-P`/`--portrait` override flags for composition-driven layout.
- Replaced the package-relative repository-root shortcut with the documented read-only
  `git rev-parse --show-toplevel` resolution helper.
- Refined the ReportLab worksheet using measured glyph widths and font ascenders for consistent
  code fitting and centering, a stronger marker-key header, color names, and PDF metadata.
- Added `none`, `balanced`, and `strong` color-enhancement presets. The strong default combines a
  gamma 0.50 selective shadow curve with a 1.15 warm-chroma scale; `-e none` preserves the original
  nearest-color baseline.
- Refreshed the README as a newcomer-facing landing page with a verified included-image quick start,
  representative output, visible palette limitations, and direct documentation routes.
- Added a two-page full-grid Letter PDF: a light-gray blank grid for the final artwork followed by
  an exactly aligned black numbered reference grid, both maximized inside 0.6-inch margins.
- Added a repository-wide documentation set covering architecture, file structure, file formats,
  development, troubleshooting, frequently asked questions, the roadmap, related projects, news,
  and release history.
- Added a privacy-safe README proof image showing the aligned blank and numbered artwork pages.
- Added three museum-hosted public-domain portrait suggestions to the README for reproducible tests
  of dark-tone detail, skin and red separation, and rapid hue changes.
- Added an evidence-led experiment plan for evaluating organic bounded Voronoi layouts against the
  square grid, including point-spacing candidates, boundary metrics, and image and print gates.
- Added the normalized geometry model for square and experimental Voronoi layouts, including the
  grid-derived site count, tolerance, degeneracy, deterministic seed, and oracle validation
  contracts.
- Added experimental bounded Voronoi geometry, metric, and artifact layers with centralized numeric
  policy, canonical site-ordered cells, grid and seeded-uniform generators, complete configuration
  digests, deterministic geometry and quality records, separate single-run timing metadata, and
  reproducible SVG diagnostics.
- Added focused permanent tests for conditioning, degeneracies, topology, ownership, independent
  analytical-oracle agreement, fixed-seed generation, metrics, and artifact stability.
- Added raw stratified-jitter and Euclidean hard-core Voronoi experiment generators. Stratified
  jitter has one site per `C x R` stratum and a documented `[0, 1]` displacement fraction;
  hard-core sampling uses an owned uniform spatial-bin index, a `d/s` center-distance input, and an
  explicit total-candidate attempt budget with deterministic failure.
- Added the Milestone 2A fixed-seed distribution screen, schema-current JSON/SVG evidence, and a
  self-contained equal-scale board for grid, uniform, jitter `0.50`/`1.00`, and hard-core
  `0.50`/`0.70` at precommitted seed `20260722`.
- Added one deterministic bounded Lloyd point-movement primitive that moves stable ordered sites
  partway toward their clipped-cell centroids and validates every moved checkpoint.
- Added the Milestone 2B fixed alpha-`0.50` point-spacing screen at cumulative steps `1`, `2`, and
  `4`, with nine JSON/SVG evaluations, three equal-scale fixed-seed boards, an aggregate summary,
  and a durable decision record.
- Added a separate Milestone 3 bounded-Voronoi image and print prototype with polygon-area
  sampling, shared-edge strong enhancement, equal-scale previews, label diagnostics, and an
  evidence-led decision record.
- Added a separate production Voronoi coordinator with hard-core `d/s = 0.70` site spacing,
  two bounded Lloyd rounds at alpha `0.50`, polygon-area color sampling, and shared-edge strong
  enhancement. It retains the square coordinator and its rectangular data model unchanged.
- Added six Voronoi-specific run artifacts: a three-page PDF, polygon and source previews,
  site-ordered polygon assignments CSV, palette legend CSV, and a replayable run summary.

### Behavior or Interface Changes

- Added `-g`/`--grid COLUMNSxROWS` for configurable landscape grid dimensions, with automatic
  dimension swapping for portrait output, and changed the default from 43 by 30 to 86 by 60.
- Reworked the README, installation guide, and usage guide around the current ReportLab workflow,
  and reduced `AGENTS.md` to concise pointers to the canonical repository rules.
- Added optional `--layout voronoi`; omitting it retains the established square output as the
  default. Voronoi runs generate an internal random seed and record it in their summary and CLI
  result without adding a user seed flag.

### Fixes and Maintenance

- Initially made square and Voronoi code labels fail when no strictly contained padded placement
  fit. Writers measure ReportLab glyph boxes in PDF points, preserve fitting centroids, and
  deterministically shift non-fitting labels; the 2026-07-23 policy supersedes the fatal case.
- Corrected region-pipeline references so previews, PDFs, CSV audit rows, and summaries describe
  their distinct rendered-region and raster or raw-assignment responsibilities accurately.
- Corrected analytical half-plane clipping to use an exact-zero, midpoint-stable algebraic
  predicate, preserving complementary cells for sites just beyond the duplicate tolerance.
- Separated coordinate-bound containment, positive individual-cell area, and aggregate area-error
  validation so thin excursions fail while valid tiny cells remain accepted.
- Replaced the sampled covering-radius estimate with the exact maximum distance from each generator
  to a vertex of its owned convex cell, in time proportional to the total vertex count.
- Separated deterministic quality metrics from variable timing metadata, defined one-site
  nearest-neighbor metrics as `None`, and versioned geometry semantics in configuration digests.
- Added an explicit Shapely 2.1 and GEOS 3.12 capability check for ordered Voronoi output while
  keeping SciPy and scikit-image outside the dependency set.
- Made polygon canonicalization topology-preserving by removing only exact duplicate closure
  vertices and exactly collinear between-neighbor vertices. Close boundary-adjacent two-site and
  three-site partitions now retain their positive thin cells.
- Added explicit site-validation and partition-validation phase timings, renamed metric timing to
  quality-measurement timing, and advanced artifact, configuration, and owned geometry semantics to
  version 3 so earlier digests cannot represent the changed records.
- Removed validation from the raw grid and uniform generators so construction performs the one
  mandatory site-validation pass. Generation, site validation, construction, partition validation,
  and quality measurement are now five disjoint phases; schema version 4 prevents reuse of the
  overlapping schema-v3 evidence names.
- Advanced the owned Voronoi geometry implementation to version 4 and configuration schema to 5 so
  jitter fraction, hard-core distance ratio and absolute distance, attempt budget, and attempt
  policy cannot share digests. Artifact schema 4 remains current because the evaluation record
  shape is unchanged; the schema-4 baseline behavior and ignored evidence remain intact.
- Advanced the owned Voronoi geometry implementation to version 6 and configuration schema to 6 so
  every cumulative bounded Lloyd alpha schedule and current step are digest-relevant. Artifact
  schema 4 remains current because the evaluation record shape is unchanged.
- Replaced site-centered Voronoi PDF labels with clipped-polygon area centroids. The real `30x43`
  Kimi CLI smoke improved from 63 to 54 labels outside their owned polygon and from six to three
  positive-area label overlaps.

### Decisions and Failures

- Selected direct nearest-color matching in CIE L*a*b* space without dithering so every square has
  one independently explainable marker code.
- Treated chart RGB values as an initial approximation because actual alcohol ink varies with paper,
  lighting, and camera capture.
- Rejected global error diffusion after it introduced background and skin speckling on
  `kimi-face.png`; rejected hue-weighted matching after it increased black hair assignments and
  changed cells outside the target region.
- Compared selective shadow and warm-tone treatments against the fixed baseline. The strong preset
  reduced black hair cells from 165 to 72, increased brown-family cells from 86 to 126, and reduced
  pale face cells from 64 to 31 while mean Delta E 76 rose from 14.427 to 15.424.
- Kept personal test portraits out of the README and used an abstract rendering of the generated
  PDF pages as the checked-in visual example.
- Kept the file-format documentation together in one guide and omitted empty TODO and cookbook
  documents because the roadmap and usage guide already own the supported material.
- Chose two deliberately separate output architectures for future work: the current square path
  retains rectangular arrays and its existing row-and-column behavior, while any selected Voronoi
  path will own ordered polygons, area sampling, labels, diagnostics, formats, and writers. A future
  CLI may select one coordinator, but the paths will not use a generic layout interface or coerce
  polygons into a grid. This is an architecture decision, not a claim that production Voronoi
  output exists.
- Declared Shapely for bounded polygon construction and topology operations while retaining the
  independent analytical half-plane oracle; SciPy and scikit-image remain undeclared.
- Kept explicit replay seeds in generator APIs, tests, artifact metadata, and maintainer experiment
  inputs. A future user-facing organic mode generates and records its seed without adding a
  production seed flag.
- Traced the reported `6.66666666666672e-05` `100x75` half-cell gap to circular ring
  canonicalization, not GEOS 3.13.1. Raw GEOS cells had zero gap and nominal area; the old seam
  deduplication removed both near-identical closure representatives and made one square triangular.
  Exact closure and proven-collinearity handling preserves the seam corner without treating
  coordinate tolerance as a simplification distance, and the bypassed Shapely path has zero gap.
  The exact analytical grid remains a proactive deterministic control, not a retry.
- Kept SciPy and scikit-image out of the dependency set because Shapely spatial indexes provide the
  required nearest-neighbor measurements and exact bounded covering radius needs only owned cell
  vertices.
- Bracketed raw hard-core sampling at `43x30`: `d/s = 0.70` reached all 1,290 sites for all three
  fixed seeds, while `0.85` exhausted the declared `100N` budget at 1,193-1,199 sites without a
  retry or repair. Retained `0.50` as the visual-disorder comparator and `0.70` as the next partial
  Lloyd starting point.
- Kept area CV, area p90/p10, exact covering radius, requested hard-core distance, boundary/interior
  median area, and equal-scale visuals as the primary Milestone 2A evidence. Nearest-neighbor CV,
  nearest-neighbor minimum/median, and boundary-band density remain secondary diagnostics and did
  not select candidates; randomness and grid signature remain human visual observations.
- Retained stratified jitter `0.50` as the equality/grid-signature comparator rather than selecting
  it from its stronger area metrics, because the equal-scale board shows visible rows and columns.
  No Lloyd schedule, boundary correction, production CLI, or production Voronoi layout was added.
- Preserved a tested-alternatives ledger with reconsideration conditions for every raw candidate.
  Withdrew the early metric-only elimination of hard-core `0.50` and jitter `1.00` after visual-policy
  review, restored their required scale checks, and recorded that superseded interpretation as a
  methodological negative result rather than erasing it.
- Selected two cumulative alpha-`0.50` bounded Lloyd movements from hard-core `d/s = 0.70` as the
  good-enough `43x30` point-spacing knee. Step `1` retains conspicuous uneven patches, while step `4`
  improves every recorded equality and covering measurement but shows stronger local honeycomb
  regularity than the requested edgy option needs.
- Kept the selected Voronoi distribution unchanged after the image prototype: all tested ownership
  and sampling paths had zero fallbacks, while site-centered numbered PDF labels failed containment
  and overlap diagnostics. The next experiment is polygon-label layout and printable density, not
  further point-spacing tuning.
- Kept local unclumping, alternate movement fractions, boundary forces, and production integration
  outside the fixed Milestone 2B screen because step `2` answered the current spacing question;
  retained explicit reconsideration triggers if image or print validation changes that conclusion.
- The earlier optional-Voronoi prototype accepted area-centroid label alignment despite boundary
  crossings and dense `60x86` labels. The strict contained-label resolver now supersedes that
  prototype decision; it preserves fitting centroids and shifts non-fitting labels. Its initial
  rejection of impossible placements was superseded by the 2026-07-23 best-effort policy.
  Printable density remains a separate design consideration.

### Developer Tests and Notes

- Verified the documented quick start with the included marker chart and the default palette and
  output filename values.
- Rendered both generated Letter orientations at 150 DPI with `pdftoppm` and visually confirmed
  one page each, square unfilled cells, readable codes, safe margins, and unclipped color keys.
- Ran `source source_me.sh && python3 -m pytest tests/`: 551 tests passed in 2.03 seconds.
- After adding configurable grids and the aligned artwork pages, ran
  `source source_me.sh && python3 -m pytest tests/`: 559 tests passed in 2.04 seconds.
- Verified the README quick start, checked the 1,920 by 1,200 documentation image visually, and
  confirmed the new and refreshed Markdown files use ASCII text and resolve to existing local
  targets.
- After the complete documentation refresh, ran
  `source source_me.sh && python3 -m pytest tests/`: 610 tests passed in 2.15 seconds.
- Ran the focused Voronoi geometry and evaluator suite: 36 tests passed in 0.21 seconds. The
  independent half-plane oracle agrees cell by cell with the general Shapely constructor, and every
  focused test remains individually under 0.03 seconds.
- With uniform seed `20260722`, the 1,290-site single run measured grid
  generation/site-validation/construction/partition-validation/quality-measurement time at
  `0.0005654999986290932/0.005488458002218977/0.007063957993523218/0.116799292009091/`
  `0.020111040998017415` seconds and uniform at
  `0.02029329098877497/0.005417667009169236/0.064053750000312/0.12270012499357108/`
  `0.016866207995917648` seconds. Grid versus uniform area CV was
  `3.2530763767410175e-15/0.5510720023875185`, p90/p10 was
  `1.0000000000000089/4.350475961135703`, and exact bounded covering radius was
  `0.019687480773954203/0.05823951931799626`.
- With uniform seed `20260722`, the 5,160-site single run measured grid
  generation/site-validation/construction/partition-validation/quality-measurement time at
  `0.0020153749937890097/0.023576042003696784/0.026376333000371233/`
  `0.45691725000506267/0.06970545800868422` seconds and uniform at
  `0.005606541992165148/0.021127749991137534/0.2537870420055697/0.4915319590072613/`
  `0.07187958300346509` seconds. Grid versus uniform area CV was
  `7.023450311237831e-15/0.538053867535535`, p90/p10 was
  `1.000000000000016/4.302361681415295`, and exact bounded covering radius was
  `0.009843740386977258/0.034659455812602415`.
- With uniform seed `20260722`, the 7,500-site single run measured grid
  generation/site-validation/construction/partition-validation/quality-measurement time at
  `0.003110500008915551/0.03300133300945163/0.04016387498995755/0.6712625000072876/`
  `0.09545083400735166` seconds and uniform at
  `0.004739124997286126/0.030911082998500206/0.36895095799991395/0.7169232500018552/`
  `0.10558850000961684` seconds. Grid versus uniform area CV was
  `8.07686366924025e-15/0.5393467462609177`, p90/p10 was
  `1.0000000000000204/4.285464871054204`, and exact bounded covering radius was
  `0.008164965809277561/0.02784734511493308`.
- Rasterized the 5,160-site uniform SVG with `rsvg-convert` and confirmed dense tiny-cell clusters
  and large interior cells, enlarged edge cells, and strongly irregular corner cells; the boundary
  coloring and site dots remained visible without clipped geometry.
- Ran `source source_me.sh && python3 -m pytest tests/`: 706 tests passed in 2.47 seconds.
- Ran the focused corrected Voronoi geometry and evaluation suite with durations: 48 tests passed in
  0.24 seconds, and every focused case completed in under 0.03 seconds.
- Ran `source source_me.sh && python3 -m pytest tests/ --durations=25`: 718 tests passed in 2.46
  seconds.
- Ran the final focused Voronoi geometry and evaluation suite with durations: 52 tests passed in
  0.22 seconds, including actual generator timing boundaries and construction-time rejection of
  invalid uniform output.
- Cross-validated all six schema-v4 JSON/SVG baseline pairs and the summary: recorded canonical
  configurations reproduce their filename digests, summary metrics and timings match the JSON
  records, each SVG parses as XML, and deterministic geometry and quality remain identical to the
  schema-v3 evidence.
- Ran the focused ASCII, typing, import, indentation, Markdown-link, pyflakes, pytest-hygiene,
  shebang, and whitespace gates: 593 tests passed in 1.09 seconds.
- Ran `source source_me.sh && python3 -m pytest tests/ --durations=25`: 722 tests passed in 2.34
  seconds.
- After documenting the separate square and Voronoi pipeline architecture, ran the focused
  Markdown-link, ASCII, and whitespace gates: 198 tests passed in 0.14 seconds.
- Ran `source source_me.sh && python3 -m pytest tests/`: 722 tests passed in 2.27 seconds.
- Ran the focused Milestone 2A generator, construction, configuration, and artifact suite with
  durations: 80 tests passed in 0.28 seconds, and every focused case remained well under one second.
- Cross-validated 48 schema-current evaluation JSON records, 19 SVG artifacts, the combined screen
  summary, configuration digests, canonical configuration text, per-seed metrics and timings,
  site/cell counts, XML parsing, and 18 hard-core requested-distance checks. All checks passed.
- Rendered the six-panel fixed-seed board headlessly with `rsvg-convert` at 2,400 pixels and
  inspected the full image. All panels use equal physical scale; labels, sites, cell outlines, and
  boundary classes remain visible without clipped geometry.
- Ran `source source_me.sh && python3 -m pytest tests/ --durations=25`: 750 tests passed in 2.56
  seconds. The slowest focused Voronoi test completed in 0.02 seconds.
- Ran the focused bounded Voronoi geometry and experiment suite after adding partial Lloyd movement:
  95 tests passed in 0.35 seconds, and every focused case completed in under 0.03 seconds.
- Validated nine schema-current relaxed evaluation JSON records, nine diagnostic SVGs, three board
  JSON/SVG pairs, complete configuration digests and schedules, canonical filenames, reconstructed
  partition validity, summary aggregates, and unchanged Milestone 2A anchor references.
- Rendered all three six-panel Milestone 2B boards headlessly with `rsvg-convert` at 2,400 pixels and
  inspected them at equal physical scale. Labels, sites, cell boundaries, and boundary classes are
  visible without clipped geometry.
- Ran `source source_me.sh && python3 -m pytest tests/ --durations=25`: 769 tests passed in 2.71
  seconds, then ran `git diff --check` successfully.
- Ran a real Voronoi CLI smoke on `kimi.png`: it created the six dedicated artifacts, recorded the
  generated seed, preserved stable site order in the assignments CSV, and produced a three-page
  Letter PDF with blank, numbered, and filled-reference pages.
- Rewrote the Voronoi pipeline, writer, and prototype tests against the pytest checklist. The
  focused behavioral, typing, and hygiene checks passed: 41 Voronoi tests in 0.67 seconds and 77
  typing/hygiene tests in 0.24 seconds.
