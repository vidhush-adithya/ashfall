#!/usr/bin/env python3
"""ASHFALL wallpaper: stencil-zone -- weathered concrete wall with a sprayed radiation trefoil.

Usage: python3 stencil-zone.py <out.png>   (also writes <outdir>/preview/<name>.jpg)"""
# ---------------------------------------------------------------- common ----
import sys, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 3840, 2160
FONTS = "/usr/share/fonts/truetype/dejavu/"

def hexc(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255.0

P = {k: hexc(v) for k, v in dict(
    ash="#0c0b09", soot="#14120f", slag="#2a2620", grit="#4a443a", dust="#6e6657",
    bone="#a89f8c", bbone="#c2b8a3", rust="#8b5a3c", ochre="#9a8348", moss="#5d6a48",
    blood="#7a3329", steel="#556270").items()}

def font(name, size):
    return ImageFont.truetype(FONTS + name, size)

def resize_f(a, w, h, method=Image.BICUBIC):
    return np.asarray(Image.fromarray(np.ascontiguousarray(a, dtype=np.float32), "F").resize((w, h), method))

def _box(a, r, axis):
    if r < 1:
        return a
    pad = [(0, 0)] * a.ndim
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    n = a.shape[axis]
    hi = np.take(c, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
    lo = np.take(c, np.arange(0, n), axis=axis)
    return ((hi - lo) / (2 * r + 1)).astype(np.float32)

def blur(a, s):
    """Approximate gaussian blur of a 2D float array (3 box passes)."""
    a = np.asarray(a, np.float32)
    if s < 0.5:
        return a
    h, w = a.shape
    if s > 12:
        f = s / 6.0
        sw, sh = max(4, int(w / f)), max(4, int(h / f))
        small = resize_f(a, sw, sh, Image.BOX)
        return resize_f(blur(small, 6.0), w, h, Image.BICUBIC)
    r = max(1, int(round((math.sqrt(4 * s * s + 1) - 1) / 2)))
    for _ in range(3):
        a = _box(_box(a, r, 0), r, 1)
    return a

def vnoise(rng, w, h, cx, cy):
    g = rng.random((max(2, int(cy)) , max(2, int(cx)))).astype(np.float32)
    return resize_f(g, w, h, Image.BICUBIC)

def fbm(rng, w, h, cells=4, octaves=6, gain=0.5, lac=2.0, aspect=None):
    aspect = (w / h) if aspect is None else aspect
    out = np.zeros((h, w), np.float32)
    amp, tot, c = 1.0, 0.0, float(cells)
    for _ in range(octaves):
        out += amp * vnoise(rng, w, h, c * aspect, c)
        tot += amp
        amp *= gain
        c *= lac
    out /= tot
    lo, hi = np.percentile(out[::8, ::8], [0.5, 99.5])
    return np.clip((out - lo) / (hi - lo + 1e-6), 0, 1)

def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)

def mix(a, b, t):
    t = np.asarray(t, np.float32)
    if t.ndim == 2:
        t = t[..., None]
    return a * (1 - t) + b * t

def solid(c, h=H, w=W):
    return np.broadcast_to(c, (h, w, 3)).astype(np.float32).copy()

def mask_from_draw(fn, ss=1, w=W, h=H):
    """Render shapes with ImageDraw into an L mask (optionally supersampled)."""
    im = Image.new("L", (w * ss, h * ss), 0)
    fn(ImageDraw.Draw(im), ss)
    if ss > 1:
        im = im.resize((w, h), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255.0

def vignette(img, strength=0.55, power=2.2):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx, ny = (xx / W - 0.5) * 2, (yy / H - 0.5) * 2
    r = np.sqrt(nx * nx * 0.85 + ny * ny * 1.0)
    v = 1 - strength * np.clip(r / 1.35, 0, 1) ** power
    return img * v[..., None]

def finish(img, rng, out, grain=0.012):
    """Grain, soft shoulder towards bright-bone, save PNG + preview JPEG."""
    g = rng.normal(0, 1, (H, W)).astype(np.float32)
    g = 0.7 * g + 0.3 * blur(g, 1.0) * 2.0
    lum = img.mean(axis=2, keepdims=True)
    img = img + g[..., None] * grain * (0.6 + 0.8 * np.sqrt(np.clip(lum, 0, 1)))
    cap = P["bbone"] * 1.02
    knee = cap * 0.82
    over = np.maximum(img - knee, 0)
    img = np.where(img > knee, knee + (cap - knee) * (1 - np.exp(-over / (cap - knee))), img)
    arr = np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
    im = Image.fromarray(arr, "RGB")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    im.save(out, optimize=True)
    pdir = os.path.join(os.path.dirname(os.path.abspath(out)), "preview")
    os.makedirs(pdir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(out))[0]
    im.resize((1280, 720), Image.LANCZOS).save(os.path.join(pdir, stem + ".jpg"), quality=82)
    print(out, os.path.getsize(out) // 1024, "KiB")
# ---------------------------------------------------------------------------

SEED = 4404


def concrete(rng):
    """Dark weathered cast-concrete wall: base tone, pour lines, tie holes, pits."""
    lowf = fbm(rng, W, H, 2.5, 5)
    mid = fbm(rng, W, H, 18, 4)
    fine = fbm(rng, W, H, 220, 3)
    tone = 0.55 * lowf + 0.3 * mid + 0.15 * fine
    img = mix(solid(P["ash"]), solid(P["slag"]), smooth(0.05, 0.95, tone) * 0.95)
    img = mix(img, solid(P["grit"]), smooth(0.62, 1.0, tone) * 0.55)
    # slight warm/cool mottling
    m2 = fbm(rng, W, H, 6, 4)
    img = mix(img, img * (P["rust"] / P["rust"].mean()), smooth(0.6, 0.95, m2) * 0.18)
    img = mix(img, img * (P["steel"] / P["steel"].mean()), smooth(0.55, 0.0, m2) * 0.12)

    # sandy surface texture
    sandy = blur(rng.normal(0, 1, (H, W)).astype(np.float32), 0.8)
    img *= (1 + 0.10 * sandy * (0.5 + fbm(rng, W, H, 40, 3)))[..., None]
    # aggregate pits / bug holes
    def pits(d, ss):
        for _ in range(9000):
            x, y = rng.random() * W, rng.random() * H
            r = rng.choice([1.2, 1.8, 2.5, 3.5, 5.0], p=[.4, .3, .17, .09, .04])
            d.ellipse([(x - r) * ss, (y - r * 0.8) * ss, (x + r) * ss, (y + r * 0.8) * ss], fill=255)
    pm = mask_from_draw(pits, 2)
    img *= (1 - 0.45 * pm)[..., None]
    img += (blur(np.roll(pm, 2, axis=0), 1.2) * 0.012)[..., None]   # tiny lit lip

    # formwork: horizontal pour seams and vertical panel joints
    seams = np.zeros((H, W), np.float32)
    jitter = blur(rng.normal(0, 1, W).astype(np.float32)[None, :].repeat(3, 0), 30)[1] * 30
    xs = np.arange(W)
    for y0 in (520, 1260, 1990):
        yline = (y0 + jitter).astype(int)
        for dy, v in ((-1, 0.6), (0, 1.0), (1, 0.8), (2, 0.4)):
            seams[np.clip(yline + dy, 0, H - 1), xs] = np.maximum(seams[np.clip(yline + dy, 0, H - 1), xs], v)
    for x0 in (610, 1830, 3050):
        seams[:, x0 - 1:x0 + 2] = np.maximum(seams[:, x0 - 1:x0 + 2], 0.7)
    seams = blur(seams, 1.3) * (0.5 + 0.5 * fbm(rng, W, H, 30, 3))
    img *= (1 - 0.55 * np.clip(seams * 1.6, 0, 1))[..., None]
    # concrete is slightly darker/grimier right along seams
    img *= (1 - 0.18 * blur(seams, 14) * 4)[..., None].clip(0.6, 1)

    holes = []
    for row_y in (890, 1625):
        for cx in np.arange(0, W + 1, 610):
            for off in (305,):
                x = cx + off + rng.normal(0, 4)
                y = row_y + rng.normal(0, 4)
                holes.append((x, y))
    hm = mask_from_draw(lambda d, ss: [d.ellipse([(x - 15) * ss, (y - 15) * ss, (x + 15) * ss, (y + 15) * ss], fill=255) for x, y in holes], 2)
    ring = mask_from_draw(lambda d, ss: [d.ellipse([(x - 23) * ss, (y - 23) * ss, (x + 23) * ss, (y + 23) * ss], outline=255, width=3 * ss) for x, y in holes], 2)
    img *= (1 - 0.8 * hm)[..., None]
    img *= (1 - 0.25 * blur(ring, 2))[..., None]
    return img, holes


def crack_mask(rng):
    def walk(d, ss, x, y, ang, length, width, depth):
        pts = [(x, y)]
        travelled = 0
        while travelled < length:
            step = rng.uniform(5, 13)
            ang += rng.normal(0, 0.28)
            x += math.cos(ang) * step
            y += math.sin(ang) * step
            travelled += step
            pts.append((x, y))
            if depth < 3 and rng.random() < 0.012:
                walk(d, ss, x, y, ang + rng.choice([-1, 1]) * rng.uniform(0.5, 1.1),
                     length * rng.uniform(0.2, 0.5), max(1, width * 0.6), depth + 1)
        n = len(pts)
        for i in range(n - 1):
            wv = max(1, width * (1 - i / n) ** 0.6)
            d.line([(pts[i][0] * ss, pts[i][1] * ss), (pts[i + 1][0] * ss, pts[i + 1][1] * ss)],
                   fill=255, width=max(1, int(wv * ss)))

    def draw(d, ss):
        starts = [(0, 700, 0.15), (W, 300, math.pi - 0.3), (1400, 0, 1.4), (2900, H, -1.7),
                  (0, 1750, -0.1), (W, 1500, math.pi + 0.15), (2200, 520, 0.4), (900, 1260, -0.6)]
        for x, y, a in starts:
            walk(d, ss, x, y, a, rng.uniform(500, 1500), rng.uniform(3, 5.5), 0)
    return mask_from_draw(draw, 2)


def stains(rng, holes):
    """Vertical run-off streaks from the top edge, seams and tie holes."""
    streak = blur(vnoise(rng, W, H, 500, 7), 1.5) * 0.25 + vnoise(rng, W, H, 110, 4) * 0.75
    streak = smooth(0.35, 0.85, streak)
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    dark = np.zeros((H, W), np.float32)
    rustm = np.zeros((H, W), np.float32)
    # long streaks from the top and from the pour seams
    for (y0, count) in ((0, 14), (525, 6), (1265, 6)):
        for _ in range(count):
            x0 = rng.uniform(0, W)
            wdt = rng.uniform(60, 260)
            ln = rng.uniform(250, 1300) if y0 else rng.uniform(500, 1600)
            gx = np.exp(-((xx - x0) / wdt) ** 2)
            fy = np.clip((yy - y0) / 40, 0, 1) * np.exp(-np.clip(yy - y0, 0, None) / ln)
            dark += gx * fy * rng.uniform(0.4, 1.0)
    dark = dark * (0.35 + 0.65 * streak)
    # rust bleeding from tie holes
    for (x, y) in holes:
        if rng.random() < 0.75:
            wdt = rng.uniform(8, 18)
            ln = rng.uniform(80, 420)
            gx = np.exp(-((xx - x - rng.normal(0, 2)) / wdt) ** 2)
            fy = (yy > y) * np.exp(-np.clip(yy - y, 0, None) / ln)
            rustm += gx * fy
    rustm = np.clip(rustm * (0.4 + 0.6 * streak), 0, 1)
    # grime at the foot of the wall and top edge
    grime = smooth(0.70, 1.0, yy / H) * (0.6 + 0.4 * fbm(rng, W, H, 8, 4)) + smooth(0.12, 0.0, yy / H) * 0.6
    return np.clip(dark, 0, 1.2), rustm, np.broadcast_to(grime, (H, W))


def trefoil_mask(cx, cy, R):
    """Radiation trefoil + stencil ring with bridges, analytic & antialiased."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dx, dy = xx - cx, -(yy - cy)
    r = np.sqrt(dx * dx + dy * dy)
    th = np.degrees(np.arctan2(dy, dx)) % 360
    aa = lambda d: np.clip(0.5 - d, 0, 1)   # signed dist -> coverage
    centre = aa(r - R)
    # blades centred at 270 (down), 30, 150; 60 degrees wide
    blade = np.zeros_like(r)
    for c in (270, 30, 150):
        dth = np.abs((th - c + 180) % 360 - 180)
        ang_d = (dth - 30) * np.pi / 180 * r        # arc distance to blade edge
        radial = np.maximum(1.5 * R - r, r - 5 * R)
        blade = np.maximum(blade, aa(np.maximum(ang_d, radial)))
    ring_in, ring_out = 5.75 * R, 6.35 * R
    ring = aa(np.maximum(ring_in - r, r - ring_out))
    # stencil bridges in the ring (4 gaps, at 0/90/180/270 rotated)
    for c in (0, 90, 180, 270):
        dth = np.abs((th - c - 45 + 180) % 360 - 180) * np.pi / 180 * r
        ring *= np.clip(dth - 0.18 * R, 0, 1)
    return np.clip(centre + blade + ring, 0, 1)


def text_mask(rng, txt, fnt, x, y, bridge=True, angle=0.0):
    im = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(im)
    d.text((x, y), txt, font=fnt, fill=255)
    if bridge:
        # stencil bridges through glyphs with closed counters
        cx = x
        for ch in txt:
            w = d.textlength(ch, font=fnt)
            if ch in "OQ0ADRP4B896":
                bx = cx + w * 0.5
                bb = d.textbbox((x, y), "Z", font=fnt)
                d.rectangle([bx - fnt.size * 0.045, bb[1] - 5, bx + fnt.size * 0.045, bb[3] + 5], fill=0)
            cx += w
    if angle:
        im = im.rotate(angle, resample=Image.BICUBIC, center=(x, y))
    return np.asarray(im, np.float32) / 255.0


def spray(rng, mask, softness=2.5, over=22, drips=20, drip_len=(40, 380)):
    """Turn a hard mask into a spray-painted coverage map (edges, overspray, drips)."""
    # drips from bottom edges
    m = mask > 0.5
    edge = m & ~np.roll(m, 4, axis=0)
    ys, xs = np.nonzero(edge[:-8])
    dm = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(dm)
    if len(xs) and drips:
        idx = rng.choice(len(xs), size=min(drips, len(xs)), replace=False)
        for i in idx:
            x, y = float(xs[i]), float(ys[i])
            L = rng.uniform(*drip_len) * rng.random() ** 0.5
            w = rng.uniform(2.5, 6.5)
            xw = x
            steps = int(L / 6) + 1
            for k in range(steps):
                t = k / steps
                ww = w * (1 - 0.45 * t)
                xw += rng.normal(0, 0.25)
                d.ellipse([xw - ww / 2, y + k * 6 - ww / 2, xw + ww / 2, y + k * 6 + ww * 1.5], fill=int(255 * (1 - 0.35 * t)))
            yb = y + steps * 6
            d.ellipse([xw - w * 0.75, yb - w * 0.6, xw + w * 0.75, yb + w * 1.1], fill=200)
    dmask = np.asarray(dm, np.float32) / 255.0
    core = np.clip(np.maximum(blur(mask, softness), blur(dmask, 0.8)), 0, 1)
    halo = blur(mask, over)
    speck = (rng.random((H, W)) < 0.10).astype(np.float32)
    speck = np.maximum(speck * rng.random((H, W)).astype(np.float32), 0)
    overspray = np.clip(halo * 1.6, 0, 1) * speck * 0.85 + halo * 0.12
    return np.clip(np.maximum(core, overspray), 0, 1)


def main(out):
    rng = np.random.default_rng(SEED)
    img, holes = concrete(rng)
    cm = crack_mask(rng)
    dark, rustm, grime = stains(rng, holes)

    # stains first (paint sits on top of old stains, cracks cut through paint)
    img *= (1 - 0.38 * np.clip(dark, 0, 1))[..., None]
    img = mix(img, img * 0.6 + P["rust"] * 0.10, rustm * 0.75)
    img *= (1 - 0.45 * grime)[..., None]

    # ----- stencil trefoil
    sand = smooth(0.2, 0.8, blur(rng.random((H, W)).astype(np.float32), 0.9) * 3 - 1)
    cx, cy, R = W * 0.615, H * 0.445, 108
    tm = trefoil_mask(cx, cy, R)
    wear = 0.25 + 0.75 * smooth(0.18, 0.42, fbm(np.random.default_rng(SEED + 7), W, H, 6, 6))  # peeled patches
    flake = smooth(0.12, 0.30, fbm(rng, W, H, 140, 3))          # small flaked chips
    density = 0.72 + 0.28 * fbm(rng, W, H, 5, 3)                 # uneven can pressure
    cov = spray(rng, tm, 2.2, 26, drips=26) * wear * flake * density * (0.8 + 0.2 * sand)
    lum = img.mean(axis=2)
    tex = np.clip(lum / (lum.mean() + 1e-4), 0.45, 1.6)[..., None]
    paint = P["rust"] * 0.78 * (0.55 + 0.45 * tex)
    img = mix(img, paint, cov * 0.66)

    # ----- stencil text, faded bone
    f = font("DejaVuSansCondensed-Bold.ttf", 132)
    txt = "ZONE 04 — NO ENTRY"
    tw = ImageDraw.Draw(Image.new("L", (1, 1))).textlength(txt, font=f)
    tmk = text_mask(rng, txt, f, cx - tw / 2, cy + 6.35 * R + 70, angle=0.6)
    cov_t = spray(rng, tmk, 1.6, 14, drips=12, drip_len=(20, 160)) * smooth(0.22, 0.5, fbm(rng, W, H, 12, 5)) * flake * (0.8 + 0.2 * sand)
    img = mix(img, P["bone"] * 0.62 * (0.6 + 0.4 * tex), cov_t * 0.55)

    # small grid reference, lower left, thin stencil
    f2 = font("DejaVuSansMono-Bold.ttf", 40)
    gm = text_mask(rng, "GRID 38T LM 4417 0962", f2, 210, H - 250, bridge=False)
    gm = np.maximum(gm, text_mask(rng, "SECTOR 4-B  /  LVL -2", f2, 210, H - 195, bridge=False))
    img = mix(img, P["bone"] * 0.55 * (0.6 + 0.4 * tex), spray(rng, gm, 1.0, 6, drips=0) * 0.5 * wear.clip(0.5, 1))
    # hand-painted arrow tick marks next to grid ref
    am = mask_from_draw(lambda d, ss: [d.line([(150 * ss, (H - 238 + 55 * k) * ss), (185 * ss, (H - 238 + 55 * k) * ss)], fill=255, width=6 * ss) for k in range(2)], 2)
    img = mix(img, P["bone"] * 0.5, spray(rng, am, 1.0, 5, drips=0) * 0.3)

    # ----- cracks (cut through everything)
    cvis = 0.35 + 0.65 * smooth(0.25, 0.6, fbm(rng, W, H, 10, 3))
    cmb = blur(cm, 1.0) * cvis
    img *= (1 - 0.75 * cmb)[..., None]
    lip = np.clip(np.roll(blur(cm, 1.2), 3, axis=0) - cmb, 0, 1)
    img += (lip * cvis * 0.045)[..., None]
    img *= (1 - 0.22 * np.clip(blur(cm, 22) * 5, 0, 1))[..., None]   # damp halo

    # ----- light: dim raking light from upper left, dark lower right
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    lx, ly = W * 0.25, -H * 0.25
    dist = np.sqrt(((xx - lx) / W) ** 2 + ((yy - ly) / H) ** 2)
    light = 1.25 - 0.55 * smooth(0.3, 1.5, dist)
    img *= light[..., None]
    img = vignette(img, 0.62, 2.0)
    finish(img, rng, out, grain=0.013)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "stencil-zone.png")
