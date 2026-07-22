# Frequently asked questions

These answers explain the converter's print workflow, grid sizing, color limits, and image-processing
choices for artists evaluating the generated pages.

## Why are there two artwork pages?

The first page contains only a light-gray grid, so printed codes do not remain in the finished
picture. The second page uses the same cell geometry with black marker codes. Print both pages at
the same scale and read the second while coloring the first.

## Are the PDFs made with ReportLab?

Yes. ReportLab draws Letter pages, vector grid lines, square cells, and fitted marker-code text in
PDF points. The blank and numbered artwork pages reuse one calculated layout so their cells align.

## Does a larger grid fill more paper?

Increasing 43 by 30 to 86 by 60 increases image resolution but preserves the same aspect ratio, so
it divides the same page area into smaller cells. The separate full-page artwork PDF gains physical
size by removing the side key and using a 0.6-inch minimum margin.

## Why does portrait swap dimensions?

The `-g` value describes landscape columns by rows. Automatic portrait output swaps the two values
so the longer grid edge follows the longer page edge. For example, `-g 86x60` becomes 60 by 86.

## Are marker colors exact?

No. The bundled palette samples RGB values from the supplied product chart. Physical ink changes
with paper, lighting, coverage, and camera processing. A photographed swatch sheet made with the
actual markers on the final paper provides better calibration.

## Why is dithering disabled?

Global error diffusion was tested and produced visible speckling in flat backgrounds and skin.
The current presets use selective shadow and warm-color enhancement, then assign one independently
explainable marker code to each cell.

## Which enhancement should I use?

- `strong` is the default and exposed the most tested dark-hair structure.
- `balanced` retains less shadow variation but stays closer to the source by mean Delta E 76.
- `none` provides direct nearest-color assignment without preprocessing.

See [VISION_PIPELINE.md](VISION_PIPELINE.md) for the controlled comparison and measured results.
