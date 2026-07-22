# Roadmap

This roadmap turns the converter's documented limitations into small, measurable experiments. It
records priorities rather than release dates or promises.

## Palette calibration

- Photograph uniform swatches from the physical marker set on the final artwork paper.
- Use controlled lighting, fixed exposure, and a neutral reference when sampling RGB values.
- Compare chart-derived and paper-derived palettes on the same fixed image set.
- Accept a replacement palette when physical swatch matching improves without hidden per-image
  exceptions.

## Generalization tests

- Build a small evaluation set covering portraits, dark fabric, wood, flat graphics, and landscapes.
- Compare `none`, `balanced`, and `strong` with fixed grids, crops, palettes, and metrics.
- Record global Delta E alongside region counts for dark, warm, and flat areas.
- Change the default enhancement only when evidence holds across the varied set.

## Print usability

- Print 43 by 30 and 86 by 60 artwork pages on the intended printer and paper.
- Compare code legibility, marker-tip control, line visibility, bleed, and page alignment.
- Test whether another light-gray value improves the finished blank page under alcohol marker ink.
- Preserve ReportLab point geometry and equal print scaling as alignment invariants.

## Deliberate exclusions

- Keep global dithering out unless a controlled experiment removes flat-region speckling.
- Keep object detection out of the deterministic quantization path unless a new workflow requires
  semantic masks and supplies evaluation data.
- Keep palette-specific calibration in YAML so alternative marker sets do not require code changes.
