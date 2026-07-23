# Voronoi Milestone 2A distribution screen

## Decision status

Milestone 2A establishes the raw site-distribution screen before any Lloyd movement. It does not
select a production feature or alter the square pipeline.

Use hard-core `d/s = 0.70` as the starting distribution for the next partial bounded Lloyd
experiment. Retain hard-core `d/s = 0.50` as the visual-disorder comparator and stratified jitter
`f = 0.50` as the equality and grid-signature comparator. Keep stratified jitter `f = 1.00` in the
record as the less visibly gridded boundary-neutral endpoint. This is an experiment recommendation,
not a final layout selection.

## Evidence policy

The screen used seeds `20260722`, `20260723`, and `20260724`, fixed before any rendering was viewed.
The grid control is deterministic and therefore has one `seed_none` observation. Every stochastic
row below uses one of the three fixed seeds.

Primary evidence:

- cell-area coefficient of variation;
- area p90/p10 ratio;
- exact bounded covering radius;
- verification that hard-core minimum distance meets the requested `d/s`;
- boundary-cell median area divided by interior-cell median area;
- equal-scale fixed-seed visuals.

Nearest-neighbor coefficient of variation, nearest-neighbor minimum/median ratio, and boundary-band
density remain secondary diagnostics. They did not select or eliminate candidates. No composite
score or ranking was formed. Randomness, grid signature, and local regularity are human observations
from the comparison board rather than inferences from numeric metrics.

Exact JSON evaluations, per-seed timing metadata, aggregate medians/ranges, explicit failures, and
the combined summary live under the ignored local path
`output/voronoi_experiment/milestone2a/`. The combined record is
`milestone_2a_screen_summary.json`.

## Generator contracts

Stratified jitter places exactly one site in each of the `C x R` rectangular strata. The
dimensionless fraction `f` scales displacement from the stratum center on both axes: `f = 0` is the
exact centered grid and `f = 1` spans the full stratum. Values outside `[0, 1]` fail explicitly.

Hard-core generation uses deterministic uniform dart throwing and an owned square-bin neighbor
index. Its minimum center distance is `d = ratio * s`, where `s = sqrt(1/N)`. The declared
`total-uniform-candidate-draws-v1` policy permits `100N` total candidate draws. Exhaustion reports
the accepted count and performs no retry, repair, joggle, or seed change.

Configuration schema 5 records `f`, `d/s`, absolute `d`, the attempt budget, and the attempt policy.
Geometry implementation version 5 adds the shared hard-core numerical preflight for requested
distance, squared distance, and maximum required bin coordinate. Configuration schema 5 and
artifact schema 4 remain valid because their record grammars did not change.

## Adaptability handoff

Adaptability comes from stable separate stages and preserved evidence: deterministic generator
contracts feed construction, validation, measurement, and rendering without combining their
responsibilities; complete versioned configurations make every candidate replayable; and the
negative-results ledger supplies explicit revisit triggers when goals change. A later experiment
can replace one stage or reconsider one candidate without erasing the controls.

This does not introduce a generic layout abstraction. The production square representation and the
experimental Voronoi representation remain separate, and they reuse only utilities already proven
representation-independent. No future production coordinator, writer, or CLI API is claimed here.

## Feasibility bracket

At `43x30`, hard-core `d/s = 0.25`, `0.50`, and `0.70` reached exactly 1,290 sites for all three
seeds. The next required probe, `d/s = 0.85`, exhausted all 129,000 draws under
`total-uniform-candidate-draws-v1`:

| Seed | Accepted | Target | Budget |
| ---: | ---: | ---: | ---: |
| 20260722 | 1,193 | 1,290 | 129,000 |
| 20260723 | 1,199 | 1,290 | 129,000 |
| 20260724 | 1,193 | 1,290 | 129,000 |

This brackets the practical raw dart-throwing region between successful `0.70` and failed `0.85`
for this generator, seed set, budget, and policy. Each `0.85` run produced no 1,290-site sample or
evaluation. This does not prove that a geometric 1,290-site configuration at that separation is
infeasible. The complete failure records remain in `milestone_2a_screen_summary.json`; variable
single-run failure timings are intentionally omitted here because they did not select a candidate.

Every successful hard-core evaluation met the requested center distance. Observed minimum `d/s`
ranges were `0.25014-0.25048`, `0.50013-0.50043`, and `0.70005-0.70094` at `43x30`;
`0.50003-0.50013` and `0.70001-0.70006` at `86x60`; and `0.70003-0.70008` at `100x75`.

## Tested alternatives ledger

This ledger preserves negative results so a later goal change can recover an alternative without
repeating the screen. The per-seed tables below and `milestone_2a_screen_summary.json` preserve the
numeric evidence.

| Alternative | Tested configuration | Observed strengths | Negative result or failure mode | Current disposition | Reconsider if |
| --- | --- | --- | --- | --- | --- |
| Grid | `43x30`, `86x60`, `100x75`; deterministic `seed_none`; no attempt budget | Exact equality, smallest covering radius, neutral boundary area, fastest construction control | Fully visible rows and columns; does not satisfy the organic-layout goal | Equality and production-square control | The goal changes to strict equality, simplest print behavior, or square-only output |
| Uniform | All three scales; seeds `20260722-20260724`; no attempt budget | Maximum unstructured visual disorder and minimal generation mechanism | Close clusters, large holes, high area CV and p90/p10, unstable boundary cells | Negative clumping control | Unconstrained randomness matters more than cell equality, hole size, and label geometry |
| Jitter `0.50` | All three scales; all three seeds; one site per stratum; no attempt budget | Best non-grid area CV and p90/p10, small covering radius, boundary area near one | Strong visible row, column, and fourfold signature | Retained equality/grid-signature comparator | Equality and boundary regularity become more important than hiding grid ancestry |
| Jitter `1.00` | All three scales; all three seeds; one site per stratum; no attempt budget | Boundary area remains near one; global grid signature is weaker than at `0.50` | Patchy cell sizes remain visible; area spread is higher than jitter `0.50` and hard-core `0.70` | Rejected as the next movement start; retained as a durable endpoint | Boundary neutrality and weaker grid signature are valued above area equality, or a different downstream step benefits from one-site-per-stratum ownership |
| Hard-core `0.25` | `43x30`; all three seeds; `100N = 129,000` draws | Enforces the proposed circle separation exactly with low generation cost | Visual holes and area spread remain close to the uniform control | Rejected raw candidate | Only the closest pair avoidance is required and larger holes are acceptable |
| Hard-core `0.50` | `43x30` and `86x60`; all three seeds; `100N` draws | Organic visual disorder, exact requested separation, and default-size boundary area near one | Larger holes and more area spread than `0.70` | Retained visual-disorder comparator | Organic disorder and boundary neutrality matter more than reducing holes and area spread |
| Hard-core `0.70` | All three scales; all three seeds; `100N` draws | Exact requested separation, lower area spread and covering radius than `0.50`, organic board without global rows or columns | Some local regularity; boundary/interior area stays below one; residual holes remain | Advance as partial-Lloyd starting point | Reconsider this lead if boundary neutrality or maximum disorder becomes the dominant goal |
| Hard-core `0.85` | `43x30`; all three seeds; `100N = 129,000` draws | Establishes the upper generator/policy bracket | This generator, seed set, budget, and policy produced no 1,290-site sample or evaluation; geometric feasibility is not disproven | Rejected under the declared raw dart-throwing policy | The generator or termination policy changes materially; do not retry the same seed and budget as if it were new evidence |

### Methodological negative results

Observed process history:

- An early metric-only interpretation treated hard-core `0.50` and jitter `1.00` as eliminations.
  That interpretation used nearest-neighbor minimum/median and boundary-band density too strongly
  before the equal-scale comparison policy was applied.
- The visual-policy review withdrew both early eliminations. Hard-core `0.50` was rerun at `86x60`
  for all three seeds and retained as the visual-disorder comparator. Jitter `1.00` was restored to
  the `100x75` survivor check because the primary covering and boundary evidence remained distinct.
- Nearest-neighbor CV, nearest-neighbor minimum/median, and the one-nominal-spacing boundary-band
  density are now secondary diagnostics. They cannot select or eliminate a candidate in this plan.
- The current numeric metrics do not measure randomness or grid signature. Those judgments require
  the precommitted-seed equal-scale board.

This superseded interpretation remains in the record as a methodological negative result. It is
not a competing current decision.

## Per-seed primary evidence

The columns are area CV, area p90/p10, exact covering radius, and boundary/interior median area.
Values are rounded here for scanning; the ignored JSON keeps full double precision.

### Initial 43x30 screen

| Candidate | Seed | Area CV | p90/p10 | Cover radius | Boundary area |
| --- | ---: | ---: | ---: | ---: | ---: |
| grid | none | 0.000000 | 1.000000 | 0.019687 | 1.000000 |
| uniform | 20260722 | 0.551072 | 4.350476 | 0.058240 | 1.246432 |
| uniform | 20260723 | 0.553580 | 4.520336 | 0.055552 | 0.942479 |
| uniform | 20260724 | 0.523912 | 4.155485 | 0.057377 | 1.056658 |
| jitter 0.50 | 20260722 | 0.127407 | 1.396531 | 0.028105 | 1.008060 |
| jitter 0.50 | 20260723 | 0.128148 | 1.388354 | 0.027494 | 1.024586 |
| jitter 0.50 | 20260724 | 0.127637 | 1.392125 | 0.025381 | 0.995637 |
| jitter 1.00 | 20260722 | 0.246971 | 1.929289 | 0.036525 | 1.000286 |
| jitter 1.00 | 20260723 | 0.247645 | 1.910417 | 0.034319 | 1.085224 |
| jitter 1.00 | 20260724 | 0.246549 | 1.944558 | 0.031185 | 0.998486 |
| hard-core 0.25 | 20260722 | 0.493519 | 3.673035 | 0.058240 | 1.138149 |
| hard-core 0.25 | 20260723 | 0.489732 | 3.483612 | 0.055676 | 0.979303 |
| hard-core 0.25 | 20260724 | 0.475921 | 3.526671 | 0.053613 | 0.929867 |
| hard-core 0.50 | 20260722 | 0.326149 | 2.318821 | 0.045483 | 1.044019 |
| hard-core 0.50 | 20260723 | 0.362393 | 2.484946 | 0.043066 | 0.877408 |
| hard-core 0.50 | 20260724 | 0.350330 | 2.443153 | 0.057377 | 0.919402 |
| hard-core 0.70 | 20260722 | 0.206949 | 1.672853 | 0.038249 | 0.893363 |
| hard-core 0.70 | 20260723 | 0.209717 | 1.686202 | 0.030919 | 0.868621 |
| hard-core 0.70 | 20260724 | 0.217754 | 1.739572 | 0.031808 | 0.822872 |

### Default 86x60 screen

| Candidate | Seed | Area CV | p90/p10 | Cover radius | Boundary area |
| --- | ---: | ---: | ---: | ---: | ---: |
| grid | none | 0.000000 | 1.000000 | 0.009844 | 1.000000 |
| uniform | 20260722 | 0.538054 | 4.302362 | 0.034659 | 1.265397 |
| uniform | 20260723 | 0.531309 | 4.263198 | 0.024333 | 1.048069 |
| uniform | 20260724 | 0.533357 | 4.397454 | 0.027264 | 1.074951 |
| jitter 0.50 | 20260722 | 0.126922 | 1.399548 | 0.013941 | 0.998625 |
| jitter 0.50 | 20260723 | 0.128738 | 1.411168 | 0.013511 | 1.002980 |
| jitter 0.50 | 20260724 | 0.126692 | 1.396108 | 0.013646 | 0.988686 |
| jitter 1.00 | 20260722 | 0.246765 | 1.931865 | 0.018067 | 0.978931 |
| jitter 1.00 | 20260723 | 0.249013 | 1.946875 | 0.017184 | 1.012434 |
| jitter 1.00 | 20260724 | 0.245132 | 1.915012 | 0.017459 | 0.979987 |
| hard-core 0.50 | 20260722 | 0.337474 | 2.353703 | 0.022209 | 0.982546 |
| hard-core 0.50 | 20260723 | 0.334980 | 2.352438 | 0.025495 | 1.031176 |
| hard-core 0.50 | 20260724 | 0.339212 | 2.380588 | 0.021876 | 0.973153 |
| hard-core 0.70 | 20260722 | 0.205104 | 1.674964 | 0.020038 | 0.871445 |
| hard-core 0.70 | 20260723 | 0.199455 | 1.655360 | 0.018830 | 0.899748 |
| hard-core 0.70 | 20260724 | 0.204454 | 1.677358 | 0.017196 | 0.856928 |

### Large 100x75 check

| Candidate | Seed | Area CV | p90/p10 | Cover radius | Boundary area |
| --- | ---: | ---: | ---: | ---: | ---: |
| grid | none | 0.000000 | 1.000000 | 0.008165 | 1.000000 |
| uniform | 20260722 | 0.539347 | 4.285465 | 0.027847 | 1.158881 |
| uniform | 20260723 | 0.537382 | 4.349028 | 0.023480 | 1.089173 |
| uniform | 20260724 | 0.535075 | 4.353832 | 0.021712 | 1.101456 |
| jitter 0.50 | 20260722 | 0.127436 | 1.396834 | 0.011650 | 1.000897 |
| jitter 0.50 | 20260723 | 0.127819 | 1.398596 | 0.011207 | 0.980919 |
| jitter 0.50 | 20260724 | 0.129535 | 1.406641 | 0.011535 | 1.002749 |
| jitter 1.00 | 20260722 | 0.245590 | 1.907775 | 0.014676 | 0.994153 |
| jitter 1.00 | 20260723 | 0.247573 | 1.933803 | 0.014253 | 0.978179 |
| jitter 1.00 | 20260724 | 0.249682 | 1.945276 | 0.014311 | 1.016512 |
| hard-core 0.70 | 20260722 | 0.201788 | 1.666808 | 0.017156 | 0.855898 |
| hard-core 0.70 | 20260723 | 0.201906 | 1.674064 | 0.016376 | 0.897345 |
| hard-core 0.70 | 20260724 | 0.205953 | 1.695536 | 0.015419 | 0.848399 |

## Median and range

Each entry is `median [minimum, maximum]` across the three fixed seeds. The grid has one exact
observation.

### Initial candidates

| Candidate | Area CV | p90/p10 | Cover radius | Boundary area |
| --- | --- | --- | --- | --- |
| grid | 0.000000 [same] | 1.000000 [same] | 0.019687 [same] | 1.000000 [same] |
| uniform | 0.551072 [0.523912, 0.553580] | 4.350476 [4.155485, 4.520336] | 0.057377 [0.055552, 0.058240] | 1.056658 [0.942479, 1.246432] |
| jitter 0.50 | 0.127637 [0.127407, 0.128148] | 1.392125 [1.388354, 1.396531] | 0.027494 [0.025381, 0.028105] | 1.008060 [0.995637, 1.024586] |
| jitter 1.00 | 0.246971 [0.246549, 0.247645] | 1.929289 [1.910417, 1.944558] | 0.034319 [0.031185, 0.036525] | 1.000286 [0.998486, 1.085224] |
| hard-core 0.25 | 0.489732 [0.475921, 0.493519] | 3.526671 [3.483612, 3.673035] | 0.055676 [0.053613, 0.058240] | 0.979303 [0.929867, 1.138149] |
| hard-core 0.50 | 0.350330 [0.326149, 0.362393] | 2.443153 [2.318821, 2.484946] | 0.045483 [0.043066, 0.057377] | 0.919402 [0.877408, 1.044019] |
| hard-core 0.70 | 0.209717 [0.206949, 0.217754] | 1.686202 [1.672853, 1.739572] | 0.031808 [0.030919, 0.038249] | 0.868621 [0.822872, 0.893363] |

### Default-size promoted regions

| Candidate | Area CV | p90/p10 | Cover radius | Boundary area |
| --- | --- | --- | --- | --- |
| uniform | 0.533357 [0.531309, 0.538054] | 4.302362 [4.263198, 4.397454] | 0.027264 [0.024333, 0.034659] | 1.074951 [1.048069, 1.265397] |
| jitter 0.50 | 0.126922 [0.126692, 0.128738] | 1.399548 [1.396108, 1.411168] | 0.013646 [0.013511, 0.013941] | 0.998625 [0.988686, 1.002980] |
| jitter 1.00 | 0.246765 [0.245132, 0.249013] | 1.931865 [1.915012, 1.946875] | 0.017459 [0.017184, 0.018067] | 0.979987 [0.978931, 1.012434] |
| hard-core 0.50 | 0.337474 [0.334980, 0.339212] | 2.353703 [2.352438, 2.380588] | 0.022209 [0.021876, 0.025495] | 0.982546 [0.973153, 1.031176] |
| hard-core 0.70 | 0.204454 [0.199455, 0.205104] | 1.674964 [1.655360, 1.677358] | 0.018830 [0.017196, 0.020038] | 0.871445 [0.856928, 0.899748] |

### Large-size survivors

| Candidate | Area CV | p90/p10 | Cover radius | Boundary area |
| --- | --- | --- | --- | --- |
| jitter 0.50 | 0.127819 [0.127436, 0.129535] | 1.398596 [1.396834, 1.406641] | 0.011535 [0.011207, 0.011650] | 1.000897 [0.980919, 1.002749] |
| jitter 1.00 | 0.247573 [0.245590, 0.249682] | 1.933803 [1.907775, 1.945276] | 0.014311 [0.014253, 0.014676] | 0.994153 [0.978179, 1.016512] |
| hard-core 0.70 | 0.201906 [0.201788, 0.205953] | 1.674064 [1.666808, 1.695536] | 0.016376 [0.015419, 0.017156] | 0.855898 [0.848399, 0.897345] |

## Default-size timings

The five disjoint phases are reported independently in seconds as
`median [minimum, maximum]`. The complete ignored summary records every per-seed timing.

| Candidate | Generation | Site validation | Construction | Partition validation | Quality measurement |
| --- | --- | --- | --- | --- | --- |
| grid | 0.00205 [same] | 0.02136 [same] | 0.02672 [same] | 0.46445 [same] | 0.06608 [same] |
| uniform | 0.00320 [0.00317, 0.00922] | 0.02125 [0.02123, 0.02219] | 0.26039 [0.25954, 0.27171] | 0.51335 [0.50487, 0.51389] | 0.07491 [0.07140, 0.07940] |
| jitter 0.50 | 0.00353 [0.00350, 0.00366] | 0.02273 [0.02124, 0.02741] | 0.26621 [0.26367, 0.27007] | 0.50729 [0.50348, 0.51110] | 0.07240 [0.07136, 0.07828] |
| jitter 1.00 | 0.00349 [0.00345, 0.00354] | 0.02102 [0.02100, 0.02105] | 0.26487 [0.26222, 0.26952] | 0.50615 [0.50496, 0.51132] | 0.07184 [0.07120, 0.07253] |
| hard-core 0.50 | 0.01845 [0.01712, 0.02589] | 0.02254 [0.02163, 0.02268] | 0.26395 [0.26312, 0.28121] | 0.50757 [0.50686, 0.51712] | 0.07429 [0.07296, 0.07628] |
| hard-core 0.70 | 0.04263 [0.04117, 0.04490] | 0.02157 [0.02136, 0.02200] | 0.25982 [0.25646, 0.27119] | 0.52416 [0.52289, 0.52440] | 0.07535 [0.07387, 0.07540] |

No timing threshold was used for selection. The observed generator cost remains small compared with
construction and partition validation at the default size.

## Visual observations

Three self-contained boards use the same physical panel size, view box, line weight, and six-panel
order for grid, uniform, jitter `0.50`, jitter `1.00`, hard-core `0.50`, and hard-core `0.70`:

- seed `20260722`:
  `milestone2a_c43_r30_seed20260722_cfg-836b7d12d8a3246ff03fa44242c29011dbeb5ac020a45fe7dbb5853df0027178_comparison-board.svg`;
- seed `20260723`:
  `milestone2a_c43_r30_seed20260723_cfg-4596861ea83bb1c599e5a43e819a7fde9e67f411cad2fb3c4ef56a9f8d582c72_comparison-board.svg`;
- seed `20260724`:
  `milestone2a_c43_r30_seed20260724_cfg-b7466162a9c265a73d42330fbbbcbe487a944504b75879291f56843d8b740189_comparison-board.svg`.

All three rendered headlessly with `rsvg-convert` and were inspected as 2,400-pixel PNGs.

Stable observations across the fixed seeds:

- Uniform sites show dense close-pair clusters and large holes.
- Jitter `0.50` shows a strong row, column, and fourfold signature despite its good area and
  boundary measurements.
- Jitter `1.00` weakens but does not eliminate grid ancestry. Full rows and columns are less
  apparent than at `0.50`, while localized alignments and patchy cell sizes remain.
- Hard-core `0.50` looks organic and more disordered, but leaves more conspicuous large cells and
  holes than `0.70`.
- Hard-core `0.70` looks organic and more even. Some local regularity is visible, but no global rows
  or columns are apparent on any board.
- The hard-core boundary cells remain more variable than the stratified boundary band. At `0.70`,
  the boundary/interior area ratio stays below one across scales.

Seed-dependent differences and negative results:

- The locations and shapes of uniform clusters, jitter-`1.00` patches, and hard-core holes change
  with the seed. No particular spatial defect repeats at one fixed page location.
- Local regularity in hard-core `0.70` changes in location and strength, so the boards support a
  distribution-level tendency rather than identical visual texture.
- The two added seeds do not reverse the `0.50` versus `0.70` tradeoff or reveal a new raw winner.
  They also do not remove residual holes, boundary variation, or local order.

This is stable enough to retain `0.70` as the next experiment start and `0.50` as its disorder
anchor. The claim is limited to the raw `43x30` geometry screen; it does not establish label
clearance, printable quality, larger-scale visual stability, a Lloyd schedule, or production
selection.

## Interpretation

The raw `0.25` circle proposal prevents only the closest pairs and remains visually and
geometrically close to the uniform control. Raising hard-core separation fixes close pairs and
reduces area spread and covering holes, but it does not remove every hole or boundary effect.
Hard-core `0.50` preserves more visible disorder and nearly neutral default-size boundary area;
`0.70` provides the more even interior and smaller covering radius while keeping an organic board.
Both remain useful because the primary evidence exposes a real boundary-versus-equality tradeoff.

Stratified jitter deserves retention as a comparator, not as the assumed winner. Fraction `0.50`
has the strongest equality and boundary evidence, but the board makes its grid ancestry obvious.
Fraction `1.00` reduces that signature while giving up area equality.

## Next experiment

Start progressive partial bounded Lloyd movement from hard-core `d/s = 0.70`. Compare every step
with the unchanged hard-core `0.50` visual-disorder anchor and jitter `0.50` equality/grid-signature
anchor. Record the same primary evidence and equal-scale visuals after each movement step. Stop at
the first Pareto knee before visible hexagonal order grows faster than the reduction in holes and
area spread.

If hard-core boundary/interior area remains systematically low after bounded centroid movement,
isolate boundary handling in a later comparison rather than changing the interior generator first.
No Lloyd count, movement fraction, boundary correction, or production layout is selected by this
record.
