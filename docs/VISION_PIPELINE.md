# Vision pipeline

## Scope

This document specifies the square default and the optional Voronoi pipeline. They share input,
palette, color-distance, orientation, and output-path utilities where those interfaces are
representation-independent. They do not share a cell model.

The shared `-g COLUMNSxROWS` value is a count and aspect convention. The square pipeline interprets
it as rectangular columns and rows. The Voronoi pipeline uses `COLUMNS * ROWS` sites in the same
aspect ratio; its polygons have stable site identifiers rather than row-and-column positions.

## Square task contract

This is deterministic color quantization, not object recognition or image generation.

- Input: one still image in any Pillow-supported format and orientation.
- Grid output: configurable, defaulting to 86 columns by 60 rows in landscape and rotating to 60
  columns by 86 rows in portrait.
- Cell output: exactly one Aoartix marker code per square.
- Diagram output: one orientation-matched marker-key PDF plus a two-page full-grid PDF containing
  an aligned blank gray grid and black numbered reference.
- Color objective: retain recognizable local structure while keeping per-cell Delta E 76 low.
- Runtime target: complete a normal photograph in under one second on the primary macOS system.

## Square processing stages

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

## Square matching experiment

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

## Square verification

`summary.txt` records the mean and maximum Delta E 76 error. The source and marker previews provide
a side-by-side inspection artifact for composition, lost detail, and palette limitations. Automated
tests cover perceptual nearest-color assignment, exact grid dimensions, alphanumeric codes, safe
page margins, square cells, blank and numbered page separation, dark-detail selectivity, automatic
selection, override behavior, and both Letter orientations.

## Square print geometry

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

## Square limitations

- The 48 chart colors approximate physical ink; swatches made on the final paper are more accurate.
- Higher grid resolutions retain more spatial detail but produce smaller printed cells and codes.
- Center crop can remove image edges; contain mode preserves them but creates border regions.
- The set has no true paper-white marker, so very bright source areas map to the nearest pale marker.
- Fluorescent inks can appear different in photographs, on screens, and under different lighting.

## Optional Voronoi task

The `--layout voronoi` option produces an organic polygon worksheet. `--layout square` remains the
default. Both modes retain the same source fitting choices, marker palette, enhancement names, and
orientation selection, but their sampling, assignment, preview, CSV, summary, and PDF writers are
separate.

- Input: one EXIF-corrected still image and the selected marker palette.
- Polygon count: `COLUMNS * ROWS` sites from `-g COLUMNSxROWS`; portrait preserves the count while
  swapping the aspect convention with the resolved page orientation.
- Distribution: uniform independent x/y candidate draws, hard-core minimum-distance acceptance,
  then two bounded Lloyd rounds at alpha `0.50`.
- Site identity: one stable zero-based identifier per site and polygon, retained across every
  Voronoi artifact.
- Randomness: the coordinator creates an internal seed for each run and records it in the summary
  and command result for replay. It is not a user-facing tuning flag.
- Diagram output: blank, centroid-labeled numbered, and palette-reference polygon pages, plus
  polygon previews, site-ordered CSV files, and a summary.

## Voronoi processing stages

1. Resolve page orientation and the `-g` count/aspect convention, then generate and record an
   internal seed.
2. Draw uniform x/y candidate sites, accept candidates that meet the hard-core spacing rule, and
   apply two bounded centroid-relaxation rounds.
3. Construct and validate the clipped, bounded Voronoi polygons in stable site order.
4. Fit the source image to a higher-resolution raster with the same crop, contain, centering,
   white-border, and Lanczos policy used by the square sampler.
5. Assign each fitted-raster pixel center to its owning polygon and average the owned RGB values.
   A center exactly on a shared boundary belongs to the lower site identifier. A numerical seam uses
   the nearest-site tie rule. A polygon that owns no center samples the fitted pixel nearest its site;
   both fallback counts are recorded in the run summary.
6. Convert polygon samples and palette colors to CIE L*a*b*, apply the selected matching preset,
   and choose the nearest marker by Delta E 76. The strong preset evaluates dark-detail contrast
   with shared-edge polygon neighbors, not a square neighborhood.
7. Send the site-ordered marker assignments to the dedicated polygon preview, CSV, summary, and PDF
   writers. The numbered PDF anchors each code at the polygon area centroid, the center of mass of
   its filled area.

## Voronoi verification

The Voronoi tests verify bounded construction, stable ownership, pixel-center sampling, fallback
accounting, shared-edge adjacency, color assignment, writer agreement, and PDF label diagnostics.
The run summary records the internal seed, Delta E values, sampling fallbacks, label font size, and
any label containment or overlap diagnostics for a concrete generated worksheet.

Evidence supports the selected two-round distribution as a good-enough balance of random appearance
and similarly sized polygons. It does not make physical marker colors exact, and dense output can
still make codes harder to read; the recorded diagnostics make such a case visible rather than
silently changing the layout.

## Voronoi boundaries

The Voronoi coordinator, ordered polygon model, and polygon writers remain separate from the square
pipeline. Shared low-level utilities retain their own representation-independent interfaces. No
generic layout abstraction, fake row/column indexing, or polygon-to-grid conversion is used.
