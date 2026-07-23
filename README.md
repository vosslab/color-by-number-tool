# Color-by-number tool

Turn photographs into printable color-by-number worksheets for marker artists, using either crisp
square cells or organic Voronoi regions with matched codes, blank artwork, and aligned references.

## See both layouts

Square mode makes a regular worksheet with predictable cell sizes. Voronoi mode follows an organic
polygon structure that better suits subjects where a rigid grid is distracting. Both modes can
merge connected shapes assigned the same marker color before the PDFs are drawn.

<!-- screenshots:begin (managed by screenshot-docs) -->
![Square and Voronoi merged marker layouts compared](docs/screenshots/paired_artwork_pages.png)
<!-- screenshots:end -->

The comparison uses a `43x30` working resolution with same-color merging enabled. Its square panel
is the generated marker preview; its Voronoi panel is rendered directly from the filled PDF
reference page. The source is Vincent van Gogh's public-domain *Self-Portrait with a Straw Hat*
from The Metropolitan Museum of Art.

## From photograph to printable regions

The tool samples the source, matches each sample to the supplied 48-color Aoartix marker palette,
and turns the assignments into printable regions:

- `square` is the default layout, with 86 by 60 landscape cells or 60 by 86 portrait cells.
- `voronoi` uses the same requested count and aspect ratio to construct bounded organic polygons.
- `-g COLUMNSxROWS` changes the working resolution for either layout.
- `-m` merges edge-adjacent shapes with the same marker assignment into a single outlined region.
- Every rendered region receives one marker code; labels are kept fully inside their region when
  space permits and otherwise use the best available maximum-clearance interior position.
- Page orientation follows the corrected source image unless `-L` or `-P` overrides it.
- Perceptual color matching and selective shadow enhancement preserve useful dark detail.

The printable PDFs are the primary result. Square mode creates a two-page blank and numbered
artwork PDF plus a compact marker-key PDF. Voronoi mode creates one three-page PDF containing the
blank artwork, numbered reference, and filled palette reference. Because the pages in each set use
the same vector geometry, they remain aligned when printed at the same scale.

## Before the first print

The built-in RGB values come from the supplied product chart, not physical ink swatches. Alcohol
ink appearance changes with paper, lighting, and camera capture. The chart palette is a useful
starting point; measured swatches on the final paper provide the closest physical match.

The default 86 by 60 resolution retains fine source detail, but its printed regions are small.
Start with `-g 43x30` for larger regions and more legible codes, then increase the resolution only
when the subject needs it. Use the generated source and marker previews to judge the crop, layout,
and palette reduction before printing.

The default strong enhancement changes only two measured color groups: locally changing dark
colors receive a shadow curve, and warm midtones receive a modest chroma boost. Flat backgrounds
and neutral black regions keep ordinary nearest-color matching. Use `-e none` for the unmodified
baseline or `-e balanced` for a gentler treatment.

## Quick start

Use Python 3.12 and install the packages in `pip_requirements.txt` as described in
[docs/INSTALL.md](docs/INSTALL.md). Then run the included marker chart through the complete path:

```bash
source source_me.sh && python3 color_by_number.py -i palettes/marker_image_set.jpg
```

The default square run writes its primary PDFs under `output/pdf/`:

```text
output/pdf/color_by_number.pdf
output/pdf/color_by_number_grid_only.pdf
```

Open `output/pdf/color_by_number_grid_only.pdf` and print both pages in its generated orientation.
Use `output/pdf/color_by_number.pdf` for the colored marker key. Replace the input path with the
photograph to convert.

For the organic layout with larger regions and same-color merging:

```bash
source source_me.sh && python3 color_by_number.py \
  -i photograph.jpg --layout voronoi -g 43x30 -m
```

Open `output/pdf/color_by_number.pdf` and print all three pages at the same scale. Page one is
blank, page two is the numbered reference, and page three is the filled marker-color reference.

## Try a public-domain portrait

These museum records provide downloadable public-domain images, so they are useful reproducible
examples without adding a large source image to this repository. Attribution is not required for
public-domain works, but keep the artist, title, and museum with shared results:

- Diego Velazquez, *Juan de Pareja*, The Metropolitan Museum of Art:
  [collection record](https://www.metmuseum.org/art/collection/search/437869) and
  [full-resolution original](https://images.metmuseum.org/CRDImages/ep/original/DP-14286-001.jpg).
  The Met marks the image Public Domain. Its dark skin, hair, clothing, and warm brown shadows test
  whether the palette preserves dark detail instead of collapsing it into marker `120`.
- Jean-Auguste-Dominique Ingres, *Madame Moitessier*, National Gallery of Art:
  [public-domain collection record and download](https://www.nga.gov/artworks/32696-madame-moitessier).
  The gallery marks the object's media free and in the public domain. Pale skin, black clothing,
  flower colors, and the patterned maroon wall test light skin separation and saturated reds.
- Vincent van Gogh, *Self-Portrait with a Straw Hat*, The Metropolitan Museum of Art:
  [public-domain collection record and download](https://www.metmuseum.org/art/collection/search/436532).
  The Met marks the image Public Domain. Alternating blue, yellow, orange, and green brushwork tests
  how a limited marker palette handles rapid hue changes and visible texture.

Download one image, save it locally, and pass its path to `-i`. Keep the museum attribution in any
published comparison so other readers can reproduce the same test.

## Outputs that support the print

| Output | What it provides |
| --- | --- |
| Square `color_by_number_grid_only.pdf` | Aligned blank-gray and black-numbered artwork pages. |
| Square `color_by_number.pdf` | Compact numbered worksheet with a colored marker key. |
| Voronoi `color_by_number.pdf` | Aligned blank, numbered, and filled-reference polygon pages. |
| Marker or polygon preview PNG | Quick visual check of selected marker colors and boundaries. |
| Source preview PNG | Orientation-matched source-color reference for comparison. |
| Legend and summary | Palette usage, rendered-region reduction, and color-error statistics. |

Use `-o output/pdf/family_portrait.pdf` to choose the worksheet filename. All companion files
inherit the `family_portrait` stem. Use `-f contain` to preserve the complete source image instead
of center cropping it.

Automatic page orientation follows the EXIF-corrected source dimensions. Use `-L` or `--landscape`
to force landscape or `-P` or `--portrait` to force portrait. The default `-g 86x60` value describes
landscape columns by rows; portrait swaps it to 60 by 86. Square sources use landscape unless
overridden. Use another resolution, such as `-g 43x30`, for larger physical squares.

Choose `-e none`, `-e balanced`, or `-e strong`. Strong is the default when preserving visible
shadow structure matters most; balanced stays closer to the source under the reported Delta E 76
metric.

Per-shape assignment CSV files are also generated for analysis and automation. They are diagnostic
companions rather than part of the normal printing workflow.

## Aoartix marker palette

The built-in [palettes/aoartix_48.yml](palettes/aoartix_48.yml) palette contains all 48 codes and
names from [palettes/marker_image_set.jpg](palettes/marker_image_set.jpg). Each RGB triplet is the
median flat-background color sampled from its reference-chart swatch.

## Documentation

- [docs/INSTALL.md](docs/INSTALL.md): Python 3.12 requirements and dependency setup.
- [docs/USAGE.md](docs/USAGE.md): fitting, sizing, custom palette, and output options.
- [docs/REGION_PIPELINE.md](docs/REGION_PIPELINE.md): printable-region lifecycle, merging, and
  renderer handoff.
- [docs/CODE_ARCHITECTURE.md](docs/CODE_ARCHITECTURE.md): pipeline stages, module boundaries, and
  data flow.
- [docs/FILE_STRUCTURE.md](docs/FILE_STRUCTURE.md): source, palette, test, and generated-output
  locations.
- [docs/VISION_PIPELINE.md](docs/VISION_PIPELINE.md): image-processing contract, metrics, and
  limitations.

## License

The source code is available under the [MIT License](LICENSE.MIT.md).
