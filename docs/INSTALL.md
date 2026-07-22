# Installation

## Requirements

- macOS or another platform with Python 3.12.
- NumPy for array operations and perceptual color matching.
- Pillow for image loading and output.
- PyYAML for marker palette data.
- ReportLab for fixed-size PDF generation.

## Install Python packages

Run from the repository root:

```bash
source source_me.sh && python3 -m pip install -r pip_requirements.txt
```

On the primary macOS system, packages install under
`/opt/homebrew/lib/python3.12/site-packages/`.

## Verify the command

```bash
source source_me.sh && python3 color_by_number.py --help
```
