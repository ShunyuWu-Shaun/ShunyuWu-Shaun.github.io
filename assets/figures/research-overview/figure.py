"""Research overview figure: one layout, two outputs.

The same geometry (inches, one origin) is written as
  1. research-overview.pptx  — native, editable PowerPoint shapes and text,
     with the two Matplotlib panels inserted as 600 dpi PNG at their reserved size;
  2. research-overview.svg   — the web version, with the Matplotlib SVG panels
     embedded inline so the whole file is vector and self-contained.

Run panels.py first, then:  python3 figure.py
"""
from __future__ import annotations

import re
from pathlib import Path

from PIL import ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

HERE = Path(__file__).resolve().parent

# ---------------------------------------------------------------- palette --
BLUE, BLUE_PALE = "0F4D92", "DDE6F0"
RED, RED_PALE = "B64342", "F5E5E5"
TEAL, TEAL_DARK, TEAL_PALE = "42949E", "317078", "E5F0F1"
N_BLACK, N_DARK, N_MID, N_LIGHT, N_PALE = "272727", "4D4D4D", "767676", "CFCECE", "F2F2F2"
WHITE = "FFFFFF"

FONT = "Arial"
ARIAL = "/System/Library/Fonts/Supplemental/Arial.ttf"
ARIAL_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

# ----------------------------------------------------------------- layout --
W, H = 10.0, 9.25
M = 0.35
BAND1 = (M, 0.35, 9.3, 1.15)
SUB = (2.0, 1.90, 6.0, 0.95)
QA = (0.35, 3.25, 4.4, 3.70)
QB = (5.25, 3.25, 4.4, 3.70)
BAND4 = (M, 7.35, 9.3, 1.60)
PANEL_W, PANEL_H = 4.1, 1.42

ARROWS = [  # (x1, y1, x2, y2, color)
    (5.0, 1.50, 5.0, 1.90, N_DARK),
    (3.5, 2.85, 3.5, 3.25, TEAL_DARK),
    (6.5, 2.85, 6.5, 3.25, TEAL_DARK),
    (5.25, 3.75, 4.75, 3.75, RED),      # return: decision-level error back to A
    (4.2, 6.95, 4.2, 7.35, BLUE),
    (5.8, 6.95, 5.8, 7.35, RED),
]

TEXT = {
    "band1_title": "Physical AI",
    "band1_sub": "Learning systems that observe, model, and act on physical systems.",
    "band1_right": "Its questions in science and engineering rest on one substrate.",
    "sub_title": "The governing dynamics of physical systems",
    "sub_body": "Ordinary and partial differential equations with initial conditions, boundary conditions, and external forcing.",
    "qa_title": "A. Learning to solve the dynamics",
    "qa_body": "Neural operators and neural solvers that return the solution field fast enough for design and control, rather than a surrogate that only predicts.",
    "qa_cap": "Computed. A two-dimensional advection-diffusion field, solved and shown at three times.",
    "qb_title": "B. The model-to-decision gap",
    "qb_body": "How the error of a learned model reaches a control or optimization decision. The gap is small over most of the state space and large near a critical point. Regret and constraint violation return to A as its training signal.",
    "qb_cap": "Computed. Shift of a bistable system's equilibrium under a fixed model error, against distance to the fold.",
    "band4_head": "Tested on the same physical systems in two branches",
    "sci_title": "Science: materials processing",
    "sci_body": "Temperature and composition fields of a processing step, and the process set-points chosen from their predicted rollouts.",
    "eng_title": "Engineering: water and energy systems",
    "eng_body": "Urban water demand and pressure, day-ahead electricity price, and hot-strip rolling energy, with the pump schedules and controller actions they set.",
}


# ------------------------------------------------------------ text metrics --
def wrap(text: str, pt: float, width_in: float, bold: bool = False) -> list[str]:
    """Greedy word wrap using the real Arial metrics, shared by both outputs."""
    font = ImageFont.truetype(ARIAL_BOLD if bold else ARIAL, size=int(round(pt * 4)))
    scale = 1 / (4 * 72.0)  # font loaded at 4x pt so that length/4 = points

    def w(s: str) -> float:
        return font.getlength(s) * scale

    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if w(trial) <= width_in * 0.94 or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def rgb(h: str) -> RGBColor:
    return RGBColor.from_string(h)


# ----------------------------------------------------------------- PPTX ----
class Pptx:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Inches(W), Inches(H)
        self.s = self.prs.slides.add_slide(self.prs.slide_layouts[6])

    def box(self, rect, fill, line, line_pt=1.25, rounded=True, name="box"):
        x, y, w, h = rect
        kind = MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE
        sh = self.s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
        sh.name = name
        if rounded:
            sh.adjustments[0] = 0.06
        sh.fill.solid(); sh.fill.fore_color.rgb = rgb(fill)
        if line:
            sh.line.color.rgb = rgb(line); sh.line.width = Pt(line_pt)
        else:
            sh.line.fill.background()
        sh.shadow.inherit = False
        sh.text_frame.text = ""
        return sh

    def text(self, x, y, w, lines, pt, color, bold=False, align="l", name="text", line_spacing=1.0):
        h = len(lines) * pt * 1.2 / 72.0 + 0.04
        tb = self.s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tb.name = name
        tf = tb.text_frame
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.TOP
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {"l": PP_ALIGN.LEFT, "c": PP_ALIGN.CENTER, "r": PP_ALIGN.RIGHT}[align]
            p.line_spacing = line_spacing
            p.space_after = Pt(0); p.space_before = Pt(0)
            r = p.add_run(); r.text = line
            r.font.name = FONT; r.font.size = Pt(pt); r.font.bold = bold
            r.font.color.rgb = rgb(color)
        return tb

    def arrow(self, x1, y1, x2, y2, color, width_pt=2.5, name="arrow"):
        c = self.s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
        c.name = name
        c.line.color.rgb = rgb(color); c.line.width = Pt(width_pt)
        ln = c.line._get_or_add_ln()
        tail = ln.makeelement(qn("a:tailEnd"), {"type": "triangle", "w": "med", "len": "med"})
        ln.append(tail)
        return c

    def picture(self, path, x, y, w, h, name="picture"):
        p = self.s.shapes.add_picture(str(path), Inches(x), Inches(y), Inches(w), Inches(h))
        p.name = name
        return p

    def dotted_vline(self, x, y1, y2, color):
        c = self.s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(y1), Inches(x), Inches(y2))
        c.name = "separator"
        c.line.color.rgb = rgb(color); c.line.width = Pt(1.0)
        ln = c.line._get_or_add_ln()
        ln.append(ln.makeelement(qn("a:prstDash"), {"val": "sysDot"}))
        return c

    def save(self, path):
        self.prs.save(str(path))


# ------------------------------------------------------------------ SVG ----
class Svg:
    PX = 96.0

    def __init__(self):
        self.parts = []
        self.defs = []

    def px(self, v):  # inches -> px
        return round(v * self.PX, 2)

    def fs(self, pt):  # points -> px
        return round(pt * self.PX / 72.0, 2)

    def box(self, rect, fill, line, line_pt=1.25, rounded=True, name="box"):
        x, y, w, h = rect
        r = self.px(min(w, h) * 0.06) if rounded else 0
        stroke = f'stroke="#{line}" stroke-width="{round(line_pt * self.PX / 72, 2)}"' if line else 'stroke="none"'
        self.parts.append(f'<rect x="{self.px(x)}" y="{self.px(y)}" width="{self.px(w)}" height="{self.px(h)}" rx="{r}" fill="#{fill}" {stroke}/>')

    def text(self, x, y, w, lines, pt, color, bold=False, align="l", name="text", line_spacing=1.15):
        size = self.fs(pt)
        anchor = {"l": "start", "c": "middle", "r": "end"}[align]
        ax = {"l": x, "c": x + w / 2, "r": x + w}[align]
        weight = ' font-weight="bold"' if bold else ""
        # first baseline sits one cap-height (~0.72 em) below the box top, like PowerPoint's top anchor
        first = self.px(y) + size * 0.86
        spans = "".join(
            f'<tspan x="{self.px(ax)}" y="{round(first + i * size * line_spacing, 2)}">{esc(line)}</tspan>'
            for i, line in enumerate(lines))
        self.parts.append(f'<text font-family="Arial, Helvetica, sans-serif" font-size="{size}" fill="#{color}" text-anchor="{anchor}"{weight}>{spans}</text>')

    def arrow(self, x1, y1, x2, y2, color, width_pt=2.5, name="arrow"):
        mid = f"ah_{color}"
        if mid not in "".join(self.defs):
            self.defs.append(
                f'<marker id="{mid}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="4.2" markerHeight="4.2" orient="auto-start-reverse">'
                f'<path d="M0 0L10 5L0 10z" fill="#{color}"/></marker>')
        # shorten the line so the head tip lands on the end point
        self.parts.append(
            f'<line x1="{self.px(x1)}" y1="{self.px(y1)}" x2="{self.px(x2)}" y2="{self.px(y2)}" stroke="#{color}" '
            f'stroke-width="{round(width_pt * self.PX / 72, 2)}" marker-end="url(#{mid})"/>')

    def picture(self, path, x, y, w, h, name="picture"):
        svg_path = Path(str(path)).with_suffix(".svg")
        src = svg_path.read_text(encoding="utf-8")
        src = re.sub(r"<\?xml[^>]*\?>", "", src)
        src = re.sub(r"<!DOCTYPE[^>]*>", "", src, flags=re.S)
        m = re.search(r"<svg\b([^>]*)>(.*)</svg>\s*$", src, flags=re.S)
        attrs, inner = m.group(1), m.group(2)
        vb = re.search(r'viewBox="([^"]+)"', attrs).group(1)
        prefix = Path(str(path)).stem.replace("-", "_")[:8]
        inner = re.sub(r'id="([^"]+)"', lambda mm: f'id="{prefix}_{mm.group(1)}"', inner)
        inner = re.sub(r'url\(#([^)]+)\)', lambda mm: f'url(#{prefix}_{mm.group(1)})', inner)
        inner = re.sub(r'href="#([^"]+)"', lambda mm: f'href="#{prefix}_{mm.group(1)}"', inner)
        self.parts.append(
            f'<svg x="{self.px(x)}" y="{self.px(y)}" width="{self.px(w)}" height="{self.px(h)}" viewBox="{vb}" '
            f'preserveAspectRatio="xMidYMid meet">{inner}</svg>')

    def dotted_vline(self, x, y1, y2, color):
        self.parts.append(
            f'<line x1="{self.px(x)}" y1="{self.px(y1)}" x2="{self.px(x)}" y2="{self.px(y2)}" stroke="#{color}" '
            f'stroke-width="1.33" stroke-dasharray="1.5 3.5" stroke-linecap="round"/>')

    def save(self, path, title, desc):
        body = "\n".join(self.parts)
        defs = "".join(self.defs)
        out = (
            f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {self.px(W)} {self.px(H)}" '
            f'role="img" aria-labelledby="ro-title ro-desc">\n<title id="ro-title">{esc(title)}</title>\n'
            f'<desc id="ro-desc">{esc(desc)}</desc>\n<defs>{defs}</defs>\n'
            f'<rect width="100%" height="100%" fill="#FFFFFF"/>\n{body}\n</svg>\n')
        Path(path).write_text(out, encoding="utf-8")


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ------------------------------------------------------------- compose -----
def compose(d):
    """Draw every element onto backend d (Pptx or Svg). Order: fills, arrows, text, panels."""
    # Row 1: Physical AI context band (borderless text band)
    d.box(BAND1, N_PALE, None, rounded=False, name="Physical AI band")
    # Row 2: substrate
    d.box(SUB, TEAL_PALE, TEAL_DARK, 1.5, name="Governing dynamics")
    # Row 3: questions
    d.box(QA, BLUE_PALE, BLUE, 1.5, name="Question A")
    d.box(QB, RED_PALE, RED, 1.5, name="Question B")
    # Row 4: test beds
    d.box(BAND4, TEAL_PALE, TEAL_DARK, 1.5, rounded=False, name="Test beds")

    for (x1, y1, x2, y2, color) in ARROWS:
        d.arrow(x1, y1, x2, y2, color)

    # --- text, row 1
    x, y, w, h = BAND1
    d.text(x + 0.25, y + 0.16, 3.0, [TEXT["band1_title"]], 22, N_BLACK, bold=True, name="Physical AI")
    d.text(x + 0.25, y + 0.60, 5.4, wrap(TEXT["band1_sub"], 14, 5.4), 14, N_DARK, name="Physical AI sub")
    right = wrap(TEXT["band1_right"], 14, 3.2)
    d.text(x + w - 3.45, y + (h - len(right) * 0.235) / 2, 3.2, right, 14, N_DARK, align="r", name="Physical AI right")

    # --- row 2
    x, y, w, h = SUB
    d.text(x + 0.2, y + 0.12, w - 0.4, [TEXT["sub_title"]], 18, TEAL_DARK, bold=True, align="c", name="Substrate title")
    d.text(x + 0.2, y + 0.50, w - 0.4, wrap(TEXT["sub_body"], 14, w - 0.4), 14, N_DARK, align="c", name="Substrate body")

    # --- row 3
    for rect, key, color, png in ((QA, "qa", BLUE, "panel_a_solve.png"), (QB, "qb", RED, "panel_b_gap.png")):
        x, y, w, h = rect
        d.text(x + 0.15, y + 0.12, w - 0.3, [TEXT[f"{key}_title"]], 18, color, bold=True, name=f"{key} title")
        d.text(x + 0.15, y + 0.46, w - 0.3, wrap(TEXT[f"{key}_body"], 14, w - 0.3), 14, N_DARK, name=f"{key} body")
        d.picture(HERE / png, x + 0.15, y + 1.84, PANEL_W, PANEL_H, name=f"{key} panel")
        d.text(x + 0.15, y + 3.30, w - 0.3, wrap(TEXT[f"{key}_cap"], 11, w - 0.3), 11, N_MID, name=f"{key} caption")

    # --- row 4
    x, y, w, h = BAND4
    d.text(x + 0.2, y + 0.10, w - 0.4, [TEXT["band4_head"]], 14, TEAL_DARK, bold=True, align="c", name="Test beds heading")
    d.dotted_vline(x + w / 2, y + 0.48, y + h - 0.15, TEAL)
    for bx, tkey, bkey in ((x + 0.3, "sci_title", "sci_body"), (x + w / 2 + 0.3, "eng_title", "eng_body")):
        bw = w / 2 - 0.6
        d.text(bx, y + 0.46, bw, [TEXT[tkey]], 14, N_BLACK, bold=True, name=tkey)
        d.text(bx, y + 0.74, bw, wrap(TEXT[bkey], 12, bw), 12, N_DARK, name=bkey)


def main():
    p = Pptx(); compose(p); p.save(HERE / "research-overview.pptx")
    s = Svg(); compose(s)
    s.save(HERE / "research-overview.svg",
           "Research overview: from Physical AI to two questions about the governing dynamics of physical systems",
           "Physical AI rests on the governing dynamics of physical systems. Two questions branch from that substrate: "
           "learning to solve the dynamics with neural operators and neural solvers, and the model-to-decision gap, "
           "the effect of learned-model error on control and optimization decisions, which grows near a critical point. "
           "Both are tested on materials processing (science) and on water-energy and industrial processes (engineering).")
    print("wrote research-overview.pptx and research-overview.svg")


if __name__ == "__main__":
    main()
