"""Three computed panels for the research architecture figure.

Each panel is a real computation on a toy problem and illustrates one relation.
They are exported as SVG with text kept as text, so the page font applies once
the SVG is embedded inline. Sizes are the reserved rectangles in the figure.

Run:  python3 panels.py
"""
from __future__ import annotations

import re

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap

for cand in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"):
    try:
        font_manager.fontManager.addfont(cand)
        break
    except Exception:
        pass

# Direction colours, from the top-conference figure library
PURPLE = "#9467BD"   # A: physical systems (CLIP variant purple)
TEAL = "#31859A"     # B: neural solver (ControlNet trainable edge)
CORAL = "#EA7F6F"    # C: decision and the model-to-decision gap (MAE decoder)
INK = "#4D4D4D"
INK_LIGHT = "#9A9A9A"
RULE = "#D9D9D9"

plt.rcParams.update({
    "font.family": "Arial",
    "font.sans-serif": ["Arial"],
    "svg.fonttype": "none",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 10,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "axes.edgecolor": INK_LIGHT,
    "axes.labelcolor": INK,
    "xtick.color": INK_LIGHT,
    "ytick.color": INK_LIGHT,
    "text.color": INK,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

W, H = 3.3, 1.55   # inches, inserted 1:1


def save(fig, name):
    fig.savefig(name, format="svg")
    plt.close(fig)
    s = open(name, encoding="utf-8").read()
    # the page loads IBM Plex Sans; Arial stays as the fallback and the layout metric
    s = re.sub(r"font-family:\s*'?Arial'?", "font-family: 'IBM Plex Sans', Arial, sans-serif", s)
    s = s.replace("font: 10px 'Arial'", "font: 10px 'IBM Plex Sans', Arial, sans-serif")
    open(name, "w", encoding="utf-8").write(s)


def panel_a_signals():
    """One day of urban water demand and day-ahead electricity price, illustrative."""
    t = np.linspace(0, 24, 289)
    demand = (0.55 + 0.30 * np.exp(-((t - 7.5) ** 2) / 2.2) + 0.38 * np.exp(-((t - 19.5) ** 2) / 3.0)
              - 0.18 * np.exp(-((t - 3.0) ** 2) / 6.0))
    price = 0.45 + 0.42 * np.exp(-((t - 17.0) ** 2) / 9.0) + 0.10 * np.exp(-((t - 9.0) ** 2) / 4.0) - 0.12 * np.exp(-((t - 4.0) ** 2) / 8.0)
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.13, 0.28, 0.84, 0.66])
    ax.plot(t, demand, color=PURPLE, lw=2.0, label="water demand")
    ax.plot(t, price, color=PURPLE, lw=1.6, ls=(0, (4, 3)), alpha=0.75, label="electricity price")
    ax.set_xlim(0, 24); ax.set_xticks([0, 6, 12, 18, 24])
    ax.set_ylim(0.2, 1.05); ax.set_yticks([])
    ax.set_xlabel("hour of day", labelpad=2)
    ax.set_ylabel("normalized", labelpad=4)
    ax.legend(loc="upper left", frameon=False, handlelength=1.6, borderaxespad=0.2, labelspacing=0.2)
    ax.tick_params(length=2.5, pad=2)
    save(fig, "panel_a_signals.svg")


def panel_b_rollout():
    """A 2D advection-diffusion field solved with an explicit upwind scheme, three times."""
    n, L = 96, 1.0
    dx = L / n
    D, cx, cy = 0.004, 0.55, 0.25
    dt = 0.35 * min(dx * dx / (4 * D), dx / (abs(cx) + abs(cy)))
    x = (np.arange(n) + 0.5) * dx
    X, Y = np.meshgrid(x, x, indexing="ij")
    u = np.exp(-((X - 0.28) ** 2 + (Y - 0.35) ** 2) / (2 * 0.06 ** 2))
    u += 0.6 * np.exp(-((X - 0.5) ** 2 + (Y - 0.7) ** 2) / (2 * 0.05 ** 2))

    def step(u):
        lap = (np.roll(u, 1, 0) + np.roll(u, -1, 0) + np.roll(u, 1, 1) + np.roll(u, -1, 1) - 4 * u) / dx ** 2
        dudx = (u - np.roll(u, 1, 0)) / dx
        dudy = (u - np.roll(u, 1, 1)) / dx
        return u + dt * (D * lap - cx * dudx - cy * dudy)

    T = 0.9
    nsteps = int(T / dt)
    frames, times = [u.copy()], [0.0]
    for k in range(1, nsteps + 1):
        u = step(u)
        if k in (nsteps // 2, nsteps):
            frames.append(u.copy()); times.append(k * dt)

    cmap = LinearSegmentedColormap.from_list("teal", ["#FFFFFF", "#BEDCE4", TEAL, "#1B4F5C"])
    fig = plt.figure(figsize=(W, H))
    left, bottom, h, w, gap = 0.03, 0.06, 0.70, 0.245, 0.035
    vmax = frames[0].max()
    for i, (f, t) in enumerate(zip(frames, times)):
        ax = fig.add_axes([left + i * (w + gap), bottom, w, h])
        im = ax.contourf(X, Y, f, levels=np.linspace(0, vmax, 12), cmap=cmap, vmin=0, vmax=vmax)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_edgecolor(RULE); s.set_linewidth(0.8)
        ax.set_title(f"t = {t:.2f}", pad=3, color=INK)
        ax.set_aspect("equal")
    cax = fig.add_axes([left + 3 * (w + gap) - 0.008, bottom, 0.025, h])
    cb = fig.colorbar(im, cax=cax, ticks=[0, vmax / 2, vmax])
    cb.ax.set_yticklabels(["0", "0.5", "1"])
    cb.outline.set_edgecolor(RULE)
    cax.set_title("u", pad=3, color=INK)
    save(fig, "panel_b_rollout.svg")


def upper_branch(r):
    out = np.empty_like(r)
    for i, ri in enumerate(r):
        roots = np.roots([-1.0, 0.0, 1.0, ri])
        real = np.sort(roots[np.abs(roots.imag) < 1e-9].real)
        stable = [v for v in real if 1 - 3 * v * v < 0]
        out[i] = max(stable)
    return out


def panel_c_gap():
    """Decision error per unit model error against distance to the fold of x' = r + x - x^3."""
    r_c = -2.0 / (3.0 * np.sqrt(3.0))
    delta = 0.01
    r = np.linspace(r_c + 0.004, r_c + 0.9, 900)
    e = np.abs(upper_branch(r) - upper_branch(r - delta)) / delta
    dist = r - r_c
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.13, 0.28, 0.83, 0.66])
    ax.plot(dist, e, color=CORAL, lw=2.0)
    ax.axhline(1.0, color=INK_LIGHT, lw=0.9, ls=(0, (3, 3)))
    ax.set_yscale("log"); ax.set_ylim(0.3, 400)
    ax.set_xlim(0, dist.max())
    ax.set_yticks([1, 10, 100]); ax.set_yticklabels(["1", "10", "100"])
    ax.set_xticks([0, 0.3, 0.6, 0.9])
    ax.set_xlabel("distance to the critical point", labelpad=2)
    ax.axvline(0, color=CORAL, lw=0.9, ls=(0, (2, 2)))
    ax.text(0.035, 190, "decision error / model error", color=INK, ha="left", va="center")
    ax.text(0.035, 22, "critical point", color=INK, ha="left", va="center")
    ax.text(dist.max() * 0.99, 1.35, "equal to the model error", color=INK_LIGHT, ha="right", va="bottom")
    ax.tick_params(length=2.5, pad=2)
    save(fig, "panel_c_gap.svg")


if __name__ == "__main__":
    panel_a_signals(); panel_b_rollout(); panel_c_gap()
    print("wrote panel_a_signals.svg, panel_b_rollout.svg, panel_c_gap.svg")
