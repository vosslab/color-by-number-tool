# Voronoi Milestone 2B decision

## Decision

Use two cumulative bounded Lloyd point movements with `alpha = 0.50` as the good-enough `43x30`
spacing checkpoint. The start remains deterministic hard-core sampling at `d/s = 0.70` with the
`100N` total-candidate budget.

This selects an experimental point distribution for the next image and print checks. It does not
add a production Voronoi mode or reopen the settled bounded-partition construction.

## Fixed experiment

The screen was fixed before viewing:

- dimensions: `43x30`, so `N = 1,290`;
- seeds: `20260722`, `20260723`, and `20260724`;
- starting generator: hard-core `d/s = 0.70`, `100N = 129,000` draws;
- movement fraction: `alpha = 0.50`;
- cumulative checkpoints: `1`, `2`, and `4`;
- unchanged anchors: jitter `0.50`, hard-core `0.50`, and raw hard-core `0.70`;
- primary evidence: area CV, area p90/p10, exact covering radius,
  boundary/interior median area, and equal-scale visuals.

No alpha or checkpoint was changed after viewing. Nearest-neighbor diagnostics remain secondary and
did not select the checkpoint. Numeric metrics do not measure randomness or grid signature.

The complete ignored record is
`output/voronoi_experiment/milestone2b/milestone_2b_screen_summary.json`. It references nine relaxed
JSON/SVG evaluation pairs and three self-contained equal-scale SVG/JSON boards.

## Aggregate evidence

Each value is the median across the three fixed seeds. Full precision and ranges remain in the
ignored summary.

| Distribution | Area CV | p90/p10 | Cover radius | Boundary area |
| --- | ---: | ---: | ---: | ---: |
| Jitter `0.50` anchor | 0.127637 | 1.392125 | 0.027494 | 1.008060 |
| Hard-core `0.50` anchor | 0.350330 | 2.443153 | 0.045483 | 0.919402 |
| Hard-core `0.70` raw | 0.209717 | 1.686202 | 0.031808 | 0.868621 |
| Lloyd step `1` | 0.180434 | 1.562397 | 0.030157 | 0.902744 |
| Lloyd step `2` | 0.160774 | 1.485329 | 0.028888 | 0.916860 |
| Lloyd step `4` | 0.136800 | 1.411041 | 0.027548 | 0.923398 |

Every additional checkpoint improves all four recorded measurements. The numbers alone therefore do
not identify the desired organic stopping point; the equal-scale boards supply the missing visual
evidence.

## Visual result

All three boards rendered headlessly at 2,400 pixels with the same physical scale and panel order.
Stable observations across seeds are:

- Step `1` reduces the largest raw hard-core cells but leaves conspicuous local size variation.
- Step `2` further reduces holes and size contrast while retaining an irregular pattern without the
  jitter anchor's global rows and columns.
- Step `4` is the most even checkpoint, but its locally honeycomb-like regularity is more visible and
  the additional reduction in conspicuous holes is less important for the requested edgy option.
- Boundary cells remain visibly distinct, and their median area ratio remains below one at every
  Lloyd checkpoint.

The board files are:

- seed `20260722`:
  `milestone2b_c43_r30_seed20260722_cfg-8d143136a69a0277bf6fe024367805ee80d64b76c5cd927dae171c2f1d20bf38_comparison-board.svg`;
- seed `20260723`:
  `milestone2b_c43_r30_seed20260723_cfg-2201c7733b3be259e2d9f070792f1c50e860628dcaca34c38b12a0c83dcb61f5_comparison-board.svg`;
- seed `20260724`:
  `milestone2b_c43_r30_seed20260724_cfg-0389036b3cbd6e9eb3c1d90cea04a6456f6e6cccd4a9a8f60cb14292bb4f93f7_comparison-board.svg`.

## Alternatives ledger

| Alternative | Positive result | Negative result | Disposition | Reconsider if |
| --- | --- | --- | --- | --- |
| Raw hard-core `0.70` | Organic start with no global rows or columns | Residual holes, larger area spread, low boundary-area ratio | Superseded by step `2` for the next check | Maximum disorder matters more than cell equality |
| Lloyd step `1` | Visible improvement with least movement | Several large cells and uneven patches remain across seeds | Rejected as too early | One step proves materially cheaper in a future production budget |
| Lloyd step `2` | Good reduction in holes and area spread while retaining irregularity | Boundary ratio remains below one; some local regularity appears | Selected good-enough knee | Image or print evidence exposes a failure |
| Lloyd step `4` | Best equality and covering measurements in this screen | Stronger local honeycomb character and two extra movements | Retained equality-first alternative | Equality or label clearance becomes more important than edginess |
| Jitter `0.50` | Strongest boundary neutrality and area equality anchor | Global rows and columns remain visible | Comparator only | Grid ancestry becomes acceptable |
| Hard-core `0.50` | Most visibly disordered hard-core anchor | Large holes and the weakest area equality | Comparator only | Disorder dominates every reconstruction and print concern |

Local unclumping, a different alpha, and boundary forces were not tested because step `2` answered
the current point-spacing question well enough. Reconsider them only if image or print validation
reveals a specific failure that this fixed screen did not measure.

## Limits and next step

This result covers `43x30` point spacing only. It does not establish behavior at `86x60` or
`100x75`, image sampling quality, label clearance, printable linework, or a production interface.
Timing metadata records raw generation and final checkpoint evaluation; it does not measure the
cumulative intermediate relaxation cost.

Next, run the selected step `2` distribution through the separate Voronoi image and print prototype
and compare it with the unchanged square output. Keep raw hard-core `0.70` and Lloyd step `4`
available only as evidence-backed fallbacks if that validation changes the goal.

This decision continues the raw screen in
[voronoi_milestone_2a_distribution_screen.md](voronoi_milestone_2a_distribution_screen.md) and the
approved experiment in
[../active/voronoi_layout_experiment_plan.md](../active/voronoi_layout_experiment_plan.md).
