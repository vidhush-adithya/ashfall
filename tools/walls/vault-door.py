#!/usr/bin/env python3
"""ASHFALL wallpaper: vault-door -- a heavy circular blast door at the end of a dark bunker corridor.

Usage: python3 vault-door.py <out.png>   (also writes <outdir>/preview/<name>.jpg)"""
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

SEED = 1977
CX, CY = W / 2, H * 0.505          # door centre
VP = (W / 2, H * 0.5)              # vanishing point of corridor
S = 0.80                           # back wall scale (corridor depth)
R_DOOR, R_GAP, R_FRAME = 712, 724, 842


def back_wall_rect():
    x0 = VP[0] - S * VP[0]; x1 = VP[0] + S * (W - VP[0])
    y0 = VP[1] - S * VP[1]; y1 = VP[1] + S * (H - VP[1])
    return x0, y0, x1, y1


def heightfield(rng, xx, yy):
    dx, dy = xx - CX, yy - CY
    r = np.sqrt(dx * dx + dy * dy)
    th = np.arctan2(dy, dx)
    st = lambda edge, w, dh: dh * smooth(edge + w, edge - w, r)   # rise inside edge
    h = np.zeros((H, W), np.float32)
    h += st(R_FRAME, 9, 46)        # frame collar
    h += st(R_FRAME - 30, 5, -6)   # small step on collar
    h += st(R_GAP, 2.5, -80)       # gap
    h += st(R_DOOR, 3, 104)        # door rim
    h += st(648, 6, -14)
    h += st(606, 4, 20)            # raised ring
    h += st(572, 5, -16)
    h += st(430, 10, -8)
    h += st(250, 6, 26)            # hub
    h += st(214, 4, -10)
    h += st(96, 6, 22)             # boss
    h += st(60, 4, -6)
    # hinge housing + knuckles + arms on the left
    hx0, hx1 = CX - 960, CX - 812
    blk = smooth(hx0 - 8, hx0 + 8, xx) * smooth(hx1 + 8, hx1 - 8, xx) * smooth(CY - 330, CY - 314, yy) * smooth(CY + 330, CY + 314, yy)
    h = np.maximum(h, 60 * blk)
    kx = (hx0 + hx1) / 2
    for (ya, yb) in ((CY - 300, CY - 70), (CY + 70, CY + 300)):
        dxk = np.abs(xx - kx)
        cyl = np.sqrt(np.clip(1 - (dxk / 52) ** 2, 0, 1)) * smooth(ya - 4, ya + 4, yy) * smooth(yb + 4, yb - 4, yy)
        h = np.maximum(h, (90 + 40 * cyl) * (cyl > 0))
        # end caps rings
    for ya in (CY - 185, CY + 185):
        arm = smooth(kx - 4, kx + 10, xx) * smooth(CX - 600, CX - 620, xx) * smooth(ya - 46, ya - 38, yy) * smooth(ya + 46, ya + 38, yy)
        h = np.maximum(h, 112 * arm)
        # rivets on arm
    # handwheel: torus + spokes
    tube = np.abs(r - 330)
    torus = np.sqrt(np.clip(1 - (tube / 22) ** 2, 0, 1))
    h = np.maximum(h, (118 + 22 * torus) * (torus > 0))
    for a in (math.pi / 4, 3 * math.pi / 4, 5 * math.pi / 4, 7 * math.pi / 4):
        ux, uy = math.cos(a), math.sin(a)
        along = dx * ux + dy * uy
        perp = np.abs(-dx * uy + dy * ux)
        spoke = np.sqrt(np.clip(1 - (perp / 15) ** 2, 0, 1)) * (along > 70) * (along < 320)
        h = np.maximum(h, (112 + 16 * spoke) * (spoke > 0))
    hubc = np.sqrt(np.clip(1 - (r / 78) ** 2, 0, 1))
    h = np.maximum(h, (120 + 30 * hubc) * (hubc > 0))
    return h, r, th


def bolts(h, r, th, xx, yy, ring_r, n, size, height, phase=0.0):
    pos = []
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        bx, by = CX + ring_r * math.cos(a), CY + ring_r * math.sin(a)
        pos.append((bx, by))
        x0, x1 = int(bx - size * 2), int(bx + size * 2) + 1
        y0, y1 = int(by - size * 2), int(by + size * 2) + 1
        px, py = xx[y0:y1, x0:x1] - bx, yy[y0:y1, x0:x1] - by
        rot = a * 0.7
        hexd = np.zeros_like(px)
        for k in range(3):
            ang = rot + k * math.pi / 3
            hexd = np.maximum(hexd, np.abs(px * math.cos(ang) + py * math.sin(ang)))
        d = np.sqrt(px * px + py * py)
        washer = smooth(size * 1.45, size * 1.30, d) * height * 0.35
        head = smooth(size, size * 0.86, hexd) * height * (0.85 + 0.15 * np.sqrt(np.clip(1 - (d / size) ** 2, 0, 1)))
        base = h[y0:y1, x0:x1]
        local = base.max()
        h[y0:y1, x0:x1] = np.maximum(base, local * (washer > 0.01) + np.maximum(washer, head))
    return pos


def main(out):
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    bx0, by0, bx1, by1 = back_wall_rect()

    h, r, th = heightfield(rng, xx, yy)
    bolt_pos = bolts(h, r, th, xx, yy, 680, 32, 15, 16, 0.05)
    bolt_pos += bolts(h, r, th, xx, yy, 176, 10, 10, 12, 0.3)
    for by_ in (CY - 300, CY - 30, CY + 30, CY + 300):
        for bx_ in (CX - 940, CX - 832):
            hb = np.zeros((40, 40), np.float32)
            py_, px_ = np.mgrid[-20:20, -20:20]
            dd = np.sqrt(px_ ** 2 + py_ ** 2)
            ys, xs_ = int(by_) - 20, int(bx_) - 20
            h[ys:ys + 40, xs_:xs_ + 40] = np.maximum(h[ys:ys + 40, xs_:xs_ + 40], 60 + 10 * np.sqrt(np.clip(1 - (dd / 11) ** 2, 0, 1)) * (dd < 11))
    # concrete micro relief on wall + metal surface relief
    door = smooth(R_GAP + 2, R_GAP - 2, r)
    wallrel = fbm(rng, W, H, 30, 5) * 5
    h = h + wallrel * (1 - door) + fbm(rng, W, H, 60, 3) * 1.2 * door
    h = blur(h, 1.2)

    # ---- lighting
    gy, gx = np.gradient(h)
    nz = np.ones_like(h)
    nrm = np.sqrt(gx * gx + gy * gy + 1)
    nx, ny, nz = -gx / nrm, -gy / nrm, nz / nrm
    LX, LY, LZ = CX + 40, by0 - 20, 430.0
    lx, ly, lz = LX - xx, LY - yy, LZ - h
    ld = np.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / ld, ly / ld, lz / ld
    lam = np.clip(nx * lx + ny * ly + nz * lz, 0, 1)
    # spotlight cone pointing down & toward wall
    spot_dir = np.array([0.0, 0.93, -0.36]); spot_dir /= np.linalg.norm(spot_dir)
    cosang = -(lx * spot_dir[0] + ly * spot_dir[1] + lz * spot_dir[2])
    spot = smooth(math.cos(math.radians(44)), math.cos(math.radians(16)), cosang)
    fall = 1.0 / (1.0 + (ld / 1100) ** 2)
    # blinn specular (view straight on)
    hx_, hy_, hz_ = lx, ly, lz + 1
    hn = np.sqrt(hx_ ** 2 + hy_ ** 2 + hz_ ** 2)
    spec = np.clip((nx * hx_ + ny * hy_ + nz * hz_) / hn, 0, 1) ** 40
    # heightfield shadows (light comes from above)
    occ = np.zeros_like(h)
    for d in range(6, 140, 6):
        sh = np.empty_like(h)
        sh[d:] = h[:-d]; sh[:d] = h[:1]
        occ = np.maximum(occ, sh - h - d * 0.9)
    shadow = 1 - 0.85 * smooth(0, 14, occ)
    ao = np.clip(1 - (blur(h, 18) - h) * 0.012, 0.35, 1.05)
    del gx, gy, nrm, hx_, hy_, hz_, hn, sh, occ, cosang

    # ---- albedo
    wall_alb = mix(solid(P["slag"]), solid(P["grit"]), fbm(rng, W, H, 4, 6) * 0.8)
    wall_alb = mix(wall_alb, solid(P["dust"]), smooth(0.65, 1, fbm(rng, W, H, 12, 4)) * 0.3)
    wall_alb *= (1 - 0.22 * smooth(0.0, 1.0, blur(vnoise(rng, W, H, 220, 4), 2.0)) * smooth(-0.2, 1, (yy - by0) / (by1 - by0)))[..., None]
    # wall panel seams on back wall
    seam = np.zeros((H, W), np.float32)
    for x in np.linspace(bx0, bx1, 7)[1:-1]:
        seam = np.maximum(seam, smooth(3, 0, np.abs(xx - x)))
    for y in (by0 + 300, by1 - 260):
        seam = np.maximum(seam, smooth(3, 0, np.abs(yy - y)))
    seam *= (1 - smooth(R_FRAME + 60, R_FRAME + 40, r))
    wall_alb *= (1 - 0.6 * seam)[..., None]

    steel = mix(P["steel"], P["grit"], 0.55)
    door_alb = solid(steel) * (0.75 + 0.5 * fbm(rng, W, H, 8, 6))[..., None]
    door_alb = mix(door_alb, solid(P["slag"]), smooth(0.5, 0.9, fbm(rng, W, H, 3, 5)) * 0.5)
    # concentric lathe marks
    lathe = np.sin(r * 0.9 + vnoise(rng, W, H, 40, 20) * 6) * 0.5 + 0.5
    door_alb *= (0.94 + 0.08 * lathe)[..., None]

    # hazard stripes on frame collar
    rmid = (R_GAP + R_FRAME) / 2
    sarc = (th * rmid + (r - rmid) * 1.0) / 64.0
    tri = np.abs((sarc % 1.0) - 0.5) * 2
    stripe = smooth(0.46, 0.54, tri)
    haz_y = mix(P["ochre"], P["grit"], 0.35) * 0.95
    haz = mix(solid(P["ash"] * 1.4), solid(haz_y), stripe)
    chip = smooth(0.62, 0.75, fbm(rng, W, H, 70, 4)) + smooth(0.68, 0.8, fbm(rng, W, H, 9, 5))
    haz = mix(haz, solid(mix(P["steel"], P["grit"], 0.6) * 0.8), np.clip(chip, 0, 1) * 0.85)
    collar = smooth(R_GAP + 6, R_GAP + 14, r) * smooth(R_FRAME - 2, R_FRAME - 12, r)
    frame_alb = solid(mix(P["steel"], P["grit"], 0.7) * 0.8)
    alb = mix(wall_alb, frame_alb, smooth(R_FRAME + 6, R_FRAME - 4, r))
    alb = mix(alb, haz, collar)
    alb = mix(alb, door_alb, smooth(R_DOOR + 4, R_DOOR - 2, r))
    gap = smooth(R_GAP + 3, R_GAP - 1, r) * smooth(R_DOOR - 2, R_DOOR + 3, r)
    alb *= (1 - 0.85 * gap)[..., None]
    # hinge parts: oily dark steel
    hinge = smooth(1, 40, h) * (1 - door) * (xx < CX - 760)
    alb = mix(alb, solid(mix(P["steel"], P["grit"], 0.5) * 1.0), np.clip(hinge, 0, 1))
    arms = (np.abs(xx - (CX - 700)) < 180) * (h > 100) * (r > R_DOOR - 100)
    alb = mix(alb, solid(mix(P["steel"], P["slag"], 0.55) * 0.9), arms.astype(np.float32))

    # rust bleeding from bolts + grime + scratches
    rustm = np.zeros((H, W), np.float32)
    streaky = vnoise(rng, W, H, 700, 6)
    for (bx, by) in bolt_pos:
        if rng.random() < 0.8:
            L = int(rng.uniform(60, 360)); wdt = rng.uniform(5, 11)
            x0, x1 = int(bx - 30), int(bx + 30)
            y0, y1 = int(by), min(H, int(by) + L)
            px = xx[y0:y1, x0:x1] - bx - rng.normal(0, 2)
            py = yy[y0:y1, x0:x1] - by
            rustm[y0:y1, x0:x1] += np.exp(-(px / (wdt * (1 + py / L))) ** 2) * np.exp(-py / (L * 0.45)) * rng.uniform(0.5, 1)
        cx0, cy0 = int(bx), int(by)
        rustm[cy0 - 40:cy0 + 40, cx0 - 40:cx0 + 40] += 0.6 * np.exp(-((xx[cy0 - 40:cy0 + 40, cx0 - 40:cx0 + 40] - bx) ** 2 + (yy[cy0 - 40:cy0 + 40, cx0 - 40:cx0 + 40] - by) ** 2) / 400)
    # rust along bottom of door and gap
    rustm += smooth(0.2, 0.75, (yy - CY) / R_DOOR) * smooth(R_DOOR - 70, R_DOOR - 10, r) * smooth(R_FRAME, R_DOOR - 10, r) * 0.7 * fbm(rng, W, H, 25, 4)
    rustm = np.clip(rustm * (0.4 + 0.8 * streaky), 0, 1)
    alb = mix(alb, solid(mix(P["rust"], P["slag"], 0.25) * 0.8), rustm * 0.9)

    def scratches(d, ss):
        for _ in range(520):
            rr = rng.uniform(80, R_DOOR - 10)
            a0 = rng.uniform(0, 2 * math.pi)
            if rng.random() < 0.55:      # arc scratches from the door swinging
                da = rng.uniform(0.02, 0.25) * (1 if rng.random() < .5 else -1)
                pts = [(CX + (rr + k * rng.uniform(-0.4, 0.4)) * math.cos(a0 + da * k / 12), CY + rr * math.sin(a0 + da * k / 12)) for k in range(13)]
            else:
                x, y = CX + rr * math.cos(a0), CY + rr * math.sin(a0)
                ang = rng.uniform(0, math.pi); L = rng.uniform(15, 140)
                pts = [(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))]
            d.line([(p[0] * ss, p[1] * ss) for p in pts], fill=int(rng.uniform(60, 255)), width=ss)
    scr = mask_from_draw(scratches, 2) * smooth(R_DOOR, R_DOOR - 6, r)
    alb = alb + (scr * 0.09)[..., None] * (P["bone"] / P["bone"].max())

    grime = smooth(0.0, 1.0, (yy - CY) / R_DOOR) * 0.55 * (0.5 + 0.5 * fbm(rng, W, H, 6, 5))
    alb *= (1 - grime * door)[..., None]

    # ---- combine lighting for back wall / door
    metal = smooth(R_GAP + 10, R_GAP, r) + hinge.clip(0, 1) * 0.8
    fdir = np.array([-0.62, 0.35, 0.70]); fdir /= np.linalg.norm(fdir)
    fill = np.clip(nx * fdir[0] + ny * fdir[1] + nz * fdir[2], 0, 1) ** 1.5
    fillmask = smooth(-0.2, 0.9, (CX + 300 - xx) / W) * 0.22
    lit = (0.04 + 2.5 * lam * spot * fall * shadow) * ao
    lit3 = lit[..., None] + (fill * fillmask * ao)[..., None] * (P["steel"] / P["steel"].mean())
    del lx, ly, lz, ld, nx, ny, nz, lam, fill
    col = alb * lit3 + (spec * spot * fall * shadow * (0.30 * np.clip(metal, 0, 1) + 0.04))[..., None] * mix(P["bone"], P["ochre"], 0.3)
    # a little cool bounce on lower half
    col += alb * 0.025
    del alb, lit3, lit, door_alb, wall_alb, haz, frame_alb, spec, rustm, scr, streaky, lathe, sarc, tri, stripe, shadow, ao
    import gc; gc.collect()

    # ---- corridor: floor, ceiling, side walls (perspective)
    def poly_mask(pts):
        return mask_from_draw(lambda d, ss: d.polygon([(x * ss, y * ss) for x, y in pts], fill=255), 2)
    floor = poly_mask([(0, H), (W, H), (bx1, by1), (bx0, by1)])
    ceil = poly_mask([(0, 0), (W, 0), (bx1, by0), (bx0, by0)])
    lwall = poly_mask([(0, 0), (bx0, by0), (bx0, by1), (0, H)])
    rwall = poly_mask([(W, 0), (bx1, by0), (bx1, by1), (W, H)])
    # perspective coordinates: depth t (0 at back wall, 1 at screen edge)
    ex, ey = (xx - VP[0]), (yy - VP[1])
    tfloor = np.clip((ey / (H - VP[1]) - S) / (1 - S), 0, 1)
    # floor: steel plates with lines converging to VP
    u = ex / np.maximum(ey, 1) * (H - VP[1]) / W     # lateral coordinate on floor
    zf = 1.0 / np.maximum(ey / (H - VP[1]), 1e-3)     # depth ~ 1/screen-y
    plates = smooth(0.92, 0.97, np.abs(((u * 10) % 1) - 0.5) * 2) + smooth(0.90, 0.96, np.abs(((zf * 9) % 1) - 0.5) * 2)
    fl_alb = solid(P["soot"]) * (0.8 + 0.5 * fbm(rng, W, H, 20, 4))[..., None]
    fl_alb = mix(fl_alb, solid(P["ash"]), np.clip(plates, 0, 1) * 0.8)
    # hazard stripe at threshold on floor
    thr = smooth(0.0, 0.02, tfloor) * smooth(0.16, 0.14, tfloor)
    fs = smooth(0.45, 0.55, np.abs(((u * 26 + tfloor * 4) % 1) - 0.5) * 2)
    fl_alb = mix(fl_alb, mix(solid(P["ash"]), solid(mix(P["ochre"], P["grit"], 0.45) * 0.85), fs), thr * (1 - 0.6 * np.clip(chip, 0, 1)) * 0.6)
    pool = np.exp(-(((xx - CX) / 1300) ** 2 + ((yy - by1 - 30) / 260) ** 2))
    fl = fl_alb * (0.14 + 2.2 * pool * (1 - 0.5 * tfloor))[..., None]
    # side walls & ceiling: dark, ribbed
    tside = np.clip((np.abs(ex) / VP[0] - S) / (1 - S), 0, 1)
    zs = 1.0 / np.maximum(np.abs(ex) / VP[0], 1e-3)
    ribs = smooth(0.80, 0.9, np.abs(((zs * 7) % 1) - 0.5) * 2)
    sw_alb = solid(P["soot"]) * (0.8 + 0.4 * fbm(rng, W, H, 10, 5))[..., None]
    sw = sw_alb * (0.55 + 0.35 * (1 - tside))[..., None] * (1 - 0.5 * ribs)[..., None]
    sw *= (1 - 0.35 * tside)[..., None]
    zc = 1.0 / np.maximum(-ey / VP[1], 1e-3)
    cribs = smooth(0.80, 0.9, np.abs(((zc * 7) % 1) - 0.5) * 2)
    ce = solid(P["ash"]) * (0.9 + 0.3 * fbm(rng, W, H, 10, 4))[..., None] * (1 - 0.5 * cribs)[..., None]
    col = mix(col, ce, ceil)
    col = mix(col, sw, np.clip(lwall + rwall, 0, 1))
    col = mix(col, fl, floor)
    # corner darkening (AO) along back wall edges
    edge_d = np.minimum.reduce([np.abs(xx - bx0), np.abs(xx - bx1), np.abs(yy - by0), np.abs(yy - by1)])
    col *= (0.55 + 0.45 * smooth(0, 90, edge_d))[..., None]

    # ---- lamp fixture hanging from ceiling + volumetric cone
    def lamp(d, ss):
        q = lambda pts: [(x * ss, y * ss) for x, y in pts]
        d.line(q([(LX - 10, 0), (LX - 10, LY - 60)]), fill=255, width=5 * ss)
        d.line(q([(LX + 10, 0), (LX + 10, LY - 60)]), fill=255, width=5 * ss)
        d.rectangle(q([(LX - 24, LY - 70), (LX + 24, LY - 50)]), fill=255)
        d.polygon(q([(LX - 40, LY - 52), (LX + 40, LY - 52), (LX + 120, LY + 4), (LX - 120, LY + 4)]), fill=255)
    lm = mask_from_draw(lamp, 3)
    col = mix(col, solid(P["ash"] * 0.9), lm)
    # faint top highlight on the shade + glowing opening
    sh_hl = mask_from_draw(lambda d, ss: d.line([((LX - 40) * ss, (LY - 52) * ss), ((LX - 120) * ss, (LY + 4) * ss)], fill=255, width=3 * ss), 3)
    col = mix(col, solid(P["grit"]), sh_hl * 0.7)
    opening = mask_from_draw(lambda d, ss: d.ellipse([(LX - 116) * ss, (LY - 4) * ss, (LX + 116) * ss, (LY + 16) * ss], fill=255), 3)
    warm = mix(P["bbone"], P["ochre"], 0.35)
    col = mix(col, solid(warm * 0.95), opening)
    bloom = np.exp(-(((xx - LX) / 260) ** 2 + ((yy - LY - 10) / 110) ** 2))
    col += (bloom * (1 - lm))[..., None] * warm * 0.22
    # screen-space cone (light scattered in dusty air)
    vx, vy = xx - LX, yy - (LY + 6)
    ang = np.degrees(np.arctan2(np.abs(vx), np.maximum(vy, 1)))
    cone = smooth(34, 20, ang) * (vy > 0) * np.exp(-np.maximum(vy, 0) / 1300)
    dustn = 0.6 + 0.6 * fbm(rng, W, H, 6, 5)
    shafts = 0.75 + 0.25 * vnoise(rng, W, H, 120, 1)
    cone = blur(cone, 10) * dustn * smooth(0, 120, vy)
    col += cone[..., None] * mix(P["dust"], P["ochre"], 0.3) * 0.26
    # dust motes inside the cone
    def motes(d, ss):
        for _ in range(420):
            x, y = rng.uniform(LX - 1100, LX + 1100), rng.uniform(LY, H)
            rr = rng.uniform(0.6, 2.6)
            v = int(rng.uniform(60, 255))
            d.ellipse([(x - rr) * ss, (y - rr) * ss, (x + rr) * ss, (y + rr) * ss], fill=v)
    mm = blur(mask_from_draw(motes, 2), 0.7) * np.clip(cone * 2.5, 0, 1)
    col += mm[..., None] * P["bone"] * 0.22

    col = vignette(col, 0.7, 1.8)
    finish(col, rng, out, grain=0.013)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "vault-door.png")
