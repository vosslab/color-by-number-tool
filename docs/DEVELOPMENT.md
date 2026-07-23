# Development

This guide describes the repository's local Python workflow, module boundaries, and verification
commands for contributors changing the converter or its documentation.

## Local environment

- Use Python 3.12 through `source source_me.sh && python3` for every Python command.
- Install runtime packages from [../pip_requirements.txt](../pip_requirements.txt).
- Install test packages from [../pip_requirements-dev.txt](../pip_requirements-dev.txt).
- Follow [PYTHON_STYLE.md](PYTHON_STYLE.md), [PYTEST_STYLE.md](PYTEST_STYLE.md), and
  [MARKDOWN_STYLE.md](MARKDOWN_STYLE.md).

## Code organization

- Keep [../color_by_number.py](../color_by_number.py) as the small executable entry point.
- Put one responsibility in each module under [../colorbynumber/](../colorbynumber/).
- Keep palette data under [../palettes/](../palettes/) rather than embedding marker colors in code.
- Add behavioral tests to [../tests/test_color_by_number.py](../tests/test_color_by_number.py).
- Keep reusable experimental geometry, metric, and artifact logic under
  [../colorbynumber/](../colorbynumber/).
- Update [CHANGELOG.md](CHANGELOG.md) whenever repository files change.

See [CODE_ARCHITECTURE.md](CODE_ARCHITECTURE.md) and [FILE_STRUCTURE.md](FILE_STRUCTURE.md) for the
complete component and path maps.

## Verification

Run the complete fast test suite:

```bash
source source_me.sh && python3 -m pytest tests/
```

For a PDF change, generate a representative artifact and render it before delivery:

```bash
source source_me.sh && python3 color_by_number.py -i palettes/marker_image_set.jpg
pdftoppm -png -r 300 output/pdf/color_by_number_grid_only.pdf /tmp/color_by_number_page
```

- Inspect both rendered artwork pages for matching geometry and readable codes.
- Confirm the blank page contains gray lines and no marker codes.
- Run the Markdown-link, ASCII, whitespace, import, typing, security, and pytest hygiene gates through
  the complete suite.

## Change boundaries

- Preserve one marker assignment per square and square physical cells.
- Keep image sampling, color matching, PDF layout, and file serialization in separate modules.
- Treat palette or enhancement changes as experiments with fixed inputs and reported measurements.
- Keep generated output under `output/`; commit only intentional documentation visuals.
