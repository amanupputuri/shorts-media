"""Candidate formats 78-97 (new eye & brain set). Registered into eyebrain.DRAW on import."""
import math, random, itertools
from PIL import Image, ImageDraw
import eyebrain as E
from eyebrain import area, _opt_row, _emoji_opts, _label, glow_box, _circle_hit, _panel, _grid_geom, INKS
from engine import emoji_img, eob, eo, cl, paste, font, F_BOLD

INK = (30, 30, 60)
GREEN = (40, 190, 90)

def _t(d, x, y, s, size, fill=INK):
    f = font(F_BOLD, size); tw = d.textlength(s, font=f); d.text((x - tw / 2, y - size * 0.68), s, font=f, fill=fill)

def _box(c):
    x0, y0, x1, y1 = area(c)
    return (x0 + 20, y0, x1 - 20, y0 + 560) if c.v else (x0 + 40, y0 + 40, x0 + 1060, y1 - 20)

def _white(d, b, r=40): d.rounded_rectangle(b, radius=r, fill=(255, 255, 255, 235))

def _opts(c, d, item, phase, pt, t, b, start=1.4):
    return _opt_row(c, d, item, phase, pt, t, item["options"], b[3] + 110 if c.v else 0, start)

def _a(phase, t, start=0.3, dur=0.4): return eob((t - start) / dur) if phase == "ask" else 1

# 78 Fruit math -------------------------------------------------------------
def fruitmath_values(item):
    em = sorted({e for terms, _ in item["eqs"] for e in terms})
    for vals in itertools.product(range(1, 21), repeat=len(em)):
        v = dict(zip(em, vals))
        if all(sum(v[e] for e in terms) == tot for terms, tot in item["eqs"]): return v
    return None

def fruitmath_answer(item):
    v = fruitmath_values(item); return None if v is None else sum(v[e] for e in item["ask"])

def draw_fruitmath(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c); _white(d, b)
    rows = item["eqs"] + [[item["ask"], None]]; n = len(rows)
    rh = (b[3] - b[1] - 40) / n; es = min(110, rh * 0.75)
    for i, (terms, tot) in enumerate(rows):
        y = b[1] + 20 + rh * (i + 0.5); a = _a(phase, t, 0.3 + 0.4 * i)
        if a < 0.05: continue
        parts = []
        for k, e in enumerate(terms):
            if k: parts.append("+")
            parts.append(e)
        parts += ["=", str(tot) if tot is not None else ("?" if phase != "reveal" or pt < 0.4 else str(fruitmath_answer(item)))]
        w = sum(es if p not in "+=" else es * 0.55 for p in parts[:-1]) + es * 1.2
        x = (b[0] + b[2]) / 2 - w / 2
        for k, p in enumerate(parts):
            if k == len(parts) - 1:
                col = GREEN if tot is None and phase == "reveal" and pt > 0.4 else ((230, 60, 90) if tot is None else INK)
                _t(d, x + es * 0.6, y, p, int(es * 0.8), col)
            elif p in "+=":
                _t(d, x + es * 0.27, y, p, int(es * 0.7)); x += es * 0.55
            else:
                paste(im, emoji_img(p, es * 0.85), x + es / 2, y, a); x += es
    _opts(c, d, item, phase, pt, t, b, 1.8)
    return (b[0] + b[2]) / 2, b[3] - rh / 2

# 79 Leg count --------------------------------------------------------------
LEGS = {"🐔": 2, "🦆": 2, "🐧": 2, "🦩": 2, "🐶": 4, "🐱": 4, "🐷": 4, "🐄": 4, "🐴": 4, "🐑": 4, "🐜": 6, "🐝": 6, "🐞": 6, "🕷️": 8, "🐙": 8}

def legcount_answer(item): return sum(LEGS[e] for e in item["animals"])

def draw_legcount(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c); _white(d, b)
    an = item["animals"]; n = len(an); cols = min(n, 3 if c.v else 4); rows = math.ceil(n / cols)
    cw = (b[2] - b[0]) / cols; ch = (b[3] - b[1]) / rows; es = min(cw, ch) * 0.6
    for i, e in enumerate(an):
        r_, q = divmod(i, cols); k = cols if r_ < rows - 1 else n - cols * (rows - 1)
        x = (b[0] + b[2]) / 2 + (q - (k - 1) / 2) * cw; y = b[1] + ch * (r_ + 0.45)
        paste(im, emoji_img(e, es), x, y, _a(phase, t, 0.3 + 0.25 * i))
        if phase == "reveal" and pt > 0.3: _t(d, x, y + es * 0.68, str(LEGS[e]), int(es * 0.32), GREEN)
    _opts(c, d, item, phase, pt, t, b, 1.6)
    return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2

# 80 Colour mix -------------------------------------------------------------
MIX = {frozenset(["red", "blue"]): ("purple", (150, 70, 200)), frozenset(["red", "yellow"]): ("orange", (250, 140, 40)),
       frozenset(["blue", "yellow"]): ("green", (60, 180, 80)), frozenset(["red", "white"]): ("pink", (255, 150, 190)),
       frozenset(["black", "white"]): ("grey", (140, 140, 150))}
PAINT = {"red": (230, 50, 60), "blue": (50, 110, 235), "yellow": (250, 210, 40), "white": (250, 250, 250), "black": (25, 25, 30)}

def colormix_answer(item): return MIX[frozenset([item["a"], item["b"]])][0]

def _blob(d, cx, cy, r, col, seed):
    rnd = random.Random(seed); pts = []
    for i in range(18):
        a = i * 2 * math.pi / 18; rr = r * rnd.uniform(0.86, 1.08); pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=col, outline=(30, 30, 60), width=5)

def draw_colormix(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c); _white(d, b)
    cy = (b[1] + b[3]) / 2; W = b[2] - b[0]; r = min(W / 9, 105)
    xs = [b[0] + W * f for f in (0.16, 0.5, 0.84)]
    _blob(d, xs[0], cy, r * _a(phase, t, 0.3), PAINT[item["a"]], 1)
    _t(d, (xs[0] + xs[1]) / 2, cy, "+", int(r * 0.9))
    _blob(d, xs[1], cy, r * _a(phase, t, 0.7), PAINT[item["b"]], 2)
    _t(d, (xs[1] + xs[2]) / 2, cy, "=", int(r * 0.9))
    if phase == "reveal" and pt > 0.3: _blob(d, xs[2], cy, r, MIX[frozenset([item["a"], item["b"]])][1], 3)
    else:
        d.ellipse((xs[2] - r, cy - r, xs[2] + r, cy + r), outline=(150, 150, 170), width=8); _t(d, xs[2], cy, "?", int(r * 1.1), (230, 60, 90))
    _opts(c, d, item, phase, pt, t, b, 1.4)
    return xs[2], cy

# 81 Number pyramid ---------------------------------------------------------
def pyramid_rows(item):
    rows = [list(item["base"])]
    while len(rows[-1]) > 1: rows.append([rows[-1][i] + rows[-1][i + 1] for i in range(len(rows[-1]) - 1)])
    return rows

def pyramid_answer(item):
    r, i = item["hide"]; return pyramid_rows(item)[r][i]

def draw_pyramid(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c)
    rows = pyramid_rows(item); n = len(rows)
    bw = min((b[2] - b[0]) / n, 200); bh = min((b[3] - b[1]) / n, 120)
    for r_, row in enumerate(rows):
        y = b[3] - (r_ + 0.5) * bh
        for i, v in enumerate(row):
            x = (b[0] + b[2]) / 2 + (i - (len(row) - 1) / 2) * bw
            a = _a(phase, t, 0.3 + 0.25 * r_)
            if a < 0.05: continue
            hid = [r_, i] == list(item["hide"]); rev = hid and phase == "reveal" and pt > 0.4
            d.rounded_rectangle((x - bw / 2 + 5, y - bh / 2 + 5, x + bw / 2 - 5, y + bh / 2 - 5), radius=16,
                                fill=GREEN if rev else ((255, 230, 120) if hid else (255, 255, 255)), outline=(200, 140, 60), width=5)
            _t(d, x, y, "?" if hid and not rev else str(v), int(bh * 0.5), (255, 255, 255) if rev else INK)
    if not c.v: _t(d, (b[0] + b[2]) / 2, b[1] - 10, "Each brick = sum of the two below", 40, (255, 255, 255))
    else: _t(d, (b[0] + b[2]) / 2, b[1] - 6, "Each brick = the two below added", 40, (255, 255, 255))
    _opts(c, d, item, phase, pt, t, b, 1.8)
    return (b[0] + b[2]) / 2, b[1] + bh

# 82 Mini sudoku ------------------------------------------------------------
def sudoku_ok(item):
    g = item["grid"]; n = len(g)
    return all(len(set(r)) == n for r in g) and all(len({g[r][k] for r in range(n)}) == n for k in range(n))

def draw_sudoku(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c); g = item["grid"]; n = len(g)
    cell = min((b[2] - b[0]) / n, (b[3] - b[1] - 50) / n, 125)
    ox = (b[0] + b[2]) / 2 - n * cell / 2; oy = b[1] + 50
    _t(d, (b[0] + b[2]) / 2, b[1] + 6, "One of each in every row & column", 38, (255, 255, 255))
    d.rounded_rectangle((ox - 14, oy - 14, ox + n * cell + 14, oy + n * cell + 14), radius=24, fill=(255, 255, 255))
    blanks = [list(p) for p in item["blanks"]]
    for r_ in range(n):
        for k in range(n):
            x, y = ox + k * cell, oy + r_ * cell
            d.rectangle((x, y, x + cell, y + cell), outline=(180, 180, 200), width=3)
            if [r_, k] == list(item["ask"]):
                if phase == "reveal" and pt > 0.4:
                    d.rectangle((x + 4, y + 4, x + cell - 4, y + cell - 4), fill=GREEN); paste(im, emoji_img(g[r_][k], cell * 0.62), x + cell / 2, y + cell / 2)
                else:
                    d.rectangle((x + 4, y + 4, x + cell - 4, y + cell - 4), fill=(255, 230, 120)); _t(d, x + cell / 2, y + cell / 2, "?", int(cell * 0.6), (230, 60, 90))
            elif [r_, k] not in blanks:
                paste(im, emoji_img(g[r_][k], cell * 0.62), x + cell / 2, y + cell / 2, _a(phase, t, 0.3 + 0.05 * (r_ * n + k)))
    _emoji_opts(c, im, d, item, phase, pt, t, 1.8, b[3] + 150)
    return ox + (item["ask"][1] + 0.5) * cell, oy + (item["ask"][0] + 0.5) * cell

# 83 Venn count -------------------------------------------------------------
def draw_venn(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c); _white(d, b)
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2; R = min((b[3] - b[1]) * 0.44, (b[2] - b[0]) * 0.3); off = R * 0.55
    ca, cb = (cx - off, cy), (cx + off, cy)
    if phase == "reveal" and pt > 0.3:
        m = Image.new("L", im.size, 0); md = ImageDraw.Draw(m)
        md.ellipse((ca[0] - R, cy - R, ca[0] + R, cy + R), fill=255)
        m2 = Image.new("L", im.size, 0); ImageDraw.Draw(m2).ellipse((cb[0] - R, cy - R, cb[0] + R, cy + R), fill=255)
        from PIL import ImageChops
        both = ImageChops.multiply(m, m2).point(lambda v: int(v * 0.55))
        im.paste(Image.new("RGBA", im.size, (90, 230, 130, 255)), (0, 0), both)
    d.ellipse((ca[0] - R, cy - R, ca[0] + R, cy + R), outline=(230, 60, 80), width=10)
    d.ellipse((cb[0] - R, cy - R, cb[0] + R, cy + R), outline=(50, 120, 235), width=10)
    rnd = random.Random(item.get("seed", 1)); es = R * 0.24
    zones = []
    def place(zone, k):
        got = 0; tries = 0
        while got < k and tries < 4000:
            tries += 1; x = rnd.uniform(cx - off - R, cx + off + R); y = rnd.uniform(cy - R, cy + R)
            ina = math.hypot(x - ca[0], y - cy) < R - es * 0.7; inb = math.hypot(x - cb[0], y - cy) < R - es * 0.7
            outa = math.hypot(x - ca[0], y - cy) > R + es * 0.0; outb = math.hypot(x - cb[0], y - cy) > R + es * 0.0
            ok = {"a": ina and outb and math.hypot(x - cb[0], y - cy) > R + es * 0.7, "b": inb and outa and math.hypot(x - ca[0], y - cy) > R + es * 0.7, "both": ina and inb}[zone]
            if ok and all(math.hypot(x - px, y - py) > es * 1.15 for px, py in zones):
                zones.append((x, y)); got += 1
    for z in ("a", "b", "both"): place(z, item[z])
    for i, (x, y) in enumerate(zones): paste(im, emoji_img(item["emoji"], es), x, y, _a(phase, t, 0.3 + 0.05 * i))
    _opts(c, d, item, phase, pt, t, b, 1.6)
    return cx, cy

# 84 Grid finder ------------------------------------------------------------
def gridfind_answer(item): return "ABCDEF"[item["pos"][1]] + str(item["pos"][0] + 1)

def draw_gridfind(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c); n = item.get("n", 5)
    cell = min((b[2] - b[0] - 80) / n, (b[3] - b[1] - 70) / n)
    ox = (b[0] + b[2]) / 2 - n * cell / 2 + 30; oy = b[1] + 60
    d.rounded_rectangle((ox - 80, oy - 70, ox + n * cell + 14, oy + n * cell + 14), radius=26, fill=(255, 255, 255))
    rnd = random.Random(item.get("seed", 1)); pool = item["pool"]
    for k in range(n): _t(d, ox + (k + 0.5) * cell, oy - 34, "ABCDEF"[k], int(cell * 0.38), (230, 60, 90))
    for r_ in range(n): _t(d, ox - 40, oy + (r_ + 0.5) * cell, str(r_ + 1), int(cell * 0.38), (50, 110, 235))
    for r_ in range(n):
        for k in range(n):
            x, y = ox + k * cell, oy + r_ * cell
            d.rectangle((x, y, x + cell, y + cell), outline=(190, 190, 210), width=3)
            e = item["target"] if [r_, k] == list(item["pos"]) else rnd.choice(pool)
            if phase == "reveal" and pt > 0.3 and [r_, k] == list(item["pos"]): d.rectangle((x + 4, y + 4, x + cell - 4, y + cell - 4), fill=GREEN)
            paste(im, emoji_img(e, cell * 0.6), x + cell / 2, y + cell / 2, _a(phase, t, 0.3 + 0.02 * (r_ * n + k)))
    if c.v:
        _t(d, b[0] + 120, b[3] + 20, "Find:", 46, (255, 255, 255)); paste(im, emoji_img(item["target"], 70), b[0] + 240, b[3] + 22)
    else:
        _t(d, b[2] + 120, b[1] + 20, "Find:", 46, (255, 255, 255)); paste(im, emoji_img(item["target"], 70), b[2] + 230, b[1] + 22)
    _opt_row(c, d, item, phase, pt, t, item["options"], b[3] + 150 if c.v else 0, 1.6)
    return ox + (item["pos"][1] + 0.5) * cell, oy + (item["pos"][0] + 0.5) * cell

# 85 Code match -------------------------------------------------------------
def draw_codematch(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cx = c.W / 2 if c.v else x0 + 420; ty = y0 + 90 if c.v else y0 + 260
    _t(d, cx, ty - 105, "Find this exact code:", 44, (255, 255, 255))
    d.rounded_rectangle((cx - 270, ty - 70, cx + 270, ty + 70), radius=26, fill=(255, 255, 255), outline=c.accent, width=8)
    _t(d, cx, ty, item["code"], 92)
    opts = item["options"]
    for q, o in enumerate(opts):
        ox, oy = (c.W / 2, y0 + 290 + q * 125) if c.v else (x0 + 1180, y0 + 90 + q * 140)
        s = eob((t - 1.2 - 0.15 * q) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 0.5: fill = GREEN if q == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox - 280, oy - 52, ox + 280, oy + 52), radius=24, fill=fill, outline=c.accent, width=5)
        _t(d, ox + 30, oy, o, 72, INK if fill == (255, 255, 255) else (255, 255, 255))
        _label(d, ox - 230, oy, "ABCDE"[q], c, r=30, size=40)
    return (c.W / 2, y0 + 290 + item["right"] * 125) if c.v else (x0 + 1180, y0 + 90 + item["right"] * 140)

# 86 Pattern match ----------------------------------------------------------
PEG = {"r": (235, 60, 70), "b": (50, 120, 235), "y": (250, 205, 40), "g": (50, 185, 90), "w": (235, 235, 240)}

def patmatch_grids(item):
    out = []; di = 0
    for k in range(3):
        g = [list(r) for r in item["grid"]]
        if k != item["right"]:
            r_, q, col = item["diffs"][di]; di += 1; g[r_][q] = col
        out.append(g)
    return out

def _peg(d, g, cx, cy, size):
    n = len(g); cs = size / n
    d.rounded_rectangle((cx - size / 2 - 12, cy - size / 2 - 12, cx + size / 2 + 12, cy + size / 2 + 12), radius=20, fill=(255, 255, 255), outline=(120, 120, 150), width=4)
    for r_ in range(n):
        for q in range(n):
            x = cx - size / 2 + (q + 0.5) * cs; y = cy - size / 2 + (r_ + 0.5) * cs; rr = cs * 0.38
            d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=PEG[g[r_][q]], outline=(90, 90, 110), width=2)

def draw_patmatch(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    tc = (c.W / 2, y0 + 170) if c.v else (x0 + 300, (y0 + y1) / 2 + 20)
    _t(d, tc[0], tc[1] - 200, "Copy this:", 44, (255, 255, 255)); _peg(d, item["grid"], tc[0], tc[1], 300)
    gs = patmatch_grids(item)
    for k, g in enumerate(gs):
        cx, cy = (x0 + (x1 - x0) * (k + 0.5) / 3, y0 + 590) if c.v else (x0 + 760 + k * 340, (y0 + y1) / 2 + 20)
        if phase == "ask" and t < 1.2 + 0.2 * k: continue
        if phase == "reveal" and pt > 0.4 and k == item["right"]: glow_box(im, (cx - 160, cy - 160, cx + 160, cy + 160), r=24)
        _peg(d, g, cx, cy, 260 if c.v else 280)
        _label(d, cx, cy + 190, "ABC"[k], c, r=34, size=44)
    k = item["right"]
    return (x0 + (x1 - x0) * (k + 0.5) / 3, y0 + 590) if c.v else (x0 + 760 + k * 340, (y0 + y1) / 2)

# 87 Break in the pattern ---------------------------------------------------
def patbreak_cells(item, n):
    u = item["unit"]; cells = [u[i % len(u)] for i in range(n)]
    cells[item["wrong"][0]] = item["wrong"][1]; return cells

def draw_patbreak(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im)
    cols, rows = (6, 7) if c.v else (12, 4)
    cell, ox, oy = _grid_geom(c, cols, rows, 40 if c.v else 70, 150)
    _panel(d, ox, oy, cols * cell, rows * cell)
    cells = patbreak_cells(item, cols * rows)
    for i, e in enumerate(cells):
        r_, k = divmod(i, cols)
        paste(im, emoji_img(e, cell * 0.66), ox + (k + 0.5) * cell, oy + (r_ + 0.5) * cell, 1, _a(phase, t, 0.3 + 0.02 * i, 0.3))
    r_, k = divmod(item["wrong"][0] % (cols * rows), cols)
    cx, cy = ox + (k + 0.5) * cell, oy + (r_ + 0.5) * cell
    if phase == "reveal": _circle_hit(d, cx, cy, cell * 0.6, pt)
    return cx, cy

# 88 Pizza slices -----------------------------------------------------------
def draw_pizza(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c)
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2; R = min(b[3] - b[1], b[2] - b[0]) * 0.44
    n = item["slices"]; eaten = set(item["eaten"])
    d.ellipse((cx - R - 24, cy - R - 24, cx + R + 24, cy + R + 24), fill=(245, 245, 250), outline=(200, 200, 215), width=6)
    rnd = random.Random(7)
    for i in range(n):
        a0 = -90 + i * 360 / n; a1 = a0 + 360 / n
        if i in eaten:
            if phase == "reveal" and pt > 0.3:
                d.pieslice((cx - R, cy - R, cx + R, cy + R), a0, a1, fill=(90, 230, 130), outline=(40, 160, 80), width=4)
            continue
        d.pieslice((cx - R, cy - R, cx + R, cy + R), a0, a1, fill=(220, 150, 60), outline=(150, 90, 30), width=5)
        d.pieslice((cx - R * 0.88, cy - R * 0.88, cx + R * 0.88, cy + R * 0.88), a0 + 1.5, a1 - 1.5, fill=(250, 200, 70))
        for _ in range(2):
            am = math.radians(rnd.uniform(a0 + 10, a1 - 10)); rr = rnd.uniform(R * 0.35, R * 0.7); pr = R * 0.08
            px, py = cx + rr * math.cos(am), cy + rr * math.sin(am); d.ellipse((px - pr, py - pr, px + pr, py + pr), fill=(200, 50, 50))
    _opts(c, d, item, phase, pt, t, b, 1.4)
    return cx, cy

# 89 Biggest number ---------------------------------------------------------
def bignum_answer(item): return max(range(len(item["nums"])), key=lambda i: item["nums"][i])

def draw_bignum(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    nums = item["nums"]; sizes = item.get("sizes", [70, 110, 90, 130]); best = bignum_answer(item)
    for q, v in enumerate(nums):
        r_, k = divmod(q, 2)
        cx, cy = (x0 + (x1 - x0) * (k + 0.5) / 2, y0 + 140 + r_ * 300) if c.v else (x0 + 300 + k * 520 + r_ * 260, y0 + 170 + r_ * 300)
        a = _a(phase, t, 0.3 + 0.2 * q)
        if a < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 0.4: fill = GREEN if q == best else (150, 40, 55)
        d.rounded_rectangle((cx - 210, cy - 120, cx + 210, cy + 120), radius=30, fill=fill, outline=c.accent, width=6)
        _t(d, cx, cy + 6, str(v), sizes[q % len(sizes)], INK if fill == (255, 255, 255) else (255, 255, 255))
        _label(d, cx - 170, cy - 80, "ABCD"[q], c, r=30, size=40)
    r_, k = divmod(best, 2)
    return (x0 + (x1 - x0) * (k + 0.5) / 2, y0 + 140 + r_ * 300) if c.v else (x0 + 300 + k * 520 + r_ * 260, y0 + 170 + r_ * 300)

# 90 Domino next ------------------------------------------------------------
PIPS = {0: [], 1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}

def _domino(d, cx, cy, w, top, bot, fill=(255, 255, 255), q=False):
    h = w * 2
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=w * 0.15, fill=fill, outline=INK, width=5)
    d.line((cx - w * 0.38, cy, cx + w * 0.38, cy), fill=INK, width=4)
    for half, v in ((-1, top), (1, bot)):
        hy = cy + half * w / 2
        if q: _t(d, cx, hy, "?", int(w * 0.6), (230, 60, 90)); continue
        for px, py in PIPS[v]:
            x, y = cx + px * w * 0.25, hy + py * w * 0.25; r = w * 0.085
            d.ellipse((x - r, y - r, x + r, y + r), fill=INK)

def draw_domino(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c); _white(d, b)
    seq = item["seq"]; n = len(seq) + 1; w = min((b[2] - b[0]) / (n * 1.5), (b[3] - b[1]) / 2.4, 130)
    for i in range(n):
        x = (b[0] + b[2]) / 2 + (i - (n - 1) / 2) * w * 1.5; y = (b[1] + b[3]) / 2
        if i < len(seq):
            if _a(phase, t, 0.3 + 0.3 * i) > 0.5: _domino(d, x, y, w, *seq[i])
        elif phase == "reveal" and pt > 0.4:
            tb = [int(v) for v in item["options"][item["right"]].split("|")]; _domino(d, x, y, w, tb[0], tb[1], fill=(170, 240, 190))
        else: _domino(d, x, y, w, 0, 0, fill=(255, 240, 160), q=True)
    _opts(c, d, item, phase, pt, t, b, 1.8)
    return (b[0] + b[2]) / 2 + ((n - 1) / 2) * w * 1.5, (b[1] + b[3]) / 2

# 91 Tally count ------------------------------------------------------------
def draw_tally(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c); _white(d, b)
    n = item["n"]; groups = [5] * (n // 5) + ([n % 5] if n % 5 else []); per = 3 if c.v else 4
    rows = math.ceil(len(groups) / per); gw = (b[2] - b[0] - 60) / per; rh = (b[3] - b[1] - 40) / max(rows, 1)
    hh = min(rh * 0.7, 150); sp = min(gw / 6, 34)
    for gi, g in enumerate(groups):
        r_, q = divmod(gi, per); gx = b[0] + 30 + gw * (q + 0.5); gy = b[1] + 20 + rh * (r_ + 0.5)
        if _a(phase, t, 0.3 + 0.15 * gi) < 0.5: continue
        col = GREEN if phase == "reveal" and pt > 0.3 else INK
        for k in range(min(g, 4)):
            x = gx + (k - 1.5) * sp; d.line((x, gy - hh / 2, x, gy + hh / 2), fill=col, width=10)
        if g == 5: d.line((gx - 2.4 * sp, gy + hh * 0.35, gx + 2.4 * sp, gy - hh * 0.35), fill=(230, 60, 80), width=10)
    _opts(c, d, item, phase, pt, t, b, 1.6)
    return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2

# 92 Symmetry finish --------------------------------------------------------
def sym_options(item):
    mir = [list(reversed(r)) for r in item["left"]]; out = []; wi = 0
    for k in range(3):
        g = [list(r) for r in mir]
        if k != item["right"]:
            r_, q = item["wrong"][wi]; wi += 1; g[r_][q] = 1 - g[r_][q]
        out.append(g)
    return out

def _pix(d, g, x, y, cs, col):
    for r_, row in enumerate(g):
        for q, v in enumerate(row):
            d.rectangle((x + q * cs, y + r_ * cs, x + (q + 1) * cs, y + (r_ + 1) * cs), fill=col if v else (255, 255, 255), outline=(200, 200, 215), width=2)

def draw_symmetry(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    L = item["left"]; rows, cols = len(L), len(L[0]); col = INKS.get(item.get("color", "blue"), (60, 130, 245))
    cs = 52 if c.v else 58
    W = cols * cs * 2; tx = (c.W / 2 - W / 2) if c.v else x0 + 60; ty = y0 + 10 if c.v else y0 + 120
    d.rectangle((tx - 14, ty - 14, tx + W + 14, ty + rows * cs + 14), fill=(255, 255, 255))
    _pix(d, L, tx, ty, cs, col)
    opts = sym_options(item)
    if phase == "reveal" and pt > 0.4: _pix(d, opts[item["right"]], tx + cols * cs, ty, cs, col)
    else:
        for r_ in range(rows):
            for q in range(cols): d.rectangle((tx + (cols + q) * cs, ty + r_ * cs, tx + (cols + q + 1) * cs, ty + (r_ + 1) * cs), outline=(200, 200, 215), width=2)
        _t(d, tx + cols * cs * 1.5, ty + rows * cs / 2, "?", 120, (230, 60, 90))
    d.line((tx + cols * cs, ty - 24, tx + cols * cs, ty + rows * cs + 24), fill=(230, 60, 90), width=6)
    ocs = 34 if c.v else 36
    for k, g in enumerate(opts):
        ox, oy = (x0 + (x1 - x0) * (k + 0.5) / 3 - cols * ocs / 2, y0 + rows * cs + 90) if c.v else (x0 + 1000 + k * 210, y0 + 170)
        if phase == "ask" and t < 1.4 + 0.2 * k: continue
        bx = (ox - 16, oy - 16, ox + cols * ocs + 16, oy + rows * ocs + 16)
        if phase == "reveal" and pt > 0.4 and k == item["right"]: glow_box(im, bx, r=16)
        d.rectangle(bx, fill=(255, 255, 255)); _pix(d, g, ox, oy, ocs, col)
        _label(d, ox + cols * ocs / 2, oy + rows * ocs + 60, "ABC"[k], c, r=32, size=42)
    return tx + W * 0.75, ty + rows * cs / 2

# 93 Finger count -----------------------------------------------------------
FINGERS = {"✋": 5, "✌️": 2, "☝️": 1, "🤟": 3}

def fingers_answer(item): return sum(FINGERS[h] for h in item["hands"])

def draw_fingers(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c); _white(d, b)
    hs = item["hands"]; n = len(hs); cols = min(n, 3 if c.v else 4); rows = math.ceil(n / cols)
    cw = (b[2] - b[0]) / cols; ch = (b[3] - b[1]) / rows; es = min(cw, ch) * 0.62
    for i, h in enumerate(hs):
        r_, q = divmod(i, cols); k = cols if r_ < rows - 1 else n - cols * (rows - 1)
        x = (b[0] + b[2]) / 2 + (q - (k - 1) / 2) * cw; y = b[1] + ch * (r_ + 0.45)
        paste(im, emoji_img(h, es), x, y, _a(phase, t, 0.3 + 0.25 * i))
        if phase == "reveal" and pt > 0.3: _t(d, x, y + es * 0.66, str(FINGERS[h]), int(es * 0.3), GREEN)
    _opts(c, d, item, phase, pt, t, b, 1.6)
    return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2

# 94 Tallest stack (most coins) ---------------------------------------------
def stacks_answer(item): return max(range(len(item["stacks"])), key=lambda i: item["stacks"][i][0])

def draw_stacks(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c); _white(d, b)
    st = item["stacks"]; n = len(st); cw = (b[2] - b[0]) / n; base = b[3] - 70; best = stacks_answer(item)
    for i, (cnt, th) in enumerate(st):
        cx = b[0] + cw * (i + 0.5); w = cw * 0.6
        hl = phase == "reveal" and pt > 0.3 and i == best
        for k in range(cnt):
            if phase == "ask" and t < 0.3 + 0.04 * k: break
            y = base - k * th
            d.ellipse((cx - w / 2, y - th * 0.9, cx + w / 2, y + th * 0.9), fill=(90, 220, 120) if hl else (250, 195, 50), outline=(170, 120, 20), width=3)
        _label(d, cx, b[3] - 32, "ABCD"[i], c, r=26, size=36)
        if phase == "reveal" and pt > 0.3: _t(d, cx, base - cnt * th - 40, str(cnt), 44, GREEN if hl else INK)
    _opt_row(c, d, item, phase, pt, t, ["A", "B", "C", "D"][:n] if False else item["options"], b[3] + 110 if c.v else 0, 1.8)
    return b[0] + cw * (best + 0.5), base - st[best][0] * st[best][1] / 2

# 95 Goes with (analogy) ----------------------------------------------------
def draw_analogy(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im); b = _box(c); _white(d, b)
    (a1, a2), (b1,) = item["pair"], [item["ask"]]
    es = min((b[3] - b[1]) * 0.3, 150)
    for r_, (l, r) in enumerate([(a1, a2), (b1, None)]):
        y = b[1] + (b[3] - b[1]) * (0.27 + 0.46 * r_); cx = (b[0] + b[2]) / 2
        if _a(phase, t, 0.3 + 0.5 * r_) < 0.5: continue
        paste(im, emoji_img(l, es), cx - es * 1.4, y)
        aw = es * 0.5; d.line((cx - aw / 2, y, cx + aw / 2 - 10, y), fill=INK, width=12)
        d.polygon([(cx + aw / 2 + 8, y), (cx + aw / 2 - 22, y - 22), (cx + aw / 2 - 22, y + 22)], fill=INK)
        if r is not None: paste(im, emoji_img(r, es), cx + es * 1.4, y)
        elif phase == "reveal" and pt > 0.4:
            d.rounded_rectangle((cx + es * 0.75, y - es * 0.65, cx + es * 2.05, y + es * 0.65), radius=24, fill=(170, 240, 190)); paste(im, emoji_img(item["options"][item["right"]], es), cx + es * 1.4, y)
        else:
            d.rounded_rectangle((cx + es * 0.75, y - es * 0.65, cx + es * 2.05, y + es * 0.65), radius=24, fill=(255, 240, 160)); _t(d, cx + es * 1.4, y, "?", int(es * 0.8), (230, 60, 90))
    _emoji_opts(c, im, d, item, phase, pt, t, 1.6, b[3] + 150)
    return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2

# 96 Odd pair out -----------------------------------------------------------
def draw_oddpair(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    ps = item["pairs"]
    for q, (e1, e2) in enumerate(ps):
        r_, k = divmod(q, 2)
        cx, cy = (x0 + (x1 - x0) * (k + 0.5) / 2, y0 + 150 + r_ * 330) if c.v else (x0 + 400 + k * 620, y0 + 170 + r_ * 330)
        a = _a(phase, t, 0.3 + 0.3 * q)
        if a < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 0.4: fill = (240, 90, 100) if q == item["right"] else (190, 235, 200)
        d.rounded_rectangle((cx - 220, cy - 130, cx + 220, cy + 130), radius=34, fill=fill, outline=c.accent, width=6)
        paste(im, emoji_img(e1, 120), cx - 95, cy, a); paste(im, emoji_img(e2, 120), cx + 95, cy, a)
        _t(d, cx, cy, "+", 60)
        _label(d, cx - 185, cy - 95, "ABCD"[q], c, r=30, size=40)
    r_, k = divmod(item["right"], 2)
    return (x0 + (x1 - x0) * (k + 0.5) / 2, y0 + 150 + r_ * 330) if c.v else (x0 + 400 + k * 620, y0 + 170 + r_ * 330)

# 97 Missing key ------------------------------------------------------------
KEYROWS = ["QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]

def draw_missingkey(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    kw = (x1 - x0 - 30) / 10 if c.v else 92; gap = 6
    W = kw * 10; ox = c.W / 2 - W / 2 if c.v else x0 + 40; oy = y0 + 40 if c.v else y0 + 160
    d.rounded_rectangle((ox - 20, oy - 20, ox + W + 20, oy + 3 * kw + 20), radius=26, fill=(60, 60, 80))
    hit = None
    for r_, row in enumerate(KEYROWS):
        sx = ox + r_ * kw * 0.5
        for k, ch in enumerate(row):
            x, y = sx + k * kw, oy + r_ * kw
            if _a(phase, t, 0.3 + 0.03 * (r_ * 10 + k)) < 0.5: continue
            hid = ch == item["hide"]; rev = hid and phase == "reveal" and pt > 0.4
            d.rounded_rectangle((x + gap / 2, y + gap / 2, x + kw - gap / 2, y + kw - gap / 2), radius=12,
                                fill=GREEN if rev else ((255, 230, 120) if hid else (245, 245, 250)))
            _t(d, x + kw / 2, y + kw / 2, ("?" if hid and not rev else ch), int(kw * 0.48), (230, 60, 90) if hid and not rev else INK)
            if hid: hit = (x + kw / 2, y + kw / 2)
    _opt_row(c, d, item, phase, pt, t, item["options"], oy + 3 * kw + 170 if c.v else 0, 1.6)
    return hit or (c.W / 2, oy)

E.DRAW.update({"fruitmath": draw_fruitmath, "legcount": draw_legcount, "colormix": draw_colormix, "pyramid": draw_pyramid,
               "sudoku": draw_sudoku, "venn": draw_venn, "gridfind": draw_gridfind, "codematch": draw_codematch,
               "patmatch": draw_patmatch, "patbreak": draw_patbreak, "pizza": draw_pizza, "bignum": draw_bignum,
               "domino": draw_domino, "tally": draw_tally, "symmetry": draw_symmetry, "fingers": draw_fingers,
               "stacks": draw_stacks, "analogy": draw_analogy, "oddpair": draw_oddpair, "missingkey": draw_missingkey})
