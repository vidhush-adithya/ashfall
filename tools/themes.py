#!/usr/bin/env python3
"""ASHFALL theme variants: palettes + recoloured wallpapers."""
import sys, os
from PIL import Image, ImageOps

THEMES = {
  "ashfall": dict(name="ASHFALL", tag="The original. Ash, bone, rust and dull ochre under a smothered sun.",
    bg="#0c0b09", panel="#14120f", line="#2a2620", dim="#6e6657", fg="#a89f8c", hi="#c2b8a3",
    accent="#8b5a3c", accent2="#9a8348", ok="#5d6a48", bad="#7a3329", steel="#556270",
    wall=("#060504", "#3a2a1c", "#a08a68")),
  "winter": dict(name="NUCLEAR WINTER", tag="Frozen steel and frost-blue. Cold, quiet, clinical.",
    bg="#0a0c0e", panel="#11151a", line="#242c33", dim="#5f6b75", fg="#9aa5ad", hi="#bcc5cb",
    accent="#5e7a8c", accent2="#8a9ba5", ok="#5f7a6e", bad="#7a4048", steel="#6a7f91",
    wall=("#040506", "#26313a", "#8d9aa4")),
  "phosphor": dict(name="VAULT PHOSPHOR", tag="A dying green CRT in a sealed bunker. Low glow, no neon.",
    bg="#080a07", panel="#0e120c", line="#1f281b", dim="#4f6145", fg="#8fa883", hi="#aec2a2",
    accent="#5f7f4f", accent2="#a3a86a", ok="#6b8a57", bad="#7a4a3a", steel="#5a7468",
    wall=("#030402", "#1d2a17", "#7f9a70")),
  "redzone": dict(name="RED ZONE", tag="Embers and dried blood. For when the sirens never stopped.",
    bg="#0d0908", panel="#160f0d", line="#2e1d19", dim="#6f5550", fg="#b09a92", hi="#c9b5ad",
    accent="#8e3b2e", accent2="#a8674e", ok="#6b6a48", bad="#a03a2e", steel="#6a5a62",
    wall=("#050303", "#3a1712", "#a8857a")),
  "dust": dict(name="DUST STORM", tag="Sepia sand and sun-bleached brass. A desert that ate a city.",
    bg="#100d09", panel="#1a150f", line="#33291d", dim="#7a6a52", fg="#c0ae8c", hi="#d4c4a4",
    accent="#a07a45", accent2="#7f6a3e", ok="#6f7048", bad="#84402e", steel="#6b6a5e",
    wall=("#070504", "#4a3622", "#b8a07a")),
  "bog": dict(name="TOXIC BOG", tag="Murky olive and chemical yellow-green. Don't drink the water.",
    bg="#0a0b07", panel="#12140d", line="#262a1b", dim="#5f6447", fg="#a3a382", hi="#bdbd9c",
    accent="#7d8a3c", accent2="#6f7a5a", ok="#6b7d45", bad="#7c4630", steel="#5a6a60",
    wall=("#040402", "#2a2e14", "#9a9a74")),
}

def walls(src, outdir, size=None, fmt="jpg"):
    os.makedirs(outdir, exist_ok=True)
    g = ImageOps.grayscale(Image.open(src))
    g = ImageOps.autocontrast(g, cutoff=0.5)
    if size: g = g.resize(size, Image.LANCZOS)
    for k, t in THEMES.items():
        b, m, w = t["wall"]
        img = ImageOps.colorize(g, black=b, mid=m, white=w, midpoint=150)
        p = os.path.join(outdir, f"{k}.{fmt}")
        img.save(p, quality=82, optimize=True) if fmt == "jpg" else img.save(p, optimize=True)
        print(p)

if __name__ == "__main__":
    walls(sys.argv[1], sys.argv[2], tuple(map(int, sys.argv[3].split("x"))) if len(sys.argv) > 3 else None,
          sys.argv[4] if len(sys.argv) > 4 else "jpg")
