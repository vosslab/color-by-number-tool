# File structure

## Top-level layout

| Path | Purpose |
| --- | --- |
| [../color_by_number.py](../color_by_number.py) | Executable command shim for the package CLI. |
| [../colorbynumber/](../colorbynumber/) | Default square pipeline and dedicated optional Voronoi polygon pipeline. |
| [../palettes/](../palettes/) | Shipped marker palette data and its source chart. |
| [../tests/](../tests/) | Functional tests and repository-wide policy checks. |
| Current directory | User, design, style, and maintenance documentation. |
| [../devel/](../devel/) | Maintainer-only release, changelog, cleanup, and repair tools. |
| [../pip_requirements.txt](../pip_requirements.txt) | Runtime Python dependencies. |
| [../pip_requirements-dev.txt](../pip_requirements-dev.txt) | Test and maintenance dependencies. |
| [../Brewfile](../Brewfile) | Homebrew declaration for Python 3.12. |
| [../source_me.sh](../source_me.sh) | Repository Python shell environment. |
| [../REPO_TYPE](../REPO_TYPE) | Repository type marker used by shared tooling. |
| [../VERSION](../VERSION) | Current project version. |
| [../README.md](../README.md) | Newcomer overview and first successful command. |
| [../AGENTS.md](../AGENTS.md) | Agent-facing repository instructions. |
| [../LICENSE.MIT.md](../LICENSE.MIT.md) | Source license. |

## Runtime package

The [../colorbynumber/](../colorbynumber/) package is divided by responsibility:

- [../colorbynumber/cli.py](../colorbynumber/cli.py) owns argument parsing and end-to-end
  orchestration.
- [../colorbynumber/image_sampler.py](../colorbynumber/image_sampler.py) and
  [../colorbynumber/orientation.py](../colorbynumber/orientation.py) prepare the source grid.
- [../colorbynumber/palette_loader.py](../colorbynumber/palette_loader.py) and
  [../colorbynumber/marker_color.py](../colorbynumber/marker_color.py) define validated palette data.
- [../colorbynumber/color_metrics.py](../colorbynumber/color_metrics.py) and
  [../colorbynumber/color_matcher.py](../colorbynumber/color_matcher.py) implement perceptual color
  assignment.
- [../colorbynumber/pdf_writer.py](../colorbynumber/pdf_writer.py) and
  [../colorbynumber/grid_only_pdf_writer.py](../colorbynumber/grid_only_pdf_writer.py) create vector
  Letter PDFs with ReportLab.
- [../colorbynumber/preview_writer.py](../colorbynumber/preview_writer.py),
  [../colorbynumber/csv_writer.py](../colorbynumber/csv_writer.py), and
  [../colorbynumber/summary_writer.py](../colorbynumber/summary_writer.py) create companion artifacts.
- [../colorbynumber/constants.py](../colorbynumber/constants.py) and
  [../colorbynumber/repo_paths.py](../colorbynumber/repo_paths.py) provide low-level configuration
  and repository data paths.
- [../colorbynumber/voronoi_geometry.py](../colorbynumber/voronoi_geometry.py) provides the durable
	geometry, raw grid, uniform, stratified-jitter and owned-bin hard-core generators,
	one bounded-centroid point-relaxation step, construction, and validation layer.
- [../colorbynumber/voronoi_metrics.py](../colorbynumber/voronoi_metrics.py) provides separate
  deterministic quality metrics and five-phase single-run timing metadata.
- [../colorbynumber/voronoi_experiment.py](../colorbynumber/voronoi_experiment.py) provides canonical
  generation timing, configuration digests, and diagnostic artifact writers.
- [../colorbynumber/voronoi_prototype.py](../colorbynumber/voronoi_prototype.py) owns reusable
  polygon sampling and matching operations: hard-core accepted uniform draws, two bounded Lloyd
  rounds, settled partition construction, pixel-center averaging, shared-edge strong matching, and
  raster reconstruction.
- [../colorbynumber/voronoi_pipeline.py](../colorbynumber/voronoi_pipeline.py) owns the optional
  end-to-end Voronoi pathway selected by `--layout voronoi`: input loading, resolved dimensions,
  internal replay seed, polygon generation, matching, and companion-output coordination.
- [../colorbynumber/voronoi_preview_writer.py](../colorbynumber/voronoi_preview_writer.py) and
  [../colorbynumber/voronoi_pdf_writer.py](../colorbynumber/voronoi_pdf_writer.py) render ordered
  polygon assignments as PNG previews and three-page printable PDFs without adapting square
  writers.
- [../colorbynumber/voronoi_csv_writer.py](../colorbynumber/voronoi_csv_writer.py) writes stable
  site-ordered polygon assignments and palette polygon counts as CSV companion artifacts.
- [../colorbynumber/voronoi_summary_writer.py](../colorbynumber/voronoi_summary_writer.py) writes
  the resolved Voronoi run settings, seed, matching errors, and geometry diagnostics as a text
  companion artifact.

## Palette data

- [../palettes/aoartix_48.yml](../palettes/aoartix_48.yml) contains ordered marker codes, names, and
  chart-derived RGB triplets.
- [../palettes/marker_image_set.jpg](../palettes/marker_image_set.jpg) is the reference chart used to
  sample the default RGB values.

The palette YAML format is a runtime interface. Custom files provide the `colors` structure shown
in [USAGE.md](USAGE.md); `name` and `source` remain descriptive metadata.

## Generated artifacts

The default square CLI creates `output/pdf/`. A chosen PDF stem names its previews, CSV files,
text summary, and grid-only PDF. The optional Voronoi pathway uses the same output-directory and
stem convention for its polygon PDF, previews, CSV files, and text summary; its PDF and preview
contents are owned by Voronoi writers. These generated paths are ignored by
[../.gitignore](../.gitignore) through the `output*/` rule.

Stable smoke-test products belong under `output_smoke/`, which the same `output*/` rule ignores.
Temporary render checks remain workspace-only and are removed after visual verification.

Maintainer geometry experiments write JSON evaluations and SVG controls under the ignored
`output/voronoi_experiment/` directory. Prototype evidence and production preview checks also use
ignored `output*/` directories. Geometry and quality records are deterministic for a fixed
configuration; single-run timing metadata may vary. These artifacts support Voronoi maintenance and
do not change the square command's output formats.

Generated filenames and their contents are listed in [USAGE.md](USAGE.md).

## Documentation map

- [INSTALL.md](INSTALL.md) covers Python 3.12 and dependency setup.
- [USAGE.md](USAGE.md) covers CLI options, printing, palettes, and every output file.
- [FILE_FORMATS.md](FILE_FORMATS.md) specifies accepted image and palette inputs plus generated
  PDF, PNG, CSV, and text outputs.
- [VISION_PIPELINE.md](VISION_PIPELINE.md) records the image-processing and print-geometry contracts.
- [GEOMETRY_MODEL.md](GEOMETRY_MODEL.md) defines the Voronoi coordinate, tolerance,
  degeneracy, and validation contracts; the analytical square cells are comparison controls.
- [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) describes runtime components and data flow.
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) diagnoses setup, input, output, printing, and color issues.
- [FAQ.md](FAQ.md) answers common workflow and output questions.
- [DEVELOPMENT.md](DEVELOPMENT.md) describes the maintainer environment and verification workflow.
- [ROADMAP.md](ROADMAP.md) separates current capabilities from evidence-backed future work.
- [RELATED_PROJECTS.md](RELATED_PROJECTS.md) records dependencies, upstream tools, and prior art.
- [NEWS.md](NEWS.md) and [RELEASE_HISTORY.md](RELEASE_HISTORY.md) summarize user-facing changes and
  releases.
- [screenshots/paired_artwork_pages.png](screenshots/paired_artwork_pages.png) is generated visual
  evidence for the aligned blank and numbered artwork pages.
- [CHANGELOG.md](CHANGELOG.md) records implementation and documentation changes by date.
- [PYTHON_STYLE.md](PYTHON_STYLE.md), [PYTEST_STYLE.md](PYTEST_STYLE.md),
  [MARKDOWN_STYLE.md](MARKDOWN_STYLE.md), and [REPO_STYLE.md](REPO_STYLE.md) define repository policy.
- [../devel/DEVEL_README.md](../devel/DEVEL_README.md) maps maintainer scripts.
- [../tests/TESTS_README.md](../tests/TESTS_README.md) describes the test suite.

## Where to add work

- Add production square behavior as one focused module under
  [../colorbynumber/](../colorbynumber/), then wire it through the current square coordinator in
  [../colorbynumber/cli.py](../colorbynumber/cli.py).
- Add square behavior through the current square coordinator in
  [../colorbynumber/cli.py](../colorbynumber/cli.py), preserving the square arrays and writers.
- Add Voronoi behavior through [../colorbynumber/voronoi_pipeline.py](../colorbynumber/voronoi_pipeline.py)
  and its dedicated polygon modules, preserving the ordered polygon contract and separate writers.
- Add square behavior tests to [../tests/test_color_by_number.py](../tests/test_color_by_number.py).
  Keep Voronoi behavior and writer tests in dedicated `test_voronoi_*.py` modules under
  [../tests/](../tests/).
- Add marker sets and their intentional source images under [../palettes/](../palettes/).
- Add user and design references alongside [USAGE.md](USAGE.md) with uppercase underscore filenames.
- Add maintainer-only automation under [../devel/](../devel/) and document it in
  [../devel/DEVEL_README.md](../devel/DEVEL_README.md).
- Keep generated worksheets and previews under an ignored `output*/` directory.
