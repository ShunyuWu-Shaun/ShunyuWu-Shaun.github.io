#!/usr/bin/env python3
"""Build the research figure on the home page.

The figure has one panel per research direction:

  A  a solution of the Kuramoto-Sivashinsky (KS) equation, drawn as a
     waterfall of profiles u(x, t) that start smooth and become chaotic;
  B  space-time fields of the same equation for three initial conditions,
     standing for the solution map a -> u that a neural solver learns;
  C  the cost J(d) of a decision under the true dynamics (purple) and under
     the learned solution (teal); the learned minimizer d-hat misses d*, and
     the coral gap J(d-hat) - J(d*) is the regret.

Every panel holds a title, a visual in the same box and one formula. The
colours keep one meaning throughout: purple for the physical system, teal
for the learned solver, coral for the decision error.

The KS equation u_t + u u_x + u_xx + u_xxxx = 0 on a periodic domain of
length 32*pi is solved with the ETDRK4 scheme of Kassam and Trefethen
(SIAM J. Sci. Comput. 26, 2005). The cost curves in C are illustrative.

Each panel is drawn once inside a hidden SVG sprite. A wide layout (three
panels in a row) and a narrow layout for phones (panels stacked) place the
panels with <use>, so the artwork is not repeated in the page. Artwork
styles are presentation attributes, which <use> clones carry.

Run from the repository root:

    python3 scripts/build_research_figure.py

The script rewrites _includes/research-overview.qmd and the field images
in assets/images/research/. It needs numpy, matplotlib and Pillow.
"""

from __future__ import annotations

import cmath
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from matplotlib.path import Path as MplPath  # noqa: E402
from matplotlib.textpath import TextPath  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ROOT / "_includes" / "research-overview.qmd"
IMAGE_DIR = ROOT / "assets" / "images" / "research"
IMAGE_URL = "/assets/images/research"

# Direction colours, identical to --c-a, --c-b and --c-c in assets/css/site.css
PURPLE, TEAL, CORAL = "#9467BD", "#31859A", "#EA7F6F"
INK, MUTED, AXIS, FLOW = "#17202a", "#66717d", "#aab3bd", "#7d8894"
FONT = "IBM Plex Sans, Helvetica Neue, Arial, sans-serif"

matplotlib.rcParams["mathtext.fontset"] = "stix"
MATH_FONT = FontProperties(family="STIXGeneral")

# Panel geometry in the panel's own coordinates
PANEL_W = 224
TITLE_Y = 16
PLOT_Y, PLOT_H = 32, 132
MATH_Y = PLOT_Y + PLOT_H + 40
PANEL_H = MATH_Y + 8


# ---------------------------------------------------------------- physics


def etdrk4_coefficients(lin, h, m=16):
    """ETDRK4 coefficients by a contour mean over m points (Kassam and Trefethen).

    The sums use scalar Python complex arithmetic. numpy's vectorized complex
    multiplication can round differently from run to run on some processors,
    and the chaotic solution would carry that last-bit difference into the
    saved images. The time steps below multiply only by real or purely
    imaginary factors, which numpy computes exactly the same way every time.
    """
    roots = [cmath.exp(1j * math.pi * (j - 0.5) / m) for j in range(1, m + 1)]
    coeffs = np.zeros((4, len(lin)))
    for i, value in enumerate(lin):
        sums = [0j, 0j, 0j, 0j]
        for r in roots:
            z = h * value + r
            ez = cmath.exp(z)
            z3 = z * z * z
            sums[0] += (cmath.exp(z / 2) - 1) / z
            sums[1] += (-4 - z + ez * (4 - 3 * z + z * z)) / z3
            sums[2] += (2 + z + ez * (z - 2)) / z3
            sums[3] += (-4 - 3 * z - z * z + ez * (4 - z)) / z3
        coeffs[:, i] = [h * (total / m).real for total in sums]
    return coeffs


def solve_ks(u0, n=128, length=32 * np.pi, t_end=150.0, h=0.25, every=2):
    """ETDRK4 solution of the KS equation; returns x and U[t, x]."""
    x = length * np.arange(1, n + 1) / n
    v = np.fft.fft(u0(x))
    k = np.concatenate([np.arange(0, n // 2), [0], np.arange(-n // 2 + 1, 0)]) * (2 * np.pi / length)
    lin = k**2 - k**4
    e, e2 = np.exp(h * lin), np.exp(h * lin / 2)
    q, f1, f2, f3 = etdrk4_coefficients(lin, h)
    g = -0.5j * k

    def nonlinear(w):
        return g * np.fft.fft(np.real(np.fft.ifft(w)) ** 2)

    frames = [np.real(np.fft.ifft(v))]
    for step in range(1, int(round(t_end / h)) + 1):
        nv = nonlinear(v)
        a = e2 * v + q * nv
        na = nonlinear(a)
        b = e2 * v + q * na
        nb = nonlinear(b)
        c = e2 * a + q * (2 * nb - nv)
        nc = nonlinear(c)
        v = e * v + nv * f1 + 2 * (na + nb) * f2 + nc * f3
        if step % every == 0:
            frames.append(np.real(np.fft.ifft(v)))
    return x, np.array(frames)


INITIAL_CONDITIONS = [
    lambda x: np.cos(x / 16) * (1 + np.sin(x / 16)),
    lambda x: np.cos(x / 8) * (1 + 0.5 * np.sin(x / 16)),
    lambda x: np.sin(x / 16) + 0.6 * np.cos(3 * x / 16),
]


# ------------------------------------------------------------ svg helpers


def f(v):
    """Format a coordinate with at most one decimal."""
    s = f"{v:.1f}"
    if s == "-0.0":
        return "0"
    return s[:-2] if s.endswith(".0") else s


def rel_path(points):
    """Polyline as an absolute move followed by relative line segments."""
    q = [(round(x, 1), round(y, 1)) for x, y in points]
    out = [f"M{f(q[0][0])} {f(q[0][1])}l"]
    for (x0, y0), (x1, y1) in zip(q, q[1:]):
        dx, dy = f(x1 - x0), f(y1 - y0)
        out.append(dx + ("" if dy.startswith("-") else " ") + dy + " ")
    return "".join(out).rstrip()


def text(x, y, content, size=11.5, fill=MUTED, anchor="start", weight=None, extra=""):
    w = f' font-weight="{weight}"' if weight else ""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{f(x)}" y="{f(y)}" font-size="{size}" fill="{fill}"{a}{w}{extra}>{content}</text>'


def arrow_head(tip_x, tip_y, direction, color, size=7.0):
    """Filled triangle whose tip sits at (tip_x, tip_y)."""
    dx, dy = {"right": (1, 0), "left": (-1, 0), "up": (0, -1), "down": (0, 1)}[direction]
    bx, by = tip_x - dx * size, tip_y - dy * size
    px, py = -dy * size * 0.45, dx * size * 0.45
    return (f'<path d="M{f(tip_x)} {f(tip_y)}L{f(bx + px)} {f(by + py)}'
            f'L{f(bx - px)} {f(by - py)}Z" fill="{color}"/>')


def math_path(tex, size, x, y, anchor="middle", color=INK):
    """Typeset TeX with matplotlib mathtext and return it as one SVG path.

    (x, y) is the baseline position; anchor is start, middle or end.
    """
    tp = TextPath((0, 0), tex, size=size, prop=MATH_FONT)
    ext = tp.get_extents()
    shift = {"start": -ext.x0, "middle": -(ext.x0 + ext.x1) / 2, "end": -ext.x1}[anchor]
    parts = []
    for verts, code in tp.iter_segments():
        pts = [(x + shift + verts[i], y - verts[i + 1]) for i in range(0, len(verts), 2)]
        coords = " ".join(f"{f(a)} {f(b)}" for a, b in pts)
        if code == MplPath.MOVETO:
            parts.append("M" + coords)
        elif code == MplPath.LINETO:
            parts.append("L" + coords)
        elif code == MplPath.CURVE3:
            parts.append("Q" + coords)
        elif code == MplPath.CURVE4:
            parts.append("C" + coords)
        elif code == MplPath.CLOSEPOLY:
            parts.append("Z")
    return f'<path d="{"".join(parts)}" fill="{color}"/>'


def mix(c1, c2, t):
    a = np.array([int(c1[i:i + 2], 16) for i in (1, 3, 5)], float)
    b = np.array([int(c2[i:i + 2], 16) for i in (1, 3, 5)], float)
    r, g, bl = np.round(a + (b - a) * t).astype(int)
    return f"#{r:02x}{g:02x}{bl:02x}"


def title(letter, name, color):
    return (f'<circle cx="10" cy="{f(TITLE_Y - 5)}" r="10" fill="{color}"/>'
            + text(10, TITLE_Y - 0.9, letter, 11.5, "#ffffff", "middle", 700)
            + text(27, TITLE_Y, name, 14.5, INK, weight=600))


# ----------------------------------------------------------------- panels


def panel_a(x, frames):
    """Physical dynamics: KS profiles stacked in time; nearer profiles hide the ones behind."""
    bottom = PLOT_Y + PLOT_H
    picks = frames[:141:20]
    n = len(picks)
    step = (PLOT_H - 26) / (n - 1)
    amp = 0.32 * step
    # The solution is periodic and smooth, so zero-padding its spectrum gives
    # smooth curves between the grid points.
    fine = 176
    spectra = np.fft.rfft(picks, axis=1)
    smooth = np.fft.irfft(spectra, n=fine, axis=1) * fine / picks.shape[1]
    xs = np.linspace(2, PANEL_W - 2, fine)
    lines = []
    for i in range(n - 1, -1, -1):
        base = bottom - 8 - i * step
        ys = base - amp * smooth[i]
        color = mix("#c9b5e0", "#4a2d6b", i / (n - 1))
        tint = mix("#ffffff", "#f1ebf8", i / (n - 1))
        # One path per profile: the tinted fill hides the profiles behind it,
        # and the clip removes the stroke along the sides and the bottom.
        d = rel_path(list(zip(xs, ys))) + f"V{f(bottom + 4)}H{f(xs[0])}Z"
        lines.append(f'<path d="{d}" fill="{tint}" stroke="{color}" stroke-width="1.2" stroke-linejoin="round"/>')
    clip = (f'<clipPath id="rf-clip-a"><rect x="{f(xs[0] + 0.7)}" y="{f(PLOT_Y - 12)}" '
            f'width="{f(xs[-1] - xs[0] - 1.4)}" height="{f(bottom - PLOT_Y + 12)}"/></clipPath>')
    out = [title("A", "Physical dynamics", PURPLE),
           f'<g clip-path="url(#rf-clip-a)">{"".join(lines)}</g>',
           math_path(r"$\partial_t u=\mathcal{N}(u;\,a)$", 16, PANEL_W / 2, MATH_Y)]
    return clip, "".join(out)


def panel_b(field_names):
    """Neural solvers: space-time fields for three initial conditions, stacked like frames."""
    fw, fh = PANEL_W * 0.70, PLOT_H * 0.70
    dx, dy = (PANEL_W - fw) / 2, (PLOT_H - fh) / 2
    out = [title("B", "Neural solvers", TEAL)]
    for k, name in enumerate(field_names):  # back to front
        fx, fy = (2 - k) * dx, PLOT_Y + k * dy
        out.append(f'<rect x="{f(fx - 0.5)}" y="{f(fy - 0.5)}" width="{f(fw + 1)}" height="{f(fh + 1)}" '
                   f'rx="1.5" fill="#ffffff" stroke="#c8cfd6" filter="url(#rf-shadow)"/>')
        out.append(f'<image href="{IMAGE_URL}/{name}" x="{f(fx)}" y="{f(fy)}" width="{f(fw)}" '
                   f'height="{f(fh)}" preserveAspectRatio="none"/>')
    out.append(math_path(r"$\hat u=G_\theta(a)$", 16, PANEL_W / 2, MATH_Y))
    return "".join(out)


def panel_c():
    """Model2Action: the learned solution moves the minimizer, and the cost gap is the regret."""
    bottom = PLOT_Y + PLOT_H
    d = np.linspace(0, 1, 81)
    d_star, d_hat = 0.34, 0.68
    j_min, j_hat_min = 0.10, 0.07
    cost = j_min + 2.3 * (d - d_star) ** 2              # under the true dynamics
    cost_hat = j_hat_min + 2.1 * (d - d_hat) ** 2       # under the learned solution
    j_at_hat = j_min + 2.3 * (d_hat - d_star) ** 2
    top = max(cost.max(), cost_hat.max())

    def px(v):
        return 6 + v * (PANEL_W - 12)

    def py(v):
        return bottom - 4 - v / top * (PLOT_H - 8)

    xs, xh = px(d_star), px(d_hat)
    out = [title("C", "Model2Action", CORAL)]
    out.append(f'<path d="M0 {f(bottom)}H{PANEL_W}" fill="none" stroke="{AXIS}" stroke-width="1.1"/>')
    for xv, yv in ((xs, py(j_min)), (xh, py(j_hat_min))):  # drop lines to the decision axis
        out.append(f'<path d="M{f(xv)} {f(yv)}V{f(bottom)}" fill="none" stroke="{AXIS}" stroke-dasharray="2 3"/>')
    out.append(f'<path d="{rel_path([(px(a), py(b)) for a, b in zip(d, cost_hat)])}" fill="none" '
               f'stroke="{TEAL}" stroke-width="1.8" stroke-dasharray="5 3.5"/>')
    out.append(f'<path d="{rel_path([(px(a), py(b)) for a, b in zip(d, cost)])}" fill="none" '
               f'stroke="{PURPLE}" stroke-width="2"/>')
    # the regret: the true cost at d-hat stands above the true cost at d*
    out.append(f'<path d="M{f(xs)} {f(py(j_min))}H{f(xh)}" fill="none" stroke="{CORAL}" '
               'stroke-width="1.2" stroke-dasharray="2 2.5"/>')
    out.append(f'<path d="M{f(xh)} {f(py(j_min))}V{f(py(j_at_hat))}" fill="none" stroke="{CORAL}" '
               'stroke-width="3.2" stroke-linecap="round"/>')
    out.append(f'<circle cx="{f(xs)}" cy="{f(py(j_min))}" r="3.6" fill="{PURPLE}"/>')
    out.append(f'<circle cx="{f(xh)}" cy="{f(py(j_hat_min))}" r="3.6" fill="{TEAL}"/>')
    out.append(f'<circle cx="{f(xh)}" cy="{f(py(j_at_hat))}" r="3.6" fill="{CORAL}"/>')
    out.append(math_path(r"$d^{*}$", 13, xs, bottom + 15, "middle", PURPLE))
    out.append(math_path(r"$\hat d$", 13, xh, bottom + 15, "middle", TEAL))
    out.append(math_path(r"$J(\hat d)-J(d^{*})$", 16, PANEL_W / 2, MATH_Y))
    return "".join(out)


# ---------------------------------------------------------------- layouts


def use(panel, x, y):
    return f'<use href="#rf-panel-{panel}" x="{f(x)}" y="{f(y)}"/>'


def flow_arrow(x0, y0, x1, y1, direction):
    return (f'<path d="M{f(x0)} {f(y0)}L{f(x1)} {f(y1)}" fill="none" stroke="{FLOW}" stroke-width="1.6"/>'
            + arrow_head(x1 + {"right": 8, "down": 0}[direction], y1 + {"right": 0, "down": 8}[direction],
                         direction, FLOW, 8))


def wide_layout():
    """Three panels in a row; the loop runs from the regret under C to the solver under B."""
    gap = 44
    xs = [0, PANEL_W + gap, 2 * (PANEL_W + gap)]
    width = xs[2] + PANEL_W
    out = [use(p, x, 0) for p, x in zip("abc", xs)]
    mid = PLOT_Y + PLOT_H / 2
    for x in xs[:2]:
        out.append(flow_arrow(x + PANEL_W + 8, mid, x + PANEL_W + gap - 16, mid, "right"))
    y0, y1 = MATH_Y + 10, MATH_Y + 30
    bx, cx = xs[1] + PANEL_W / 2, xs[2] + PANEL_W / 2
    out.append(f'<path d="M{f(cx)} {f(y0)}V{f(y1)}H{f(bx)}V{f(y0 + 8)}" fill="none" stroke="{CORAL}" '
               'stroke-width="1.8" stroke-linejoin="round"/>')
    out.append(arrow_head(bx, y0 + 1, "up", CORAL, 8))
    return width, int(y1 + 6), "".join(out)


def narrow_layout():
    """Panels stacked for phones; the loop runs up the right side from C to B."""
    x0, y, out, tops = 4, 0, [], {}
    for p in "abc":
        tops[p] = y
        out.append(use(p, x0, y))
        y += PANEL_H
        if p != "c":
            ax = x0 + PANEL_W / 2
            out.append(flow_arrow(ax, y + 4, ax, y + 20, "down"))
            y += 40
    yb = tops["b"] + PLOT_Y + PLOT_H / 2
    yc = tops["c"] + PLOT_Y + PLOT_H / 2
    right, lx = x0 + PANEL_W + 8, x0 + PANEL_W + 26
    out.append(f'<path d="M{f(right)} {f(yc)}H{f(lx)}V{f(yb)}H{f(right + 8)}" fill="none" stroke="{CORAL}" '
               'stroke-width="1.8" stroke-linejoin="round"/>')
    out.append(arrow_head(right, yb, "left", CORAL, 8))
    return int(lx + 8), int(y + 4), "".join(out)


# ------------------------------------------------------------------ output

DESCRIPTION = (
    "Research overview in three panels. Panel A, physical dynamics, shows profiles of a "
    "Kuramoto-Sivashinsky solution that start smooth and become chaotic. Panel B, neural solvers, "
    "shows the solution fields for three initial conditions, each returned by a neural operator in "
    "one forward pass. Panel C, Model2Action, shows the cost of a decision under the true dynamics "
    "and under the learned solution. The learned solution moves the minimizer from d* to d-hat, and "
    "the cost gap J(d-hat) minus J(d*) is the regret. An arrow from C back to B shows that the "
    "regret trains the solver. The cost curves are illustrative."
)


def write_fields(frames_by_ic):
    """Save each space-time field as a WebP image, time running upward."""
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    cmap = LinearSegmentedColormap.from_list("teal", ["#f4fafb", "#a9d3dc", TEAL, "#123c45"])
    names = []
    for k, frames in enumerate(frames_by_ic, start=1):
        lo, hi = np.percentile(frames, [1, 99])
        rgb = cmap(np.clip((frames[::-1] - lo) / (hi - lo), 0, 1))[..., :3]
        img = Image.fromarray((rgb * 255).round().astype(np.uint8))
        # twice the display size keeps the field sharp on high-density screens
        img = img.resize((300, 196), Image.BICUBIC)
        name = f"ks-field-{k}.webp"
        img.save(IMAGE_DIR / name, quality=82, method=6)
        names.append(name)
    for old in IMAGE_DIR.glob("ks-field-*.png"):
        old.unlink()
    return names


def main():
    solutions = [solve_ks(ic) for ic in INITIAL_CONDITIONS]
    x, frames = solutions[0]
    names = write_fields([s[1] for s in solutions])
    clip, art_a = panel_a(x, frames)
    # back to front: the first initial condition, also drawn in A, is the front frame
    art_b = panel_b(names[::-1])
    art_c = panel_c()
    sprite = (
        '<svg class="rf__defs" width="0" height="0" aria-hidden="true" focusable="false">'
        f'<defs font-family="{FONT}">'
        '<filter id="rf-shadow" x="-10%" y="-10%" width="130%" height="140%">'
        '<feDropShadow dx="0" dy="1.2" stdDeviation="1.4" flood-color="#17202a" flood-opacity="0.18"/></filter>'
        f'{clip}'
        f'<g id="rf-panel-a" font-family="{FONT}">{art_a}</g>'
        f'<g id="rf-panel-b" font-family="{FONT}">{art_b}</g>'
        f'<g id="rf-panel-c" font-family="{FONT}">{art_c}</g>'
        '</defs></svg>'
    )
    ww, wh, wide = wide_layout()
    nw, nh, narrow = narrow_layout()
    html = f"""```{{=html}}
<!-- Generated by scripts/build_research_figure.py. Edit the script, not this file. -->
<figure class="rf">
  {sprite}
  <p class="visually-hidden" id="rf-desc">{DESCRIPTION}</p>
  <svg class="rf__wide" viewBox="0 0 {ww} {wh}" role="img" aria-labelledby="rf-desc">{wide}</svg>
  <svg class="rf__narrow" viewBox="0 0 {nw} {nh}" role="img" aria-labelledby="rf-desc">{narrow}</svg>
</figure>
```
"""
    INCLUDE.write_text(html, encoding="utf-8")
    sizes = ", ".join(f"{(IMAGE_DIR / n).stat().st_size / 1024:.1f}" for n in names)
    print(f"wrote {INCLUDE.relative_to(ROOT)} ({len(html.encode()) / 1024:.1f} KiB); images {sizes} KiB")


if __name__ == "__main__":
    main()
