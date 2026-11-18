#!/usr/bin/env python3
"""ASHFALL wallpaper: radar-sweep — dim phosphor PPI scope with sweep, blips, bezel."""
import sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H = 3840, 2160
OUT = sys.argv[1] if len(sys.argv) > 1 else "radar-sweep.png"
random.seed(4040)
BG = (8, 10, 7); RING = (47, 60, 40); DIM = (79, 97, 69); MID = (95, 127, 79); HI = (143, 168, 131); AMB = (163, 168, 106)
try:
    F = lambda s: ImageFont.truetype("DejaVuSansMono.ttf", s)
    FB = lambda s: ImageFont.truetype("DejaVuSansMono-Bold.ttf", s)
except OSError:
    F = FB = lambda s: ImageFont.load_default()

img = Image.new("RGB", (W, H), BG)
cx, cy, R = W // 2, H // 2 + 20, 940

# sweep wedge: angular falloff behind the beam
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
dx, dy = xx - cx, yy - cy
r = np.sqrt(dx * dx + dy * dy)
ang = (np.degrees(np.arctan2(dy, dx)) + 360) % 360
beam = 312.0
behind = (beam - ang) % 360
glow = np.exp(-behind / 38.0) * (r < R)
glowimg = np.zeros((H, W, 3), np.float32)
glowimg += glow[..., None] * np.array([28, 46, 26], np.float32)
# faint scope fill
glowimg += (r < R)[..., None] * np.array([3, 6, 3], np.float32)
img = Image.fromarray(np.clip(np.asarray(img, np.float32) + glowimg, 0, 255).astype(np.uint8))
d = ImageDraw.Draw(img, "RGBA")

# range rings + labels
for k in range(1, 5):
    rr = R * k / 4
    d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=RING + (255,), width=3 if k == 4 else 2)
    d.text((cx + 10, cy - rr + 8), f"{k*10}KM", font=F(26), fill=DIM + (220,))
# cross hairs
d.line([(cx - R, cy), (cx + R, cy)], fill=RING + (200,), width=2)
d.line([(cx, cy - R), (cx, cy + R)], fill=RING + (200,), width=2)
# bearing ticks
for deg in range(0, 360, 5):
    a = math.radians(deg - 90)
    L = 34 if deg % 30 == 0 else (18 if deg % 10 == 0 else 10)
    x1, y1 = cx + R * math.cos(a), cy + R * math.sin(a)
    x2, y2 = cx + (R + L) * math.cos(a), cy + (R + L) * math.sin(a)
    d.line([(x1, y1), (x2, y2)], fill=DIM + (230,), width=3 if deg % 30 == 0 else 2)
    if deg % 30 == 0:
        tx, ty = cx + (R + 76) * math.cos(a), cy + (R + 76) * math.sin(a)
        s = f"{deg:03d}"; d.text((tx - 30, ty - 16), s, font=F(30), fill=DIM + (230,))
# beam line
a = math.radians(beam)
d.line([(cx, cy), (cx + R * math.cos(a), cy + R * math.sin(a))], fill=HI + (230,), width=4)

# blips: brighter just behind the beam
blips = [(296, 0.62, "K-07"), (280, 0.35, "HX-2"), (245, 0.78, "?"), (200, 0.5, "RLY"), (120, 0.86, "K-11"), (60, 0.28, "")]
for b_ang, b_r, lab in blips:
    age = (beam - b_ang) % 360
    inten = max(0.18, math.exp(-age / 90))
    x = cx + R * b_r * math.cos(math.radians(b_ang)); y = cy + R * b_r * math.sin(math.radians(b_ang))
    c = tuple(int(BG[i] + (HI[i] - BG[i]) * inten) for i in range(3))
    for s, al in [(26, 50), (16, 110), (8, 255)]:
        d.ellipse([x - s, y - s, x + s, y + s], fill=c + (int(al * inten),))
    if lab:
        d.text((x + 24, y - 34), lab, font=F(26), fill=c + (int(255 * max(inten, .5)),))
img = img.filter(ImageFilter.GaussianBlur(1.2))
d = ImageDraw.Draw(img, "RGBA")

# panel labels
d.text((150, 130), "SECTOR 07", font=FB(44), fill=MID + (230,))
d.text((150, 190), "PPI // SURFACE SEARCH", font=F(28), fill=DIM + (230,))
d.text((150, H - 210), "RNG 40KM   GAIN 0.6   PRF 1200", font=F(28), fill=DIM + (220,))
d.text((150, H - 160), "BRG 312   TRK 04 ACTIVE", font=F(28), fill=AMB + (200,))
d.text((W - 640, 130), "ASHFALL // AIR WATCH", font=F(28), fill=DIM + (220,))
d.text((W - 640, 180), "LINK: DEGRADED", font=F(28), fill=(130, 90, 60, 220))

# scanlines
sl = Image.new("L", (W, H), 255); sd = ImageDraw.Draw(sl)
for y in range(0, H, 4): sd.line([(0, y), (W, y)], fill=200)
img = ImageChops.multiply(img, Image.merge("RGB", (sl, sl, sl)))
# grain + CRT vignette
noise = Image.effect_noise((W, H), 20).convert("RGB")
img = Image.blend(img, ImageChops.multiply(img, noise.point(lambda v: 205 + v // 5)), 0.4)
vig = Image.new("L", (W, H), 0); ImageDraw.Draw(vig).rounded_rectangle([-W * .05, -H * .1, W * 1.05, H * 1.1], radius=900, fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(260))
img = Image.composite(img, Image.new("RGB", (W, H), (3, 4, 3)), vig)
img.save(OUT, optimize=True); print("wrote", OUT)
