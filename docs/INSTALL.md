# Install

This repository runs as a Python 3.12 command-line tool from its source checkout. Installation
provides the image, YAML, numeric, and PDF libraries used by `color_by_number.py`; it does not
install a separate console command.

## Requirements

- Bash for the repository bootstrap command.
- Python 3.12, pinned by [../Brewfile](../Brewfile) on the primary macOS system.
- NumPy and Pillow for image sampling, color calculations, and PNG previews.
- PyYAML for marker palette loading.
- ReportLab for vector Letter PDFs with exact square-cell geometry.

## Install steps

Obtain the source and enter the repository root. On macOS with Homebrew, install the pinned Python
version:

```bash
brew bundle
```

Install the runtime packages listed in [../pip_requirements.txt](../pip_requirements.txt):

```bash
source source_me.sh && python3 -m pip install -r pip_requirements.txt
```

On the primary macOS system, packages install under
`/opt/homebrew/lib/python3.12/site-packages/`.

For development and test work, also install
[../pip_requirements-dev.txt](../pip_requirements-dev.txt):

```bash
source source_me.sh && python3 -m pip install -r pip_requirements-dev.txt
```

## Verify install

```bash
source source_me.sh && python3 color_by_number.py --help
```

The command succeeds when it prints the input, output, palette, fitting, grid, enhancement, and
orientation options.

## Runtime notes

- Run commands from the repository root so the package and default palette resolve correctly.
- The tool requires no project-specific environment variables.
- Generated files go under `output/pdf/` by default and remain outside version control.
- The `source_me.sh` bootstrap selects the repository's Python 3.12 environment conventions.

## Troubleshooting

If `source source_me.sh` prints `use bash for your shell`, start a Bash shell and rerun the command.
The bootstrap intentionally rejects other shells before loading the Python environment.
