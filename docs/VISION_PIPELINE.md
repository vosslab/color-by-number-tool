# Vision pipeline

## Task contract

This is deterministic color quantization, not object recognition or image generation.

- Input: one still image in any Pillow-supported format and orientation.
- Grid output: configurable, defaulting to 86 columns by 60 rows in landscape and rotating to 60
  columns by 86 rows in portrait.
- Cell output: exactly one Aoartix marker code per square.
- Diagram output: one orientation-matched marker-key PDF plus a two-page full-grid PDF containing
  an aligned blank gray grid and black numbered reference.
- Color objective: retain recognizable local structure while keeping per-cell Delta E 76 low.
- Runtime target: complete a normal photograph in under one second on the primary macOS system.

## Processing stages

1. Apply the image EXIF orientation and flatten transparent pixels onto white.
2. Select landscape for wide or square sources and portrait for tall sources, unless overridden.
3. Center crop or contain the image at the selected grid aspect ratio.
4. Downsample to one source RGB value for every square, 5,160 at the default resolution.
5. Convert source and palette RGB colors to CIE L*a*b* with a D65 white point.
6. Locate cells that are dark, chromatic, and locally changing in Lab space.
7. Apply the preset's gamma lightness curve only to those cells so shadow structure survives.
8. Locate warm midtones and highlights and apply the preset's modest chroma scale.
9. Assign the marker with the smallest Delta E 76 distance to each square.
10. Render the marker-key PDF, two aligned full-grid pages, previews, CSV data, and error summary.

No dithering is applied. Global error diffusion was tested on `kimi-face.png`; it added visible
speckling to flat teal and skin regions. Selective shadow expansion produced cleaner regions while
recovering more hair structure. `-e none` restores direct nearest-color assignment.

## Matching experiment

The upper hair region of `kimi-face.png` is the current hard-case fixture. These historical color
experiments used the original 43 by 30 grid. The source, grid size, palette, crop, and Delta E
measurement remained fixed while one preprocessing factor changed.

| Preset | Shadow gamma | Warm chroma | Black hair | Brown family | Pale face | Mean Delta E |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| None | n/a | 1.00 | 165 | 86 | 64 | 14.427 |
| Balanced | 0.65 | 1.15 | 104 | 109 | 31 | 14.910 |
| Strong | 0.50 | 1.15 | 72 | 126 | 31 | 15.424 |

Hue-weighted matching, global diffusion, and detail-aware diffusion were tested independently.
None reduced black assignments without worse substitutions or noise, so they are not part of the
production pipeline. Warm lightness contrast also failed to improve the washed-out skin fixture;
a 1.15 chroma scale improved separation with less error than the tested 1.30 scale.

## Verification

`summary.txt` records the mean and maximum Delta E 76 error. The source and marker previews provide
a side-by-side inspection artifact for composition, lost detail, and palette limitations. Automated
tests cover perceptual nearest-color assignment, exact grid dimensions, alphanumeric codes, safe
page margins, square cells, blank and numbered page separation, dark-detail selectivity, automatic
selection, override behavior, and both Letter orientations.

## Print geometry contract

- Coordinates are two-dimensional PDF points with a bottom-left origin and 72 points per inch.
- Letter pages are 612 by 792 points in portrait and 792 by 612 points in landscape.
- The marker-key worksheet uses 46.8-point outer margins, equal to 0.65 inches.
- The full-grid PDF maximizes the grid inside a 43.2-point, or 0.6-inch, minimum margin. The limiting
  axis touches that margin while the other axis is centered with equal larger margins.
- The blank and numbered full-grid pages reuse the same calculated geometry so every cell aligns.
- The CLI grid value describes landscape columns by rows; portrait swaps those dimensions. The
  default is 86 by 60 in landscape and 60 by 86 in portrait.
- One scalar cell size is the minimum of available width per column and height per row. Reusing that
  scalar for both axes guarantees square cells without an epsilon-based correction.
- Invalid orientation names and non-positive image dimensions are rejected rather than approximated.

## Known limitations

- The 48 chart colors approximate physical ink; swatches made on the final paper are more accurate.
- Higher grid resolutions retain more spatial detail but produce smaller printed cells and codes.
- Center crop can remove image edges; contain mode preserves them but creates border regions.
- The set has no true paper-white marker, so very bright source areas map to the nearest pale marker.
- Fluorescent inks can appear different in photographs, on screens, and under different lighting.
