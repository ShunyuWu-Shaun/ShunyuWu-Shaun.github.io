# Research overview figure: build notes and QA

## Files

| File | Role |
|---|---|
| `00_figure_contract.md` | Reader takeaway, research object, obstacle, abstraction, colour semantics, exclusions |
| `panels.py` | Matplotlib source for the two computed panels (Arial, palette hues, 4.1 x 1.42 in) |
| `panel_a_solve.svg` / `.png` | Panel A: 2D advection-diffusion field solved with an explicit upwind scheme on a 96 x 96 periodic grid, three times |
| `panel_b_gap.svg` / `.png` | Panel B: shift of the operating equilibrium of x' = r + x - x^3 under a fixed parameter error, against distance to the fold |
| `figure.py` | One layout in inches, written twice: python-pptx shapes for the PPTX, hand-written SVG for the web |
| `research-overview.pptx` | Editable PowerPoint source (10 x 9.25 in canvas, native shapes, panels as 600 dpi PNG) |
| `research-overview.svg` | Web version, fully vector, panels embedded inline; used on the homepage at about 780 px wide |
| `research-overview.pdf` / `research-overview-pptx-render.png` | Check render exported by PowerPoint for Mac 16.112 through AppleScript |

## Figure sources (figure-assets ledger)

- Panel A: own computation, `panels.py::panel_a`. Illustrative of a solved field trajectory; no data claim.
- Panel B: own computation, `panels.py::panel_b`. Illustrative of the model-to-decision gap near a fold; no data claim.
- Layout: after the observation-to-inference overview archetype (one substrate, two questions, one evidence band), drawn as native shapes. No literature panel is reproduced.

## Type and geometry

- Arial throughout; PowerPoint text boxes have zero margins and single line spacing, and the SVG uses 1.15 em, so both wrap on the same greedy lines computed from the Arial metrics with a 0.94 width factor.
- Type on the canvas: 22 pt Physical AI, 18 pt box titles, 14 pt body and band titles, 12 pt branch bodies, 11 pt captions and axis text. At 780 px insertion width (1 in = 78 px) the smallest text is about 12 px.
- Connectors: six straight 2.5 pt arrows with triangle heads. No connector changes direction, so no bent connector is used.
- Colour: blue_main #0F4D92 for Question A, red_strong #B64342 for Question B and the return path, teal #42949E / #317078 for the substrate and the test-bed band, neutrals for the Physical AI band and captions. Pale fills #DDE6F0, #F5E5E5, #E5F0F1, #F2F2F2.

## QA record (8 September 2026)

- `overlap_check.py`: zero text-text intersections. Its out-of-canvas rows come from the script's fixed 13.33 x 7.5 in canvas; a bounds check against the true 10 x 9.25 in canvas reports zero.
- Repair-prompt scan on the packed XML: no negative extents, no `mc:AlternateContent`, all `srgbClr` values six hex digits, no `bentConnector2`. Media entries are the two intended PNG panels.
- PowerPoint for Mac opened the file without a repair prompt and exported the PDF used for the check render.
- SVG parses as XML (root declares the xlink namespace the embedded Matplotlib panels use) and renders in Chrome with no broken glyphs.
- Equations: none. Greek letters: none; the operator label is the plain text G with a subscript run.

## Rebuild

```bash
cd assets/figures/research-overview
python3 panels.py && python3 figure.py
```
