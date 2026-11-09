#!/usr/bin/env python3
"""ASHFALL wallpaper generator: ruined skyline under a dim, ash-choked sun."""
import random, math, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

W, H = 3840, 2160
OUT = sys.argv[1] if len(sys.argv) > 1 else "ashfall.png"
LOCK = sys.argv[2] if len(sys.argv) > 2 else "ashfall-lock.png"
random.seed(1944)

def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

# --- sky: near-black top -> murky ochre-brown haze at horizon
sky = Image.new("RGB", (W, H))
d = ImageDraw.Draw(sky)
top, mid, hor = (9, 8, 7), (24, 20, 16), (58, 44, 30)
for y in range(H):
    t = y / H
    c = lerp(top, mid, t / 0.55) if t < 0.55 else lerp(mid, hor, min(1, (t - 0.55) / 0.25))
    d.line([(0, y), (W, y)], fill=c)

# --- dim sun behind haze
sun = Image.new("RGB", (W, H), (0, 0, 0))
sd = ImageDraw.Draw(sun)
cx, cy = int(W * 0.68), int(H * 0.60)
for r, col in [(620, (40, 26, 14)), (380, (70, 44, 22)), (210, (110, 72, 36)), (150, (128, 88, 46))]:
    sd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
sun = sun.filter(ImageFilter.GaussianBlur(120))
sky = ImageChops.add(sky, sun)
core = Image.new("L", (W, H), 0)
ImageDraw.Draw(core).ellipse([cx - 135, cy - 135, cx + 135, cy + 135], fill=150)
core = core.filter(ImageFilter.GaussianBlur(6))
sky = Image.composite(Image.new("RGB", (W, H), (138, 98, 56)), sky, core)

# --- haze bands
haze = Image.new("RGB", (W, H), (0, 0, 0))
hd = ImageDraw.Draw(haze)
for _ in range(14):
    y = random.randint(int(H * 0.35), int(H * 0.72))
    hd.rectangle([0, y, W, y + random.randint(20, 70)], fill=(22, 17, 12))
haze = haze.filter(ImageFilter.GaussianBlur(40))
sky = ImageChops.add(sky, haze)

def ruined_building(dr, x, base, w, h, col, broken=True):
    top = base - h
    pts = [(x, base), (x, top)]
    if broken and random.random() < 0.8:
        steps = random.randint(3, 7)
        for i in range(1, steps):
            pts.append((x + w * i / steps, top + random.randint(-int(h * .08), int(h * .25))))
    pts += [(x + w, top + (random.randint(0, int(h * .3)) if broken else 0)), (x + w, base)]
    dr.polygon(pts, fill=col)
    # antenna / rebar
    if random.random() < 0.3:
        ax = x + random.randint(2, max(3, int(w) - 2))
        dr.line([(ax, top), (ax + random.randint(-15, 15), top - random.randint(30, 140))], fill=col, width=4)
    return top

def skyline(layer_col, base, hmin, hmax, wmin, wmax, windows=False, win_col=None):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(lay)
    x = -50
    while x < W + 50:
        w = random.randint(wmin, wmax)
        h = random.randint(hmin, hmax)
        top = ruined_building(dr, x, base, w, h, layer_col)
        if windows and random.random() < 0.6:
            for wy in range(int(top) + 40, base - 20, 34):
                for wx in range(int(x) + 12, int(x + w) - 12, 26):
                    if random.random() < 0.035:  # rare dying lights
                        dr.rectangle([wx, wy, wx + 8, wy + 12], fill=win_col)
        x += w + random.randint(-10, 30)
    dr.rectangle([0, base, W, H], fill=layer_col)
    return lay

img = sky.convert("RGBA")
for col, base, hr, wr, blur in [
    ((34, 28, 22, 255), int(H * .80), (260, 640), (90, 220), 6),
    ((22, 19, 16, 255), int(H * .85), (200, 520), (120, 260), 2),
]:
    img = Image.alpha_composite(img, skyline(col, base, *hr, *wr).filter(ImageFilter.GaussianBlur(blur)))

# foreground: collapsed towers, a leaning crane, a dead radio mast
fg = skyline((12, 11, 9, 255), int(H * .90), 140, 460, 160, 340, windows=True, win_col=(92, 64, 34, 255))
fd = ImageDraw.Draw(fg)
mx, my = int(W * 0.18), int(H * 0.90)
for i in range(0, 900, 60):  # lattice mast
    w0, w1 = 70 * (1 - i / 900), 70 * (1 - (i + 60) / 900)
    fd.line([(mx - w0, my - i), (mx + w1, my - i - 60)], fill=(12, 11, 9), width=5)
    fd.line([(mx + w0, my - i), (mx - w1, my - i - 60)], fill=(12, 11, 9), width=5)
fd.line([(mx - 70, my), (mx, my - 900)], fill=(12, 11, 9), width=9)
fd.line([(mx + 70, my), (mx, my - 900)], fill=(12, 11, 9), width=9)
cxr, cyr = int(W * 0.86), int(H * 0.90)
fd.line([(cxr, cyr), (cxr - 60, cyr - 820)], fill=(12, 11, 9), width=22)          # crane tower
fd.line([(cxr - 60, cyr - 820), (cxr - 620, cyr - 700)], fill=(12, 11, 9), width=14)  # sagging jib
fd.line([(cxr - 60, cyr - 820), (cxr + 200, cyr - 860)], fill=(12, 11, 9), width=14)
fd.line([(cxr - 480, cyr - 730), (cxr - 470, cyr - 420)], fill=(12, 11, 9), width=3)  # dangling cable
img = Image.alpha_composite(img, fg)

# --- falling ash
ash = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ad = ImageDraw.Draw(ash)
for _ in range(5200):
    x, y = random.randint(0, W), random.randint(0, H)
    r = random.choice([1, 1, 1, 2, 2, 3])
    a = random.randint(25, 90)
    g = random.randint(120, 170)
    ad.ellipse([x, y, x + r, y + r * random.choice([1, 2])], fill=(g, g - 10, g - 25, a))
img = Image.alpha_composite(img, ash.filter(ImageFilter.GaussianBlur(0.8)))

# --- film grain + vignette
noise = Image.effect_noise((W, H), 22).convert("RGB")
img = Image.blend(img.convert("RGB"), ImageChops.multiply(img.convert("RGB"), noise.point(lambda v: 200 + v // 5)), 0.35)
vig = Image.new("L", (W, H), 0)
ImageDraw.Draw(vig).ellipse([-W * .15, -H * .25, W * 1.15, H * 1.25], fill=255)
vig = vig.filter(ImageFilter.GaussianBlur(320))
img = Image.composite(img, Image.new("RGB", (W, H), (4, 4, 3)), vig)

# --- tiny stencil text
try:
    font = ImageFont.truetype("DejaVuSansMono.ttf", 30)
except OSError:
    font = ImageFont.load_default()
td = ImageDraw.Draw(img)
td.text((90, H - 120), "ASHFALL // SECTOR 07 // NO SIGNAL", font=font, fill=(78, 70, 58))
td.text((90, H - 80), "47.3N 08.5E  RAD 4.2mSv/h  AIR: UNSAFE", font=font, fill=(58, 52, 44))

img.save(OUT, optimize=True)
img.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * 0.55)).save(LOCK, optimize=True)
print("wrote", OUT, LOCK)
