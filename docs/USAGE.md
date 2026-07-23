# Usage

Convert a still image into ReportLab Letter PDFs, marker and source previews, assignments, a marker
legend, and color-error metrics. The default square layout uses grid cells; the optional Voronoi
layout uses organically spaced polygons with the same grid-derived count and aspect ratio.

## Quick start

Run the included palette chart through the complete conversion path:

```bash
source source_me.sh && python3 color_by_number.py -i palettes/marker_image_set.jpg
```

The command writes seven files under `output/pdf/`. Open `color_by_number_grid_only.pdf` for the
blank and numbered artwork pages, and use `color_by_number.pdf` for the colored marker key.

Replace the input path with a photograph. The default center crop fills all 86 by 60 landscape
squares, rotated for portrait. To preserve the complete image and add borders where needed, use:

```bash
source source_me.sh && python3 color_by_number.py -i portrait.jpg -f contain
```

## CLI options

| Option | Purpose |
| --- | --- |
| `-i`, `--input` | Select the required source image. |
| `-o`, `--output` | Set the marker-key PDF path and companion filename stem. |
| `-p`, `--palette` | Load another marker palette YAML file. |
| `-f`, `--fit` | Choose center crop or contain with borders. |
| `--layout` | Choose `square` (default) or `voronoi` polygons. |
| `-g`, `--grid` | Set landscape columns by rows; portrait swaps them. |
| `-e`, `--enhancement` | Choose `none`, `balanced`, or `strong` color treatment. |
| `-L`, `-P` | Force landscape or portrait page orientation. |

## Choose page orientation

Page orientation follows the EXIF-corrected source dimensions by default:

- Wide and square images produce a landscape Letter page with 86 columns by 60 rows by default.
- Tall images produce a portrait Letter page with 60 columns by 86 rows by default.

Force either layout when composition matters more than source aspect ratio:

```bash
source source_me.sh && python3 color_by_number.py -i kimi.png -L
source source_me.sh && python3 color_by_number.py -i kimi.png -P
```

The short and long flags are equivalent: `-L` or `--landscape`, and `-P` or `--portrait`.

## Choose grid resolution

Use `-g` or `--grid` with landscape columns by rows. Portrait output swaps the two dimensions:

```bash
source source_me.sh && python3 color_by_number.py -i kimi-face.png -g 86x60
```

The default is `86x60`. For example, `-g 43x30` restores the original lower-resolution grid with
cells twice as wide and twice as tall. The first dimension must be at least as large as the second
so automatic orientation always places the longer grid dimension along the page's longer edge.

Changing from 43 by 30 to 86 by 60 increases the number of image samples from 1,290 to 5,160. It
does not enlarge the grid's physical page footprint because both grids have the same aspect ratio;
it divides the same area into smaller cells.

## Choose an organic layout

The default `square` layout keeps the existing square-cell workflow. Use `--layout voronoi` to make
the same count of organic, bounded polygons instead. `-g` still supplies landscape columns by rows:
it sets the polygon count and worksheet aspect ratio, not polygon rows and columns.

```bash
source source_me.sh && python3 color_by_number.py -i kimi-face.png --layout voronoi -g 43x30
```

Voronoi placement is random for each run. The program generates its own seed rather than exposing a
seed option, then records that seed in the Voronoi summary for maintainer replay. The selected
distribution spaces accepted points apart and applies two bounded relaxation rounds before drawing
the clipped polygons. It samples the source over each polygon area and applies the chosen `-e` color
enhancement to neighboring polygon assignments.

`-f crop` and `-f contain`, `-L` and `-P`, `-g`, `-p`, and `-e` work with both layouts. Portrait
output still swaps the configured landscape dimensions before the polygon count and page geometry
are resolved.

## Choose color enhancement

The default `strong` preset expands lightness differences only in locally changing dark colors and
adds 15% chroma only to warm midtones and highlights. This keeps textured brown hair, wood, fabric,
skin, and similar regions from collapsing into black or pale blocks without adding noise to flat
backgrounds.

Use the original nearest-color behavior for a baseline comparison:

```bash
source source_me.sh && python3 color_by_number.py -i kimi-face.png -e none
```

Use the gentler tested treatment when lower color error matters more than maximum hair detail:

```bash
source source_me.sh && python3 color_by_number.py -i kimi-face.png -e balanced
```

On `kimi-face.png`, `strong` reduced black assignments in the measured upper-hair region from 165
to 72, increased brown-family assignments from 86 to 126, and reduced pale face assignments from
64 to 31. Mean Delta E 76 increased from 14.427 to 15.424. The `balanced` preset reduced black hair
assignments to 104 with a lower mean error of 14.910.

## Print the artwork pages

The generated `color_by_number_grid_only.pdf` contains two full Letter pages with identical grid
positions and 0.6-inch minimum margins:

1. Page one has light-gray grid lines and no codes. Color this page as the final artwork.
2. Page two has black grid lines and one marker code in every cell. Use it as the reference.

Print both at actual size in the generated orientation. The cells line up exactly because ReportLab
draws both pages from the same point-based geometry. Fitting to the printer area also keeps cells
square, but both pages must use the same print scaling.

The separate `color_by_number.pdf` is the marker-key worksheet. It uses 0.65-inch outer margins and
places a smaller numbered grid on the left beside a two-column colored key on the right.

Every grid cell remains unfilled. Only the side-key swatches in the marker-key worksheet contain
color.

For Voronoi output, `<stem>.pdf` contains three aligned Letter pages with the same bounded polygons:
a blank light-gray artwork page, a black numbered reference page, and a filled palette reference
page. Numbered labels are centered at each polygon's area centroid. Print all three at the same scale
when using the reference pages with the blank artwork.

## Output files

| File | Purpose |
| --- | --- |
| `color_by_number.pdf` | Letter page with the white code grid and colored key on the right. |
| `color_by_number_grid_only.pdf` | Blank gray grid and aligned black numbered grid on two pages. |
| `color_by_number_marker_preview.png` | Filled preview of the selected marker colors. |
| `color_by_number_source_preview.png` | Unquantized, orientation-matched source-color reference. |
| `color_by_number_assignments.csv` | Row, column, marker code, color name, and RGB per square. |
| `color_by_number_legend.csv` | All marker colors and their assigned square counts. |
| `color_by_number_summary.txt` | Inputs, grid invariants, fit mode, enhancement, and metrics. |

## Voronoi output files

With `--layout voronoi`, the requested `<stem>.pdf` supplies the dedicated polygon worksheet. Its
companions share the same stem:

| File | Purpose |
| --- | --- |
| `color_by_number.pdf` | Three aligned Letter pages: blank artwork, numbered reference, and filled palette reference. |
| `color_by_number_polygon_preview.png` | Palette-colored polygon preview with visible boundaries. |
| `color_by_number_source_preview.png` | Fitted source-color reference at the polygon sampling resolution. |
| `color_by_number_polygon_assignments.csv` | One stable site-ordered polygon assignment, including sampled source RGB and Delta E 76. |
| `color_by_number_legend.csv` | Every palette color and its assigned polygon count. |
| `color_by_number_summary.txt` | Resolved layout, generated seed, point-spacing policy, matching metrics, and label diagnostics. |

## Marker palette data

The default [../palettes/aoartix_48.yml](../palettes/aoartix_48.yml) file uses this shape:

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

Use another palette with `-p`:

```bash
source source_me.sh && python3 color_by_number.py -i portrait.jpg -p palettes/custom.yml
```

Use another worksheet filename with `-o`; companion artifact names use the same stem:

```bash
source source_me.sh && python3 color_by_number.py -i portrait.jpg -o output/pdf/family_portrait.pdf
```

Codes remain strings so numeric and alphanumeric labels print exactly as written.

## Palette accuracy

The built-in RGB values come from the product chart in
[../palettes/marker_image_set.jpg](../palettes/marker_image_set.jpg). A screen chart cannot perfectly predict how
alcohol ink looks on a particular paper under a particular light. For the closest physical match,
replace the RGB values with measurements from a uniformly lit, photographed swatch sheet made on
the paper used for the final artwork.
