#!/usr/bin/env python3
"""Build the research illustration on the home page.

One isometric scene with a platform per research direction:

  A  Physical dynamics: an iCVD chamber with a liquid-crystal film, and an
     integrated energy and water network (wind, solar, a plant, a water
     tower, pipes, buildings);
  B  Neural solvers: an input field passes up through glass operator
     layers and leaves as the predicted solution;
  C  Model2Action: prediction tokens and action tokens drive a robot arm,
     in the style of a vision-language-action model.

Plain words label the flows: model (A to B), decide (B to C), act (C back
to A), and a dashed loop from C to B, "decision error trains the solver".

Each platform is drawn once inside a zero-size SVG sprite. Three layouts
place the platforms with <use> and add their own flows and labels:

  wide    three platforms in a row            (figure at least 600 px wide)
  mid     A on top, B and C below             (440 to 599 px)
  narrow  platforms stacked                   (under 440 px)

assets/css/site.css (section 7) switches between them with container
queries, so the choice follows the width of the figure, not of the window.

Run from the repository root; the script needs only the standard library:

    python3 scripts/build_research_figure.py
"""

from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ROOT / "_includes" / "research-overview.qmd"

# Direction colours, identical to --c-a, --c-b and --c-c in assets/css/site.css
PURPLE, TEAL, CORAL = "#9467BD", "#31859A", "#EA7F6F"
INK, MUTED = "#17202a", "#66717d"
FONT = "IBM Plex Sans, Helvetica Neue, Arial, sans-serif"
SERIF = "IBM Plex Serif, Georgia, serif"
C, H = 2 / 5 ** 0.5, 1 / 5 ** 0.5            # 2:1 isometric projection
SA, SB = 150, 118                            # side of platform A, and of B and C

# Object colours
TOP, LEFT, RIGHT, EDGE = "#ffffff", "#e6eaef", "#d3dae2", "#c3ccd6"
LEG, PIPE, PIPE_HI = "#9aa6b2", "#6f93b0", "#b9d0e2"


# ------------------------------------------------------------------ helpers


def f(v):
    """Format a coordinate with at most one decimal."""
    s = f"{v:.1f}"
    return "0" if s == "-0.0" else (s[:-2] if s.endswith(".0") else s)


def mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(a, b))


class Iso:
    """Isometric drawing with the platform's top corner at the origin.

    World axes: x to the lower right, y to the lower left, z up.
    """

    def p(self, x, y, z=0):
        return ((x - y) * C, (x + y) * H - z)

    def poly(self, pts, fill, stroke="none", sw=0, extra=""):
        d = "M" + "L".join(f"{f(a)} {f(b)}" for a, b in (self.p(*q) for q in pts)) + "Z"
        s = f' stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"' if stroke != "none" else ""
        return f'<path d="{d}" fill="{fill}"{s}{extra}/>'

    def line(self, pts, stroke, sw=1.2, extra=""):
        d = "M" + "L".join(f"{f(a)} {f(b)}" for a, b in (self.p(*q) for q in pts))
        return (f'<path d="{d}" fill="none" stroke="{stroke}" stroke-width="{sw}" '
                f'stroke-linecap="round" stroke-linejoin="round"{extra}/>')

    def box(self, x, y, z, w, d, h, top=TOP, left=LEFT, right=RIGHT):
        return (self.poly([(x, y + d, z), (x + w, y + d, z), (x + w, y + d, z + h), (x, y + d, z + h)], left)
                + self.poly([(x + w, y, z), (x + w, y + d, z), (x + w, y + d, z + h), (x + w, y, z + h)], right)
                + self.poly([(x, y, z + h), (x + w, y, z + h), (x + w, y + d, z + h), (x, y + d, z + h)], top))

    def radii(self, r):
        return r * 2 ** 0.5 * C, r * 2 ** 0.5 * H

    def cylinder(self, cx, cy, z, r, h, grad, top=TOP):
        bx, by = self.p(cx, cy, z)
        a, b = self.radii(r)
        side = (f'<path d="M{f(bx - a)} {f(by - h)}L{f(bx - a)} {f(by)}A{f(a)} {f(b)} 0 0 0 {f(bx + a)} {f(by)}'
                f'L{f(bx + a)} {f(by - h)}Z" fill="url(#rf-{grad})" stroke="{EDGE}" stroke-width="0.6"/>')
        cap = (f'<ellipse cx="{f(bx)}" cy="{f(by - h)}" rx="{f(a)}" ry="{f(b)}" fill="{top}" '
               f'stroke="{EDGE}" stroke-width="0.6"/>')
        return side + cap

    def ellipse(self, cx, cy, z, r, fill, stroke="none", sw=0):
        bx, by = self.p(cx, cy, z)
        a, b = self.radii(r)
        s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke != "none" else ""
        return f'<ellipse cx="{f(bx)}" cy="{f(by)}" rx="{f(a)}" ry="{f(b)}" fill="{fill}"{s}/>'


ISO = Iso()


def text(x, y, s, size=13, fill=MUTED, anchor="middle", weight=None, family=None, extra=""):
    w = f' font-weight="{weight}"' if weight else ""
    fam = f' font-family="{family}"' if family else ""
    a = f' text-anchor="{anchor}"' if anchor != "start" else ""
    return f'<text x="{f(x)}" y="{f(y)}" font-size="{size}" fill="{fill}"{a}{w}{fam}{extra}>{s}</text>'


# ------------------------------------------------------------------ objects on platform A


def turbine(x, y, height, angle):
    bx, by = ISO.p(x, y, 0)
    tx, ty = bx, by - height
    out = [f'<path d="M{f(bx - 2.6)} {f(by)}L{f(tx - 1.1)} {f(ty)}L{f(tx + 1.1)} {f(ty)}L{f(bx + 2.6)} {f(by)}Z" '
           f'fill="#ffffff" stroke="#b9c3cd" stroke-width="0.7"/>',
           f'<rect x="{f(tx - 4)}" y="{f(ty - 3)}" width="9" height="5" rx="2" fill="#ffffff" stroke="#b9c3cd" stroke-width="0.7"/>']
    for j in range(3):
        a = math.radians(angle + 120 * j)
        ex, ey = tx + 26 * math.cos(a), ty - 26 * math.sin(a)
        nx, ny = -math.sin(a) * 2.6, -math.cos(a) * 2.6
        out.append(f'<path d="M{f(tx)} {f(ty)}Q{f((tx + ex) / 2 + nx)} {f((ty + ey) / 2 + ny)} {f(ex)} {f(ey)}'
                   f'Q{f((tx + ex) / 2 - nx * 0.3)} {f((ty + ey) / 2 - ny * 0.3)} {f(tx)} {f(ty)}Z" '
                   f'fill="#ffffff" stroke="#b9c3cd" stroke-width="0.7"/>')
    out.append(f'<circle cx="{f(tx)}" cy="{f(ty)}" r="2.2" fill="#8d99a6"/>')
    return "".join(out)


def solar(x, y, w, d):
    out = [ISO.poly([(x, y, 7), (x + w, y, 7), (x + w, y + d, 2), (x, y + d, 2)], "#51667d", "#3e5165", 0.6)]
    for j in range(1, 3):
        out.append(ISO.line([(x + w * j / 3, y, 7), (x + w * j / 3, y + d, 2)], "#8ea3b8", 0.5))
    out.append(ISO.line([(x, y + d / 2, 4.5), (x + w, y + d / 2, 4.5)], "#8ea3b8", 0.5))
    return "".join(out)


def water_tower(x, y):
    out = [ISO.line([(x + dx, y + dy, 0), (x + dx * 0.6, y + dy * 0.6, 26)], LEG, 1.1)
           for dx, dy in ((-5, -5), (5, -5), (-5, 5), (5, 5))]
    out.append(ISO.cylinder(x, y, 26, 9, 14, "gw", top="#eef4f8"))
    bx, by = ISO.p(x, y, 40)
    a, _ = ISO.radii(9)
    out.append(f'<path d="M{f(bx - a)} {f(by)}Q{f(bx)} {f(by - 12)} {f(bx + a)} {f(by)}" fill="#dfe8ef" '
               f'stroke="{EDGE}" stroke-width="0.6"/>')
    return "".join(out)


def building(x, y, w, d, h):
    out = [ISO.box(x, y, 0, w, d, h)]
    for r in range(int((h - 6) // 7)):
        z0 = 5 + r * 7
        for j in range(int((w - 3) // 6)):
            x0 = x + 3 + j * 6
            out.append(ISO.poly([(x0, y + d, z0), (x0 + 3, y + d, z0), (x0 + 3, y + d, z0 + 3.5), (x0, y + d, z0 + 3.5)], "#b8c6d4"))
        for j in range(int((d - 3) // 6)):
            y0 = y + 3 + j * 6
            out.append(ISO.poly([(x + w, y0, z0), (x + w, y0 + 3, z0), (x + w, y0 + 3, z0 + 3.5), (x + w, y0, z0 + 3.5)], "#a9b8c7"))
    return "".join(out)


def reactor(x, y):
    """iCVD chamber: steel base, glass bell jar, liquid-crystal film inside, monomer vapor."""
    out = [ISO.cylinder(x, y, 0, 15, 7, "gs")]
    bx, by = ISO.p(x, y, 7)
    a, b = ISO.radii(13)
    out.append(ISO.ellipse(x, y, 9, 9.5, "url(#rf-lc)", "#ffffff", 0.8))
    fx, fy = ISO.p(x, y, 9)
    for dx, dy, rot in [(-6, -1, 20), (-1, 2, -30), (5, -1, 60), (7, 2, 10), (0, -3, 90), (-4, 3, 45)]:
        out.append(f'<ellipse cx="{f(fx + dx)}" cy="{f(fy + dy)}" rx="2.6" ry="0.8" fill="#ffffff" opacity="0.9" '
                   f'transform="rotate({rot} {f(fx + dx)} {f(fy + dy)})"/>')
    for j, (dx, dy) in enumerate([(-5, -9), (2, -14), (7, -8), (-1, -20), (-8, -16), (5, -22)]):
        out.append(f'<circle cx="{f(fx + dx)}" cy="{f(fy + dy)}" r="1.4" fill="{PURPLE}" opacity="{0.45 + 0.08 * j:.2f}"/>')
    top = by - 26
    out.append(f'<path d="M{f(bx - a)} {f(by)}L{f(bx - a)} {f(top)}A{f(a)} {f(a * 0.9)} 0 0 1 {f(bx + a)} {f(top)}'
               f'L{f(bx + a)} {f(by)}A{f(a)} {f(b)} 0 0 1 {f(bx - a)} {f(by)}Z" fill="#ffffff" fill-opacity="0.28" '
               f'stroke="#aeb9c4" stroke-width="0.9"/>')
    out.append(f'<path d="M{f(bx - a * 0.62)} {f(top - 4)}A{f(a * 0.7)} {f(a * 0.6)} 0 0 1 {f(bx + a * 0.1)} {f(top - a * 0.62)}" '
               f'fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" opacity="0.85"/>')
    return "".join(out)


# ------------------------------------------------------------------ platforms


def tile(s, tint, thick=10):
    """Glass platform: gradient top, tinted sides, soft shadow."""
    top_pts = [(0, 0, 0), (s, 0, 0), (s, s, 0), (0, s, 0)]
    left_pts = [(0, s, -thick), (s, s, -thick), (s, s, 0), (0, s, 0)]
    right_pts = [(s, 0, -thick), (s, s, -thick), (s, s, 0), (s, 0, 0)]
    cx, cy = ISO.p(s / 2, s / 2, -thick)
    return (f'<ellipse cx="{f(cx)}" cy="{f(cy + 14)}" rx="{f(s * C * 1.05)}" ry="{f(s * H * 0.55)}" '
            f'fill="#17202a" opacity="0.07" filter="url(#rf-soft)"/>'
            + ISO.poly(left_pts, mix(tint, "#ffffff", 0.45)) + ISO.poly(right_pts, mix(tint, "#ffffff", 0.2))
            + ISO.poly(top_pts, f"url(#rf-top-{tint[1:]})", "#ffffff", 1.6)
            + ISO.line([(0, s, 0), (s, s, 0), (s, 0, 0)], mix(tint, "#ffffff", 0.3), 1.2, ' opacity="0.7"'))


def platform_a():
    """Physical dynamics: materials processing, integrated energy, urban water."""
    out = [tile(SA, PURPLE)]
    for pts in ([(28, 28), (60, 60), (100, 64)], [(95, 24), (100, 64)], [(100, 64), (120, 106)], [(60, 60), (84, 118)]):
        out.append(ISO.line([(a, b, 0.6) for a, b in pts], PURPLE, 1.6, ' opacity="0.8"'))
    for pts in ([(74, 88), (74, 128), (130, 128)], [(74, 88), (130, 88), (130, 128)]):
        out.append(ISO.line([(a, b, 0.8) for a, b in pts], PIPE, 3.2))
        out.append(ISO.line([(a, b, 0.8) for a, b in pts], PIPE_HI, 1.1))
    for a, b in [(60, 60), (100, 64), (120, 106), (84, 118)]:
        out.append(ISO.ellipse(a, b, 0.6, 3, PURPLE))
    out.append(solar(80, 8, 26, 18))
    out.append(solar(108, 8, 26, 18))
    out.append(turbine(22, 22, 80, 78))
    out.append(turbine(44, 10, 64, 20))
    out.append(ISO.box(88, 48, 0, 26, 20, 20))
    out.append(ISO.cylinder(108, 52, 20, 4, 18, "gs"))
    out.append(water_tower(74, 88))
    out.append(ISO.cylinder(130, 88, 0, 8, 9, "gw", top="#dcebf5"))
    out.append(building(112, 100, 16, 12, 24))
    out.append(building(130, 114, 12, 14, 17))
    out.append(ISO.line([(48, 112, 5), (58, 112, 5), (58, 134, 5)], LEG, 2.2))
    out.append(ISO.cylinder(58, 138, 0, 5, 12, "gs"))
    out.append(reactor(30, 110))
    return "".join(out)


def grid_plate(x0, y0, z, size, n, colors, gap=1.4):
    """An n-by-n grid of coloured cells lying flat at height z."""
    cell = size / n
    out = [ISO.poly([(x0 - 1.5, y0 - 1.5, z), (x0 + size + 1.5, y0 - 1.5, z), (x0 + size + 1.5, y0 + size + 1.5, z),
                     (x0 - 1.5, y0 + size + 1.5, z)], "#ffffff", "#ffffff", 0.8, ' fill-opacity="0.85"')]
    for i in range(n):
        for j in range(n):
            a, b = x0 + i * cell + gap / 2, y0 + j * cell + gap / 2
            out.append(ISO.poly([(a, b, z), (a + cell - gap, b, z), (a + cell - gap, b + cell - gap, z), (a, b + cell - gap, z)],
                                colors[i][j]))
    return "".join(out)


def glass_layer(x0, y0, z, size):
    out = [ISO.poly([(x0, y0, z), (x0 + size, y0, z), (x0 + size, y0 + size, z), (x0, y0 + size, z)],
                    TEAL, "#ffffff", 1.1, ' fill-opacity="0.16"')]
    for w in range(3):
        yy = y0 + size * (w + 1) / 4
        pts = [(x0 + 3 + (size - 6) * s / 24, yy + 3.2 * math.sin(2 * math.pi * (w + 1) * s / 24), z) for s in range(25)]
        out.append(ISO.line(pts, TEAL, 0.9, ' opacity="0.75"'))
    out.append('<g filter="url(#rf-glow)">'
               + ISO.line([(x0, y0, z), (x0 + size, y0, z), (x0 + size, y0 + size, z), (x0, y0 + size, z), (x0, y0, z)],
                          TEAL, 0.9, ' opacity="0.8"') + "</g>")
    return "".join(out)


OP_X = OP_Y = 35                              # corner of the operator stack on platform B
OP_SIZE, OP_TOP = 48, 78


def platform_b():
    """Neural solvers: an input field passes up through operator layers and leaves as the solution."""
    n = 5
    fin = [[mix("#f1e9fa", PURPLE, 0.5 + 0.45 * math.sin(1.3 * i + 0.8 * j) * math.cos(0.7 * j - 0.4 * i)) for j in range(n)]
           for i in range(n)]
    fout = [[mix("#e2f3f6", TEAL, 0.5 + 0.42 * math.sin(0.9 * i + 0.6 * j + 0.8)) for j in range(n)] for i in range(n)]
    out = [tile(SB, TEAL),
           ISO.box(OP_X - 4, OP_Y - 4, 0, OP_SIZE + 8, OP_SIZE + 8, 4, top="#ffffff", left="#dbe8eb", right="#c7dde2")]
    for cx, cy in ((OP_X, OP_Y), (OP_X + OP_SIZE, OP_Y), (OP_X + OP_SIZE, OP_Y + OP_SIZE), (OP_X, OP_Y + OP_SIZE)):
        out.append(ISO.line([(cx, cy, 6), (cx, cy, OP_TOP)], TEAL, 0.8, ' opacity="0.35"'))
    out.append(grid_plate(OP_X, OP_Y, 6, OP_SIZE, n, fin))
    for z in (26, 42, 58):
        out.append(glass_layer(OP_X, OP_Y, z, OP_SIZE))
    out.append(grid_plate(OP_X, OP_Y, OP_TOP, OP_SIZE, n, fout))
    return "".join(out)


def capsule(a, b, width):
    d = f"M{f(a[0])} {f(a[1])}L{f(b[0])} {f(b[1])}"
    return (f'<path d="{d}" stroke="#b3bec9" stroke-width="{width + 1.6}" stroke-linecap="round" fill="none"/>'
            f'<path d="{d}" stroke="#ffffff" stroke-width="{width}" stroke-linecap="round" fill="none"/>')


TOKEN_X, TOKEN_Y, TOKEN_Z = 70, 50, 92       # centre of the token row on platform C


def platform_c():
    """Model2Action: prediction tokens and action tokens drive an arm, as in a vision-language-action model."""
    out = [tile(SB, CORAL),
           ISO.box(24, 72, 0, 20, 20, 5),
           ISO.ellipse(34, 82, 5.2, 6.5, "url(#rf-lc)", "#ffffff", 0.8),
           ISO.cylinder(76, 66, 0, 13, 5, "gs"),
           ISO.cylinder(76, 66, 5, 8, 9, "gs")]
    shoulder, elbow = ISO.p(76, 66, 14), ISO.p(64, 52, 52)
    wrist, tool = ISO.p(38, 80, 48), ISO.p(34, 82, 26)
    out += [capsule(shoulder, elbow, 10), capsule(elbow, wrist, 8), capsule(wrist, tool, 6)]
    tx, ty = tool
    out.append(f'<path d="M{f(tx - 5)} {f(ty - 1)}L{f(tx - 6)} {f(ty + 8)}M{f(tx + 5)} {f(ty - 1)}L{f(tx + 6)} {f(ty + 8)}" '
               'stroke="#6b7785" stroke-width="2.6" stroke-linecap="round" fill="none"/>')
    for (jx, jy), r in ((shoulder, 6), (elbow, 5.5), (wrist, 4.5)):
        out.append(f'<circle cx="{f(jx)}" cy="{f(jy)}" r="{r}" fill="{CORAL}" stroke="#ffffff" stroke-width="1.4"/>')
    tokens = []
    for j in range(6):
        u = (j - 2.5) * 11
        color = TEAL if j < 3 else CORAL
        tokens.append(ISO.box(TOKEN_X + u - 3.5, TOKEN_Y - u - 3.5, TOKEN_Z, 7, 7, 7,
                              top=mix(color, "#ffffff", 0.45), left=color, right=mix(color, "#000000", 0.12)))
    out.append(f'<g filter="url(#rf-glow)">{"".join(tokens)}</g>')
    ax, ay = ISO.p(TOKEN_X + 16.5, TOKEN_Y - 16.5, TOKEN_Z)
    out.append(f'<path d="M{f(ax)} {f(ay + 4)}C{f(ax - 4)} {f(ay + 30)} {f(tx + 30)} {f(ty - 50)} {f(tx + 8)} {f(ty - 30)}" '
               f'fill="none" stroke="{CORAL}" stroke-width="1.3" stroke-dasharray="3 3"/>')
    return "".join(out)


# Points on the platforms that the flows attach to, relative to each platform's top corner
B_OUT = ISO.p(OP_X + OP_SIZE, OP_Y, OP_TOP + 2)            # right corner of the solver's output layer
B_TOP = ISO.p(OP_X, OP_Y, OP_TOP)[1]                       # highest point of the operator stack
C_TOKENS = ISO.p(TOKEN_X, TOKEN_Y, TOKEN_Z + 12)           # just above the middle of the token row
C_TOKENS_RIGHT = ISO.p(TOKEN_X + 33, TOKEN_Y - 33, TOKEN_Z + 3.5)
A_TOP = -88                                                # turbine tips above platform A's top corner


def sprite_defs():
    tops = "".join(
        f'<linearGradient id="rf-top-{c[1:]}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffffff"/>'
        f'<stop offset="1" stop-color="{mix(c, "#ffffff", 0.8)}"/></linearGradient>' for c in (PURPLE, TEAL, CORAL))
    letters = "".join(
        f'<linearGradient id="rf-letter-{k}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{a}"/>'
        f'<stop offset="1" stop-color="{b}"/></linearGradient>'
        for k, a, b in (("a", "#c3a6e2", "#6d45a0"), ("b", "#6fc3d3", "#1f5f6f"), ("c", "#f7b8ab", "#c8513f")))
    return (
        '<filter id="rf-soft" x="-30%" y="-60%" width="160%" height="220%"><feGaussianBlur stdDeviation="7"/></filter>'
        '<filter id="rf-blob" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="38"/></filter>'
        '<filter id="rf-glow" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="2.2" result="b"/>'
        '<feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        '<linearGradient id="rf-gs" x1="0" x2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="0.55" stop-color="#e3e8ed"/>'
        '<stop offset="1" stop-color="#c3ccd6"/></linearGradient>'
        '<linearGradient id="rf-gw" x1="0" x2="1"><stop offset="0" stop-color="#f5f9fc"/><stop offset="1" stop-color="#bcd0df"/></linearGradient>'
        f'<radialGradient id="rf-lc" cx="0.45" cy="0.45" r="0.6"><stop offset="0" stop-color="#efe6f8"/>'
        f'<stop offset="0.55" stop-color="#b594d6"/><stop offset="1" stop-color="{PURPLE}"/></radialGradient>'
        '<linearGradient id="rf-bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fbfaff"/>'
        '<stop offset="0.5" stop-color="#f6fbfc"/><stop offset="1" stop-color="#fffaf8"/></linearGradient>'
        + tops + letters)


# ------------------------------------------------------------------ layouts


def bez(p0, p1, p2, p3, s):
    u = 1 - s
    return (u ** 3 * p0[0] + 3 * u * u * s * p1[0] + 3 * u * s * s * p2[0] + s ** 3 * p3[0],
            u ** 3 * p0[1] + 3 * u * u * s * p1[1] + 3 * u * s * s * p2[1] + s ** 3 * p3[1])


def head(x, y, ang, color, size=9):
    a = math.radians(ang)
    ux, uy = math.cos(a), math.sin(a)
    bx, by = x - ux * size, y - uy * size
    px, py = -uy * size * 0.45, ux * size * 0.45
    return f'<path d="M{f(x)} {f(y)}L{f(bx + px)} {f(by + py)}L{f(bx - px)} {f(by - py)}Z" fill="{color}"/>'


class Layout:
    """One arrangement of the three platforms with its own card, flows and labels."""

    def __init__(self, name, width, height, type_scale=1.0):
        self.name, self.w, self.h = name, width, height
        self.ts = type_scale                     # text is set larger where the layout is shown scaled down
        self.defs, self.body, self.n = [], [], 0

    def add(self, *parts):
        self.body.extend(parts)

    def use(self, panel, x, y):
        self.add(f'<use href="#rf-{panel}" x="{f(x)}" y="{f(y)}"/>')

    def card(self, blobs):
        w, h, n = self.w, self.h, self.name
        self.defs.append(f'<clipPath id="rf-{n}-clip"><rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="18"/></clipPath>')
        glow = "".join(f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{r}" fill="{color}" opacity="0.19" filter="url(#rf-blob)"/>'
                       for cx, cy, r, color in blobs)
        self.add(f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="18" fill="url(#rf-bg)"/>',
                 f'<g clip-path="url(#rf-{n}-clip)">{glow}</g>',
                 f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="18" fill="none" stroke="#e8ebf0"/>')

    def gradient(self, a, b, c0, c1):
        """A gradient in user space, so that vertical and horizontal paths are painted too."""
        self.n += 1
        gid = f"rf-{self.name}-g{self.n}"
        self.defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{f(a[0])}" y1="{f(a[1])}" '
                         f'x2="{f(b[0])}" y2="{f(b[1])}"><stop offset="0" stop-color="{c0}"/><stop offset="1" stop-color="{c1}"/>'
                         '</linearGradient>')
        return f"url(#{gid})"

    def curve(self, p0, p1, p2, p3, c0, c1, particles=(0.35, 0.62), dashed=False):
        """A cubic flow from p0 to p3 with an arrow head, a soft ribbon and a few particles."""
        d = f"M{f(p0[0])} {f(p0[1])}C{f(p1[0])} {f(p1[1])} {f(p2[0])} {f(p2[1])} {f(p3[0])} {f(p3[1])}"
        ex, ey = p3
        qx, qy = bez(p0, p1, p2, p3, 0.97)
        ang = math.degrees(math.atan2(ey - qy, ex - qx))
        tip = (ex + math.cos(math.radians(ang)) * 7, ey + math.sin(math.radians(ang)) * 7)
        if dashed:
            self.add(f'<path d="{d}" fill="none" stroke="{c0}" stroke-width="2" stroke-linecap="round" stroke-dasharray="5 4"/>',
                     head(*tip, ang, c1))
            return
        paint = self.gradient(p0, p3, c0, c1)
        self.add(f'<path d="{d}" fill="none" stroke="{paint}" stroke-width="11" stroke-linecap="round" opacity="0.18"/>',
                 f'<path d="{d}" fill="none" stroke="{paint}" stroke-width="2.4" stroke-linecap="round"/>')
        for s in particles:
            x, y = bez(p0, p1, p2, p3, s)
            self.add(f'<circle cx="{f(x)}" cy="{f(y)}" r="2.3" fill="#ffffff" stroke="{c1}" stroke-width="1.1"/>')
        self.add(head(*tip, ang, c1))

    def route(self, pts, c0, c1, end_dir, dashed=False, radius=10, particles=()):
        """A flow along straight segments with rounded corners, ending in an arrow head."""
        d = [f"M{f(pts[0][0])} {f(pts[0][1])}"]
        for prev, cur, nxt in zip(pts, pts[1:], pts[2:]):
            v1 = (cur[0] - prev[0], cur[1] - prev[1])
            v2 = (nxt[0] - cur[0], nxt[1] - cur[1])
            l1, l2 = math.hypot(*v1), math.hypot(*v2)
            r = min(radius, l1 / 2, l2 / 2)
            a = (cur[0] - v1[0] / l1 * r, cur[1] - v1[1] / l1 * r)
            b = (cur[0] + v2[0] / l2 * r, cur[1] + v2[1] / l2 * r)
            d.append(f"L{f(a[0])} {f(a[1])}Q{f(cur[0])} {f(cur[1])} {f(b[0])} {f(b[1])}")
        d.append(f"L{f(pts[-1][0])} {f(pts[-1][1])}")
        d = "".join(d)
        ang = {"right": 0, "down": 90, "left": 180, "up": 270}[end_dir]
        ex, ey = pts[-1]
        tip = (ex + math.cos(math.radians(ang)) * 7, ey + math.sin(math.radians(ang)) * 7)
        if dashed:
            self.add(f'<path d="{d}" fill="none" stroke="{c0}" stroke-width="2" stroke-linecap="round" '
                     'stroke-linejoin="round" stroke-dasharray="5 4"/>', head(*tip, ang, c1))
            return
        paint = self.gradient(pts[0], pts[-1], c0, c1)
        self.add(f'<path d="{d}" fill="none" stroke="{paint}" stroke-width="11" stroke-linecap="round" stroke-linejoin="round" opacity="0.18"/>',
                 f'<path d="{d}" fill="none" stroke="{paint}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>')
        for x, y in particles:
            self.add(f'<circle cx="{f(x)}" cy="{f(y)}" r="2.3" fill="#ffffff" stroke="{c1}" stroke-width="1.1"/>')
        self.add(head(*tip, ang, c1))

    def label(self, cx, y, key, title, lines):
        """Large serif letter, direction name, and one plain phrase underneath."""
        ts = self.ts
        total = (24 + 9 + 8.2 * len(title)) * ts
        x0 = cx - total / 2
        self.add(text(x0, y + 5 * ts, key.upper(), round(31 * ts, 1), f"url(#rf-letter-{key})", "start", 600, SERIF),
                 text(x0 + 33 * ts, y, title, round(15 * ts, 1), INK, "start", 600))
        for i, line in enumerate(lines):
            self.add(text(cx, y + (22 + 17 * i) * ts, line, round(13 * ts, 1), MUTED))

    def word(self, x, y, s, color, anchor="middle", extra=""):
        self.add(text(x, y, s, round(13 * self.ts, 1), color, anchor, 600, extra=extra))

    def svg(self):
        defs = f'<defs>{"".join(self.defs)}</defs>' if self.defs else ""
        return (f'<svg class="rf__{self.name}" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="rf-desc" '
                f'font-family="{FONT}">{defs}{"".join(self.body)}</svg>')


LABELS = {
    "a": ("Physical dynamics", "materials, energy and water systems"),
    "b": ("Neural solvers", "solve the equations in one pass"),
    "c": ("Model2Action", "measure errors in decisions"),
}
WORD_MODEL, WORD_DECIDE = "#7b54a8", "#277084"
LOOP_TEXT, LOOP_COLOR = "decision error trains the solver", "#c9604f"


def wide():
    """Three platforms in a row: decision error arcs over the top, act returns along the bottom."""
    lay = Layout("wide", 760, 408, type_scale=14 / 13)
    mid = 206                                   # the left and right platform corners sit on this line
    xa = 19 + SA * C
    xb = xa + SA * C + 16 + SB * C
    xc = xb + SB * C + 16 + SB * C
    ya, yb = mid - SA * H, mid - SB * H
    lay.card([(150, 210, 150, PURPLE), (410, 150, 120, TEAL), (650, 230, 140, CORAL)])
    lay.use("a", xa, ya)
    lay.use("b", xb, yb)
    lay.use("c", xc, yb)
    ax0, ax1 = xa + SA * C - 26, xb - 54
    lay.curve((ax0, mid - 4), (ax0 + 22, mid - 22), (ax1 - 22, mid - 22), (ax1, mid - 12), PURPLE, TEAL)
    lay.word((ax0 + ax1) / 2, mid - 31, "model", WORD_MODEL)
    bx0, bx1 = xb + SB * C - 36, xc - 80
    lay.curve((bx0, mid - 8), (bx0 + 22, mid - 26), (bx1 - 22, mid - 26), (bx1, mid - 14), TEAL, CORAL)
    lay.word((bx0 + bx1) / 2, mid - 35, "decide", WORD_DECIDE)
    sx, sy = xc + C_TOKENS[0], yb + C_TOKENS[1]
    tx, ty = xb + B_OUT[0], yb + B_OUT[1]
    ctrl = ((sx - 6, sy - 6), (sx - 20, sy - 70), (tx + 90, ty - 80), (tx + 12, ty - 10))
    lay.curve(*ctrl, CORAL, CORAL, dashed=True)
    apex = min((bez(*ctrl, j / 50) for j in range(51)), key=lambda q: q[1])
    lay.word(apex[0], apex[1] - 10, LOOP_TEXT, LOOP_COLOR)
    base = mid + 108
    for key, x in (("a", xa), ("b", xb), ("c", xc)):
        lay.label(x, base, key, LABELS[key][0], [LABELS[key][1]])
    lay.curve((xc, base + 38), (xc - 40, base + 66), (xa + 40, base + 66), (xa, base + 42), CORAL, PURPLE,
              particles=(0.3, 0.5, 0.7))
    lay.word((xa + xc) / 2, base + 79, "act", MUTED)
    return lay


def mid():
    """A on top, B and C below: model and act run down and up the sides, the loop closes underneath."""
    lay = Layout("mid", 520, 636)
    xa, ya = 260, 110
    xb, xc, yb = 132, 388, 396
    lay.card([(260, 180, 150, PURPLE), (120, 440, 125, TEAL), (400, 440, 130, CORAL)])
    lay.use("a", xa, ya)
    lay.use("b", xb, yb)
    lay.use("c", xc, yb)
    lay.label(xa, ya + 2 * SA * H + 42, "a", LABELS["a"][0], [LABELS["a"][1]])
    a_left = (xa - SA * C, ya + SA * H)
    a_right = (xa + SA * C, ya + SA * H)
    end = (xb - 30, yb + B_TOP - 6)
    lay.curve((a_left[0] + 2, a_left[1] + 20), (a_left[0] - 34, a_left[1] + 60), (end[0] - 22, end[1] - 70), end, PURPLE, TEAL)
    lay.word(a_left[0] - 78, a_left[1] + 86, "model", WORD_MODEL)
    bx0, bx1 = xb + SB * C - 12, xc - SB * C + 8
    corner = yb + SB * H
    lay.curve((bx0, corner - 6), (bx0 + 18, corner - 22), (bx1 - 18, corner - 22), (bx1, corner - 8), TEAL, CORAL,
              particles=(0.5,))
    lay.word((bx0 + bx1) / 2, corner - 30, "decide", WORD_DECIDE)
    start = (xc + C_TOKENS_RIGHT[0] + 12, yb + C_TOKENS_RIGHT[1])
    lay.curve(start, (start[0] + 26, start[1] - 50), (a_right[0] + 70, a_right[1] + 70), (a_right[0] + 8, a_right[1] + 18),
              CORAL, PURPLE)
    lay.word(a_right[0] + 108, a_right[1] + 86, "act", MUTED)
    base = yb + 2 * SB * H + 40
    lay.label(xb, base, "b", LABELS["b"][0], [LABELS["b"][1]])
    lay.label(xc, base, "c", LABELS["c"][0], [LABELS["c"][1]])
    lay.curve((xc, base + 36), (xc - 30, base + 62), (xb + 30, base + 62), (xb, base + 40), CORAL, CORAL, dashed=True)
    lay.word((xb + xc) / 2, base + 74, LOOP_TEXT, LOOP_COLOR)
    return lay


def narrow():
    """Platforms stacked for phones: the loop runs up the right side, act returns up the left."""
    x = 160
    ya = 20 - A_TOP
    a_label = ya + 2 * SA * H + 40
    yb = a_label + 22 + 44 - B_TOP + 8
    b_label = yb + 2 * SB * H + 40
    yc = b_label + 22 + 44 - (C_TOKENS[1] - 8) + 8
    c_label = yc + 2 * SB * H + 40
    height = int(c_label + 22 + 62)
    lay = Layout("narrow", 336, height)
    lay.card([(x, ya + 70, 150, PURPLE), (x, yb + 40, 125, TEAL), (x, yc + 40, 135, CORAL)])
    lay.use("a", x, ya)
    lay.use("b", x, yb)
    lay.use("c", x, yc)
    lay.label(x, a_label, "a", LABELS["a"][0], [LABELS["a"][1]])
    lay.label(x, b_label, "b", LABELS["b"][0], [LABELS["b"][1]])
    lay.label(x, c_label, "c", LABELS["c"][0], [LABELS["c"][1]])
    for top, word, c0, c1, color in ((a_label + 34, "model", PURPLE, TEAL, WORD_MODEL),
                                     (b_label + 34, "decide", TEAL, CORAL, WORD_DECIDE)):
        lay.route([(x, top), (x, top + 22)], c0, c1, "down")
        lay.word(x + 14, top + 17, word, color, "start")
    # decision error: from the token row on C up the right side to the solver's output layer on B
    right = lay.w - 26
    start = (x + C_TOKENS_RIGHT[0] + 10, yc + C_TOKENS_RIGHT[1])
    end = (x + B_OUT[0] + 14, yb + B_OUT[1])
    lay.route([start, (right, start[1]), (right, end[1]), end], CORAL, CORAL, "left", dashed=True)
    my = (start[1] + end[1]) / 2
    lay.word(0, 0, LOOP_TEXT, LOOP_COLOR, extra=f' transform="translate({f(right + 15)} {f(my)}) rotate(90)"')
    # act: from under C's label back up the left side to platform A
    left = 14
    bottom = c_label + 22 + 30
    a_corner = (x - SA * C, ya + SA * H)
    lay.route([(x, c_label + 34), (x, bottom), (left, bottom), (left, a_corner[1] + 20)], CORAL, PURPLE, "up",
              particles=((x - 50, bottom), (left, (bottom + a_corner[1]) / 2)))
    lay.word((x + left) / 2, bottom + 19, "act", MUTED)
    return lay


# ------------------------------------------------------------------ output

DESCRIPTION = (
    "Research overview as one isometric scene with three platforms. Platform A, physical dynamics, holds an "
    "iCVD chamber with a liquid-crystal film and an integrated energy and water network with wind turbines, "
    "solar panels, a plant, a water tower, pipes and buildings. Platform B, neural solvers, shows an input field "
    "passing up through operator layers and leaving as the predicted solution. Platform C, Model2Action, shows "
    "prediction tokens and action tokens driving a robot arm. Arrows read model from A to B, decide from B to C, "
    "and act from C back to A. A dashed arrow from C to B reads decision error trains the solver."
)


def main():
    sprite = (
        '<svg class="rf__defs" width="0" height="0" aria-hidden="true" focusable="false">'
        f'<defs>{sprite_defs()}'
        f'<g id="rf-a">{platform_a()}</g><g id="rf-b">{platform_b()}</g><g id="rf-c">{platform_c()}</g>'
        '</defs></svg>'
    )
    layouts = "\n  ".join(lay.svg() for lay in (wide(), mid(), narrow()))
    html = f"""```{{=html}}
<!-- Generated by scripts/build_research_figure.py. Edit the script, not this file. -->
<figure class="rf">
  {sprite}
  <p class="visually-hidden" id="rf-desc">{DESCRIPTION}</p>
  {layouts}
</figure>
```
"""
    INCLUDE.write_text(html, encoding="utf-8")
    print(f"wrote {INCLUDE.relative_to(ROOT)} ({len(html.encode()) / 1024:.1f} KiB)")


if __name__ == "__main__":
    main()
