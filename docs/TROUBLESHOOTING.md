# Troubleshooting

This guide covers failures and print problems that follow from the converter's validated inputs,
shell bootstrap, and ReportLab page geometry.

## Command does not start

- Run commands from the repository root so `color_by_number.py` and the default palette resolve.
- Use `source source_me.sh && python3`; the bootstrap requires Bash and Python 3.12.
- If the shell prints `use bash for your shell`, start Bash before sourcing `source_me.sh`.
- Install the packages in [../pip_requirements.txt](../pip_requirements.txt) when an import fails.

## Input is rejected

- `Input image does not exist` means the `-i` path does not point to a readable file.
- `Palette file does not exist` means the `-p` path is wrong or the YAML file is missing.
- Palette colors require a nonempty `code`, `name`, and three integer RGB channels from 0 to 255.
- Marker codes must be unique within one palette.

See [FILE_FORMATS.md](FILE_FORMATS.md) for the complete input contract.

## Grid size is rejected

- Write the value as landscape `COLUMNSxROWS`, for example `86x60`.
- Use positive integers and place the longer dimension first.
- Portrait output swaps the dimensions automatically, so `86x60` becomes 60 columns by 86 rows.

## Codes print too small

- Reduce the resolution with `-g 43x30` to double each cell's width and height relative to `86x60`.
- Print at actual size; printer scaling can reduce already-small marker codes.
- Use the full-page numbered reference in `color_by_number_grid_only.pdf`; its grid is larger than
  the grid beside the marker key.

## Artwork pages do not align

- Print both pages from the same `color_by_number_grid_only.pdf` file.
- Apply the same printer orientation and scaling to both pages.
- Prefer actual size. If the printer requires fit-to-page, select it for both pages.
- Confirm the PDF page size remains Letter rather than converting one page to another paper size.

## Colors differ on paper

- The bundled RGB values come from a photographed product chart, not measured alcohol ink.
- Paper, lighting, ink coverage, and camera processing can change the physical result.
- Photograph uniformly filled marker swatches on the final paper for the closest palette calibration.
- Compare the source and marker preview PNGs before printing a large artwork grid.
