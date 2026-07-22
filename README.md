# Color-by-number tool

Turn any photograph into a printable 43 by 30 color-by-number grid for artists who need exactly one Aoartix marker code in every unfilled square.

<!-- screenshots:begin (managed by screenshot-docs) -->
<!-- screenshots:end -->

## From photo to 1,290 decisions

The tool reduces a photograph to a strict physical worksheet instead of a blended digital effect.
Every square is an independent, usable marker decision:

- 43 columns by 30 rows of equal-width and equal-height squares.
- One printed marker code in every square, including codes such as `120` and `BG7`.
- White worksheet cells with black grid lines and no pre-colored boxes.
- Perceptual matching against the supplied 48-color Aoartix marker set.
- Separate source and marker previews for judging the result before printing.

The primary output is one landscape 8.5 by 11-inch PDF with 0.65-inch margins. The numbered grid
sits on the left, and a two-column key of the used marker colors sits on the right. Grid cells stay
white; only the separate key swatches use color.

Use the PDF as a reference map while coloring the matching rows and columns on a separate 43 by 30
sheet of graph paper.

## Before the first print

The built-in RGB values come from the supplied product chart, not physical ink swatches. Alcohol
ink appearance changes with paper, lighting, and camera capture. The chart palette is a useful
starting point; measured swatches on the final paper provide the closest physical match.

The fixed 43 by 30 resolution also removes small facial details. Use the generated source and
marker previews to choose the crop before printing the worksheet.

## Quick start

Use Python 3.12 and install the packages in `pip_requirements.txt` as described in
[docs/INSTALL.md](docs/INSTALL.md). Then run the included marker chart through the complete path:

```bash
source source_me.sh && python3 color_by_number.py -i palettes/marker_image_set.jpg
```

The command creates the worksheet and five companion artifacts under `output/`:

```text
Created a 43 x 30 color-by-number diagram:
  diagram: output/pdf/color_by_number.pdf
  marker preview: output/pdf/color_by_number_marker_preview.png
  source preview: output/pdf/color_by_number_source_preview.png
  assignments: output/pdf/color_by_number_assignments.csv
  legend: output/pdf/color_by_number_legend.csv
  summary: output/pdf/color_by_number_summary.txt
```

Open `output/pdf/color_by_number.pdf` and print in landscape orientation. Replace the input path
with the photograph to convert.

## One image, six artifacts

| Output | What it provides |
| --- | --- |
| `color_by_number.pdf` | One Letter page with the white code grid and a colored side key. |
| `color_by_number_marker_preview.png` | The photograph reconstructed with marker colors. |
| `color_by_number_source_preview.png` | The unquantized 43 by 30 source-color reference. |
| `color_by_number_assignments.csv` | The code, name, and RGB choice for every grid position. |
| `color_by_number_legend.csv` | Every palette entry and its assigned square count. |
| `color_by_number_summary.txt` | Grid invariants, fit mode, and Delta E 76 error metrics. |

Use `-o output/pdf/family_portrait.pdf` to choose the worksheet filename. All companion files inherit
the `family_portrait` stem. Use `-f contain` to preserve the complete source image instead of center
cropping it.

## Aoartix marker palette

The built-in [palettes/aoartix_48.yml](palettes/aoartix_48.yml) palette contains all 48 codes and
names from [palettes/marker_image_set.jpg](palettes/marker_image_set.jpg). Each RGB triplet is the
median flat-background color sampled from its reference-chart swatch.

## Documentation

- [docs/INSTALL.md](docs/INSTALL.md): Python 3.12 requirements and dependency setup.
- [docs/USAGE.md](docs/USAGE.md): fitting, sizing, custom palette, and output options.
- [docs/VISION_PIPELINE.md](docs/VISION_PIPELINE.md): image-processing contract, metrics, and
  limitations.

## License

The source code is available under the [MIT License](LICENSE.MIT.md).
