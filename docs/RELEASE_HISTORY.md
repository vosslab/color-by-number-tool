# Release history

This log records each released version with its user-facing behavior, compatibility details, and
validation evidence.

## v26.07 - 2026-07-22

### Highlights

- Converts an image into an exact square-cell color-by-number design with one Aoartix marker code
  in each numbered cell.
- Includes a 48-color Aoartix YAML palette sampled from the supplied product chart and reports
  per-cell assignments, marker counts, previews, and color-distance metrics.
- Produces a ReportLab Letter worksheet with crisp vector geometry, fitted marker codes, a colored
  marker key, and automatic portrait or landscape layout.
- Produces an aligned two-page artwork PDF: a light-gray blank grid for coloring and a black
  numbered reference grid.
- Supports configurable grid dimensions through `-g`/`--grid`, explicit page-orientation
  overrides, crop or contain fitting, and deterministic palette and output defaults.
- Provides `none`, `balanced`, and `strong` color-enhancement presets. The strong default restores
  more brown hair and skin-tone separation in the tested portrait without global dithering.
- Keeps image sampling, perceptual matching, PDF generation, previews, CSV output, and summary
  output in focused Python 3.12 modules behind a small command-line entry point.

### Compatibility notes

- The default landscape grid is 86 by 60. Use `-g 43x30` to reproduce the earlier worksheet
  density; portrait output swaps the configured dimensions automatically.
- Matching uses independent nearest-color selection in CIE L*a*b* space. The tool does not apply
  global error diffusion, so each square remains independently explainable.
- Product-chart RGB values are an initial palette approximation. Paper, lighting, camera capture,
  and the physical alcohol markers can produce different results.

### Validation

- The documented quick start was exercised with the included marker chart and default paths.
- The portrait and landscape marker-key worksheets were rendered at 150 DPI and checked for
  square unfilled cells, readable codes, safe margins, and unclipped color keys.
- The portrait 60 by 86 two-page artwork PDF was rendered at 300 DPI and checked for aligned grid
  geometry, light-gray blank lines, black numbered lines, and readable marker codes.
- The final Python 3.12 test run passed all 610 tests.
