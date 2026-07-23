# File formats

This reference defines the image and palette inputs plus the artifacts produced by a conversion.
All companion output names inherit the selected marker-key PDF stem. The default square layout and
the optional Voronoi layout are separate output contracts: a selected layout determines the meaning
of its artifacts without changing the other layout's formats.

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

## Square PDF output

- `<stem>.pdf` is one Letter marker-key worksheet with a numbered grid and colored side key.
- `<stem>_grid_only.pdf` contains two aligned Letter pages.
- Page one of the full-grid PDF has gray lines and no codes.
- Page two has black lines and one marker code per cell by default.
- Both full-grid pages maximize perfect squares inside a 0.6-inch minimum margin.
- With `--merge-regions`, edge-adjacent same-color cells render as one boundary and one code; the
  blank page remains code-free.

## Square PNG previews

- `<stem>_marker_preview.png` reconstructs the sampled image with assigned palette RGB colors.
- `<stem>_source_preview.png` shows the sampled source RGB values before palette assignment.
- Preview cells use nearest-neighbor enlargement to 24 pixels per grid cell.
- PNGs are visual checks and do not control PDF geometry.

## Square assignment CSV

`<stem>_assignments.csv` contains one row for every cell:

| Column | Meaning |
| --- | --- |
| `row` | One-based row from the top of the sampled image. |
| `column` | One-based column from the left. |
| `code` | Selected marker code. |
| `color_name` | Palette display name. |
| `red`, `green`, `blue` | Selected palette RGB channels. |

## Square legend CSV

`<stem>_legend.csv` contains every palette entry with `code`, `color_name`, RGB channels, and
`square_count` and `region_count`. Unused markers remain present with zero counts. The assignment
CSV remains one row per original square even when PDF regions merge.

## Square summary text

`<stem>_summary.txt` records the input and palette paths, grid dimensions, assignment count, fit
mode, page orientation, matching metric, enhancement preset, and mean and maximum Delta E 76. It
also records whether same-color merging is enabled, the base square count, rendered-region count,
and region-count reduction.

## Voronoi PDF output

With `--layout voronoi`, `<stem>.pdf` is a three-page Letter polygon worksheet. The page order is
fixed:

1. Blank artwork: white printable regions with light-gray boundaries and no codes.
2. Numbered reference: white printable regions with black boundaries and one marker code whose
   measured padded glyph box is strictly contained when the region is large enough.
3. Palette reference: printable regions filled with their assigned palette RGB colors and dark
   boundaries.

With `--merge-regions`, all three pages use the connected same-color region boundaries; holes remain
visible, and each numbered region receives one code. The area centroid remains the preferred
anchor; a deterministic shift finds a contained box when possible, while an undersized region uses
its maximum-clearance interior point as a recorded best-effort placement.

The resolved `-g COLUMNSxROWS` still chooses the page aspect and site count `N = COLUMNS * ROWS`.
It does not define rows or columns of polygon assignments.

## Voronoi PNG previews

- `<stem>_source_preview.png` shows the fitted source image before palette assignment.
- `<stem>_polygon_preview.png` shows palette-colored pixels with printable-region boundaries.
- Both previews use raster pixels for their colors and the same printable-region boundaries as the
  PDF. They are visual checks; PDF geometry is authoritative.

## Voronoi assignment CSV

`<stem>_assignments.csv` contains one row for each polygon in stable site order:

| Column | Meaning |
| --- | --- |
| `site_identifier` | Zero-based owner identifier from the bounded geometry partition. It is not a square `row` or `column`. |
| `site_x`, `site_y` | Site coordinates in the normalized Voronoi domain. |
| `source_red`, `source_green`, `source_blue` | Area-sampled source RGB channels for the owned polygon. |
| `code` | Selected marker code. |
| `color_name` | Palette display name. |
| `red`, `green`, `blue` | Selected palette RGB channels. |
| `delta_e_76` | CIE Delta E 76 matching error for the polygon sample and selected marker color. |

Rows follow increasing `site_identifier`, the geometry ownership order used for polygon sampling.
The assignment CSV retains that stable raw site order even when printable regions merge. It is
deliberately distinct from the one-based square `row` and `column` coordinates.

## Voronoi legend CSV

`<stem>_legend.csv` contains every palette entry with `code`, `color_name`, RGB channels, and
`polygon_count` and `region_count`. Unused markers remain present with zero counts.
`polygon_count` replaces the square layout's `square_count` because the rows describe polygon
assignments.

## Voronoi summary text

`<stem>_summary.txt` records the following resolved run information:

- Input image and palette paths, layout, grid-derived site count, fit mode, page orientation, and
  enhancement preset.
- The internal generated/replay seed, hard-core plus bounded-Lloyd distribution, hard-core distance
  and candidate-budget policy, and Lloyd round count and alpha.
- Polygon-area sampling policy, numerical-seam fallback pixel count, and zero-pixel-polygon
  fallback count.
- Matching metric plus mean and maximum Delta E 76 error.
- Label diagnostics: font size, shifted-label count, best-effort-label count, total and maximum
  shift in points, and overlapping final-label pairs. Labels use a strictly contained
  `0.25`-point padded box whenever one fits.
- Same-color merge status, base Voronoi polygon count, rendered-region count, and region-count
  reduction.

The seed is recorded for reproduction but is not a user-facing layout parameter.
