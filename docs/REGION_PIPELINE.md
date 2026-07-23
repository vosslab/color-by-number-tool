# Region pipeline

## Scope and invariant

This reference follows printable regions after color assignment. Square and Voronoi layouts keep
their own source geometry and assignments, then both materialize exactly one concrete immutable
`tuple[RenderRegion, ...]`. Ordinary one-shape regions and unioned same-color regions use the same
record and the same downstream interfaces.

`-m`/`--merge-regions` enables merging. `-M`/`--no-merge-regions` explicitly keeps one printable
region per assigned shape; it is the default.

```text
source shapes + palette assignments
                |
                v
build_square_regions() or build_voronoi_regions()
                |
                v
tuple[RenderRegion, ...]
     |          |           |           |
     v          v           v           v
PDF pages   boundaries    legend      summary
```

Assignment CSVs and square raster previews are intentionally outside this branch. Voronoi previews
use raster pixels for their fills but draw boundaries from the `RenderRegion` tuple.

## Source shapes

Square assignments form row-major unit boxes. A member identifier is the flattened row-major grid
position, and its palette index comes from the matching result.

Voronoi assignments form stable site-ordered bounded cells. A member identifier is the stable site
identifier, and its palette index comes from the polygon matching result. The Voronoi partition
remains authoritative for sampling and assignment audits; it is not coerced into a grid.

[../colorbynumber/render_regions.py](../colorbynumber/render_regions.py) converts either source into
the shared output model through `build_square_regions()` or `build_voronoi_regions()`. Both call the
same `build_regions()` implementation.

## Render-region model

`RenderRegion` is a frozen record with three fields:

| Field | Meaning |
| --- | --- |
| `palette_index` | Zero-based index of the one palette color used by this printable region. |
| `member_identifiers` | Source-shape identifiers represented by this connected printable region. |
| `polygon` | One valid, nonempty Shapely `Polygon` used by every region-aware renderer. |

`member_identifiers` retain traceability to the original assignments. A region with `(12, 13, 14)`
is one printable connected component representing exactly those source squares or Voronoi cells;
it does not replace or rewrite their CSV audit rows.

## Building regions

With merging disabled, the builder emits one `RenderRegion` for every source shape, in authoritative
assignment order. Downstream consumers therefore do not need a special unmerged path.

With merging enabled, the builder:

1. Groups source polygons by their exact palette index.
2. Uses Shapely union on each color group.
3. Emits each connected `Polygon` component as one `RenderRegion`.
4. Sorts the result by its first member identifier for deterministic output.

Positive-length shared edges combine. Point-only contacts and disconnected same-color components
remain separate printable regions. Polygon holes remain holes in the region geometry.

The builder rejects malformed source geometry and checks these invariants:

- Every source member identifier occurs exactly once across the resulting tuple.
- A merged color group preserves the sum of its assigned polygon areas.
- Every region has nonempty valid polygon geometry and a nonnegative palette index.
- Output writers also validate that each palette index is inside the selected palette.

## Rendering and diagnostics

All region-aware output receives the same concrete tuple:

- [../colorbynumber/pdf_writer.py](../colorbynumber/pdf_writer.py) writes the square worksheet and
  marker key.
- [../colorbynumber/grid_only_pdf_writer.py](../colorbynumber/grid_only_pdf_writer.py) writes the
  square blank and numbered pages.
- [../colorbynumber/voronoi_pdf_writer.py](../colorbynumber/voronoi_pdf_writer.py) writes the blank,
  numbered, and palette-reference pages.
- [../colorbynumber/voronoi_preview_writer.py](../colorbynumber/voronoi_preview_writer.py) draws
  printable-region boundaries on both Voronoi previews.
- [../colorbynumber/csv_writer.py](../colorbynumber/csv_writer.py) and
  [../colorbynumber/voronoi_csv_writer.py](../colorbynumber/voronoi_csv_writer.py) derive legend
  base-shape and rendered-region counts.

PDF code anchors begin at the Shapely area centroid of each `RenderRegion.polygon`, then transform
the region into physical PDF points. The writer measures the actual code glyph box, adds `0.25`
points of inward padding, and preserves the exact centroid only when the padded box is strictly
inside the region. Otherwise a deterministic contained-position search shifts the label and
revalidates the final box against the original PDF-space polygon. If the region cannot hold the
complete padded box, the code uses its maximum-clearance interior point and the PDF records a
best-effort placement instead of failing.
PDF paths use even-odd filling, so region holes remain visible on blank, numbered, and reference
pages.

Summaries record whether merging is enabled, the base shape count, the rendered-region count, and
the reduction. Assignment CSVs remain the raw per-square or per-polygon audit output and never
consume merged geometry. Square PNG previews remain raster-only and do not add region boundaries.

## Extending geometry

To support a new source of more complex Shapely polygons, adapt that source into a dedicated
builder which calls `build_regions()`. Preserve the `RenderRegion` tuple and all consumers. This
keeps topology details such as multipart color groups and holes at the boundary where geometry is
created, rather than spreading layout-specific cases through PDFs, previews, legends, or summaries.

## Verification

- [../tests/test_render_regions.py](../tests/test_render_regions.py) covers shared-edge merging,
  diagonal separation, holes, membership, validation, and the Voronoi adapter.
- [../tests/test_color_by_number.py](../tests/test_color_by_number.py) covers square PDFs, legend
  counts, summaries, and the default unmerged coordinator path.
- [../tests/test_voronoi_output_writers.py](../tests/test_voronoi_output_writers.py) and
  [../tests/test_voronoi_pipeline.py](../tests/test_voronoi_pipeline.py) cover Voronoi writers,
  summaries, CLI flags, and coordinator output.

Run `source source_me.sh && python3 -m pytest tests/` for the full suite.
