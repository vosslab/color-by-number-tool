# File formats

This reference defines the image and palette inputs plus the seven artifacts produced for each
conversion. All companion output names inherit the selected marker-key PDF stem.

## Image input

- `-i` accepts any still-image format supported by the installed Pillow build.
- EXIF orientation is applied before aspect-ratio selection and sampling.
- Images convert to RGB; transparent pixels flatten onto white.
- Crop mode fills the grid, while contain mode adds white borders as needed.

## Palette YAML

The `-p` file contains a top-level nonempty `colors` list. Every entry requires one marker code,
display name, and RGB triplet:

```yaml
name: Example marker set
colors:
  - code: "120"
    name: Black
    rgb: [14, 14, 14]
  - code: "BG7"
    name: Blue Grey
    rgb: [67, 71, 80]
```

- Codes convert to strings, so numeric and alphanumeric labels remain printable.
- Codes must be unique and names must not be empty.
- Each RGB value contains exactly three integer channels from 0 through 255.
- The optional top-level metadata does not change matching behavior.

The bundled example is [../palettes/aoartix_48.yml](../palettes/aoartix_48.yml).

## PDF output

- `<stem>.pdf` is one Letter marker-key worksheet with a numbered grid and colored side key.
- `<stem>_grid_only.pdf` contains two aligned Letter pages.
- Page one of the full-grid PDF has gray lines and no codes.
- Page two has black lines and one marker code per cell.
- Both full-grid pages maximize perfect squares inside a 0.6-inch minimum margin.

## PNG previews

- `<stem>_marker_preview.png` reconstructs the sampled image with assigned palette RGB colors.
- `<stem>_source_preview.png` shows the sampled source RGB values before palette assignment.
- Preview cells use nearest-neighbor enlargement to 24 pixels per grid cell.
- PNGs are visual checks and do not control PDF geometry.

## Assignment CSV

`<stem>_assignments.csv` contains one row for every cell:

| Column | Meaning |
| --- | --- |
| `row` | One-based row from the top of the sampled image. |
| `column` | One-based column from the left. |
| `code` | Selected marker code. |
| `color_name` | Palette display name. |
| `red`, `green`, `blue` | Selected palette RGB channels. |

## Legend CSV

`<stem>_legend.csv` contains every palette entry with `code`, `color_name`, RGB channels, and
`square_count`. Unused markers remain present with a zero count.

## Summary text

`<stem>_summary.txt` records the input and palette paths, grid dimensions, assignment count, fit
mode, page orientation, matching metric, enhancement preset, and mean and maximum Delta E 76.
