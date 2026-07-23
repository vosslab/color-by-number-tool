# Voronoi Milestone 3 decision

## Decision

The selected Voronoi pathway is accepted as an optional production output: deterministic selected
sites create ordered polygons, polygon-area sampling assigns every site, and the rendered previews
show the intended irregular polygon appearance. Bounded Voronoi construction is settled plumbing;
the user framing has not changed. The pathway uses a clipped-polygon area centroid as its
good-enough label anchor, not a label-optimization system.

Square remains the default output, while `--layout voronoi` selects this separate pathway. The
production run generates and records an internal random seed; it does not add a user seed flag.
The accepted limitations are remaining boundary-label crossings and single-page density at `60x86`.
They do not reopen point-spacing search.

## Fixed prototype

The prototype reused the Milestone 2B selection without tuning it:

- hard-core `d/s = 0.70` with a `100N` total-draw budget;
- two cumulative bounded Lloyd moves at `alpha = 0.50`;
- replay seed `20260722`;
- existing Aoartix 48 palette, crop fit, and strong enhancement;
- equal-weight fitted-raster pixel-center sampling for each owned polygon;
- shared-edge polygon adjacency for strong enhancement, replacing only the square path's
  four-neighbor relation while retaining its thresholds and transforms.

The square control remains its separate square pipeline. No generic layout model or rectangular
Voronoi assignment was introduced.

## Image evidence

All observed image runs have zero polygon-sampling fallbacks and zero ownership-seam fallbacks.
Kimi's portrait comparisons preserve the broad face, hair, clothing, and background regions while
replacing square seams with irregular polygon boundaries.

| Case | Square mean/max Delta E 76 | Voronoi mean/max Delta E 76 | Result |
| --- | --- | --- | --- |
| Kimi `30x43` | 18.0950 / 95.1638 | 18.1563 / 96.0332 | Square lower |
| Kimi `60x86` | 16.7776 / 90.3531 | 16.8489 / 92.5184 | Square lower |
| Marker chart `43x30` | 17.926 / 118.326 | 17.001 / 113.842 | Voronoi lower |
| Synthetic hard edge `43x30` | 6.015 / 137.712 | 6.247 / 132.418 | Mixed: square mean lower, Voronoi max lower |

There is no composite score and no image-quality winner. Pixel-weighted Delta E at fitted raster
centers measures palette reconstruction, not hand-coloring usability, label fit, print quality, or
human preference. The marker chart is not a photograph, and the synthetic fixture deliberately
emphasizes sharp edges. These results validate the pathway and show its tradeoffs; they do not
justify retuning the selected distribution.

Ignored local evidence contains 23 Milestone 3 artifacts: 16 PNGs, five PDFs, and two JSON records.
It includes the Kimi, marker-chart, synthetic-edge, and print comparisons.

## Print evidence and accepted limitation

The three-page Voronoi PDFs have correctly ordered blank, numbered, and palette-reference pages,
with intact margins, outlines, and reference art. The earlier site-centered numbered labels failed
the print-readiness gate:

| Case | Font points | Outside polygon | Positive-area overlaps | Domain-edge clipping |
| --- | ---: | ---: | ---: | ---: |
| Kimi resolved `30x43` | 6.500 | 63 | 6 | 14 |
| Kimi resolved `60x86` | 3.282 | 302 | 43 | 19 |
| Marker chart `43x30` | 6.500 | 57 | 6 | 23 |

The accepted clipped-polygon area-centroid anchor improves the real Kimi `30x43` CLI smoke from
63 outside-polygon labels and six positive-area overlaps with the site-centered anchor to 54 and
three, respectively. It is a pragmatic alignment anchor, not an optimization of label fit. Some
boundary crossings remain. The `60x86` Kimi page remains too dense for dependable single-page
code reading. The square `86x60` control is also beyond a comfortable single-page code density at
3.030-point labels, so the density limit is partly shared with square output. This is not evidence
that site distribution needs adjustment.

## Production follow-through

- `--layout voronoi` is an optional public pathway; square is still the default.
- Voronoi owns six dedicated output artifacts for its PDF, previews, assignments, summary, and
  diagnostics rather than sharing square-grid output structures.
- The internal random seed is recorded for replay and support without exposing a production seed
  option.
- Area-centroid labels are accepted as good enough for this output option. They do not guarantee
  containment, collision freedom, or best visual placement.
- Strong enhancement has only been compared with the square thresholds and transforms; shared-edge
  adjacency makes that comparison meaningful, not automatically optimal.
- Larger raster exports need an explicit performance check because ownership is polygon by polygon.
- The selected spacing remains a `43x30` experiment selection even though image evidence also ran
  at resolved `60x86`.

No further spacing search is planned. A future label-layout or multipage-density workstream may
improve this optional pathway if user value warrants it. Reconsider point distribution only if that
work identifies a specific cell-shape or boundary failure attributable to spacing.

This decision follows
[voronoi_milestone_2b_partial_lloyd_screen.md](voronoi_milestone_2b_partial_lloyd_screen.md) and
updates the active
[voronoi_layout_experiment_plan.md](../active/voronoi_layout_experiment_plan.md).
