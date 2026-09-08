"""Quantitative panels for the research overview figure.

Both panels are real computations on toy problems, used to illustrate a relation,
not to report a result. They are exported as SVG (vector, text kept as text) and
as 600 dpi PNG for the PowerPoint source. Sizes are the reserved rectangles in the
figure, in inches, so the panels are inserted 1:1 and never rescaled.

Run:  python3 panels.py
"""
from __future__ import annotations

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Register Arial explicitly (macOS keeps it under Supplemental).
for cand in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/Library/Fonts/Arial.ttf"):
    try:
        font_manager.fontManager.addfont(cand)
        break
    except Exception:
        pass

BLUE = "#0F4D92"
RED = "#B64342"
TEAL_DARK = "#317078"
N_BLACK = "#272727"
N_DARK = "#4D4D4D"
N_MID = "#767676"
N_LIGHT = "#CFCECE"

plt.rcParams.update({
    "font.family": "Arial",
    "font.sans-serif": ["Arial"],
    "svg.fonttype": "none",
    "font.size": 11,
    "axes.labelsize": 11,
    "axes.titlesize": 11,
    "xtick.labelsize": 11,
    "ytick.labelsize": 11,
    "axes.edgecolor": N_MID,
    "axes.labelcolor": N_BLACK,
    "xtick.color": N_MID,
    "ytick.color": N_MID,
    "text.color": N_BLACK,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
})

# Reserved rectangles inside the two question boxes (inches).
PANEL_W, PANEL_H = 4.1, 1.42


def panel_a():
    """A 2D advection-diffusion field solved with an explicit scheme, three times."""
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
        dudx = (u - np.roll(u, 1, 0)) / dx if cx > 0 else (np.roll(u, -1, 0) - u) / dx
        dudy = (u - np.roll(u, 1, 1)) / dx if cy > 0 else (np.roll(u, -1, 1) - u) / dx
        return u + dt * (D * lap - cx * dudx - cy * dudy)

    T = 0.9
    nsteps = int(T / dt)
    frames, times = [u.copy()], [0.0]
    for k in range(1, nsteps + 1):
        u = step(u)
        if k in (nsteps // 2, nsteps):
            frames.append(u.copy())
            times.append(k * dt)

    fig = plt.figure(figsize=(PANEL_W, PANEL_H))
    # three field axes plus a slim colorbar
    left, bottom, h = 0.02, 0.06, 0.74
    w = 0.255
    gap = 0.03
    vmax = frames[0].max()
    axes = []
    for i, (f, t) in enumerate(zip(frames, times)):
        ax = fig.add_axes([left + i * (w + gap), bottom, w, h])
        im = ax.contourf(X, Y, f, levels=np.linspace(0, vmax, 12), cmap="Blues", vmin=0, vmax=vmax)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_edgecolor(N_LIGHT); s.set_linewidth(0.8)
        ax.set_title(f"t = {t:.2f}", pad=3, color=N_DARK)
        ax.set_aspect("equal")
        axes.append(ax)
    cax = fig.add_axes([left + 3 * (w + gap) - 0.005, bottom, 0.022, h])
    cb = fig.colorbar(im, cax=cax, ticks=[0, vmax / 2, vmax])
    cb.ax.set_yticklabels(["0", "0.5", "1"])
    cb.outline.set_edgecolor(N_LIGHT)
    cax.set_title("u", pad=3, color=N_DARK)
    fig.savefig("panel_a_solve.svg")
    fig.savefig("panel_a_solve.png", dpi=600)
    plt.close(fig)


def upper_branch(r: np.ndarray) -> np.ndarray:
    """Operating equilibrium of x' = r + x - x^3: the upper stable branch while it exists,
    the remaining stable branch after the fold."""
    out = np.empty_like(r)
    for i, ri in enumerate(r):
        roots = np.roots([-1.0, 0.0, 1.0, ri])
        real = np.sort(roots[np.abs(roots.imag) < 1e-9].real)
        stable = [v for v in real if 1 - 3 * v * v < 0]   # f'(x) = 1 - 3x^2 < 0
        out[i] = max(stable)
    return out


def panel_b():
    """Decision error caused by a fixed model error, against distance to the fold."""
    r_c = -2.0 / (3.0 * np.sqrt(3.0))       # fold of the upper branch
    delta = 0.01                             # fixed model error in the parameter
    r = np.linspace(r_c + 0.004, r_c + 0.9, 900)
    e = np.abs(upper_branch(r) - upper_branch(r - delta)) / delta
    dist = r - r_c

    fig = plt.figure(figsize=(PANEL_W, PANEL_H))
    ax = fig.add_axes([0.17, 0.28, 0.79, 0.66])
    ax.plot(dist, e, color=RED, lw=2.0)
    ax.axhline(1.0, color=N_MID, lw=0.9, ls=(0, (3, 3)))
    ax.set_yscale("log")
    ax.set_ylim(0.3, 400)
    ax.set_xlim(0, dist.max())
    ax.set_yticks([1, 10, 100])
    ax.set_yticklabels(["1", "10", "100"])
    ax.set_xticks([0, 0.3, 0.6, 0.9])
    ax.set_xlabel("distance to the critical point", labelpad=2)
    ax.set_ylabel("decision error\n/ model error", labelpad=3)
    ax.axvline(0, color=RED, lw=0.9, ls=(0, (2, 2)))
    ax.text(0.03, 170, "critical point", color=RED, ha="left", va="center")
    ax.text(dist.max() * 0.99, 1.35, "same as the model error", color=N_MID, ha="right", va="bottom")
    ax.tick_params(length=2.5, pad=2)
    fig.savefig("panel_b_gap.svg")
    fig.savefig("panel_b_gap.png", dpi=600)
    plt.close(fig)


if __name__ == "__main__":
    panel_a()
    panel_b()
    print("wrote panel_a_solve.{svg,png} and panel_b_gap.{svg,png}")
