# Usage

## Create a worksheet

Run the converter with a photograph:

```bash
source source_me.sh && python3 color_by_number.py -i portrait.jpg
```

The default center crop fills all 43 by 30 squares. To preserve the entire source image and
add borders where needed, use:

```bash
source source_me.sh && python3 color_by_number.py -i portrait.jpg -f contain
```

## Print the reference page

The primary PDF is one 11-inch by 8.5-inch landscape Letter page. It uses 0.65-inch outer margins,
which are larger than 0.6 inches on every side. The 43 by 30 code grid sits on the left, while a
two-column key on the right shows a colored swatch, code, and square count for every marker used.

Every grid cell is a perfect square and remains unfilled. Use the PDF as a reference while coloring
the corresponding row and column on a separate 43 by 30 sheet of graph paper. Only the side-key
swatches contain color.

Print in landscape orientation. Actual-size printing preserves the designed margins; fitting to the
printer area is also safe because the PDF scales uniformly and keeps the grid cells square.

## Output files

| File | Purpose |
| --- | --- |
| `color_by_number.pdf` | Letter page with the white code grid and colored key on the right. |
| `color_by_number_marker_preview.png` | Filled preview of the selected marker colors. |
| `color_by_number_source_preview.png` | Unquantized 43 by 30 source-color reference. |
| `color_by_number_assignments.csv` | Row, column, marker code, color name, and RGB per square. |
| `color_by_number_legend.csv` | All marker colors and their assigned square counts. |
| `color_by_number_summary.txt` | Inputs, grid invariants, fit mode, and color metrics. |

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
