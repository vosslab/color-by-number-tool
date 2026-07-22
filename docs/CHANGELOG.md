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

### Behavior or Interface Changes

- Added `-g`/`--grid COLUMNSxROWS` for configurable landscape grid dimensions, with automatic
  dimension swapping for portrait output, and changed the default from 43 by 30 to 86 by 60.
- Reworked the README, installation guide, and usage guide around the current ReportLab workflow,
  and reduced `AGENTS.md` to concise pointers to the canonical repository rules.

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
