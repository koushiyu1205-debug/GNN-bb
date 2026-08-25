"""Draw a deterministic journal-style lunar exploration scenario schematic."""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, PathPatch, Polygon, Rectangle
from matplotlib.path import Path as MplPath


OUT = Path(__file__).with_name("lunar_water_ice_exploration_schematic_v2.png")

INK = "#263238"
MID = "#7B8790"
LIGHT = "#C7CDD2"
TEAL = "#007F86"
ORANGE = "#D95F02"
ROUGH = "#D8B55B"
PSR = "#3F4850"


def arrow(ax, start, end, color, rad=0.0, lw=2.0, zorder=8):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=lw,
        color=color,
        connectionstyle=f"arc3,rad={rad}",
        shrinkA=5,
        shrinkB=5,
        zorder=zorder,
    )
    patch.set_path_effects([pe.Stroke(linewidth=lw + 2.2, foreground="white"), pe.Normal()])
    ax.add_patch(patch)


def curved_route(ax, vertices, color, lw=2.0, zorder=7):
    path = MplPath(vertices, [MplPath.MOVETO] + [MplPath.CURVE4] * (len(vertices) - 1))
    patch = PathPatch(path, fill=False, color=color, linewidth=lw, zorder=zorder)
    patch.set_path_effects([pe.Stroke(linewidth=lw + 2.2, foreground="white"), pe.Normal()])
    ax.add_patch(patch)
    # A separate final arrowhead makes the direction independently auditable.
    p0 = vertices[-2]
    p1 = vertices[-1]
    head = FancyArrowPatch(
        p0,
        p1,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=lw,
        color=color,
        shrinkA=0,
        shrinkB=5,
        zorder=zorder + 1,
    )
    head.set_path_effects([pe.Stroke(linewidth=lw + 2.2, foreground="white"), pe.Normal()])
    ax.add_patch(head)


def node(ax, xy, name, subtype=None, label_offset=(0, 1.6), align="center"):
    ax.add_patch(Circle(xy, 0.58, facecolor="white", edgecolor=INK, linewidth=1.25, zorder=10))
    x, y = xy
    tx = x + label_offset[0]
    ty = y + label_offset[1]
    ax.text(tx, ty, name, ha=align, va="bottom", fontsize=9.2, fontweight="semibold", color=INK, zorder=11)
    if subtype:
        ax.text(tx, ty - 0.15, f"\n{subtype}", ha=align, va="top", fontsize=7.7, color=INK, zorder=11)


def irregular_contour(ax, cx, cy, rx, ry, phase=0.0, ls="-", alpha=1.0):
    t = np.linspace(0, 2 * np.pi, 360)
    ripple = 1 + 0.035 * np.sin(5 * t + phase) + 0.018 * np.sin(9 * t - phase)
    x = cx + rx * ripple * np.cos(t)
    y = cy + ry * ripple * np.sin(t)
    ax.plot(x, y, color=LIGHT, linewidth=0.65, linestyle=ls, alpha=alpha, zorder=0)


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 8.5,
        "axes.linewidth": 0.0,
    }
)

fig, ax = plt.subplots(figsize=(13.5, 7.6), dpi=300)
fig.patch.set_facecolor("white")
ax.set_xlim(0, 100)
ax.set_ylim(0, 62)
ax.set_aspect("equal")
ax.axis("off")

# Panel guides and headings.
ax.plot([75.5, 75.5], [14, 59.5], color=LIGHT, linewidth=0.8, zorder=0)
ax.plot([2.5, 97.5], [12.2, 12.2], color=LIGHT, linewidth=0.8, zorder=0)
ax.text(2.6, 60.0, "(a) Lunar multi-trip task network", fontsize=11.2, fontweight="semibold", color=INK)
ax.text(78.0, 60.0, "(b) Candidate-path choice", fontsize=11.2, fontweight="semibold", color=INK)
ax.text(2.6, 10.6, "(c) Operational sequence", fontsize=10.2, fontweight="semibold", color=INK)

# Restrained terrain context.
boundary_t = np.linspace(0, 2 * np.pi, 420)
boundary_r = 1 + 0.028 * np.sin(6 * boundary_t) + 0.018 * np.sin(11 * boundary_t + 0.8)
bx = 37.8 + 35.0 * boundary_r * np.cos(boundary_t)
by = 36.2 + 22.6 * boundary_r * np.sin(boundary_t)
ax.fill(bx, by, color="#FBFCFC", zorder=-2)
ax.plot(bx, by, color=LIGHT, linewidth=0.8, zorder=-1)
for rx, ry, phase in [(31.5, 19.8, 0.3), (27.0, 16.5, 1.1), (22.2, 13.2, 2.0), (17.2, 10.0, 2.6)]:
    irregular_contour(ax, 37.8, 36.2, rx, ry, phase)

# Small secondary craters, drawn as quiet topographic context rather than decoration.
for cx, cy, rx, ry in [
    (14, 50, 2.7, 1.6),
    (20, 25, 2.2, 1.5),
    (30, 45, 2.5, 1.4),
    (43, 17, 2.8, 1.4),
    (54, 51, 2.4, 1.5),
    (62, 27, 2.5, 1.4),
    (67, 49, 2.1, 1.3),
]:
    irregular_contour(ax, cx, cy, rx, ry, phase=cx / 10)
    irregular_contour(ax, cx, cy, rx * 0.55, ry * 0.55, phase=cy / 10, ls="--", alpha=0.8)

# Permanently shadowed and rough-terrain regions.
psr_vertices = [
    (27, 46),
    (32, 51),
    (40, 50),
    (45, 45),
    (43, 39),
    (47, 34),
    (44, 27),
    (36, 23),
    (29, 26),
    (25, 33),
    (23, 40),
]
ax.add_patch(Polygon(psr_vertices, closed=True, facecolor=PSR, edgecolor=INK, linewidth=0.9, zorder=1))
ax.text(35.8, 37.5, "PSR", ha="center", va="center", color="white", fontsize=9.4, fontweight="semibold", zorder=2)

rough_vertices = [(48, 46), (56, 49), (64, 43), (66, 35), (62, 27), (54, 25), (47, 30), (45, 38)]
ax.add_patch(
    Polygon(
        rough_vertices,
        closed=True,
        facecolor="#FBF7EC",
        edgecolor=ROUGH,
        linewidth=0.8,
        hatch="////",
        zorder=1,
    )
)
ax.text(56.4, 36.4, "rough terrain", ha="center", va="center", color=INK, fontsize=8.2, zorder=2)

# Task and depot locations.
depot = (7.2, 19.2)
t1 = (18.0, 37.0)
t2 = (32.0, 52.5)
t3 = (33.0, 18.3)
t4 = (58.2, 20.2)
t5 = (67.2, 42.2)

ax.add_patch(Rectangle((depot[0] - 0.75, depot[1] - 0.75), 1.5, 1.5, facecolor="white", edgecolor=INK, linewidth=1.35, zorder=10))
ax.text(depot[0], depot[1] - 1.8, "Depot", ha="center", va="top", fontsize=8.6, fontweight="semibold", color=INK)
node(ax, t1, "T1", "detection", label_offset=(-1.5, 1.1), align="right")
node(ax, t2, "T2", "sampling", label_offset=(0, 1.2))
node(ax, t3, "T3", "drilling", label_offset=(-1.3, 1.0), align="right")
node(ax, t4, "T4", label_offset=(0, 1.3))
node(ax, t5, "T5", label_offset=(0, 1.3))

# Trip 1: Depot -> T1 -> T2 -> Depot. Each directed leg is drawn explicitly.
arrow(ax, depot, t1, TEAL, rad=-0.04)
arrow(ax, t1, t2, TEAL, rad=0.0)
curved_route(
    ax,
    [t2, (25.0, 57.5), (17.0, 56.0), (12.5, 50.0), (8.5, 43.0), (8.5, 28.0), depot],
    TEAL,
)
ax.text(12.0, 46.3, "Trip 1", color=TEAL, fontsize=9.1, fontweight="semibold", zorder=12)

# Trip 2: Depot -> T3 -> T4 -> T5 -> Depot. T4--T5 is the selected candidate path.
arrow(ax, depot, t3, ORANGE, rad=0.06)
arrow(ax, t3, t4, ORANGE, rad=-0.05)
arrow(ax, t4, t5, ORANGE, rad=-0.13)
curved_route(
    ax,
    [
        t5,
        (71.5, 50.0),
        (69.5, 55.5),
        (63.0, 57.0),
        (47.0, 59.0),
        (20.0, 59.0),
        (9.0, 53.5),
        (3.5, 46.0),
        (3.5, 29.0),
        depot,
    ],
    ORANGE,
)
ax.text(43.5, 16.0, "Trip 2", color=ORANGE, fontsize=9.1, fontweight="semibold", zorder=12)

# Candidate-path inset: one selected path and two alternatives for the same ordered pair.
u = (80.0, 49.0)
v = (95.0, 49.0)
ax.add_patch(Circle(u, 0.50, facecolor="white", edgecolor=INK, linewidth=1.15, zorder=10))
ax.add_patch(Circle(v, 0.50, facecolor="white", edgecolor=INK, linewidth=1.15, zorder=10))
ax.text(u[0], u[1] - 1.5, "T4", ha="center", va="top", fontsize=8.3, color=INK)
ax.text(v[0], v[1] - 1.5, "T5", ha="center", va="top", fontsize=8.3, color=INK)
arrow(ax, u, v, ORANGE, rad=-0.02, lw=1.8)
alt_top = FancyArrowPatch(u, v, arrowstyle="-", linewidth=1.25, color=MID, connectionstyle="arc3,rad=-0.34", shrinkA=5, shrinkB=5, zorder=5)
alt_bottom = FancyArrowPatch(u, v, arrowstyle="-", linewidth=1.25, linestyle=(0, (4, 3)), color=MID, connectionstyle="arc3,rad=0.30", shrinkA=5, shrinkB=5, zorder=5)
ax.add_patch(alt_top)
ax.add_patch(alt_bottom)

ax.text(78.0, 42.0, "Path attributes", fontsize=8.7, fontweight="semibold", color=INK)
rows = [
    (r"$\tau^{\omega}$", "travel time"),
    (r"$e^{\omega}$", "energy"),
    (r"$\rho^{\omega}$", "risk"),
    (r"$h^{\omega}$", "shadow exposure"),
]
for idx, (symbol, label) in enumerate(rows):
    yy = 39.7 - idx * 2.35
    ax.text(79.0, yy, symbol, fontsize=9.0, color=INK, ha="left", va="center")
    ax.text(83.0, yy, label, fontsize=8.1, color=INK, ha="left", va="center")

ax.text(78.0, 29.0, "Task attributes", fontsize=8.7, fontweight="semibold", color=INK)
ax.text(79.0, 26.7, r"$[r_i,D_i]$", fontsize=8.8, color=INK, ha="left", va="center")
ax.text(84.0, 26.7, "task window", fontsize=8.1, color=INK, ha="left", va="center")
ax.text(79.0, 24.3, r"$w_i$", fontsize=8.8, color=INK, ha="left", va="center")
ax.text(84.0, 24.3, "science weight", fontsize=8.1, color=INK, ha="left", va="center")

# Compact visual key, without icon cards.
ax.plot([79.0, 83.0], [20.55, 20.55], color=TEAL, linewidth=2.0)
ax.plot([79.0, 83.0], [20.05, 20.05], color=ORANGE, linewidth=2.0)
ax.text(84.0, 20.3, "selected trips", va="center", fontsize=7.9, color=INK)
ax.plot([79.0, 83.0], [18.0, 18.0], color=MID, linewidth=1.25, linestyle=(0, (4, 3)))
ax.text(84.0, 18.0, "alternative path", va="center", fontsize=7.9, color=INK)
ax.text(78.0, 14.9, "Path attributes are fixed\nwithin one mission epoch.", fontsize=7.4, color=MID, va="top", linespacing=1.25)

# Bottom operational sequence.
stages = [
    (6.0, "depot departure"),
    (28.0, "immediate task service"),
    (55.5, "return & recharge"),
    (80.0, "next trip"),
]
for x, text_label in stages:
    ax.text(x, 7.0, text_label, fontsize=8.3, color=INK, ha="center", va="center")
for x0, x1 in [(13.0, 20.5), (38.5, 47.2), (64.0, 72.5)]:
    ax.add_patch(
        FancyArrowPatch(
            (x0, 7.0),
            (x1, 7.0),
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=1.0,
            color=INK,
            shrinkA=0,
            shrinkB=0,
            zorder=4,
        )
    )
ax.text(
    50.0,
    3.9,
    "No waiting at task nodes or en route; trip departure may be delayed at the depot.",
    ha="center",
    va="center",
    fontsize=7.9,
    color=INK,
)

fig.savefig(OUT, dpi=300, bbox_inches="tight", pad_inches=0.04, facecolor="white")
print(OUT)
