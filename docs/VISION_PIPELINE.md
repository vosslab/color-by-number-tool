# Vision pipeline

## Task contract

This is deterministic color quantization, not object recognition or image generation.

- Input: one still image in any Pillow-supported format and orientation.
- Grid output: exactly 43 columns by 30 rows.
- Cell output: exactly one Aoartix marker code per square.
- Diagram output: one landscape Letter PDF with white square cells, black codes, and a side key.
- Color objective: minimize the per-cell perceptual distance to the available marker palette.
- Runtime target: complete a normal photograph in under one second on the primary macOS system.

## Processing stages

1. Apply the image EXIF orientation and flatten transparent pixels onto white.
2. Center crop or contain the image at the 43:30 target aspect ratio.
3. Downsample to one source RGB value for each of the 1,290 squares.
4. Convert source and palette RGB colors to CIE L*a*b* with a D65 white point.
5. Assign the marker with the smallest Delta E 76 distance to each square.
6. Render the single-page PDF, colored preview, source preview, CSV data, and error summary.

No dithering is applied. Dithering can improve distant visual averages, but the direct nearest-color
assignment produces cleaner marker regions and keeps every square independently explainable.

## Verification

`summary.txt` records the mean and maximum Delta E 76 error. The source and marker previews provide
a side-by-side inspection artifact for composition, lost detail, and palette limitations. Automated
tests cover perceptual nearest-color assignment, exact grid dimensions, alphanumeric codes, safe
page margins, square cells, and one-page landscape Letter output.

## Known limitations

- The 48 chart colors approximate physical ink; swatches made on the final paper are more accurate.
- A 43 by 30 grid cannot retain small facial details or fine background texture.
- Center crop can remove image edges; contain mode preserves them but creates border regions.
- The set has no true paper-white marker, so very bright source areas map to the nearest pale marker.
- Fluorescent inks can appear different in photographs, on screens, and under different lighting.
