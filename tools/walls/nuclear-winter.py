#!/usr/bin/env python3
"""ASHFALL wallpaper: nuclear-winter
Snow-buried rubble field, a row of lattice pylons with sagging cables vanishing
into freezing fog, wind-driven snow.  Usage: python3 nuclear-winter.py out.png
"""
import sys, math
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import gaussian_filter

W, H = 3840, 2160
SS = 2  # supersampling for vector masks
SEED = 0x5E0C0D


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




# cold palette
C0, C1, C2, C3 = map(hexc, ['#0a0c0e', '#11151a', '#242c33', '#5f6b75'])
C4, CB, CMAX = map(hexc, ['#9aa5ad', '#5e7a8c', '#bcc5cb'])


def shift_down(m, k):
    out = np.zeros_like(m)
    if k <= 0:
        return m.copy()
    out[k:] = m[:-k]
    return out


# ------------------------------------------------------------------- scene --
def main(out):
    rng = np.random.default_rng(SEED)
    HY = 1300  # horizon (mostly lost in fog)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    FOG = C3 * 0.85 + CB * 0.10 + C4 * 0.05

    # ---- sky: dark overcast fading into bright-ish freezing fog -------------
    t = np.clip(yy / HY, 0, 1)[..., None]
    img = C1 * (1 - t) ** 1.0 + (C2 * 0.35 + FOG * 0.65) * t
    img = img * (1 - t ** 3 * 0.25) + FOG * t ** 3 * 0.25
    # cloud mottling
    n = noise(H, W, rng, 260, 1100, 5, 0.55)
    cl = np.clip(0.5 + 0.5 * n, 0, 1) * (1 - t[..., 0]) ** 0.6
    img = over(img, C2 * 1.1, cl * 0.35)
    # wind-torn veils of fog drifting across the sky, denser toward the horizon
    for yc, th, a0, sx in [(380, 260, 0.20, 1500), (720, 300, 0.28, 1200), (1020, 260, 0.34, 900)]:
        n2 = noise(H, W, rng, 90, sx, 5, 0.55)
        # shear the veils slightly with the wind
        n2 = np.roll(n2, 0, axis=1)
        prof = np.exp(-((yy - yc) / th) ** 2)
        img = over(img, C3 * 0.9 + CB * 0.1, np.clip(prof * (0.35 + 0.45 * n2), 0, 1) * a0)
    # very faint diffuse light patch (sun lost in the overcast)
    d = np.sqrt((xx - 2700) ** 2 + ((yy - 520) * 1.6) ** 2)
    img = img + (CB * 0.5 + C3 * 0.5) * (np.exp(-(d / 900) ** 2) * 0.16)[..., None]

    def fogcol(col, f):
        return col * (1 - f) + FOG * f

    # ---- depth-sorted layers: rubble rows and pylons -----------------------
    YB0 = 2250.0  # ground y at depth 1 (just below frame)

    def ground_y(d):
        return HY + (YB0 - HY) / d

    def fog_of(d):
        return float(np.clip(1 - math.exp(-(d - 0.9) / 7.5), 0, 0.97))

    r = np.random.default_rng(SEED + 1)

    def rubble_layer(img, d, seed):
        rr = np.random.default_rng(SEED + 100 + seed)
        gy = ground_y(d)
        sc = 1.0 / d  # px scale
        amp = 560 * sc  # rubble pile height at this depth
        step = max(3, int(14 * sc ** 0.5))
        xs = np.arange(-60, W + 61, step, dtype=np.float32)
        prof = np.zeros_like(xs)
        for fl, a in [(1300, 1.0), (520, 0.55), (190, 0.30), (70, 0.16)]:
            fl2 = fl * sc ** 0.6
            ph = rr.uniform(0, 1000)
            k = rr.uniform(0.7, 1.3)
            prof += a * (np.sin(xs / fl2 * k + ph) * 0.6 + np.sin(xs / fl2 * 1.9 * k + ph * 1.3) * 0.4)
        # small-scale jagged roughness (broken material), smoothed random walk
        rw = gaussian_filter(rr.normal(0, 1, xs.size), 1.2)
        prof += 0.22 * rw
        heap = np.zeros_like(xs)
        for _ in range(int(5 + 4 * rr.random())):
            cxh = rr.uniform(-200, W + 200)
            wh = rr.uniform(120, 650) * sc ** 0.5
            heap += rr.uniform(0.3, 1.1) * np.exp(-np.abs((xs - cxh) / wh) ** 1.4)
        top = gy - amp * (0.10 + 0.16 * (prof * 0.5 + 0.5) + 0.55 * heap)
        slope = np.gradient(top, step)

        tpoly = [(-80, H + 10)] + list(zip(xs.tolist(), top.tolist())) + [(W + 80, H + 10)]
        polys, lines = [], []
        nch = int(22 + 12 * rr.random())
        for _ in range(nch):
            x = rr.uniform(-100, W + 100)
            yt = float(np.interp(x, xs, top))
            kind = rr.choice(['slab', 'block', 'rebar', 'beam'], p=[.45, .22, .18, .15])
            s = amp * rr.uniform(0.15, 0.42)
            if kind == 'slab':
                ang = rr.uniform(-0.9, 0.9)
                L, T = s * rr.uniform(1.6, 3.4), s * rr.uniform(0.14, 0.26)
                ca, sa = math.cos(ang), math.sin(ang)
                cx, cy = x, yt + T * 0.2
                pts = [(-L / 2, -T / 2), (L / 2, -T / 2), (L / 2, T / 2), (-L / 2, T / 2)]
                polys.append([(cx + px * ca - py * sa, cy + px * sa + py * ca) for px, py in pts])
            elif kind == 'block':
                bw, bh = s * rr.uniform(1.2, 2.4), s * rr.uniform(0.5, 1.0)
                sk = rr.uniform(-0.2, 0.2) * bw
                polys.append([(x, yt + bh * 0.5), (x + sk, yt - bh), (x + bw * 0.6 + sk, yt - bh * rr.uniform(0.8, 1.2)),
                              (x + bw + sk, yt - bh * rr.uniform(0.6, 0.9)), (x + bw, yt + bh * 0.5)])
            elif kind == 'rebar':
                for _ in range(rr.integers(2, 6)):
                    ang = -math.pi / 2 + rr.uniform(-1.0, 1.0)
                    ln = s * rr.uniform(0.6, 1.7)
                    bend = rr.uniform(-0.8, 0.8)
                    x0 = x + rr.uniform(-30, 30) * sc
                    pts = []
                    for tt in np.linspace(0, 1, 7):
                        a2 = ang + bend * tt * tt
                        pts.append((x0 + math.cos(a2) * ln * tt, yt + 6 * sc + math.sin(a2) * ln * tt))
                    lines.append((pts, max(1.0, 4.5 * sc)))
            else:
                ang = -math.pi / 2 + rr.uniform(-1.1, 1.1)
                ln = s * rr.uniform(1.0, 2.4)
                lines.append(([(x, yt + 10 * sc), (x + math.cos(ang) * ln, yt + math.sin(ang) * ln)],
                              max(1.5, 20 * sc)))

        mt = mask(lambda dr, s: dr.polygon([(a * s, b * s) for a, b in tpoly], fill=255))

        def ch_fn(dr, s):
            for p in polys:
                dr.polygon([(a * s, b * s) for a, b in p], fill=255)
        mc = mask(ch_fn)

        def ln_fn(dr, s):
            for pts, w in lines:
                dr.line([(a * s, b * s) for a, b in pts], fill=255, width=max(1, int(w * s)), joint='curve')
        ml = mask(ln_fn)

        y0 = max(0, int(min(np.min(top) - amp, H - 1)))
        sub = slice(y0, H)
        hh = H - y0
        Y = yy[sub]
        topc = np.interp(np.arange(W, dtype=np.float32), xs, top)[None, :]
        slc = np.interp(np.arange(W, dtype=np.float32), xs, slope)[None, :]
        dist = Y - topc  # depth below the pile surface

        sn = noise(hh, W, rr, max(6, 80 * sc), max(12, 260 * sc), 4, 0.55)
        sn1 = np.interp(np.arange(W, dtype=np.float32), xs,
                        gaussian_filter(rr.normal(0, 1, xs.size), 3) * 2.5)[None, :]
        sd = amp * np.clip(0.30 + 0.12 * sn1, 0.08, 0.6)  # snow depth
        steep = smoothstep(0.7, 1.8, np.abs(slc))
        snow = smoothstep(sd, sd * 0.35, dist) * (1 - 0.85 * steep)
        snow = np.clip(snow + 0.18 * np.clip(sn, 0, 2) * smoothstep(sd * 2, sd, dist), 0, 1)

        # snow shading: bright crest, cooler/darker deeper down, lit slightly from upper left
        u = np.clip(dist / (sd + 1), 0, 1.5)
        lit = np.clip(0.72 - 0.42 * u - 0.10 * slc + 0.05 * sn, 0.15, 0.85)[..., None]
        snowcol = C3 * 0.85 * (1 - lit) + (C4 * 0.84 + CB * 0.16) * lit
        body = C1 * (1 + 0.30 * sn[..., None]) * (1 - 0.3 * smoothstep(0, amp, dist))[..., None]
        col = body * (1 - snow[..., None]) + snowcol * snow[..., None]

        # chunks: dark concrete faces with snow caps
        b = mc[sub] > 0.5
        cs = np.cumsum(b, axis=0)
        reset = np.maximum.accumulate(np.where(~b, cs, 0), axis=0)
        cd = (cs - reset).astype(np.float32)
        cap = smoothstep(max(2, 16 * sc), max(1, 5 * sc), cd)
        cface = C2 * (0.65 + 0.25 * sn[..., None])
        ccol = cface * (1 - cap[..., None]) + (C4 * 0.72 + CB * 0.12 + C3 * 0.16) * cap[..., None]
        col = col * (1 - mc[sub][..., None]) + ccol * mc[sub][..., None]
        col = col * (1 - ml[sub][..., None]) + (C0 * 1.3) * ml[sub][..., None]

        f = fog_of(d)
        # pockets of fog between rows: more fog deeper below the crest line
        fl = f + (1 - f) * 0.45 * smoothstep(0, amp * 1.1, dist)
        col = fogcol(col, fl[..., None])
        a = np.maximum(np.maximum(mt[sub], mc[sub]), ml[sub])
        img[sub] = over(img[sub], col, a)
        return img

    def pylon_draw(x, yb, hgt, broken=False, lean=0.0):
        L, arms = [], []

        def P(u, v):
            return (x + u * hgt + lean * v * v * hgt, yb - v * hgt)
        legs = [(0.0, 0.135), (0.55, 0.048), (0.80, 0.030), (1.0, 0.016)]

        def hw(v):
            for (v0, a0), (v1, a1) in zip(legs, legs[1:]):
                if v0 <= v <= v1:
                    return a0 + (a1 - a0) * (v - v0) / (v1 - v0)
            return 0.016
        vmax = 0.62 if broken else 1.0
        for sg in (-1, 1):
            pts = [P(sg * a, v) for v, a in legs if v <= vmax]
            if broken:
                pts.append(P(sg * hw(vmax), vmax))
            L.append((pts, 3.2))
        vs = [0, .07, .14, .21, .28, .35, .42, .49, .55, .62, .69, .76, .82, .88, .94, 1.0]
        vs = [v for v in vs if v <= vmax]
        for v0, v1 in zip(vs, vs[1:]):
            L.append(([P(-hw(v0), v0), P(hw(v1), v1)], 1.5))
            L.append(([P(hw(v0), v0), P(-hw(v1), v1)], 1.5))
            L.append(([P(-hw(v1), v1), P(hw(v1), v1)], 1.3))
        if not broken:
            for v, wd in [(0.69, 0.30), (0.88, 0.21)]:
                h0 = hw(v)
                L.append(([P(-wd, v), P(wd, v)], 2.6))
                L.append(([P(-wd, v), P(-hw(v + 0.06), v + 0.06), P(hw(v + 0.06), v + 0.06), P(wd, v)], 1.6))
                for sg in (-1, 1):
                    a = P(sg * (wd - 0.02), v)
                    bb = (a[0], a[1] + 0.055 * hgt)
                    L.append(([a, bb], 2.4))
                    arms.append(bb)
            L.append(([P(-0.016, 1.0), P(0, 1.05), P(0.016, 1.0)], 1.8))
        else:
            a = P(0, vmax)
            L.append(([P(-hw(vmax), vmax), (a[0] - 0.20 * hgt, a[1] + 0.08 * hgt)], 2.8))
            L.append(([P(hw(vmax), vmax), (a[0] - 0.13 * hgt, a[1] + 0.15 * hgt)], 2.4))
            L.append(([(a[0] - 0.20 * hgt, a[1] + 0.08 * hgt), (a[0] - 0.26 * hgt, a[1] + 0.32 * hgt)], 2.0))
        return L, arms

    # pylon row receding from left foreground into the fog
    VPX = 2650.0
    X0 = 330.0
    pdepths = [1.15, 1.9, 3.1, 4.9, 7.4, 11, 16, 23, 33]
    pyl = []
    for i, d in enumerate(pdepths):
        x = VPX + (X0 - VPX) / d
        yb = ground_y(d) - 60 / d
        hgt = 1500.0 / d
        pyl.append(dict(d=d, x=x, yb=yb, h=hgt, broken=(i == 3), lean=(-0.04 if i == 5 else 0.0)))
    for p in pyl:
        p['L'], p['arms'] = pylon_draw(p['x'], p['yb'], p['h'], p['broken'], p['lean'])

    def draw_pylon(img, i):
        p = pyl[i]
        d = p['d']
        scl = max(0.55, 2.3 / d ** 0.6)

        def fn(dr, s):
            for pts, w in p['L']:
                dr.line([(a * s, b * s) for a, b in pts], fill=255, width=max(1, int(round(w * scl * s))),
                        joint='curve')
        m = mask(fn)
        f = fog_of(d)
        img = over(img, fogcol(C0 * 1.2, f), m)
        # rime on the top of members
        k = max(1, int(round(3 / d ** 0.5)))
        thick = gaussian_filter(m, 1.5) > 0.6
        rime = m * (1 - shift_down(m, k)) * thick
        img = over(img, fogcol(C4 * 0.80, f), rime * 0.45)
        # cables to the next (farther) pylon; from the nearest also to off-frame left
        def cable(dr, s, a, b, sag, snap=False, seed=0):
            (x0, y0), (x1, y1) = a, b
            pts = []
            if snap:
                rr = np.random.default_rng(SEED + 900 + seed)
                ln = rr.uniform(0.35, 0.65) * (H - y0)
                for t in np.linspace(0, 1, 40):
                    pts.append(((x0 + (x1 - x0) * 0.08 * t + 30 * t * t / d) * s, (y0 + ln * t ** 1.2) * s))
            else:
                for t in np.linspace(0, 1, 80):
                    pts.append(((x0 + (x1 - x0) * t) * s, (y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)) * s))
            dr.line(pts, fill=255, width=max(1, int(round(2.6 * s / d ** 0.45))))
        if p['arms']:
            nxt = None
            for j in range(i + 1, len(pyl)):
                if pyl[j]['arms']:
                    nxt = pyl[j]
                    break

            def fnc(dr, s):
                if nxt is not None:
                    for k_, (a, b) in enumerate(zip(p['arms'], nxt['arms'])):
                        span = abs(a[0] - b[0])
                        cable(dr, s, a, b, 0.09 * span + 10, snap=(i == 2 and k_ in (0, 3)), seed=k_)
                if i == 0:
                    for a in p['arms']:
                        b = (a[0] - 1400, a[1] + 260)
                        cable(dr, s, a, b, 260)
            mc = mask(fnc)
            img = over(img, fogcol(C0 * 1.3, f * 0.92), mc * 0.9)
        # cables of a broken pylon: drooping from previous span onto the rubble
        return img

    layers = [(d, 'r', k) for k, d in enumerate([40, 30, 22, 16.5, 12.5, 9.5, 7.2, 5.5, 4.2, 3.2, 2.45, 1.85, 1.4, 1.08])]
    layers += [(p['d'] + 0.01, 'p', i) for i, p in enumerate(pyl)]
    layers.sort(key=lambda t: -t[0])

    for d, kind, k in layers:
        if kind == 'r':
            img = rubble_layer(img, d, k)
            # a band of ground fog after every few layers
            if k in (3, 6, 9):
                gy = ground_y(d)
                n = noise(H, W, rng, 50, 800, 4, 0.55)
                prof = np.exp(-((yy - gy) / (180 / d ** 0.3)) ** 2)
                img = over(img, FOG, np.clip(prof * (0.35 + 0.25 * n), 0, 0.7))
        else:
            img = draw_pylon(img, k)

    # ---- ruined wall fragments half buried, mid distance ---------------------
    # (drawn as part of a separate pass so they sit between rubble rows)

    # ---- wind-driven snow ----------------------------------------------------
    r = np.random.default_rng(SEED + 500)
    ang = math.radians(14)  # blowing left->right, slightly down
    ca, sa = math.cos(ang), math.sin(ang)
    streak = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(streak)
    for _ in range(16000):
        x, y = r.uniform(-200, W), r.uniform(0, H)
        ln = r.choice([6, 10, 16, 24, 40]) * r.uniform(0.7, 1.3)
        v = int(r.uniform(40, 150))
        w = int(r.choice([1, 1, 2, 2, 3]))
        dr.line([(x, y), (x + ca * ln, y + sa * ln)], fill=v, width=w)
    streak = gaussian_filter(np.asarray(streak, np.float32) / 255, 0.8)
    big = Image.new('L', (W, H), 0)
    dr = ImageDraw.Draw(big)
    for _ in range(260):
        x, y = r.uniform(-200, W), r.uniform(0, H)
        ln = r.uniform(30, 110)
        w = int(r.uniform(6, 16))
        dr.line([(x, y), (x + ca * ln, y + sa * ln)], fill=int(r.uniform(60, 160)), width=w)
    big = gaussian_filter(np.asarray(big, np.float32) / 255, 6)
    # gusting: modulate density with large-scale noise
    gust = np.clip(0.55 + 0.45 * noise(H, W, rng, 700, 1400, 3), 0.1, 1)
    img = over(img, C4 * 0.9 + CB * 0.1, (streak * 0.42 + big * 0.28) * gust)

    # spindrift: horizontal blowing snow sheets near ground
    n = noise(H, W, rng, 40, 1200, 5, 0.6)
    prof = smoothstep(HY + 60, H, yy) * (1 - smoothstep(H - 200, H, yy) * 0.3)
    img = over(img, C4 * 0.8 + C3 * 0.2, np.clip((0.15 + 0.22 * n) * prof, 0, 0.5) * 0.55)

    # global cold fog veil + slight bloom
    lum = img.mean(axis=2)
    img = img + gaussian_filter(np.maximum(lum - 0.30, 0), 40)[..., None] * (C4 * 0.5)[None, None] * 0.4

    img = finish(img, rng, grain=0.010, vig=0.55, cap='#bcc5cb')
    save(img, out)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '/home/claude/walls_new/nuclear-winter.png')
