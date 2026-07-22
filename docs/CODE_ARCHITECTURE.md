# Code architecture

## Overview

The project is a Python 3.12 command-line application that converts one image into a fixed grid of
marker assignments. The runtime is deterministic: it samples one source color per cell, assigns one
palette entry with CIE Delta E 76 matching, and writes printable and machine-readable artifacts.

The executable [../color_by_number.py](../color_by_number.py) is a small entry-point shim. Runtime
behavior lives in the [../colorbynumber/](../colorbynumber/) package, with
[../colorbynumber/cli.py](../colorbynumber/cli.py) as the pipeline coordinator.

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

## Data flow

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

## Testing and verification

- [../tests/test_color_by_number.py](../tests/test_color_by_number.py) verifies perceptual matching,
  enhancement selectivity, grid parsing, orientation, square-cell geometry, page counts, and codes.
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
- Add a companion artifact as a dedicated writer module, then register its path and call in
  [../colorbynumber/cli.py](../colorbynumber/cli.py).
- Keep printable geometry in the two PDF writer modules and reuse the shared `PageLayout` record
  when pages must align.

## Known gaps

- Verify the default palette against photographed marker swatches on the final paper before treating
  chart-derived RGB values as physical color measurements.
