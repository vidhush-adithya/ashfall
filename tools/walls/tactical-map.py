#!/usr/bin/env python3
"""ASHFALL wallpaper: tactical-map — night topographic sheet with contours, grid, red zone, routes."""
import sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H = 3840, 2160
OUT = sys.argv[1] if len(sys.argv) > 1 else "tactical-map.png"
rng = np.random.default_rng(1983); random.seed(1983)

def fbm(w, h, octaves=6, base=6):
    acc = np.zeros((h, w), np.float32); amp = 1.0; tot = 0
    for o in range(octaves):
        n = base * 2 ** o
        g = rng.random((n + 1, int(n * w / h) + 2)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        acc += amp * (np.asarray(im, np.float32) / 255.0); tot += amp; amp *= 0.5
    return acc / tot

S = 4  # compute heightfield at quarter res, upscale
hf = fbm(W // S, H // S, 6, 3)
hf = (hf - hf.min()) / (hf.max() - hf.min())
hf = Image.fromarray((hf * 65535).astype(np.uint16)).resize((W, H), Image.BICUBIC)
hf = np.asarray(hf, np.float32) / 65535.0

# paper: very dark, faint fibre
paper = np.zeros((H, W, 3), np.float32); paper[:] = (13, 12, 10)
fib = fbm(W // 8, H // 8, 4, 40); fib = np.asarray(Image.fromarray((fib * 255).astype(np.uint8)).resize((W, H)), np.float32) / 255
paper += (fib[..., None] - 0.5) * 10
# subtle elevation tint
paper += (hf[..., None] - 0.5) * np.array([14, 11, 7], np.float32)

# contour lines: where frac(h*levels) near 0
levels = 34
v = hf * levels
frac = np.abs(v - np.round(v))
gy, gx = np.gradient(hf * levels)
grad = np.sqrt(gx ** 2 + gy ** 2) + 1e-6
dist = frac / grad  # pixel distance to contour
idx = np.round(v).astype(int)
index = (idx % 5 == 0)
width = np.where(index, 2.2, 1.1)
line = np.clip(1.0 - dist / width, 0, 1)
col_minor = np.array([92, 84, 70], np.float32)
col_index = np.array([150, 132, 98], np.float32)
col = np.where(index[..., None], col_index, col_minor)
alpha = line * np.where(index, 0.85, 0.55)
img = paper * (1 - alpha[..., None]) + col * alpha[..., None]
img = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(img, "RGBA")

try:
    F = lambda s: ImageFont.truetype("DejaVuSansMono.ttf", s)
    FB = lambda s: ImageFont.truetype("DejaVuSansMono-Bold.ttf", s)
except OSError:
    F = FB = lambda s: ImageFont.load_default()

# grid
step = 240; m = 120
for i, x in enumerate(range(m, W - m + 1, step)):
    d.line([(x, m), (x, H - m)], fill=(110, 102, 87, 70), width=2)
    d.text((x + 8, m - 46), f"{i:02d}", font=F(30), fill=(110, 102, 87, 200))
    d.text((x + 8, H - m + 12), f"{i:02d}", font=F(30), fill=(110, 102, 87, 200))
for j, y in enumerate(range(m, H - m + 1, step)):
    d.line([(m, y), (W - m, y)], fill=(110, 102, 87, 70), width=2)
    lab = chr(65 + j)
    d.text((m - 44, y + 8), lab, font=F(30), fill=(110, 102, 87, 200))
    d.text((W - m + 16, y + 8), lab, font=F(30), fill=(110, 102, 87, 200))
d.rectangle([m, m, W - m, H - m], outline=(110, 102, 87, 160), width=3)

# red zone: irregular polygon, hatched
cx, cy, R = int(W * 0.66), int(H * 0.42), 360
pts = []
for k in range(14):
    a = 2 * math.pi * k / 14
    r = R * (0.75 + 0.35 * random.random())
    pts.append((cx + r * math.cos(a) * 1.25, cy + r * math.sin(a)))
mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).polygon(pts, fill=255)
hatch = Image.new("L", (W, H), 0); hd = ImageDraw.Draw(hatch)
for k in range(-H, W, 26):
    hd.line([(k, 0), (k + H, H)], fill=110, width=3)
hatch = ImageChops.multiply(hatch, mask)
img.paste(Image.new("RGB", (W, H), (122, 51, 41)), (0, 0), hatch)
d = ImageDraw.Draw(img, "RGBA")
d.polygon(pts, outline=(139, 70, 52, 230), width=5)
d.text((cx - 150, cy - 30), "ZONE RED", font=FB(54), fill=(160, 90, 70, 235))
d.text((cx - 150, cy + 34), "CONTAMINATED // AVOID", font=F(28), fill=(150, 100, 80, 200))

# dashed routes
def dashed(path, colr, w=5, dash=36, gap=22):
    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        L = math.hypot(x2 - x1, y2 - y1); n = int(L // (dash + gap)) + 1
        for t in range(n):
            a = t * (dash + gap) / L; b = min(1, (t * (dash + gap) + dash) / L)
            if a >= 1: break
            d.line([(x1 + (x2 - x1) * a, y1 + (y2 - y1) * a), (x1 + (x2 - x1) * b, y1 + (y2 - y1) * b)], fill=colr, width=w)
route1 = [(260, 1820), (700, 1600), (1100, 1640), (1500, 1380), (1900, 1300), (2250, 980), (2780, 900)]
route2 = [(600, 380), (980, 620), (1420, 700), (1820, 980), (1900, 1300)]
dashed(route1, (154, 131, 72, 230)); dashed(route2, (154, 131, 72, 170), 4)
def marker(x, y, kind, label):
    c = (194, 184, 163, 235)
    if kind == "sq": d.rectangle([x - 16, y - 16, x + 16, y + 16], outline=c, width=4)
    elif kind == "tri": d.polygon([(x, y - 20), (x - 18, y + 14), (x + 18, y + 14)], outline=c, width=4)
    else: d.ellipse([x - 16, y - 16, x + 16, y + 16], outline=c, width=4)
    d.text((x + 28, y - 18), label, font=F(28), fill=(168, 159, 140, 220))
marker(260, 1820, "sq", "LZ ALPHA"); marker(1900, 1300, "tri", "RALLY 2")
marker(2780, 900, "o", "OBJ // RELAY"); marker(600, 380, "sq", "OUTPOST 7")

# compass rose
rx, ry = W - 360, H - 380
for a, L in [(0, 150), (90, 110), (180, 110), (270, 110)]:
    ang = math.radians(a - 90)
    tip = (rx + L * math.cos(ang), ry + L * math.sin(ang))
    l = (rx + 22 * math.cos(ang + math.pi / 2), ry + 22 * math.sin(ang + math.pi / 2))
    r = (rx + 22 * math.cos(ang - math.pi / 2), ry + 22 * math.sin(ang - math.pi / 2))
    d.polygon([tip, l, (rx, ry), r], outline=(168, 159, 140, 200), fill=(42, 38, 32, 200) if a else (139, 90, 60, 220))
d.ellipse([rx - 80, ry - 80, rx + 80, ry + 80], outline=(110, 102, 87, 160), width=3)
d.text((rx - 12, ry - 210), "N", font=FB(40), fill=(194, 184, 163, 230))

# stamps
d.text((m + 20, m + 20), "SHEET 7 // RESTRICTED", font=FB(40), fill=(139, 90, 60, 210))
d.text((m + 20, m + 72), "SCALE 1:50 000   CONTOUR INTERVAL 20M   GRID 1KM", font=F(26), fill=(110, 102, 87, 200))
d.text((m + 20, H - m - 60), "ASHFALL CARTOGRAPHIC // REV 4 // DO NOT REPRODUCE", font=F(24), fill=(90, 84, 70, 200))

# grain + vignette
img = img.filter(ImageFilter.GaussianBlur(0.6))
noise = Image.effect_noise((W, H), 18).convert("RGB")
img = Image.blend(img, ImageChops.multiply(img, noise.point(lambda v: 210 + v // 6)), 0.4)
vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).ellipse([-W * .2, -H * .3, W * 1.2, H * 1.3], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(300))
img = Image.composite(img, Image.new("RGB", (W, H), (4, 4, 3)), vig)
img.save(OUT, optimize=True); print("wrote", OUT)
