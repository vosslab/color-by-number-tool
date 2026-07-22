## 2026-07-22

### Additions and New Features

- Added a Python 3.12 converter that creates a strict 43 by 30 code-only PDF worksheet, source and
  marker previews, per-cell assignments, a marker legend, and color-distance metrics.
- Added the 48-color Aoartix palette in YAML using median RGB values sampled from the supplied
  product chart, including numeric, grey-series, and blue-grey codes.
- Added focused unit tests and installation, usage, and vision-pipeline documentation.
- Split the implementation into dedicated modules for palette loading, image sampling, perceptual
  matching, PDF output, PNG previews, CSV output, and summary metrics while keeping the root command
  as a small executable entry point.
- Added explicit default argparse values for `palettes/aoartix_48.yml` and
  `output/pdf/color_by_number.pdf`; companion output names derive from the PDF stem.
- Changed the primary print artifact to one landscape Letter page with 0.65-inch margins, a white
  43 by 30 grid on the left, and a two-column colored marker key on the right.
- Refreshed the README as a newcomer-facing landing page with a verified included-image quick start,
  representative output, visible palette limitations, and direct documentation routes.

### Decisions and Failures

- Selected direct nearest-color matching in CIE L*a*b* space without dithering so every square has
  one independently explainable marker code.
- Treated chart RGB values as an initial approximation because actual alcohol ink varies with paper,
  lighting, and camera capture.

### Developer Tests and Notes

- Verified the documented quick start with the included marker chart and the default palette and
  output filename values.
- Rendered the generated Letter PDF at 150 DPI with `pdftoppm` and visually confirmed one page,
  square unfilled cells, readable codes, safe margins, and an unclipped two-column color key.
- Ran `source source_me.sh && python3 -m pytest tests/`: 512 tests passed in 1.93 seconds.
