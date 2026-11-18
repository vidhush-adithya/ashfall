#!/usr/bin/env python3
"""Ash-chan: original ASHFALL pixel-art mascot (chibi, helmet, twin tails). One PNG per mood."""
import sys, os
from PIL import Image

OUT = sys.argv[1] if len(sys.argv) > 1 else "ashchan"
SCALE = int(sys.argv[2]) if len(sys.argv) > 2 else 12
os.makedirs(OUT, exist_ok=True)
W = 32

P = {
    "O": (20, 18, 15), "H": (93, 106, 72), "h": (63, 74, 50), "R": (154, 131, 72), "r": (20, 18, 15),
    "A": (122, 98, 76), "a": (90, 72, 56), "S": (198, 170, 146), "s": (164, 136, 116),
    "E": (34, 30, 26), "W": (214, 204, 186), "I": (139, 98, 60), "B": (172, 112, 92), "M": (122, 51, 41),
    "G": (110, 102, 87), "g": (74, 68, 58), "J": (79, 90, 60), "j": (58, 66, 44), "K": (42, 38, 32),
    "D": (120, 150, 170), "Z": (168, 159, 140), "X": (214, 196, 140), "F": (154, 131, 72), "P": (110, 102, 87),
}
def C(s): return s.center(W, ".")
def face(inner, hl="AA", hr="AA"):
    assert len(inner) == 16, inner
    return C("O" + hl + inner + hr + "O")

TOP = [
    C("OOOOOOOO"),
    C("OOHHHHHHHHOO"),
    C("OHHHHHHRRHHHHHHO"),
    C("OHHHHHHRrrRHHHHHHO"),
    C("OhHHHHHHHRRHHHHHHHhO"),
    C("OhhhhhhhhhhhhhhhhhhhhO"),
    C("OOOOOOOOOOOOOOOOOOOOOOOO"),
    face("AAAaAAAAAAaAAAAA"),
    face("AASAAaSSSSaAASAA"),
    face("SSSSSSSSSSSSSSSS"),
]
EYES = {  # rows 10..16 of the face (7 rows)
    "neutral": ["SOOOOSSSSSSOOOOS", "SSWEESSSSSSWEESS", "SSEEESSSSSSEEESS", "SSIIISSSSSSIIISS",
                "BBSSSSSSSSSSSSBB", "SSSSSSSMMSSSSSSS", "SSSSSSSSSSSSSSSS"],
    "happy":   ["SSSSSSSSSSSSSSSS", "SSSOSSSSSSSSOSSS", "SSOSOSSSSSSOSOSS", "SOSSSOSSSSOSSSOS",
                "BBSSSSSMMSSSSSBB", "SSSSSSSMMSSSSSSS", "SSSSSSSSSSSSSSSS"],
    "panic":   ["SOOOOSSSSSSOOOOS", "SSWWWSSSSSSWWWSS", "SSWEWSSSSSSWEWSS", "SSWWWSSSSSSWWWSS",
                "BBSSSSSSSSSSSSBB", "SSSSSMSMSMSSSSSS", "SSSSSSMSMSSSSSSS"],
    "sleepy":  ["SSSSSSSSSSSSSSSS", "SSSSSSSSSSSSSSSS", "SOOOOSSSSSSOOOOS", "SSSSSSSSSSSSSSSS",
                "BBSSSSSSSSSSSSBB", "SSSSSSSOSSSSSSSS", "SSSSSSSSSSSSSSSS"],
    "smug":    ["SSSSSSSSSSSSSSSS", "SOOOOSSSSSSOOOOS", "SSEEESSSSSSEEESS", "SSIIISSSSSSIIISS",
                "BBSSSSMSSMSSSSBB", "SSSSSSSMMSSSSSSS", "SSSSSSSSSSSSSSSS"],
    "flag":    ["SSSXSSSSSSSSXSSS", "SSXXXSSSSSSXXXSS", "SXXXXXSSSSXXXXXS", "SSXXXSSSSSSXXXSS",
                "BBSSSXSMMSSXSSBB", "SSSSSSSMMSSSSSSS", "SSSSSSSSSSSSSSSS"],
}
BOTTOM = [
    C("OAasSSSSSSSSSSSSSSsaAO"),
    C("OOOssssssssssssOOO"),
    C("OGGGGggggGGGGO"),
    C("OJJJGGGggGGGJJJO"),
    C("OJJJJJJJJJJJJJJJJO"),
    C("OSJJJJjJJJJJJjJJJJSO"),
    C("OSOJJJJjJJJJjJJJJOSO"),
    C("O.OJJJJJJJJJJJJO.O"),
    C("OKKKO....OKKKO"),
    C("OOOOO....OOOOO"),
]
def build(m):
    rows = TOP + [face(r) for r in EYES[m]] + BOTTOM
    g = [list(r) for r in rows]
    # twin tails: hang from the sides of the head, rows 8..21
    for y in range(8, 22):
        span = 3 if 10 <= y <= 18 else 2
        for k in range(span):
            lx, rx = 3 - k, W - 4 + k
            if g[y][lx] == ".": g[y][lx] = "a" if k == span - 1 else "A"
            if g[y][rx] == ".": g[y][rx] = "a" if k == span - 1 else "A"
        g[y][4 - span] = "O" if g[y][4 - span] == "." else g[y][4 - span]
    for y, x, c in EXTRA.get(m, []):
        g[y][x] = c
    return ["".join(r) for r in g]
EXTRA = {
    "panic": [(9, 24, "D"), (10, 25, "D"), (11, 25, "D")],
    "sleepy": [(2, 26, "Z"), (1, 28, "Z"), (0, 30, "Z")],
    "flag": [(y, 29, "P") for y in range(10, 27)] + [(y, x, "F") for y in range(10, 14) for x in range(25, 29)] + [(11, 26, "r"), (12, 27, "r")],
}
for m in EYES:
    rows = build(m)
    h = len(rows)
    im = Image.new("RGBA", (W, h), (0, 0, 0, 0))
    for y, r in enumerate(rows):
        for x, c in enumerate(r):
            col = P.get(c)
            if col: im.putpixel((x, y), col + (255,))
    im.resize((W * SCALE, h * SCALE), Image.NEAREST).save(os.path.join(OUT, f"ashchan-{m}.png"))
print("ok", list(EYES))
