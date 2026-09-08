# Research architecture figure: build notes

## Files

| File | Role |
|---|---|
| `00_figure_contract.md` | What the figure says, the backbone, the panels, the colours, the exclusions |
| `panels.py` | Matplotlib source for the three panels, 3.3 x 1.55 in each, text kept as text |
| `panel_a_signals.svg` | A: one day of demand and price, illustrative |
| `panel_b_rollout.svg` | B: advection-diffusion field solved with an explicit upwind scheme on a 96 x 96 periodic grid, three times |
| `panel_c_gap.svg` | C: shift of the operating equilibrium of x' = r + x - x^3 under a fixed parameter error, against distance to the fold |
| `build.py` | Writes `_includes/research-overview.qmd`, the HTML figure with the panels inlined |

The figure itself is HTML and CSS. The stage cards, the connecting arrows, the return path, and all labels are page elements styled by the `.arch` rules in `assets/css/site.css`, so they use the page font (IBM Plex Sans) and the page colours. Matplotlib lays the panels out with Arial metrics; `panels.py` rewrites the font family in the SVG to IBM Plex Sans with Arial as the fallback.

## Colour

Purple #9467BD (A), teal #31859A (B), coral #EA7F6F (C), from the top-conference figure library (CLIP variant purple, ControlNet trainable edge, MAE decoder). The same three hues drive the direction list, the direction and system tags, and the links (teal) across the site.

## Rebuild

```bash
cd assets/figures/research-overview
python3 panels.py && python3 build.py
```

## QA record (8 September 2026)

- The include parses as HTML inside Quarto; the three inline SVGs carry unique id prefixes (`pa-`, `pb-`, `pc-`) so their clip paths do not collide.
- Rendered at 1180 px and at 375 px; no horizontal overflow, the stage cards stack their panel below the text under 760 px, and the return path stays attached to stages B and C.
