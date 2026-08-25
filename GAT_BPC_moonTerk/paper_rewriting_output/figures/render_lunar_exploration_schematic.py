from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


W, H = 2400, 1400
OUT = Path(__file__).with_name("lunar_water_ice_exploration_schematic.png")

NAVY = "#14213D"
INK = "#243247"
MUTED = "#607086"
GRID = "#C9D1D9"
LIGHT = "#F7F8FA"
TERRAIN = "#EEF1F3"
CONTOUR = "#C8CED4"
PSR = "#26384D"
PSR_DARK = "#182638"
RIM = "#E7B64A"
TEAL = "#008B95"
ORANGE = "#E66A12"
ALT = "#7B8490"
PURPLE = "#6554C0"
WHITE = "#FFFFFF"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/{name}", size)


F_TITLE = font(42, True)
F_HEAD = font(34, True)
F_LABEL = font(30, True)
F_BODY = font(27)
F_SMALL = font(23)
F_TINY = font(20)


img = Image.new("RGB", (W, H), WHITE)
draw = ImageDraw.Draw(img)


def text_center(x: float, y: float, txt: str, fnt, fill=INK) -> None:
    box = draw.textbbox((0, 0), txt, font=fnt)
    draw.text((x - (box[2] - box[0]) / 2, y - (box[3] - box[1]) / 2), txt, font=fnt, fill=fill)


def pill(x: int, y: int, txt: str, fnt=F_SMALL, fill=WHITE, outline=GRID, color=INK, pad=12):
    box = draw.textbbox((0, 0), txt, font=fnt)
    w = box[2] - box[0] + 2 * pad
    h = box[3] - box[1] + 2 * pad
    draw.rounded_rectangle((x, y, x + w, y + h), radius=13, fill=fill, outline=outline, width=2)
    draw.text((x + pad, y + pad - 2), txt, font=fnt, fill=color)
    return w, h


def bezier(p0, p1, p2, p3, steps=100):
    pts = []
    for k in range(steps + 1):
        t = k / steps
        u = 1 - t
        x = u**3 * p0[0] + 3 * u**2 * t * p1[0] + 3 * u * t**2 * p2[0] + t**3 * p3[0]
        y = u**3 * p0[1] + 3 * u**2 * t * p1[1] + 3 * u * t**2 * p2[1] + t**3 * p3[1]
        pts.append((x, y))
    return pts


def arrow(points, color, ratio=0.68, size=24):
    i = max(1, min(len(points) - 1, int((len(points) - 1) * ratio)))
    x1, y1 = points[max(0, i - 1)]
    x2, y2 = points[i]
    ang = math.atan2(y2 - y1, x2 - x1)
    tip = (x2, y2)
    left = (x2 - size * math.cos(ang) + size * 0.55 * math.sin(ang),
            y2 - size * math.sin(ang) - size * 0.55 * math.cos(ang))
    right = (x2 - size * math.cos(ang) - size * 0.55 * math.sin(ang),
             y2 - size * math.sin(ang) + size * 0.55 * math.cos(ang))
    draw.polygon([tip, left, right], fill=color)


def route(points, color, width=13, arrow_ratio=0.68):
    draw.line(points, fill=WHITE, width=width + 10, joint="curve")
    draw.line(points, fill=color, width=width, joint="curve")
    arrow(points, color, ratio=arrow_ratio, size=28)


def dashed(points, color=ALT, width=8, dash=22, gap=15, arrow_ratio=0.70):
    distances = [0.0]
    for a, b in zip(points, points[1:]):
        distances.append(distances[-1] + math.dist(a, b))
    total = distances[-1]

    def point_at(d):
        for i in range(1, len(distances)):
            if d <= distances[i]:
                span = distances[i] - distances[i - 1]
                t = 0 if span == 0 else (d - distances[i - 1]) / span
                a, b = points[i - 1], points[i]
                return (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
        return points[-1]

    d = 0.0
    while d < total:
        a = point_at(d)
        b = point_at(min(total, d + dash))
        draw.line([a, b], fill=WHITE, width=width + 6)
        draw.line([a, b], fill=color, width=width)
        d += dash + gap
    arrow(points, color, ratio=arrow_ratio, size=22)


def star(cx, cy, r1=22, r2=10, color=RIM):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        r = r1 if k % 2 == 0 else r2
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw.polygon(pts, fill=color, outline=INK)


def icon_detection(cx, cy, color):
    draw.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=color)
    for r in (16, 27):
        draw.arc((cx - r, cy - r, cx + r, cy + r), 205, 335, fill=color, width=4)
    draw.line((cx, cy, cx + 31, cy), fill=color, width=4)


def icon_sampling(cx, cy, color):
    draw.rounded_rectangle((cx - 13, cy - 27, cx + 13, cy + 27), radius=5, outline=color, width=4)
    draw.line((cx - 10, cy - 4, cx + 10, cy - 4), fill=color, width=4)
    draw.ellipse((cx + 19, cy + 10, cx + 31, cy + 22), fill=color)


def icon_drilling(cx, cy, color):
    draw.rectangle((cx - 13, cy - 28, cx + 13, cy - 18), outline=color, width=4)
    draw.line((cx, cy - 18, cx, cy + 21), fill=color, width=5)
    draw.polygon([(cx - 10, cy + 20), (cx + 10, cy + 20), (cx, cy + 35)], fill=color)


def task_node(x, y, code, task, color, icon, label_pos="above"):
    draw.ellipse((x - 52, y - 52, x + 52, y + 52), fill="#D9DEE4")
    draw.ellipse((x - 48, y - 48, x + 48, y + 48), fill=WHITE, outline=color, width=7)
    icon(x, y, color)
    lines = [code, task]
    if label_pos == "above":
        text_center(x, y - 94, lines[0], F_LABEL)
        text_center(x, y - 60, lines[1], F_BODY)
    elif label_pos == "below":
        text_center(x, y + 74, lines[0], F_LABEL)
        text_center(x, y + 110, lines[1], F_BODY)
    elif label_pos == "right":
        draw.text((x + 68, y - 33), lines[0], font=F_LABEL, fill=INK)
        draw.text((x + 68, y + 3), lines[1], font=F_BODY, fill=INK)


def draw_depot(x, y):
    draw.ellipse((x - 88, y + 48, x + 88, y + 77), fill="#D7DCE1")
    draw.rounded_rectangle((x - 62, y - 62, x + 62, y + 55), radius=14, fill="#DCE4E8", outline=NAVY, width=5)
    draw.polygon([(x - 62, y - 62), (x, y - 94), (x + 62, y - 62)], fill="#EDF2F4", outline=NAVY)
    draw.rounded_rectangle((x - 18, y + 2, x + 20, y + 55), radius=5, fill="#7B8FA3", outline=NAVY, width=3)
    draw.ellipse((x - 26, y - 47, x + 26, y - 13), fill=WHITE, outline=TEAL, width=4)
    draw.line((x, y - 94, x, y - 132), fill=NAVY, width=4)
    draw.ellipse((x - 6, y - 140, x + 6, y - 128), fill=RIM, outline=NAVY)
    # rover
    rx, ry = x - 125, y + 32
    draw.rectangle((rx - 42, ry - 28, rx + 42, ry + 18), fill="#C9D2D9", outline=NAVY, width=4)
    draw.rectangle((rx - 24, ry - 53, rx + 18, ry - 28), fill="#E9EEF1", outline=NAVY, width=3)
    for wx in (rx - 37, rx + 37):
        for wy in (ry + 25,):
            draw.ellipse((wx - 18, wy - 13, wx + 18, wy + 13), fill=NAVY)
    draw.line((rx + 8, ry - 53, rx + 8, ry - 78), fill=NAVY, width=3)
    draw.ellipse((rx + 1, ry - 85, rx + 15, ry - 71), fill=TEAL, outline=NAVY)


# Panel structure
draw.rounded_rectangle((35, 30, 1855, 1365), radius=22, fill=LIGHT, outline="#D8DEE5", width=3)
draw.line((1885, 60, 1885, 1340), fill="#D8DEE5", width=3)
draw.text((75, 58), "(a) Multi-trip lunar exploration", font=F_TITLE, fill=NAVY)
draw.text((1925, 58), "(b) Route-choice factors", font=F_HEAD, fill=NAVY)

# Lunar surface and contours
terrain_poly = [(70, 310), (230, 190), (530, 130), (910, 115), (1320, 135), (1680, 230),
                (1810, 500), (1790, 860), (1660, 1160), (1320, 1280), (900, 1310),
                (520, 1280), (190, 1170), (70, 900)]
draw.polygon(terrain_poly, fill=TERRAIN, outline="#BAC2CA")
for inset in range(0, 7):
    box = (210 + inset * 55, 155 + inset * 35, 1740 - inset * 45, 1240 - inset * 34)
    draw.arc(box, 195, 348, fill=CONTOUR, width=3)
    draw.arc(box, 18, 165, fill=CONTOUR, width=3)

# Small craters
for cx, cy, rx, ry in [(205, 410, 52, 24), (345, 255, 32, 17), (520, 1160, 43, 19),
                       (1020, 185, 38, 18), (1680, 1040, 55, 24), (1740, 450, 35, 16),
                       (1320, 1200, 28, 14), (280, 900, 28, 14)]:
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill="#D3D8DD", outline="#AEB7C0", width=3)
    draw.arc((cx - rx + 6, cy - ry + 4, cx + rx - 6, cy + ry - 4), 185, 345, fill=WHITE, width=4)

# Main crater and permanently shadowed region
draw.ellipse((500, 235, 1695, 1045), fill="#D7DDE1", outline="#9BA8B4", width=5)
draw.ellipse((565, 300, 1630, 975), fill=PSR, outline=NAVY, width=6)
draw.ellipse((690, 370, 1540, 905), fill=PSR_DARK)
draw.arc((505, 238, 1690, 1042), 195, 350, fill=RIM, width=20)
draw.arc((505, 238, 1690, 1042), 12, 158, fill="#F0D27D", width=13)
draw.arc((620, 335, 1570, 920), 190, 345, fill="#43556A", width=5)
draw.arc((740, 410, 1490, 855), 195, 338, fill="#526478", width=4)

# Rough-terrain symbols
rng = random.Random(12)
for _ in range(55):
    cx = rng.randint(1130, 1540)
    cy = rng.randint(570, 880)
    if ((cx - 1350) / 310) ** 2 + ((cy - 720) / 210) ** 2 < 1:
        r = rng.randint(5, 15)
        draw.ellipse((cx - r, cy - r * 0.65, cx + r, cy + r * 0.65), fill="#647386", outline="#182638")

# Environment labels
pill(1060, 295, "Permanently shadowed region (PSR)", F_SMALL, fill="#EEF2F5", outline=NAVY)
pill(1280, 475, "Rough terrain", F_SMALL, fill="#EEF2F5", outline=NAVY)
pill(760, 180, "Illuminated crater rim", F_SMALL, fill="#FFF8E5", outline=RIM)

# Low-angle sunlight cue
sun_x, sun_y = 160, 175
draw.ellipse((sun_x - 25, sun_y - 25, sun_x + 25, sun_y + 25), fill=RIM, outline="#9C7617", width=3)
for a in range(0, 360, 45):
    rad = math.radians(a)
    draw.line((sun_x + 35 * math.cos(rad), sun_y + 35 * math.sin(rad),
               sun_x + 56 * math.cos(rad), sun_y + 56 * math.sin(rad)), fill=RIM, width=5)
sun_arrow = [(215, 205), (360, 300), (510, 350)]
draw.line(sun_arrow, fill=RIM, width=7)
arrow(sun_arrow, RIM, ratio=0.98, size=23)
draw.text((80, 235), "Low-angle illumination", font=F_TINY, fill=MUTED)

# Key locations
DEPOT = (270, 1050)
T1 = (430, 655)
T2 = (845, 245)
T3 = (820, 1040)
T4 = (1510, 885)
T5 = (1580, 420)

# Trip 1: depot -> T1 -> T2 -> depot
trip1_a = bezier((300, 1015), (320, 900), (360, 740), (395, 690))
trip1_b = bezier((465, 620), (560, 475), (710, 335), (810, 275))
trip1_c = bezier((815, 215), (580, 80), (180, 165), (135, 520))
trip1_c += bezier((135, 520), (100, 755), (160, 930), (235, 1020))[1:]
route(trip1_a, TEAL, arrow_ratio=0.65)
route(trip1_b, TEAL, arrow_ratio=0.62)
route(trip1_c, TEAL, arrow_ratio=0.78)

# Trip 2: depot -> T3 -> T4 -> T5 -> depot
trip2_a = bezier((315, 1060), (470, 1085), (635, 1085), (775, 1050))
trip2_b = bezier((870, 1025), (1030, 940), (1290, 945), (1465, 900))
trip2_c = bezier((1530, 835), (1600, 700), (1620, 560), (1592, 470))
trip2_d = bezier((1620, 395), (1810, 560), (1810, 1110), (1390, 1240))
trip2_d += bezier((1390, 1240), (980, 1360), (500, 1300), (295, 1090))[1:]
route(trip2_a, ORANGE, arrow_ratio=0.65)
route(trip2_b, ORANGE, arrow_ratio=0.63)
route(trip2_c, ORANGE, arrow_ratio=0.60)
route(trip2_d, ORANGE, arrow_ratio=0.78)
arrow(trip2_d, ORANGE, ratio=0.43, size=28)

# Two alternatives between T3 and T4
alt_shadow = bezier((855, 1008), (980, 720), (1260, 650), (1470, 855))
alt_rim = bezier((855, 1070), (1020, 1230), (1330, 1190), (1480, 930))
dashed(alt_shadow, ALT, width=8, arrow_ratio=0.63)
dashed(alt_rim, "#A1A9B2", width=8, arrow_ratio=0.63)

# Route annotations
pill(315, 370, "Trip 1", F_LABEL, fill="#E8F6F6", outline=TEAL, color=TEAL)
pill(455, 1110, "Trip 2", F_LABEL, fill="#FFF1E8", outline=ORANGE, color=ORANGE)
pill(1005, 695, "shorter • more shadow / roughness", F_TINY, fill=WHITE, outline=ALT)
pill(1050, 1180, "longer detour • lower terrain risk", F_TINY, fill=WHITE, outline="#A1A9B2")

# Depot and task nodes on top of routes
draw_depot(*DEPOT)
draw.text((135, 1160), "Support depot", font=F_LABEL, fill=NAVY)
draw.rounded_rectangle((305, 1004, 365, 1064), radius=12, fill=WHITE, outline=TEAL, width=4)
draw.polygon([(335, 1015), (319, 1042), (334, 1042), (326, 1055), (351, 1030), (337, 1030)], fill=TEAL)
draw.text((375, 1018), "Recharge", font=F_BODY, fill=INK)
task_node(*T1, "T1", "Detection", TEAL, icon_detection, "above")
task_node(*T2, "T2", "Sampling", TEAL, icon_sampling, "above")
task_node(*T3, "T3", "Drilling", ORANGE, icon_drilling, "below")
task_node(*T4, "T4", "Detection", ORANGE, icon_detection, "below")
task_node(*T5, "T5", "Sampling", ORANGE, icon_sampling, "right")

# Operational semantics callouts
draw.rounded_rectangle((75, 1238, 730, 1328), radius=18, fill=WHITE, outline=TEAL, width=3)
draw.text((100, 1253), "Depot: waiting, docking and recharging allowed", font=F_SMALL, fill=NAVY)
draw.text((100, 1287), "Task nodes: arrival → immediate service", font=F_SMALL, fill=NAVY)

# Right legend panel
legend_x = 1940
factor_y = 150
factor_gap = 112


def factor_icon(y, kind, color):
    cx = legend_x + 35
    draw.ellipse((cx - 34, y - 34, cx + 34, y + 34), fill=WHITE, outline=color, width=4)
    if kind == "clock":
        draw.ellipse((cx - 19, y - 19, cx + 19, y + 19), outline=color, width=3)
        draw.line((cx, y, cx, y - 13), fill=color, width=4)
        draw.line((cx, y, cx + 12, y + 8), fill=color, width=4)
    elif kind == "battery":
        draw.rectangle((cx - 14, y - 19, cx + 14, y + 20), outline=color, width=4)
        draw.rectangle((cx - 5, y - 25, cx + 5, y - 19), fill=color)
        draw.rectangle((cx - 8, y - 10, cx + 8, y + 14), fill=color)
    elif kind == "risk":
        draw.polygon([(cx, y - 23), (cx - 24, y + 20), (cx + 24, y + 20)], fill="#FFF0E8", outline=color)
        draw.line((cx, y - 9, cx, y + 7), fill=color, width=5)
        draw.ellipse((cx - 3, y + 12, cx + 3, y + 18), fill=color)
    elif kind == "shadow":
        draw.pieslice((cx - 21, y - 21, cx + 21, y + 21), 90, 270, fill=PSR_DARK)
        draw.arc((cx - 21, y - 21, cx + 21, y + 21), 0, 360, fill=color, width=3)
    elif kind == "window":
        draw.rectangle((cx - 20, y - 17, cx + 20, y + 20), outline=color, width=4)
        draw.line((cx - 20, y - 6, cx + 20, y - 6), fill=color, width=4)
        for dx in (-10, 0, 10):
            draw.ellipse((cx + dx - 2, y + 5, cx + dx + 2, y + 9), fill=color)
    elif kind == "star":
        star(cx, y, 23, 10, RIM)


factors = [
    ("Travel time", "clock", NAVY),
    ("Energy", "battery", TEAL),
    ("Risk", "risk", ORANGE),
    ("Shadow exposure", "shadow", NAVY),
    ("Task window", "window", PURPLE),
    ("Science value", "star", "#9B7619"),
]
for idx, (label, kind, color) in enumerate(factors):
    y = factor_y + idx * factor_gap
    factor_icon(y, kind, color)
    draw.text((legend_x + 92, y - 19), label, font=F_BODY, fill=INK)

draw.line((1930, 825, 2325, 825), fill=GRID, width=3)
draw.text((1935, 855), "Route styles", font=F_LABEL, fill=NAVY)
draw.line((1950, 930, 2040, 930), fill=TEAL, width=12)
arrow([(1950, 930), (2040, 930)], TEAL, ratio=0.95, size=22)
draw.text((2070, 910), "Trip 1 (selected)", font=F_SMALL, fill=INK)
draw.line((1950, 995, 2040, 995), fill=ORANGE, width=12)
arrow([(1950, 995), (2040, 995)], ORANGE, ratio=0.95, size=22)
draw.text((2070, 975), "Trip 2 (selected)", font=F_SMALL, fill=INK)
dashed([(1950, 1060), (2040, 1060)], ALT, width=7, dash=16, gap=12, arrow_ratio=0.95)
draw.text((2070, 1040), "Candidate alternative", font=F_SMALL, fill=INK)

draw.rounded_rectangle((1925, 1130, 2335, 1305), radius=18, fill="#F1F5F7", outline=GRID, width=3)
draw.text((1955, 1160), "Fixed mission epoch", font=F_LABEL, fill=NAVY)
draw.text((1955, 1206), "Path attributes remain", font=F_SMALL, fill=MUTED)
draw.text((1955, 1240), "constant within one solve.", font=F_SMALL, fill=MUTED)

# Export at publication-friendly resolution metadata.
img.save(OUT, format="PNG", dpi=(300, 300), optimize=True)
print(OUT)
