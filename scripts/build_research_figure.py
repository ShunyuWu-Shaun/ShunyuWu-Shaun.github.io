#!/usr/bin/env python3
"""Build editable SVG illustrations for the research overview and applications.

The overview links physical dynamics, learned trajectories, and optimized inputs.
Three layouts follow the figure's container width. The applications illustration
shows water-energy coupling around a data center and structure evolution during
materials processing. All curves and fields are conceptual schematics.

Run from the repository root with Python's standard library:
    python3 scripts/build_research_figure.py
"""

from __future__ import annotations

import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INCLUDE = ROOT / "_includes" / "research-overview.qmd"
APPLICATIONS = ROOT / "_includes" / "dynamics-applications.qmd"

# Direction colours, identical to --c-a, --c-b and --c-c in assets/css/site.css
PURPLE, TEAL, CORAL = "#9467BD", "#31859A", "#EA7F6F"
INK, MUTED = "#17202a", "#66717d"
SERIF = "IBM Plex Serif, Georgia, serif"
FONT = SERIF
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


def server_rack(x, y, height=43):
    out = [ISO.box(x, y, 0, 14, 20, height, top="#e5edf2", left="#d1dfe6", right="#afc4cf")]
    for z in (7, 15, 23, 31):
        out.append(ISO.poly([(x + 2, y + 20, z), (x + 12, y + 20, z),
                             (x + 12, y + 20, z + 4), (x + 2, y + 20, z + 4)], "#ffffff"))
        out.append(ISO.line([(x + 3, y + 20.2, z + 2), (x + 6, y + 20.2, z + 2)], TEAL, 0.9))
    return "".join(out)


def structure_tile(x, y, stage):
    out = [ISO.box(x, y, 0, 27, 27, 3, top="#f6f0fb", left="#d8c4eb", right="#bea1d7")]
    for j in range(3):
        for k in range(3):
            a, b = x + 6 + j * 7, y + 6 + k * 7
            angle = (j * 1.1 + k * 0.8) * (1 - stage / 2)
            dx, dy = 3.5 * math.cos(angle), 3.5 * math.sin(angle)
            out.append(ISO.line([(a - dx, b - dy, 3.5), (a + dx, b + dy, 3.5)], PURPLE, 1.5))
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
    """Data center water-energy coupling above a sequence of material states."""
    out = [tile(SA, PURPLE)]
    for pts in ([(35, 43), (35, 62), (113, 62), (113, 34)],
                [(72, 35), (94, 35), (94, 20)]):
        out.append(ISO.line([(a, b, 0.8) for a, b in pts], PIPE, 3.2))
        out.append(ISO.line([(a, b, 0.8) for a, b in pts], PIPE_HI, 1.1))
    for x in (20, 39, 58):
        out.append(server_rack(x, 18))
    out.append(ISO.cylinder(96, 22, 0, 9, 19, "gw", top="#dcebf5"))
    out.append(ISO.box(102, 43, 0, 20, 16, 12))
    out.append(ISO.line([(10, 78, 0.5), (137, 78, 0.5)], PURPLE, 1, ' opacity="0.3"'))
    for stage, x in enumerate((24, 65, 106)):
        out.append(structure_tile(x, 106, stage))
    for x in (55, 96):
        out.append(ISO.line([(x, 119, 1), (x + 6, 119, 1)], PURPLE, 1.3))
        out.append(ISO.line([(x + 3, 116, 1), (x + 6, 119, 1), (x + 3, 122, 1)], PURPLE, 1.3))
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


def platform_c():
    """A predicted state trajectory under a limit and an optimized input schedule."""
    out = [tile(SB, CORAL),
           '<path d="M-55 63V18M55 63V18" stroke="#b8c5cf" stroke-width="3"/>',
           '<rect x="-78" y="-42" width="156" height="105" rx="7" fill="#ffffff" stroke="#d7dfe6"/>',
           '<path d="M-61 -23V44H62" fill="none" stroke="#9faebb" stroke-width="1"/>',
           '<path d="M-61 -13H62" fill="none" stroke="#b7a4ca" stroke-width="1.2" stroke-dasharray="4 3"/>',
           '<path d="M-60 36C-41 33 -33 11 -17 8S11 -3 26 -3S44 -1 61 -1" '
           f'fill="none" stroke="{CORAL}" stroke-width="2.6"/>',
           text(-60, -29, "state", 9, MUTED, "start"),
           text(60, -20, "limit", 9, MUTED, "end"),
           text(56, 38, "time", 9, MUTED)]
    for j, height in enumerate((8, 15, 21, 15, 11, 13)):
        out.append(ISO.box(28 + j * 10, 88 - j * 3, 0, 7, 7, height,
                           top=mix(CORAL, "#ffffff", 0.5), left=mix(CORAL, "#ffffff", 0.2), right=CORAL))
    return "".join(out)


# Points on the platforms that the flows attach to, relative to each platform's top corner
B_OUT = ISO.p(OP_X + OP_SIZE, OP_Y, OP_TOP + 2)            # right corner of the solver's output layer
B_TOP = ISO.p(OP_X, OP_Y, OP_TOP)[1]                       # highest point of the operator stack
C_OUTPUT = (0, -48)                                       # above the trajectory plot
C_RIGHT = (78, 8)                                         # right edge of the trajectory plot
A_TOP = -50


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
            self.add(text(cx, y + (30 + 17 * i) * ts, line, round(13 * ts, 1), MUTED))

    def word(self, x, y, s, color, anchor="middle", extra=""):
        self.add(text(x, y, s, round(13 * self.ts, 1), color, anchor, 600, extra=extra))

    def svg(self):
        defs = f'<defs>{"".join(self.defs)}</defs>' if self.defs else ""
        return (f'<svg class="rf__{self.name}" viewBox="0 0 {self.w} {self.h}" role="img" aria-labelledby="rf-desc" '
                f'font-family="{FONT}">{defs}{"".join(self.body)}</svg>')


LABELS = {
    "a": ("Physical dynamics", "water-energy and materials"),
    "b": ("Learning dynamics", "predict evolving physical fields"),
    "c": ("Model2Action", "control and optimization"),
}
WORD_MODEL, WORD_DECIDE = "#7b54a8", "#277084"
LOOP_TEXT, LOOP_COLOR = "decision error trains the model", "#c9604f"


def wide():
    """Three platforms in a row: decision error arcs over the top, act returns along the bottom."""
    lay = Layout("wide", 760, 420, type_scale=14 / 13)
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
    lay.word((ax0 + ax1) / 2, mid - 31, "learn", WORD_MODEL)
    bx0, bx1 = xb + SB * C - 36, xc - 80
    lay.curve((bx0, mid - 8), (bx0 + 22, mid - 26), (bx1 - 22, mid - 26), (bx1, mid - 14), TEAL, CORAL)
    lay.word((bx0 + bx1) / 2, mid - 35, "optimize", WORD_DECIDE)
    sx, sy = xc + C_OUTPUT[0], yb + C_OUTPUT[1]
    tx, ty = xb + B_OUT[0], yb + B_OUT[1]
    ctrl = ((sx - 6, sy - 6), (sx - 20, sy - 70), (tx + 90, ty - 80), (tx + 12, ty - 10))
    lay.curve(*ctrl, CORAL, CORAL, dashed=True)
    apex = min((bez(*ctrl, j / 50) for j in range(51)), key=lambda q: q[1])
    lay.word(apex[0], apex[1] - 10, LOOP_TEXT, LOOP_COLOR)
    base = mid + 108
    for key, x in (("a", xa), ("b", xb), ("c", xc)):
        lay.label(x, base, key, LABELS[key][0], [LABELS[key][1]])
    lay.curve((xc, base + 46), (xc - 40, base + 74), (xa + 40, base + 74), (xa, base + 50), CORAL, PURPLE,
              particles=(0.3, 0.5, 0.7))
    lay.word((xa + xc) / 2, base + 87, "act", MUTED)
    return lay


def mid():
    """A on top, B and C below: model and act run down and up the sides, the loop closes underneath."""
    lay = Layout("mid", 520, 650)
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
    lay.word(a_left[0] - 78, a_left[1] + 86, "learn", WORD_MODEL)
    bx0, bx1 = xb + SB * C - 12, xc - SB * C + 8
    corner = yb + SB * H
    lay.curve((bx0, corner - 6), (bx0 + 18, corner - 22), (bx1 - 18, corner - 22), (bx1, corner - 8), TEAL, CORAL,
              particles=(0.5,))
    lay.word((bx0 + bx1) / 2, corner - 30, "optimize", WORD_DECIDE)
    start = (xc + C_RIGHT[0] + 12, yb + C_RIGHT[1])
    lay.curve(start, (start[0] + 26, start[1] - 50), (a_right[0] + 70, a_right[1] + 70), (a_right[0] + 8, a_right[1] + 18),
              CORAL, PURPLE)
    lay.word(a_right[0] + 108, a_right[1] + 86, "act", MUTED)
    base = yb + 2 * SB * H + 40
    lay.label(xb, base, "b", LABELS["b"][0], [LABELS["b"][1]])
    lay.label(xc, base, "c", LABELS["c"][0], [LABELS["c"][1]])
    lay.curve((xc, base + 44), (xc - 30, base + 70), (xb + 30, base + 70), (xb, base + 48), CORAL, CORAL, dashed=True)
    lay.word((xb + xc) / 2, base + 82, LOOP_TEXT, LOOP_COLOR)
    return lay


def narrow():
    """Platforms stacked for phones: the loop runs up the right side, act returns up the left."""
    x = 160
    ya = 20 - A_TOP
    a_label = ya + 2 * SA * H + 40
    yb = a_label + 30 + 44 - B_TOP + 8
    b_label = yb + 2 * SB * H + 40
    yc = b_label + 30 + 44 - (C_OUTPUT[1] - 8) + 8
    c_label = yc + 2 * SB * H + 40
    height = int(c_label + 30 + 62)
    lay = Layout("narrow", 336, height)
    lay.card([(x, ya + 70, 150, PURPLE), (x, yb + 40, 125, TEAL), (x, yc + 40, 135, CORAL)])
    lay.use("a", x, ya)
    lay.use("b", x, yb)
    lay.use("c", x, yc)
    lay.label(x, a_label, "a", LABELS["a"][0], [LABELS["a"][1]])
    lay.label(x, b_label, "b", LABELS["b"][0], [LABELS["b"][1]])
    lay.label(x, c_label, "c", LABELS["c"][0], [LABELS["c"][1]])
    for top, word, c0, c1, color in ((a_label + 42, "learn", PURPLE, TEAL, WORD_MODEL),
                                     (b_label + 42, "optimize", TEAL, CORAL, WORD_DECIDE)):
        lay.route([(x, top), (x, top + 22)], c0, c1, "down")
        lay.word(x + 14, top + 17, word, color, "start")
    # Decision error from the trajectory plot to the learned field.
    right = lay.w - 26
    start = (x + C_RIGHT[0] + 10, yc + C_RIGHT[1])
    end = (x + B_OUT[0] + 14, yb + B_OUT[1])
    lay.route([start, (right, start[1]), (right, end[1]), end], CORAL, CORAL, "left", dashed=True)
    my = (start[1] + end[1]) / 2
    lay.word(0, 0, LOOP_TEXT, LOOP_COLOR, extra=f' transform="translate({f(right + 5)} {f(my)}) rotate(90)"')
    # act: from under C's label back up the left side to platform A
    left = 14
    bottom = c_label + 30 + 30
    a_corner = (x - SA * C, ya + SA * H)
    lay.route([(x, c_label + 42), (x, bottom), (left, bottom), (left, a_corner[1] + 20)], CORAL, PURPLE, "up",
              particles=((x - 50, bottom), (left, (bottom + a_corner[1]) / 2)))
    lay.word((x + left) / 2, bottom + 19, "act", MUTED)
    return lay


# ------------------------------------------------------------------ output

DESCRIPTION = (
    "Three research directions form one sequence. A shows data center water-energy coupling and a sequence "
    "of evolving material structures. B shows a neural operator mapping an input field to a predicted state. "
    "C shows an illustrative state trajectory under a constraint and an input schedule. The solid arrows "
    "connect learning, optimization, and physical action. A dashed arrow returns decision error to model training."
)


def arrow(x1, y1, x2, y2, color, width=1.8):
    angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
    return (f'<path d="M{f(x1)} {f(y1)}L{f(x2)} {f(y2)}" fill="none" '
            f'stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>'
            + head(x2, y2, angle, color, size=6))


def field_patch(x, y, stage, width=72, height=50):
    out = [f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="4" '
           'fill="#f6f0fb" stroke="#d9c7e9"/>']
    for j in range(4):
        for k in range(3):
            cx, cy = x + 12 + j * 16, y + 11 + k * 14
            angle = (j * 1.2 + k * 0.7) * (1 - stage / 2)
            dx, dy = 5 * math.cos(angle), 5 * math.sin(angle)
            out.append(f'<path d="M{f(cx - dx)} {f(cy - dy)}L{f(cx + dx)} {f(cy + dy)}" '
                       f'stroke="{PURPLE}" stroke-width="2" stroke-linecap="round"/>')
    return "".join(out)


def engineering_application():
    out = [
        text(190, 28, "Computing demand", 16, INK, weight=500),
        f'<path d="M151 49H170V62H194V45H216V58H229" fill="none" stroke="{PURPLE}" stroke-width="2"/>',
        arrow(190, 70, 190, 86, PURPLE),
        '<rect x="122" y="91" width="140" height="100" rx="7" fill="#f3f7f9" stroke="#c9d7df"/>',
        text(192, 216, "Data center", 16, INK, weight=500),
        '<rect x="18" y="119" width="64" height="52" rx="6" fill="#f3eef9" stroke="#c8b2df"/>',
        f'<path d="M52 125L39 145H49L45 163L62 140H52Z" fill="{PURPLE}"/>',
        text(51, 104, "Energy supply", 13, INK),
        arrow(82, 145, 118, 145, PURPLE),
        '<rect x="296" y="119" width="62" height="58" rx="6" fill="#eef7fa" stroke="#aacdd8"/>',
        '<circle cx="327" cy="147" r="18" fill="#ffffff" stroke="#aacdd8"/>',
        f'<path d="M327 147C310 130 336 119 330 143C352 131 356 157 332 150C340 174 312 177 324 152Z" fill="{TEAL}" opacity="0.6"/>',
        text(327, 216, "Cooling", 16, INK, weight=500),
        text(278, 112, "heat", 12, "#c9604f"),
        arrow(262, 128, 292, 128, CORAL),
        arrow(296, 163, 266, 163, TEAL),
        text(327, 70, "Water", 14, TEAL),
        arrow(327, 80, 327, 115, TEAL),
        '<path d="M45 245H335" stroke="#e1e6eb"/>',
        text(190, 270, "Dynamic optimization of operation", 16, INK, weight=500),
        text(190, 299, "Energy use · Water use · Emissions", 13, MUTED),
    ]
    for x in (138, 173, 208):
        out.append(f'<rect x="{x}" y="107" width="27" height="64" rx="3" fill="#d8e5ec" stroke="#a7bdc9"/>')
        for y in (114, 128, 142, 156):
            out.append(f'<rect x="{x + 4}" y="{y}" width="19" height="8" rx="1.5" fill="#ffffff"/>')
            out.append(f'<circle cx="{x + 8}" cy="{y + 4}" r="1.3" fill="{TEAL}"/>')
    return (f'<svg viewBox="0 0 380 350" role="img" aria-labelledby="da-engineering-title" font-family="{FONT}">'
            '<title id="da-engineering-title">Data center dynamics connect computing demand, energy supply, and cooling to sustainable operation.</title>'
            + "".join(out) + '</svg>')


def materials_application():
    out = [
        '<rect x="75" y="11" width="230" height="36" rx="5" fill="#f5effa" stroke="#cbb5df"/>',
        text(190, 35, "Processing conditions", 16, INK, weight=500),
        arrow(190, 50, 190, 77, PURPLE),
        f'<g transform="translate(190 164) scale(1.7)">{reactor(0, 0).replace("rf-", "da-")}</g>',
        text(190, 191, "Material formation", 15, INK),
        f'<path d="M190 200V213H52V226" fill="none" stroke="{PURPLE}" stroke-width="1.6"/>',
        head(52, 226, 90, PURPLE, size=6),
    ]
    for stage, x in enumerate((40, 154, 268)):
        out.append(field_patch(x, 232, stage))
        out.append(text(x + 36, 225, ("t₀", "t₁", "t₂")[stage], 13, MUTED))
    out += [arrow(117, 257, 148, 257, PURPLE), arrow(231, 257, 262, 257, PURPLE),
            text(76, 302, "Initial state", 13, MUTED),
            text(190, 302, "Evolution", 13, MUTED),
            text(304, 302, "Target structure", 13, MUTED),
            f'<path d="M304 309V323H20V29H70" fill="none" stroke="{CORAL}" stroke-width="1.6" stroke-dasharray="4 3"/>',
            head(70, 29, 0, CORAL, size=6),
            text(190, 344, "Optimize the processing trajectory", 15, "#c9604f", weight=500)]
    return (f'<svg viewBox="0 0 380 350" role="img" aria-labelledby="da-materials-title" font-family="{FONT}">'
            '<title id="da-materials-title">Processing conditions drive material structure evolution. Dynamic models guide the optimization of those conditions.</title>'
            f'<defs>{sprite_defs().replace("rf-", "da-")}</defs>'
            + "".join(out) + '</svg>')


def applications_include():
    return f'''```{{=html}}
<!-- Generated by scripts/build_research_figure.py. -->
<div class="dynamics-applications">
  <figure class="da-card">
    <header><p>Engineering</p><h3>Water-energy dynamics</h3></header>
    {engineering_application()}
    <figcaption>Computing demand and thermal response connect operating decisions to energy and water use.</figcaption>
  </figure>
  <figure class="da-card">
    <header><p>Science</p><h3>Materials process dynamics</h3></header>
    {materials_application()}
    <figcaption>Dynamic models connect processing conditions to evolving material structure.</figcaption>
  </figure>
</div>
```
'''


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
    APPLICATIONS.write_text(applications_include(), encoding="utf-8")
    print(f"wrote {APPLICATIONS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
