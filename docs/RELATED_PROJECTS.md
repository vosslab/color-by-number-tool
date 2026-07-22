# Related projects

This page maps the external projects that directly support the tool and one independent project
that solves a related image-to-artwork problem. Relationship labels describe evidence, not project
quality or popularity.

## Confirmed related projects

### NumPy

- Relationship: Direct dependency
- Link: [NumPy documentation](https://numpy.org/doc/)
- Evidence: [../pip_requirements.txt](../pip_requirements.txt) installs NumPy, and the production
  modules use its arrays for image grids, CIE Lab conversion, Delta E measurement, and marker
  assignment.
- Notes: NumPy provides the numerical representation shared by sampling, matching, preview, CSV,
  and PDF output code.

### Pillow

- Relationship: Direct dependency
- Link: [Pillow documentation](https://pillow.readthedocs.io/en/stable/)
- Evidence: [../pip_requirements.txt](../pip_requirements.txt) installs Pillow;
  [../colorbynumber/image_sampler.py](../colorbynumber/image_sampler.py) uses it for image loading,
  EXIF correction, fitting, and grid resampling.
- Notes: [../colorbynumber/preview_writer.py](../colorbynumber/preview_writer.py) also uses Pillow to
  write the source and marker previews.

### PyYAML

- Relationship: Direct dependency
- Link: [PyYAML source repository](https://github.com/yaml/pyyaml)
- Evidence: [../pip_requirements.txt](../pip_requirements.txt) installs PyYAML, and
  [../colorbynumber/palette_loader.py](../colorbynumber/palette_loader.py) uses `yaml.safe_load` to
  read marker palettes.
- Notes: PyYAML supplies the parser for the user-editable palette interface.

### ReportLab

- Relationship: Direct dependency
- Link: [ReportLab documentation](https://docs.reportlab.com/)
- Evidence: [../pip_requirements.txt](../pip_requirements.txt) installs ReportLab;
  [../colorbynumber/pdf_writer.py](../colorbynumber/pdf_writer.py) and
  [../colorbynumber/grid_only_pdf_writer.py](../colorbynumber/grid_only_pdf_writer.py) use its
  canvas, page-size, color, and font-metric APIs.
- Notes: ReportLab produces the vector marker-key worksheet and the aligned two-page artwork PDF.

## Possible related projects

### ethan-grinberg/paint-by-number

- Relationship: Same problem domain, independent implementation
- Link: [ethan-grinberg/paint-by-number](https://github.com/ethan-grinberg/paint-by-number)
- Evidence: Its README documents a Python image-to-paint-by-number generator that writes a
  black-and-white SVG and JSON palette for a React coloring interface.
- Notes: It creates segmented SVG regions instead of this repository's fixed square marker grid;
  no dependency, integration, or reciprocal link is present.
- Confidence: Low

## Evidence notes

Confirmed entries come from the runtime dependency manifest and direct production imports. The
possible entry comes from a bounded search of public project repositories and its own README. No
upstream, fork, integration target, companion repository, or same-author sibling is identified in
the current repository evidence.
