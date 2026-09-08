"""Assemble the research architecture figure as an HTML include for the home page.

The figure is HTML and CSS (see the `.arch` rules in assets/css/site.css) with the
three Matplotlib panels embedded as inline SVG, so the page font and the page
colours apply to everything in it.

Run:  python3 panels.py && python3 build.py
Writes: _includes/research-overview.qmd
"""
from __future__ import annotations

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parents[2] / "_includes" / "research-overview.qmd"


def inline_svg(name: str, prefix: str, label: str) -> str:
    src = (HERE / name).read_text(encoding="utf-8")
    src = re.sub(r"<\?xml[^>]*\?>", "", src)
    src = re.sub(r"<!DOCTYPE[^>]*>", "", src, flags=re.S)
    m = re.search(r"<svg\b([^>]*)>(.*)</svg>\s*$", src, flags=re.S)
    attrs, inner = m.group(1), m.group(2)
    vb = re.search(r'viewBox="([^"]+)"', attrs).group(1)
    inner = re.sub(r'id="([^"]+)"', lambda mm: f'id="{prefix}-{mm.group(1)}"', inner)
    inner = re.sub(r'url\(#([^)]+)\)', lambda mm: f'url(#{prefix}-{mm.group(1)})', inner)
    inner = re.sub(r'href="#([^"]+)"', lambda mm: f'href="#{prefix}-{mm.group(1)}"', inner)
    return (f'<svg class="arch__svg" viewBox="{vb}" role="img" aria-label="{label}" '
            f'xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">{inner}</svg>')


ARROW = ('<svg class="arch__arrow" viewBox="0 0 16 30" aria-hidden="true">'
         '<path d="M8 0v22" stroke="currentColor" stroke-width="2"/>'
         '<path d="M2 21l6 8 6-8z" fill="currentColor"/></svg>')

HTML = f"""```{{=html}}
<figure class="arch" aria-labelledby="arch-caption">
  <div class="arch__stage arch__stage--a">
    <div class="arch__text">
      <p class="arch__kicker"><span class="arch__letter">A</span>Physical systems in science and engineering</p>
      <p class="arch__body"><strong>Science.</strong> Temperature and composition fields of a materials processing step.</p>
      <p class="arch__body"><strong>Engineering.</strong> Urban water demand and network pressure, day-ahead electricity price, and hot-strip rolling energy.</p>
    </div>
    <div class="arch__panel">
      {inline_svg("panel_a_signals.svg", "pa", "One day of urban water demand and electricity price, illustrative")}
      <p class="arch__note">Illustrative. One day of demand and price in a water system.</p>
    </div>
  </div>

  <div class="arch__link">{ARROW}<span>the governing dynamics, with their initial conditions, boundary conditions, and forcing</span></div>

  <div class="arch__loop">
    <div class="arch__return" aria-hidden="true"><span>decision error trains the solver</span></div>

    <div class="arch__stage arch__stage--b">
      <div class="arch__text">
        <p class="arch__kicker"><span class="arch__letter">B</span>Solving the dynamics with neural networks</p>
        <p class="arch__body">A neural operator maps initial conditions, boundary conditions, and forcing to the solution field in one forward pass. Its rollouts and sensitivities are what the next stage uses.</p>
      </div>
      <div class="arch__panel">
        {inline_svg("panel_b_rollout.svg", "pb", "A two-dimensional advection-diffusion field solved and shown at three times")}
        <p class="arch__note">Computed. An advection-diffusion field solved at three times.</p>
      </div>
    </div>

    <div class="arch__link">{ARROW}<span>the solution field and its sensitivities</span></div>

    <div class="arch__stage arch__stage--c">
      <div class="arch__text">
        <p class="arch__kicker"><span class="arch__letter">C</span>The model-to-decision gap</p>
        <p class="arch__body">A controller or an optimizer decides with the solution. The decision error is small over most of the state space and large near a critical point, and it is measured as regret, closed-loop cost, and constraint violation.</p>
      </div>
      <div class="arch__panel">
        {inline_svg("panel_c_gap.svg", "pc", "Decision error per unit model error against distance to a critical point, computed on a bistable system")}
        <p class="arch__note">Computed. Equilibrium shift of a bistable system under a fixed model error.</p>
      </div>
    </div>
  </div>

  <figcaption id="arch-caption">A physical system supplies the governing dynamics (A). A neural operator learns to solve them (B). A controller or an optimizer decides with the solution, and the decision error returns to train the solver (C). The panels are computed on toy problems and illustrate a relation; they are not results.</figcaption>
</figure>
```
"""

if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(HTML, encoding="utf-8")
    print("wrote", OUT.relative_to(HERE.parents[2]))
