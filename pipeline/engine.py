"""Multi-format quiz/puzzle video engine (frames drawn in code, piped to ffmpeg).

usage:
  python3 engine.py SPEC.json still SEGMENT T OUT.jpg     # one frame
  python3 engine.py SPEC.json video SEGMENT OUT.mp4       # one scene file
SEGMENT is "intro", "i0".."iN", or "outro". SPEC must already contain timings (see build.py).
"""
import sys, os, math, json, subprocess, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
F_BOLD = os.path.join(FONTS, "Poppins-Bold.ttf")
F_MED = os.path.join(FONTS, "Poppins-Medium.ttf")
EMOJI = os.path.join(FONTS, "NotoColorEmoji.ttf")
if not os.path.exists(EMOJI):
    EMOJI = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
FPS = 30

_fc = {}
def font(path, size):
    k = (path, int(size))
    if k not in _fc: _fc[k] = ImageFont.truetype(path, int(size))
    return _fc[k]

_ec = {}
def emoji_img(s, size):
    """Render an emoji string (may be several emoji) scaled so its height == size."""
    k = (s, int(size))
    if k not in _ec:
        f = ImageFont.truetype(EMOJI, 109)
        tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        w = int(tmp.textlength(s, font=f)) + 40
        im = Image.new("RGBA", (max(w, 160), 170), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((20, 15), s, font=f, embedded_color=True)
        bb = im.getbbox()
        im = im.crop(bb) if bb else im
        sc = size / im.height
        _ec[k] = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    return _ec[k]

def eob(t):
    t = max(0, min(1, t)); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
def eo(t):
    t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def cl(t): return max(0.0, min(1.0, t))

class Ctx:
    def __init__(self, spec):
        self.spec = spec
        self.v = spec.get("orientation", "v") == "v"
        self.W, self.H = (1080, 1920) if self.v else (1920, 1080)
        st = spec.get("style", {})
        self.pal = [tuple(c) for c in st.get("palette", [[20, 40, 110], [70, 20, 120]])]
        self.accent = tuple(st.get("accent", [255, 210, 60]))
        self.bgkind = st.get("bg", "bubbles")
        self.card_fill = tuple(st.get("card", [255, 255, 255]))
        self._bg = None

    def background(self, t):
        W, H = self.W, self.H
        if self._bg is None:
            a, b = self.pal
            g = Image.new("RGB", (1, 256))
            for y in range(256):
                u = y / 255
                g.putpixel((0, y), tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3)))
            self._bg = g.resize((W, H))
        im = self._bg.copy().convert("RGBA")
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        k = self.bgkind
        if k == "bubbles":
            for i in range(10):
                x = (i * 263 + 140 * math.sin(t * 0.5 + i)) % W
                y = (H - ((t * (40 + i * 9) + i * 311) % (H + 300))) + 150
                r = 30 + (i * 37) % 70
                d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 18))
        elif k == "stars":
            rnd = random.Random(7)
            for i in range(70):
                x, y = rnd.random() * W, rnd.random() * H
                tw = 0.5 + 0.5 * math.sin(t * 2 + i)
                r = 2 + rnd.random() * 4
                d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, int(40 + 120 * tw)))
        elif k == "grid":
            step = 90; off = (t * 30) % step
            for x in range(-step, W + step, step):
                d.line((x + off, 0, x + off, H), fill=(255, 255, 255, 22), width=3)
            for y in range(-step, H + step, step):
                d.line((0, y + off, W, y + off), fill=(255, 255, 255, 22), width=3)
        elif k == "waves":
            for j in range(6):
                pts = []
                base = H * (0.15 + j * 0.15)
                for x in range(0, W + 40, 40):
                    pts.append((x, base + 40 * math.sin(x / 160 + t * 1.2 + j)))
                d.line(pts, fill=(255, 255, 255, 26), width=10)
        elif k == "confetti":
            rnd = random.Random(3)
            cols = [(255, 210, 60), (255, 100, 150), (90, 210, 255), (120, 255, 150)]
            for i in range(45):
                x0, sp = rnd.random() * W, 60 + rnd.random() * 80
                y = (rnd.random() * H + t * sp) % (H + 40) - 20
                x = x0 + 20 * math.sin(t + i)
                c = cols[i % 4]
                d.rectangle((x - 9, y - 4, x + 9, y + 4), fill=c + (70,))
        im.alpha_composite(ov)
        return im

def text_center(d, txt, cx, y, size, fill=(255, 255, 255), fnt=F_BOLD, stroke=0, sfill=(20, 10, 40), maxw=900):
    f = font(fnt, size)
    while d.textlength(txt, font=f) > maxw and size > 24:
        size -= 3; f = font(fnt, size)
    w = d.textlength(txt, font=f)
    d.text((cx - w / 2, y), txt, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return size

def wrap(txt, size, maxw, fnt=F_BOLD):
    f = font(fnt, size); d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    words = txt.split(); lines = []; cur = ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=f) <= maxw: cur = t
        else:
            if cur: lines.append(cur)
            cur = w_
    if cur: lines.append(cur)
    return lines

def paste(base, im, cx, cy, s=1.0, alpha=1.0):
    if s <= 0.01 or alpha <= 0.01: return
    w, h = max(1, int(im.width * s)), max(1, int(im.height * s))
    im2 = im.resize((w, h), Image.BILINEAR) if s != 1.0 else im.copy()
    if alpha < 1:
        im2.putalpha(im2.split()[-1].point(lambda v: int(v * alpha)))
    base.paste(im2, (int(cx - w / 2), int(cy - h / 2)), im2)

def pill(label, color, size=46):
    f = font(F_BOLD, size)
    tw = ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(label, font=f)
    h = int(size * 1.95)
    im = Image.new("RGBA", (int(tw) + int(size * 1.7), h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, im.width - 1, h - 1), radius=h // 2, fill=color)
    d.text((size * 0.85, h * 0.13), label, font=f, fill=(255, 255, 255))
    return im

_cardc = {}
def card(w, h, letter, label, emo, state, fill=(255, 255, 255), accent=(255, 210, 60)):
    key = (w, h, letter, label, emo, state, fill)
    if key in _cardc: return _cardc[key]
    pad = 24
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    rad = min(50, h // 3)
    if state == "right":
        glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(glow).rounded_rectangle((8, 8, w + pad * 2 - 8, h + pad * 2 - 8), radius=rad + 10, fill=(60, 255, 120, 200))
        im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14)))
        bg, edge, lt = (40, 190, 90), (200, 255, 210), (255, 255, 255)
    elif state == "wrong":
        bg, edge, lt = (150, 40, 55), (230, 120, 130), (255, 210, 210)
    else:
        bg, edge, lt = fill, accent, (30, 30, 60)
    d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=rad, fill=bg, outline=edge, width=8)
    cy = pad + h / 2
    x = pad + 30
    if w / h < 2.3:
        # stacked: emoji on top, label underneath, small letter badge in corner
        if emo:
            e = emoji_img(emo, h * 0.46)
            im.alpha_composite(e, (int(pad + w / 2 - e.width / 2), int(pad + h * 0.1)))
        sz = h * 0.2; f = font(F_BOLD, sz)
        while d.textlength(label, font=f) > w - 40 and sz > 24: sz -= 3; f = font(F_BOLD, sz)
        tw = d.textlength(label, font=f)
        ly = pad + h * (0.62 if emo else 0.5 - 0.12)
        d.text((pad + w / 2 - tw / 2, ly), label, font=f, fill=lt)
        if letter:
            r = 34
            d.ellipse((pad + 18, pad + 18, pad + 18 + 2 * r, pad + 18 + 2 * r), fill=accent if state == "normal" else (255, 255, 255))
            lf = font(F_BOLD, 44); lw = d.textlength(letter, font=lf)
            d.text((pad + 18 + r - lw / 2, pad + 18 + 4), letter, font=lf, fill=(30, 30, 60))
        letter = None; label = ""; emo = None
    if letter:
        r = min(56, h * 0.28)
        d.ellipse((x, cy - r, x + 2 * r, cy + r), fill=accent if state == "normal" else (255, 255, 255))
        lf = font(F_BOLD, r * 1.3); lw = d.textlength(letter, font=lf)
        d.text((x + r - lw / 2, cy - r * 0.95), letter, font=lf, fill=(30, 30, 60))
        x += 2 * r + 24
    ew = 0
    if emo:
        e = emoji_img(emo, min(h * 0.62, 170)); ew = e.width + 30
        im.alpha_composite(e, (int(pad + w - 30 - e.width), int(cy - e.height / 2)))
    maxw = pad + w - ew - x - 20
    sz = min(96, h * 0.34); f = font(F_BOLD, sz)
    if not label: maxw = 10**6
    while d.textlength(label, font=f) > maxw and sz > 26: sz -= 3; f = font(F_BOLD, sz)
    if not letter and not emo:
        tw = d.textlength(label, font=f); x = pad + (w - tw) / 2
    d.text((x, cy - sz * 0.66), label, font=f, fill=lt)
    if state in ("right", "wrong"):
        bx, by = pad + w - 46, pad - 14
        d.ellipse((bx - 40, by - 40, bx + 40, by + 40), fill=(255, 255, 255))
        if state == "right":
            d.line((bx - 20, by + 2, bx - 4, by + 18, bx + 24, by - 16), fill=(40, 190, 90), width=12)
        else:
            d.line((bx - 16, by - 16, bx + 16, by + 16), fill=(200, 40, 60), width=12)
            d.line((bx + 16, by - 16, bx - 16, by + 16), fill=(200, 40, 60), width=12)
    _cardc[key] = im
    return im

def tiles_img(chars, tile, states, accent):
    """chars: list of single chars ('' for blank). states: list of 'n','blank','fill'"""
    gap = int(tile * 0.14)
    n = len(chars)
    im = Image.new("RGBA", (n * tile + (n - 1) * gap + 20, tile + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = font(F_BOLD, tile * 0.62)
    for i, (c, s) in enumerate(zip(chars, states)):
        x = 10 + i * (tile + gap); y = 10
        if s == "blank":
            d.rounded_rectangle((x, y, x + tile, y + tile), radius=tile // 5, fill=(255, 255, 255, 40), outline=accent, width=6)
            d.text((x + tile / 2 - d.textlength("?", font=f) / 2, y + tile * 0.12), "?", font=f, fill=accent)
            continue
        fill = (60, 200, 100) if s == "fill" else (255, 255, 255)
        tc = (255, 255, 255) if s == "fill" else (30, 30, 60)
        d.rounded_rectangle((x, y, x + tile, y + tile), radius=tile // 5, fill=fill)
        d.text((x + tile / 2 - d.textlength(c, font=f) / 2, y + tile * 0.12), c, font=f, fill=tc)
    return im

def tiles_for(word, tile_max, maxw):
    n = len(word)
    gap = 0.14
    return int(min(tile_max, maxw / (n + (n - 1) * gap)))

# ------------------------------------------------------------------ layout
def layout(c, item):
    W, H = c.W, c.H
    has_disp = bool(item.get("display"))
    nopt = len(item.get("options", []))
    if c.v:
        L = dict(head=190, prompt=330, prompt_size=88, prompt_w=W - 120,
                 disp=(W / 2, 880), disp_h=260, disp_w=W - 120,
                 opt_box=(60, 1060 if has_disp else 760, W - 60, 1480),
                 bottom=1520, count=(W / 2, 1600), bar=(160, 1750, W - 160, 1786))
    else:
        L = dict(head=80, prompt=140, prompt_size=78, prompt_w=W - 300,
                 disp=(W / 2, 540), disp_h=200, disp_w=W - 300,
                 opt_box=(160, 690 if has_disp else 400, W - 160, 900 if has_disp else 880),
                 bottom=930, count=(W - 140, 140), bar=(560, 1040, W - 560, 1062))
    if not has_disp and c.v and nopt == 0:
        L["disp"] = (W / 2, 900)
    return L

def option_rects(c, L, n):
    x0, y0, x1, y1 = L["opt_box"]; bw, bh = x1 - x0, y1 - y0
    rects = []
    if n == 2:
        if c.v:
            h = min(300, (bh - 60) / 2)
            for i in range(2):
                cy = y0 + bh / 4 + i * bh / 2
                rects.append((W2(c), cy, bw - 40, h))
        else:
            w = (bw - 80) / 2; h = min(300, bh - 40)
            for i in range(2):
                rects.append((x0 + w / 2 + i * (w + 80), y0 + bh / 2, w, h))
    elif n == 4:
        if c.v:
            w = (bw - 50) / 2; h = min(270, (bh - 50) / 2)
            for i in range(4):
                r, k = divmod(i, 2)
                rects.append((x0 + w / 2 + k * (w + 50), y0 + h / 2 + 10 + r * (h + 50), w, h))
        else:
            w = (bw - 60) / 2; h = min(200, (bh - 50) / 2)
            for i in range(4):
                r, k = divmod(i, 2)
                rects.append((x0 + w / 2 + k * (w + 60), y0 + h / 2 + 10 + r * (h + 40), w, h))
    elif n == 3:
        if c.v:
            h = min(200, (bh - 60) / 3)
            for i in range(3):
                rects.append((W2(c), y0 + h / 2 + i * (h + 30), bw - 40, h))
        else:
            w = (bw - 100) / 3; h = min(260, bh - 40)
            for i in range(3):
                rects.append((x0 + w / 2 + i * (w + 50), y0 + bh / 2, w, h))
    return rects

def W2(c): return c.W / 2

def draw_display(c, base, L, item, phase, pt, t):
    disp = item["display"]; kind = disp["kind"]
    cx, cy = L["disp"]
    a = eob((t - 0.5) / 0.45) if phase == "ask" else 1.0
    if kind in ("tiles", "scramble"):
        if kind == "tiles":
            word = disp["text"].upper(); ans = disp["answer"].upper()
            chars = [("" if ch == "_" else ch) for ch in word]
            if phase == "reveal" and pt > 0.15:
                states = ["fill" if word[i] == "_" else "n" for i in range(len(word))]
                chars = list(ans)
            else:
                states = ["blank" if ch == "_" else "n" for ch in word]
            tile = tiles_for(word, 150 if c.v else 140, L["disp_w"])
            im = tiles_img(chars, tile, states, c.accent)
            paste(base, im, cx, cy, a)
        else:
            letters = disp["text"].upper(); ans = disp["answer"].upper()
            tile = tiles_for(letters, 140 if c.v else 130, L["disp_w"])
            if phase == "reveal" and pt > 0.15:
                im = tiles_img(list(ans), tile, ["fill"] * len(ans), c.accent)
            else:
                im = tiles_img(list(letters), tile, ["n"] * len(letters), c.accent)
            paste(base, im, cx, cy, a)
        if disp.get("hint"):
            e = emoji_img(disp["hint"], 150 if c.v else 105)
            paste(base, e, cx, cy - (220 if c.v else 200), a)
    elif kind == "emoji":
        e = emoji_img(disp["text"], 220 if c.v else 220)
        if e.width > L["disp_w"]:
            e = e.resize((int(L["disp_w"]), int(e.height * L["disp_w"] / e.width)), Image.LANCZOS)
        paste(base, e, cx, cy, a)
    elif kind == "big":
        lay = Image.new("RGBA", (c.W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        text_center(d, disp["text"], c.W / 2, 60, 130 if c.v else 120, fill=c.accent, stroke=8, maxw=L["disp_w"])
        paste(base, lay, cx, cy, a)
    # answer pill for no-option kinds
    if phase == "reveal" and not item.get("options") and kind in ("emoji", "big"):
        s = eob(pt / 0.45)
        p = pill(disp["answer"].upper(), (40, 190, 90), 70 if c.v else 64)
        paste(base, p, cx, cy + (L["disp_h"] * 0.5 + 110 if c.v else 190), s)


# ---------------------------------------------------------------- Professor Hoot overlay
_hc = {}
def hoot_img(size, pose, blink):
    b = round(blink * 4) / 4
    k = (int(size), pose, b)
    if k not in _hc:
        import mascot
        _hc[k] = mascot.hoot(int(size), pose, blink=b)
    return _hc[k]

def blink_at(t, period=3.3):
    p = t % period
    return max(0.0, 1 - abs(p - 0.09) / 0.09) if p < 0.18 else 0.0

def draw_hoot_corner(c, im, phase, t, pt):
    if c.spec.get("mascot") is False: return
    size = 210 if c.v else 190
    x, y = (130, 205) if c.v else (125, 960)
    pose, bob = "idle", 0.0
    if phase == "count": pose = "think"
    elif phase == "reveal":
        pose = "cheer"; bob = abs(math.sin(pt * 7)) * 24 * max(0.0, 1 - pt / 2.5)
    else:
        bob = math.sin(t * 2.4) * 5
    s = eob(t / 0.5) if phase == "ask" else 1
    paste(im, hoot_img(size, pose, blink_at(t + 0.7)), x, y - bob, s)

def draw_item(c, idx, t, phase, pt):
    item = c.spec["items"][idx]
    L = layout(c, item)
    im = c.background(t); d = ImageDraw.Draw(im)
    W = c.W
    n_total = len(c.spec["items"])
    lab = c.spec.get("label", "QUESTION")
    p = pill(f"{lab} {idx + 1} / {n_total}", tuple(c.spec.get("style", {}).get("pill", [230, 60, 90])), 46 if c.v else 40)
    paste(im, p, W / 2, L["head"], eob(t / 0.4) if phase == "ask" else 1)
    # prompt
    qa = eo(t / 0.4) if phase == "ask" else 1
    size = L["prompt_size"]
    ptxt = item["prompt"]
    if item.get("prompt2") and (phase != "ask" or t >= 3.0): ptxt = item["prompt2"]
    lines = wrap(ptxt, size, L["prompt_w"])
    while len(lines) > (3 if c.v else 2) and size > 40:
        size -= 6; lines = wrap(ptxt, size, L["prompt_w"])
    lay = Image.new("RGBA", (W, int(size * 1.25 * len(lines) + 40)), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for i, ln in enumerate(lines):
        text_center(ld, ln, W / 2, 10 + i * size * 1.22, size, stroke=6, maxw=L["prompt_w"])
    if qa < 1: lay.putalpha(lay.split()[-1].point(lambda v: int(v * qa)))
    im.alpha_composite(lay, (0, int(L["prompt"] - (1 - qa) * 40)))
    custom_origin = None
    if item.get("type") in __import__("eyebrain").DRAW:
        import eyebrain
        custom_origin = eyebrain.DRAW[item["type"]](c, im, item, phase, pt, t)
        d = ImageDraw.Draw(im)
    if item.get("display"):
        draw_display(c, im, L, item, phase, pt, t)
    # options
    opts = [] if custom_origin else item.get("options", [])
    rects = option_rects(c, L, len(opts))
    letters = "ABCD"
    for k, (o, r) in enumerate(zip(opts, rects)):
        cx, cy, w, h = r
        label = o[0]; emo = o[1] if len(o) > 1 else None
        st = "normal"
        if phase == "reveal":
            st = "right" if k == item["right"] else "wrong"
        delay = (1.0 if item.get("display") else 0.8) + 0.35 * k
        s = eob((t - delay) / 0.45) if phase == "ask" else 1.0
        if phase == "reveal" and k == item["right"]:
            s = 1 + 0.07 * math.sin(cl(pt / 0.5) * math.pi)
        if phase == "reveal" and k != item["right"]:
            s = 1 - 0.08 * eo(pt / 0.4)
        a = 0.55 if (phase == "reveal" and k != item["right"]) else 1.0
        if phase == "reveal" and k == item["right"] and item.get("type") == "odd4" and pt < 0.8:
            cx += 18 * math.sin(pt * 40) * (1 - pt / 0.8)
        paste(im, card(int(w), int(h), letters[k] if item.get("letters", True) else None, label, emo, st, c.card_fill, c.accent), cx, cy, s, a)
    # bottom area
    if phase == "count":
        cs = c.spec["count_secs"]
        nleft = max(1, cs - int(pt)); frac = pt - int(pt)
        sz = 1.25 - 0.25 * eo(frac / 0.3)
        f = font(F_BOLD, 200 if c.v else 120)
        num = Image.new("RGBA", (400, 280), (0, 0, 0, 0)); nd = ImageDraw.Draw(num)
        tw = nd.textlength(str(nleft), font=f)
        if not c.v:
            nd.ellipse((60, 20, 340, 260), fill=(0, 0, 0, 90), outline=c.accent, width=10)
            nd.text(((400 - tw) / 2, 50), str(nleft), font=f, fill=c.accent)
        else:
            nd.text(((400 - tw) / 2, 0), str(nleft), font=f, fill=c.accent, stroke_width=10, stroke_fill=(30, 10, 50))
        paste(im, num, L["count"][0], L["count"][1], sz * (0.7 if not c.v else 1))
        x0, y0, x1, y1 = L["bar"]
        bw = (x1 - x0) * (1 - pt / cs)
        d.rounded_rectangle((x0, y0, x1, y1), radius=(y1 - y0) // 2, fill=(255, 255, 255, 60))
        d.rounded_rectangle((x0, y0, x0 + max(y1 - y0, bw), y1), radius=(y1 - y0) // 2, fill=c.accent)
    elif phase == "ask" and c.v:
        if t > 2.2:
            a_ = eo((t - 2.2) / 0.4)
            lay = Image.new("RGBA", (W, 140), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            text_center(ld, item.get("nudge", "Comment your answer below!"), W / 2, 30, 62, maxw=W - 120)
            lay.putalpha(lay.split()[-1].point(lambda v: int(v * a_)))
            im.alpha_composite(lay, (0, L["bottom"]))
    elif phase == "reveal":
        for i, ln in enumerate(item.get("fact", [])):
            a_ = eo((pt - 0.6 - i * 0.9) / 0.4)
            if a_ <= 0: continue
            sz = (64 if i == 0 else 52) if c.v else (56 if i == 0 else 46)
            lay = Image.new("RGBA", (W, 110), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            text_center(ld, ln, W / 2, 10, sz, fill=c.accent if i == 0 else (255, 255, 255), stroke=5, maxw=W - 120)
            lay.putalpha(lay.split()[-1].point(lambda v: int(v * a_)))
            im.alpha_composite(lay, (0, int(L["bottom"] + i * (95 if c.v else 70) + (1 - a_) * 20)))
        if pt < 2.4:
            cols = [(255, 210, 60), (60, 255, 120), (255, 90, 140), (90, 200, 255)]
            ox = W / 2; oy = c.H * 0.55
            if custom_origin:
                ox, oy = custom_origin
            elif opts and rects:
                ox, oy = rects[item["right"]][0], rects[item["right"]][1]
            for i in range(40):
                ang = i * 2.399; sp = 500 + (i * 53) % 400
                x = ox + math.cos(ang) * sp * pt; y = oy + math.sin(ang) * sp * pt + 600 * pt * pt
                d.rectangle((x - 12, y - 6, x + 12, y + 6), fill=cols[i % 4])
    draw_hoot_corner(c, im, phase, t, pt)
    return im.convert("RGB")

def draw_intro(c, t):
    im = c.background(t); d = ImageDraw.Draw(im); W, H = c.W, c.H
    tc = c.spec["title_card"]
    if c.spec.get("mascot") is False:
        e = emoji_img(tc.get("emoji", "🧠"), 340 if c.v else 260)
        paste(im, e, W / 2, (560 if c.v else 250) + 18 * math.sin(t * 3), eob(t / 0.5))
    else:
        pose = "cheer" if t < 1.0 else "idle"
        hs = 520 if c.v else 380
        paste(im, hoot_img(hs, pose, blink_at(t)), W / 2, (520 if c.v else 250) - abs(math.sin(t * 3)) * 18, eob(t / 0.5))
    ys = (860, 1030) if c.v else (470, 610)
    for i, (txt, col) in enumerate([(tc["line1"], (255, 255, 255)), (tc["line2"], c.accent)]):
        s = eob((t - 0.4 - i * 0.35) / 0.4)
        lay = Image.new("RGBA", (W, 200), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        text_center(ld, txt, W / 2, 10, 140 if c.v else 120, fill=col, stroke=8, maxw=W - 100)
        paste(im, lay, W / 2, ys[i] + 90, s)
    if tc.get("tag"):
        s = eob((t - 1.4) / 0.5)
        p = pill(tc["tag"], tuple(c.spec.get("style", {}).get("pill", [230, 60, 90])), 72 if c.v else 60)
        paste(im, p, W / 2, 1400 if c.v else 900, s * (1 + 0.03 * math.sin(t * 6)))
    return im.convert("RGB")

def draw_outro(c, t):
    im = c.background(t); d = ImageDraw.Draw(im); W, H = c.W, c.H
    oc = c.spec["outro"]
    s = eob(t / 0.5)
    lay = Image.new("RGBA", (W, 380), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    text_center(ld, oc["line1"], W / 2, 10, 120 if c.v else 100, stroke=8, maxw=W - 100)
    text_center(ld, oc["line2"], W / 2, 170, 120 if c.v else 100, fill=c.accent, stroke=8, maxw=W - 100)
    paste(im, lay, W / 2, 520 if c.v else 260, s)
    a_ = eo((t - 1.0) / 0.4)
    lay = Image.new("RGBA", (W, 140), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    text_center(ld, oc.get("line3", "Comment your score below!"), W / 2, 20, 70 if c.v else 60, maxw=W - 120)
    lay.putalpha(lay.split()[-1].point(lambda v: int(v * a_))); im.alpha_composite(lay, (0, 900 if c.v else 520))
    if c.spec.get("mascot") is not False:
        hs = 300 if c.v else 300
        hx, hy = (W / 2 - 350, 1110) if c.v else (W / 2 - 560, 800)
        paste(im, hoot_img(hs, "point" if t > 1.8 else "idle", blink_at(t)), hx, hy - abs(math.sin(t * 2.5)) * 10, eob((t - 0.6) / 0.5))
    s2 = eob((t - 2.0) / 0.5)
    cta = oc.get("cta", "SUBSCRIBE")
    btn = Image.new("RGBA", (800, 220), (0, 0, 0, 0)); bd = ImageDraw.Draw(btn)
    bd.rounded_rectangle((0, 0, 799, 219), radius=110, fill=(255, 40, 70))
    f = font(F_BOLD, 76); tw = bd.textlength(cta, font=f); bd.text(((800 - tw) / 2, 28), cta, font=f, fill=(255, 255, 255))
    sub = oc.get("cta_sub", "and hit LIKE for more puzzles!")
    f2 = font(F_MED, 44); tw = bd.textlength(sub, font=f2); bd.text(((800 - tw) / 2, 128), sub, font=f2, fill=(255, 230, 230))
    paste(im, btn, W / 2, 1350 if c.v else 800, s2 * (1 + 0.04 * math.sin(t * 5)))
    return im.convert("RGB")

def frame_at(c, seg, t):
    tm = c.spec["timing"]
    if seg == "intro": return draw_intro(c, t)
    if seg == "outro": return draw_outro(c, t)
    i = int(seg[1:]); s = tm[seg]
    a, cs = s["ask"], c.spec["count_secs"]
    if t < a: return draw_item(c, i, t, "ask", t)
    if t < a + cs: return draw_item(c, i, t, "count", t - a)
    return draw_item(c, i, t, "reveal", t - a - cs)

if __name__ == "__main__":
    spec = json.load(open(sys.argv[1])); c = Ctx(spec)
    if sys.argv[2] == "still":
        frame_at(c, sys.argv[3], float(sys.argv[4])).save(sys.argv[5], quality=90)
    else:
        seg, out = sys.argv[3], sys.argv[4]
        n = round(spec["timing"][seg]["dur"] * FPS)
        tmp = out[:-4] + ".part.mp4"
        p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{c.W}x{c.H}", "-r", str(FPS),
                              "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        for k in range(n):
            p.stdin.write(frame_at(c, seg, k / FPS).tobytes())
        p.stdin.close()
        if p.wait() == 0: os.rename(tmp, out)
        else: sys.exit(1)
