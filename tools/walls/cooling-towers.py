#!/usr/bin/env python3
"""ASHFALL wallpaper: cooling-towers
Dead hyperboloid cooling towers on a flat smog-choked plain, a receding row of
dead pylons, a dim sun disc and falling ash.  Usage: python3 cooling-towers.py out.png
"""
import sys, math
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

W, H = 3840, 2160
SS = 2  # supersampling for vector masks
SEED = 0xA5F011


# ----------------------------------------------------------------- helpers --
def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def noise(h, w, rng, sy, sx, octaves=5, persist=0.5):
    """fBm value noise; sy/sx = feature size in px of the first octave."""
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh = max(2, int(h / sy * 2 ** o) + 2)
        gw = max(2, int(w / sx * 2 ** o) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray(g, 'F').resize((w, h), Image.BICUBIC)
        out += np.asarray(im) * amp
        tot += amp
        amp *= persist
    out /= tot
    out = (out - out.mean()) / (out.std() + 1e-6)
    return out


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def mask(draw_fn):
    """Draw with PIL at SS x resolution, return anti-aliased float mask (H, W)."""
    im = Image.new('L', (W * SS, H * SS), 0)
    draw_fn(ImageDraw.Draw(im), SS)
    im = im.resize((W, H), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255.0


def over(img, col, a):
    a = np.clip(a, 0, 1)[..., None]
    col = np.asarray(col, np.float32)
    return img * (1 - a) + col * a


def finish(img, rng, grain=0.010, vig=0.55, cap='#c2b8a3'):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx = (xx / W - 0.5) * (W / H)
    ny = yy / H - 0.5
    r = np.sqrt(nx * nx + ny * ny) / math.hypot(0.5 * W / H, 0.5)
    v = 1.0 - vig * smoothstep(0.30, 1.05, r) ** 1.3
    img = img * v[..., None]
    # mono film grain: fine + coarse, slightly stronger in midtones
    g = rng.normal(0, 1, (H, W)).astype(np.float32)
    g = gaussian_filter(g, 0.55)
    g /= g.std()
    gc = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
    gc = np.array(Image.fromarray(gc, 'F').resize((W, H), Image.BILINEAR))
    gc /= gc.std()
    lum = img.mean(axis=2)
    amp = grain * (0.55 + 0.9 * smoothstep(0.02, 0.35, lum))
    img = img + ((0.75 * g + 0.45 * gc) * amp)[..., None]
    img = np.minimum(img, hexc(cap)[None, None, :])
    return np.clip(img, 0, 1)


def save(img, path):
    import os
    u8 = (img * 255 + 0.5).astype(np.uint8)
    im = Image.fromarray(u8, 'RGB')
    im.save(path, optimize=True)
    d = os.path.dirname(os.path.abspath(path))
    slug = os.path.splitext(os.path.basename(path))[0]
    pd = os.path.join(d, 'preview')
    os.makedirs(pd, exist_ok=True)
    im.resize((1280, 720), Image.LANCZOS).save(os.path.join(pd, slug + '.jpg'), quality=82)


# palette
ASH, SOOT, SLAG, GRIT = map(hexc, ['#0c0b09', '#14120f', '#2a2620', '#4a443a'])
DUST, BONE, BBONE = map(hexc, ['#6e6657', '#a89f8c', '#c2b8a3'])
RUST, OCHRE, MOSS, BLOOD, STEEL = map(hexc, ['#8b5a3c', '#9a8348', '#5d6a48', '#7a3329', '#556270'])


# ------------------------------------------------------------------- scene --
def main(out):
    rng = np.random.default_rng(SEED)
    HY = 1585  # horizon
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    # ---- sky ---------------------------------------------------------------
    t = np.clip(yy / HY, 0, 1)
    sky = (ASH * (1 - t[..., None]) + SLAG * t[..., None])
    hz = smoothstep(0.55, 1.0, t)[..., None]
    sky = sky * (1 - hz * 0.7) + (GRIT * 0.92 + RUST * 0.08) * hz * 0.7

    SX, SY, SR = 2800.0, 700.0, 88.0
    d = np.sqrt((xx - SX) ** 2 + (yy - SY) ** 2)
    glow = np.exp(-(d / 520) ** 2) * 0.55 + np.exp(-(d / 1500) ** 2) * 0.35
    sky = sky + (DUST * 0.55 + OCHRE * 0.12)[None, None, :] * glow[..., None] * 0.55
    disc = smoothstep(SR + 2.5, SR - 2.5, d)
    # disc is faintly mottled by haze
    dm = noise(H, W, rng, 60, 160, 3)
    sky = over(sky, DUST * 0.55 + BONE * 0.30 + OCHRE * 0.15, disc * (0.40 + 0.05 * dm))

    # ---- smog layers (over sky, under towers) -------------------------------
    img = sky
    for i, (yc, thick, dens, col) in enumerate([
            (420, 380, 0.35, SLAG), (760, 300, 0.45, GRIT * 0.9),
            (1060, 260, 0.40, GRIT), (1330, 240, 0.45, DUST * 0.82)]):
        n = noise(H, W, rng, 140, 900, 5, 0.55)
        prof = np.exp(-((yy - yc) / thick) ** 2)
        a = np.clip(prof * (0.45 + 0.35 * n) * dens, 0, 0.8)
        img = over(img, col, a)

    def fogged(col, f):
        return col * (1 - f) + (GRIT * 0.85 + DUST * 0.15) * f

    # ---- distant flat ruin line on the horizon ------------------------------
    def ruins(dr, s):
        x = 0
        r = np.random.default_rng(SEED + 7)
        pts = [(0, (HY + 2) * s)]
        while x < W:
            w = r.integers(20, 140)
            h = r.choice([0, 0, 2, 4, 6, 10, 16, 26], p=[.3, .2, .15, .12, .1, .07, .04, .02])
            pts += [(x * s, (HY - h) * s), ((x + w) * s, (HY - h) * s)]
            x += w
        pts += [(W * s, (HY + 2) * s)]
        dr.polygon(pts, fill=255)
    m = mask(ruins)
    img = over(img, fogged(SLAG, 0.55), m)

    # ---- cooling towers ------------------------------------------------------
    def tower(img, cx, h, a_throat, r_base, fog, broken=False, seed=1):
        r = np.random.default_rng(SEED + seed)
        base = HY + 4
        top = base - h
        ht = 0.74 * h  # throat height above base (real towers: ~70-80 %)
        c = ht / math.sqrt((r_base / a_throat) ** 2 - 1)

        def rad(y):
            z = (base - y) - ht
            return a_throat * np.sqrt(1 + (z / c) ** 2)

        ys = np.linspace(top, base, 260)
        rt = float(rad(top))
        poly = [(cx - rad(y), y) for y in ys[::-1]]  # left side, base -> top
        poly += [(cx + rad(y), y) for y in ys]       # right side, top -> base
        m = mask(lambda dr, s: dr.polygon([(x * s, y * s) for x, y in poly], fill=255))

        # analytic cylinder shading
        y0, y1 = int(top) - 2, int(base) + 2
        sub = slice(y0, y1)
        yv = yy[sub]
        rv = rad(np.clip(yv, top, base))
        u = np.clip((xx[sub] - cx) / rv, -1, 1)
        nz = np.sqrt(1 - u * u)
        lam = np.clip(u * 0.62 + nz * 0.50, 0, 1)
        col = SLAG[None, None] * 0.80 + (GRIT * 1.05 - SLAG * 0.80)[None, None] * lam[..., None] ** 1.5
        # vertical weathering streaks (subtle, mostly darkening)
        st = noise(y1 - y0, W, r, 700, 22, 4, 0.5)
        col = col * (1 + 0.035 * st[..., None])
        # horizontal formwork lift lines
        lift = (np.mod(yv - top, h / 38.0) < 1.6).astype(np.float32)
        col = col * (1 - 0.06 * lift[..., None])
        # soot / water stains bleeding down from the rim (darken only)
        rs = np.clip(noise(y1 - y0, W, r, 500, 60, 3), 0, 2)
        rim_fall = np.exp(-((yv - top) / (0.40 * h)))
        col = col * (1 - 0.22 * (rs * rim_fall)[..., None]) + RUST * 0.025 * (rs * rim_fall)[..., None]
        # limb darkening
        col = col * (1 - 0.30 * smoothstep(0.75, 1.0, np.abs(u)))[..., None]

        if broken:
            # missing chunk of the near wall: reveals the dark inside of the far wall
            x0, x1 = cx - 0.10 * rt, cx + rt * 0.80
            n = 30
            edge = []
            for i in range(n + 1):
                uu = i / n
                x = x0 + (x1 - x0) * uu
                depth = math.sin(uu * math.pi) ** 0.6 * h * 0.15
                depth += r.uniform(-1, 1) * h * 0.016
                if i in (0, n):
                    depth = 0
                edge.append((x + r.uniform(-4, 4), top + max(0, depth)))
            hole = [(x0, top - 3)] + edge + [(x1, top - 3)]
            mh = mask(lambda dr, s: dr.polygon([(x * s, y * s) for x, y in hole], fill=255))[sub]
            # inner face: lit from the left-inside (reverse gradient), darker
            inner = SLAG[None, None] * (0.62 + 0.38 * np.clip(-u, 0, 1) ** 0.7)[..., None]
            inner = inner * (1 + 0.04 * st[..., None])
            col = col * (1 - mh[..., None]) + inner * mh[..., None]
            # broken wall thickness: a lighter fractured lip along the edge
            def lip(dr, s):
                pts = [(x * s, (y + 2) * s) for x, y in edge]
                dr.line(pts, fill=255, width=int(4 * s), joint='curve')
            ml = mask(lip)[sub] * m[sub]
            col = col * (1 - ml[..., None] * 0.7) + (GRIT * 1.15)[None, None] * ml[..., None] * 0.7
            # a slight shadow just under the lip on the inner face
            sh = gaussian_filter(ml, 3) * mh
            col = col * (1 - 0.0 * sh[..., None])
            self_edge = edge

        # haze increases toward the ground
        lowhaze = smoothstep(top + 0.45 * h, base, yv) * 0.30
        f = np.clip(fog + lowhaze * (1 - fog), 0, 1)[..., None]
        col = col * (1 - f) + (GRIT * 0.85 + DUST * 0.15) * f
        img[sub] = over(img[sub], col, m[sub])

        # base: ring of diagonal support columns (dark gap)
        bh = 0.035 * h
        rb = float(rad(base))

        def legs(dr, s):
            dr.rectangle([(cx - rb * 0.995) * s, (base - bh) * s, (cx + rb * 0.995) * s, base * s], fill=255)
        mb = mask(legs)
        img = over(img, fogged(ASH * 1.2, min(1, fog * 1.1 + 0.1)), mb * 0.95)

        def legs2(dr, s):
            n = int(rb / 7)
            for i in range(n + 1):
                # columns foreshortened toward the silhouette edges
                th = -math.pi / 2 + math.pi * i / n
                x = cx + rb * math.sin(th)
                w = max(1, int(2.0 * s * (1 - fog) * math.cos(th) ** 0.5 + 0.5))
                dr.line([(x * s, base * s), ((x + bh * 0.7) * s, (base - bh) * s)], fill=255, width=w)
                dr.line([(x * s, base * s), ((x - bh * 0.7) * s, (base - bh) * s)], fill=255, width=w)
        ml2 = mask(legs2) * mb
        img = over(img, fogged(SLAG * 1.15, fog), ml2 * 0.9)

        if broken:
            def cracks(dr, s):
                for k, (sx_, depthf) in enumerate([(0.42, 0.55), (-0.02, 0.28)]):
                    x = cx + rt * sx_
                    y = top + h * 0.13 * (1 if k == 0 else 0.4)
                    pts = [(x, y)]
                    for i in range(int(22 * depthf) + 2):
                        x += r.uniform(-11, 9)
                        y += r.uniform(14, 28)
                        pts.append((x, y))
                    dr.line([(p * s, q * s) for p, q in pts], fill=255, width=2 * s)
            mc = mask(cracks) * m
            img = over(img, fogged(ASH * 1.2, fog), mc * 0.75)

            def rebar(dr, s):
                for x, y in self_edge[2:-2:2]:
                    ln = r.uniform(8, 34)
                    ang = r.uniform(-0.7, 0.35) - math.pi / 2
                    dr.line([(x * s, y * s), ((x + math.cos(ang) * ln) * s, (y + math.sin(ang) * ln) * s)],
                            fill=255, width=max(1, int(1.3 * s)))
            mr = mask(rebar)
            img = over(img, fogged(SLAG * 0.85, fog), mr * 0.8)
        return img

    img = tower(img, 760, 600, 128, 228, fog=0.62, seed=11)
    img = tower(img, 2470, 780, 165, 292, fog=0.42, seed=12)
    img = tower(img, 1560, 1000, 212, 372, fog=0.18, broken=True, seed=13)

    # low smog creeping over the tower bases
    n = noise(H, W, rng, 70, 700, 5, 0.55)
    prof = np.exp(-((yy - (HY - 40)) / 130) ** 2)
    img = over(img, GRIT * 0.9 + DUST * 0.1, np.clip(prof * (0.42 + 0.22 * n), 0, 0.75))

    # ---- ground -------------------------------------------------------------
    g = (yy - HY) / (H - HY)
    gmask = smoothstep(HY - 1, HY + 1, yy)
    gt = np.clip(g, 0, 1)[..., None]
    gcol = (SLAG * 0.95) * (1 - gt) + ASH * gt
    tex = noise(H, W, rng, 40, 420, 5, 0.6)
    gcol = gcol * (1 + 0.10 * tex[..., None])
    # horizon haze on ground
    gcol = over(gcol, GRIT * 0.9, np.exp(-np.clip(g, 0, 9) * 9) * 0.65)
    img = img * (1 - gmask[..., None]) + gcol * gmask[..., None]

    # tire ruts / drainage lines converging towards the horizon
    def ruts(dr, s):
        r = np.random.default_rng(SEED + 99)
        for i in range(9):
            xb = r.uniform(-800, W + 800)
            vx = 1500 + r.uniform(-200, 200)
            pts = []
            for k in range(30):
                u = k / 29
                y = HY + 6 + (H - HY) * u ** 1.6
                f = (y - HY) / (H - HY)
                x = vx + (xb - vx) * f + r.uniform(-3, 3) * f * 8
                pts.append((x * s, y * s))
            dr.line(pts, fill=int(r.uniform(90, 200)), width=int(2 * s))
    mr = mask(ruts)
    mr = mr * smoothstep(HY, HY + 200, yy)
    img = over(img, ASH, mr * 0.45)

    # ---- pylon row ----------------------------------------------------------
    VPX = 2050.0

    def pylon_lines(x, yb, hgt, broken=False, tilt=0.0):
        """Return list of polylines (in px) and widths for a lattice pylon."""
        L = []

        def P(u, v):
            # u: horizontal (units of height), v: height fraction
            px = x + u * hgt + tilt * v * v * hgt
            return (px, yb - v * hgt)
        top_v = 0.72 if broken else 1.0
        legs = [(-0.13, 0.0), (-0.045, 0.55), (-0.028, 0.86), (-0.012, 1.0)]
        lw = [P(u, v) for u, v in legs if v <= top_v + 1e-6]
        rw = [P(-u, v) for u, v in legs if v <= top_v + 1e-6]
        L.append((lw, 2.6))
        L.append((rw, 2.6))

        def halfw(v):
            for (u0, v0), (u1, v1) in zip(legs, legs[1:]):
                if v0 <= v <= v1:
                    return -(u0 + (u1 - u0) * (v - v0) / (v1 - v0))
            return 0.012
        # X bracing
        vs = [0.0, 0.08, 0.16, 0.24, 0.32, 0.40, 0.48, 0.55, 0.62, 0.70, 0.78, 0.86, 0.93, 1.0]
        vs = [v for v in vs if v <= top_v]
        for v0, v1 in zip(vs, vs[1:]):
            L.append(([P(-halfw(v0), v0), P(halfw(v1), v1)], 1.2))
            L.append(([P(halfw(v0), v0), P(-halfw(v1), v1)], 1.2))
            L.append(([P(-halfw(v1), v1), P(halfw(v1), v1)], 1.0))
        arms = []
        for v, wd in [(0.62, 0.36), (0.78, 0.29), (0.90, 0.22)]:
            if v > top_v:
                continue
            hw = halfw(v)
            L.append(([P(-wd, v), P(wd, v)], 2.0))
            L.append(([P(-wd, v), P(-hw, v + 0.045), P(hw, v + 0.045), P(wd, v)], 1.4))
            # hanging insulator strings
            for sgn in (-1, 1):
                a = P(sgn * (wd - 0.015), v)
                b = (a[0], a[1] + 0.045 * hgt)
                L.append(([a, b], 1.6))
                arms.append(b)
        if broken:
            # snapped stub bent sideways
            a = P(0, top_v)
            L.append(([P(-halfw(top_v), top_v), (a[0] + 0.20 * hgt, a[1] + 0.06 * hgt)], 2.2))
            L.append(([P(halfw(top_v), top_v), (a[0] + 0.26 * hgt, a[1] + 0.12 * hgt)], 2.0))
        else:
            L.append(([P(-0.012, 1.0), P(0, 1.06), P(0.012, 1.0)], 1.6))
        return L, arms

    pyl = []
    dists = [1.0, 1.75, 2.9, 4.6, 7.0, 10.5, 15.5, 23, 34]
    X0, YB0, H0 = 3380.0, 2120.0, 1180.0
    for i, dd in enumerate(dists):
        x = VPX + (X0 - VPX) / dd
        yb = HY + (YB0 - HY) / dd
        hgt = H0 / dd
        broken = (i == 2)
        tilt = 0.05 if i == 4 else 0.0
        pyl.append((x, yb, hgt, broken, tilt, dd))

    # draw from far to near so fog layering is right
    arms_by = []
    for (x, yb, hgt, broken, tilt, dd) in pyl:
        L, arms = pylon_lines(x, yb, hgt, broken, tilt)
        arms_by.append(arms)
    for idx in range(len(pyl) - 1, -1, -1):
        x, yb, hgt, broken, tilt, dd = pyl[idx]
        L, arms = pylon_lines(x, yb, hgt, broken, tilt)
        scale = max(0.6, 2.2 / dd ** 0.55)

        def drawp(dr, s, L=L, scale=scale):
            for pts, w in L:
                dr.line([(p * s, q * s) for p, q in pts], fill=255,
                        width=max(1, int(round(w * scale * s))), joint='curve')
        m = mask(drawp)
        fog = min(0.92, 0.08 + 0.12 * (dd - 1))
        img = over(img, fogged(ASH * 1.15, fog), m)

        # cables to the next (farther) pylon
        if idx + 1 < len(pyl):
            a_near, a_far = arms_by[idx], arms_by[idx + 1]
            k = min(len(a_near), len(a_far))

            def drawc(dr, s, a_near=a_near, a_far=a_far, k=k, idx=idx):
                rr = np.random.default_rng(SEED + 300 + idx)
                for j in range(k):
                    (x0, y0), (x1, y1) = a_near[j], a_far[j]
                    span = abs(x0 - x1) + abs(y0 - y1)
                    sag = 0.07 * span + 6
                    snapped = (idx == 1 and j in (0, 2)) or (idx == 2)
                    pts = []
                    if snapped:
                        # dangling from the near pylon
                        ln = rr.uniform(0.25, 0.55) * (yb - y0) if False else rr.uniform(120, 360) / dd ** 0.3
                        for t in np.linspace(0, 1, 30):
                            pts.append(((x0 + (x1 - x0) * 0.06 * t + 8 * t * t) * s, (y0 + ln * t ** 1.3) * s))
                    else:
                        for t in np.linspace(0, 1, 60):
                            px = x0 + (x1 - x0) * t
                            py = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
                            pts.append((px * s, py * s))
                    dr.line(pts, fill=255, width=max(1, int(round(1.5 * s / dd ** 0.3))))
            mc = mask(drawc)
            img = over(img, fogged(ASH * 1.2, fog * 0.9), mc * 0.85)

    # ---- foreground: low rubble bank + dead stalks, bottom left -------------
    r = np.random.default_rng(SEED + 700)

    def bank(dr, s):
        pts = [(0, H * s)]
        x = 0.0
        while x <= 2300:
            u = x / 2300
            y = H - 340 * (1 - u) ** 1.5 - 30 + r.uniform(-1, 1) * 10 * (1 - u)
            if r.random() < 0.10:  # angular debris lumps
                pts.append((x * s, (y - r.uniform(10, 45) * (1 - u)) * s))
            pts.append((x * s, y * s))
            x += r.uniform(10, 40)
        pts += [(2300 * s, H * s)]
        dr.polygon(pts, fill=255)
    mbk = mask(bank)
    bt = noise(H, W, r, 30, 90, 4, 0.6)
    bcol = (ASH * 1.05)[None, None] * (1 + 0.12 * bt[..., None])
    img = img * (1 - mbk[..., None]) + bcol * mbk[..., None]
    # faint rim light on the bank top edge from the hazy sky
    rimb = gaussian_filter(np.clip(mbk - np.roll(mbk, 4, axis=0), 0, 1), 1.5)
    img = over(img, GRIT * 0.9, rimb * 0.25)

    def stalks(dr, s):
        for _ in range(160):
            x = r.uniform(0, 2000)
            u = x / 2300
            yb = H - 340 * (1 - u) ** 1.5 - 22
            ln = r.uniform(30, 150) * (1 - u) ** 0.7 + 8
            ang = -math.pi / 2 + r.uniform(-0.35, 0.25)
            bend = r.uniform(-0.2, 0.2)
            pts = []
            for t in np.linspace(0, 1, 8):
                a2 = ang + bend * t * t * 3
                pts.append(((x + math.cos(a2) * ln * t) * s, (yb + math.sin(a2) * ln * t) * s))
            dr.line(pts, fill=255, width=max(1, int(1.6 * s * (1 - u) + 1)))
    mst = mask(stalks)
    img = over(img, ASH * 1.1, mst * 0.95)

    # ---- falling ash -------------------------------------------------------
    r = np.random.default_rng(SEED + 500)
    fine = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(fine)
    for _ in range(5200):
        x, y = r.uniform(0, W), r.uniform(0, H)
        sz = r.choice([1.0, 1.4, 1.8, 2.4], p=[.45, .3, .17, .08])
        ln = sz * r.uniform(1.0, 2.6)
        v = int(r.uniform(60, 200))
        dr.line([(x, y), (x - ln * 0.35, y - ln)], fill=v, width=max(1, int(sz)))
    fine = np.asarray(fine, np.float32) / 255
    fine = gaussian_filter(fine, 0.6)
    big = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(big)
    for _ in range(170):
        x, y = r.uniform(0, W), r.uniform(0, H)
        sz = r.uniform(6, 16)
        v = int(r.uniform(70, 180))
        dr.ellipse([x - sz, y - sz * 0.8, x + sz, y + sz * 0.8], fill=v)
    big = gaussian_filter(np.asarray(big, np.float32) / 255, 5)
    ashcol = BONE * 0.8 + DUST * 0.2
    img = over(img, ashcol, fine * 0.30 + big * 0.22)

    # very soft overall bloom of the sky glow (gives the air a dusty density)
    img = img + (gaussian_filter(np.maximum(img.mean(axis=2) - 0.25, 0), 60)[..., None]
                 * (DUST * 0.6)[None, None] * 0.35)

    img = finish(img, rng, grain=0.011, vig=0.55)
    save(img, out)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/walls_new/cooling-towers.png')
