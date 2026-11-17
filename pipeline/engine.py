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
F_BOLD = os.path.join(FONTS, "Fredoka-SemiBold.ttf")   # premium rounded headline font
F_MED = os.path.join(FONTS, "Nunito-Bold.ttf")
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
            bg = g.resize((W, H)).convert("RGBA")
            # premium depth: soft light from the top, gentle vignette at the edges
            import numpy as np
            yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
            dx = (xx - W / 2) / (W * 0.75); dy = (yy - H * 0.18) / (H * 0.75)
            light = np.clip(1 - np.sqrt(dx * dx + dy * dy), 0, 1) ** 2 * 70
            ex = (xx - W / 2) / (W / 2); ey = (yy - H / 2) / (H / 2)
            vig = np.clip(np.sqrt(ex * ex + ey * ey) - 0.75, 0, 1) * 90
            a = np.zeros((H, W, 4), np.uint8); a[..., :3] = 255; a[..., 3] = light.astype(np.uint8)
            bg.alpha_composite(Image.fromarray(a, "RGBA"))
            b_ = np.zeros((H, W, 4), np.uint8); b_[..., :3] = (20, 10, 50); b_[..., 3] = vig.astype(np.uint8)
            bg.alpha_composite(Image.fromarray(b_, "RGBA"))
            self._bg = bg.convert("RGB")
        im = self._bg.copy().convert("RGBA")
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        k = self.bgkind
        if k == "blobs":  # modern minimal: 3 big soft shapes drifting slowly
            spots = [(0.15, 0.12, 0.42), (0.92, 0.48, 0.36), (0.25, 0.9, 0.5)]
            for i, (fx, fy, fr) in enumerate(spots):
                x = W * fx + 30 * math.sin(t * 0.4 + i * 2); y = H * fy + 30 * math.cos(t * 0.35 + i)
                r = min(W, H) * fr
                d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 20))
        elif k == "dots":  # soft polka dots
            step = 120; off = (t * 12) % step
            for yy in range(-step, H + step, step):
                for xx in range(-step, W + step, step):
                    sx = xx + (step / 2 if (yy // step) % 2 else 0) + off
                    d.ellipse((sx - 9, yy + off - 9, sx + 9, yy + off + 9), fill=(255, 255, 255, 30))
        elif k == "bubbles":
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

def soft_shadow(base, box, r=30, off=14, blur=18, alpha=70):
    """Draw a soft drop shadow under a rounded box onto base (RGBA)."""
    x0, y0, x1, y1 = [int(v) for v in box]; pad = blur * 3
    sh = Image.new("RGBA", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad, pad + x1 - x0, pad + y1 - y0), radius=r, fill=(15, 5, 40, alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(sh, (max(0, x0 - pad), max(0, y0 - pad + off))) if x0 - pad >= 0 and y0 - pad + off >= 0 else base.paste(sh, (x0 - pad, y0 - pad + off), sh)

def text_center(d, txt, cx, y, size, fill=(255, 255, 255), fnt=F_BOLD, stroke=0, sfill=(20, 10, 40), maxw=900):
    f = font(fnt, size)
    while d.textlength(txt, font=f) > maxw and size > 24:
        size -= 3; f = font(fnt, size)
    w = d.textlength(txt, font=f)
    if stroke:  # modern look: soft drop shadow instead of a thick dark outline
        off = max(3, int(size * 0.05))
        d.text((cx - w / 2, y + off), txt, font=f, fill=(20, 10, 50, 80))
    d.text((cx - w / 2, y), txt, font=f, fill=fill)
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
        bg, edge, lt = fill, (232, 234, 246), (30, 30, 60)
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle((pad + 4, pad + 12, pad + w - 4, pad + h + 8), radius=rad, fill=(15, 5, 40, 70))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d.rounded_rectangle((pad, pad, pad + w, pad + h), radius=rad, fill=bg, outline=edge, width=4 if state == "normal" else 8)
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
        L = dict(head=190, prompt=320, prompt_size=112, prompt_w=W - 100,
                 disp=(W / 2, 880), disp_h=260, disp_w=W - 120,
                 opt_box=(60, 1060 if has_disp else 760, W - 60, 1480),
                 bottom=1520, count=(W / 2, 1600), bar=(160, 1750, W - 160, 1786))
    else:
        L = dict(head=80, prompt=140, prompt_size=86, prompt_w=W - 300,
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

ANSWER_HINTS = {
    "memgrid": "Watch the flashes",
    "spotdiff": "Look at A and B",
    "missing": "Remember all 9 images",
    "flipped": "",
    "numflash": "Remember all 6 digits",
    "bug": "Listen to Hoot!",
    "cardflip": "Remember the cards",
    "zoom": "Guess early!",
    "diceflash": "Remember the dice",
    "rowdiff": "",
    "letterhunt": "",
    "crowd": "",
}
def answer_hint(item):
    """one short line under the question that says HOW to answer (shown from the first frame)"""
    t = item.get("type")
    if t in ANSWER_HINTS: return ANSWER_HINTS[t]
    return ""

def draw_item(c, idx, t, phase, pt):
    item = c.spec["items"][idx]
    L = layout(c, item)
    im = c.background(t); d = ImageDraw.Draw(im)
    W = c.W
    n_total = len(c.spec["items"])
    lab = c.spec.get("label", "QUESTION")
    levels = c.spec.get("levels")
    if not levels and c.v and n_total >= 3:  # easy → medium → hard across the Short
        ne = n_total // 3; nh = n_total // 3  # 6 puzzles → 2 easy, 2 medium, 2 hard
        levels = ["EASY"] * ne + ["MEDIUM"] * (n_total - ne - nh) + ["HARD"] * nh
    if levels:
        lv = levels[idx]; lcol = {"EASY": (40, 185, 100), "MEDIUM": (250, 150, 30), "HARD": (235, 50, 80)}.get(lv, (230, 60, 90))
        p = pill(f"LEVEL {idx + 1}  ·  {lv}", lcol, 46 if c.v else 40)
    else:
        p = pill(c.spec.get("pill_text") or f"{lab} {idx + 1} / {n_total}", tuple(c.spec.get("style", {}).get("pill", [230, 60, 90])), 46 if c.v else 40)
    paste(im, p, W / 2, L["head"], eob(t / 0.4) if phase == "ask" else 1)
    if n_total > 1:  # progress dots
        gap = 26 if c.v else 22; r0 = 7 if c.v else 6
        if n_total > 8: gap, r0 = gap * 0.7, r0 * 0.8
        dx0 = W / 2 - (n_total - 1) * gap / 2; dy = L["head"] + (66 if c.v else 56)
        for k in range(n_total):
            rr = r0 * (1.5 if k == idx else 1)
            col = c.accent + (255,) if k == idx else ((255, 255, 255, 230) if k < idx else (255, 255, 255, 90))
            d.ellipse((dx0 + k * gap - rr, dy - rr, dx0 + k * gap + rr, dy + rr), fill=col)
    # prompt
    qa = eo(t / 0.4) if phase == "ask" else 1
    size = L["prompt_size"]
    # QUESTION FIRST: show the real question (prompt2 if there is one) from the very first frame, plus how to answer
    ptxt = item["prompt"]; stack = bool(item.get("stack") and item.get("prompt2"))
    if item.get("prompt2") and not stack:  # two-stage question: first part -> second part
        import eyebrain
        se = item.get("stage_end") or max(1.5, eyebrain.min_ask(item) - 1.5)
        if phase != "ask" or t >= se: ptxt = item["prompt2"]
    def _lines(sz):
        if stack: return wrap(item["prompt"], sz, L["prompt_w"]) + wrap(item["prompt2"], sz, L["prompt_w"])
        return wrap(ptxt, sz, L["prompt_w"])
    lines = _lines(size)
    while len(lines) > (3 if stack else 2) and size > 56:
        size -= 6; lines = _lines(size)
    n_first = len(wrap(item["prompt"], size, L["prompt_w"])) if stack else 0
    hint = item["hint"] if "hint" in item else answer_hint(item)
    hsize = int(size * 0.5) if hint else 0
    hint_h = int(hsize * 1.5) if hint else 0
    lay = Image.new("RGBA", (W, int(size * 1.25 * len(lines) + 40 + hint_h)), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    for i, ln in enumerate(lines):
        text_center(ld, ln, W / 2, 10 + i * size * 1.22, size, fill=(c.accent if (stack and i < n_first) else (255, 255, 255)), stroke=6, maxw=L["prompt_w"])
    if hint:
        text_center(ld, hint, W / 2, 10 + len(lines) * size * 1.22 + 6, hsize, fill=c.accent, stroke=4, maxw=L["prompt_w"])
    if qa < 1: lay.putalpha(lay.split()[-1].point(lambda v: int(v * qa)))
    im.alpha_composite(lay, (0, int(L["prompt"] - (1 - qa) * 40)))
    custom_origin = None
    prompt_bottom = L["prompt"] + len(lines) * size * 1.22 + 20 + hint_h
    if item.get("type") in __import__("eyebrain").DRAW:
        import eyebrain
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0))
        custom_origin = eyebrain.DRAW[item["type"]](c, lay, item, phase, pt, t)
        bb = lay.getbbox()
        # fill the empty space: scale the whole puzzle up to the free area (same scale every frame of the scene)
        if bb and item.get("autofit", True):
            ref = getattr(c, "_fit", {}).get(idx)
            if ref is None:
                lay0 = Image.new("RGBA", im.size, (0, 0, 0, 0))
                tm0 = c.spec.get("timing", {}).get(f"i{idx}", {})
                eyebrain.DRAW[item["type"]](c, lay0, item, "reveal", 1.5, tm0.get("ask", 6) + c.spec["count_secs"] + 1.5)
                b0 = lay0.getbbox() or bb
                fx0, fy0, fx1, fy1 = (40, prompt_bottom + 30, W - 40, L["bottom"] - 75) if c.v else (60, prompt_bottom + 20, W - 60, L["bottom"] - 45)
                sc = min((fx1 - fx0) / (b0[2] - b0[0]), (fy1 - fy0) / (b0[3] - b0[1]), 1.45)
                ref = (b0, max(0.75, sc), ((fx0 + fx1) / 2, (fy0 + fy1) / 2))
                if not hasattr(c, "_fit"): c._fit = {}
                c._fit[idx] = ref
            b0, sc, (tcx, tcy) = ref
            if True:  # always fit & centre in the free area (scale up to fill, down if it would overlap text)
                crop = lay.crop(b0); crop = crop.resize((int(crop.width * sc), int(crop.height * sc)), Image.LANCZOS)
                ox_ = int(tcx - crop.width / 2); oy_ = int(tcy - crop.height / 2)
                im.alpha_composite(crop, (max(0, ox_), max(0, oy_))) if ox_ >= 0 and oy_ >= 0 else im.paste(crop, (ox_, oy_), crop)
                if custom_origin:
                    custom_origin = (tcx + (custom_origin[0] - (b0[0] + b0[2]) / 2) * sc, tcy + (custom_origin[1] - (b0[1] + b0[3]) / 2) * sc)
            else:
                im.alpha_composite(lay)
        else:
            im.alpha_composite(lay)
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
    fact_y = None
    if phase == "count":
        cs = c.spec["count_secs"]
        nleft = max(1, cs - int(pt)); frac = pt - int(pt)
        R = 120 if c.v else 80; S = int(R * 2 + 60)
        ring = Image.new("RGBA", (S, S), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
        rd.ellipse((30, 30, S - 30, S - 30), fill=(255, 255, 255, 235))
        rd.ellipse((14, 14, S - 14, S - 14), outline=(255, 255, 255, 90), width=14)
        rd.arc((14, 14, S - 14, S - 14), -90, -90 + 360 * (1 - pt / cs), fill=c.accent, width=14)
        f = font(F_BOLD, int(R * 1.15)); txt = str(nleft); tw = rd.textlength(txt, font=f)
        rd.text(((S - tw) / 2, S / 2 - R * 0.78), txt, font=f, fill=(40, 30, 90))
        sz = 1.12 - 0.12 * eo(frac / 0.25)
        paste(im, ring, L["count"][0], L["count"][1], sz)
        x0, y0, x1, y1 = L["bar"]
        bw = (x1 - x0) * (1 - pt / cs)
        d.rounded_rectangle((x0, y0, x1, y1), radius=(y1 - y0) // 2, fill=(255, 255, 255, 60))
        d.rounded_rectangle((x0, y0, x0 + max(y1 - y0, bw), y1), radius=(y1 - y0) // 2, fill=c.accent)
    elif phase == "ask" and c.v:
        if t > 2.2:
            a_ = eo((t - 2.2) / 0.4)
            lay = Image.new("RGBA", (W, 140), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            text_center(ld, item.get("nudge", "Comment your answer below!"), W / 2, 30, 76, maxw=W - 80)
            lay.putalpha(lay.split()[-1].point(lambda v: int(v * a_)))
            im.alpha_composite(lay, (0, L["bottom"]))
    elif phase == "reveal":
        fact_y = L["bottom"] + 10 if item.get("fact") else None
        for i, ln in enumerate(item.get("fact", [])):
            a_ = eo((pt - 0.6 - i * 0.9) / 0.4)
            if a_ <= 0: continue
            sz = (84 if i == 0 else 62) if c.v else (60 if i == 0 else 48)
            lay = Image.new("RGBA", (W, 135), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            text_center(ld, ln, W / 2, 10, sz, fill=c.accent if i == 0 else (255, 255, 255), stroke=5, maxw=W - 120)
            lay.putalpha(lay.split()[-1].point(lambda v: int(v * a_)))
            im.alpha_composite(lay, (0, int(L["bottom"] + i * (115 if c.v else 72) + (1 - a_) * 20)))
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
    if phase == "reveal" and fact_y is not None and pt > 0.35:
        a_ = eob((pt - 0.35) / 0.35)
        chip = pill("ANSWER", (40, 190, 90), 38 if c.v else 32)
        paste(im, chip, W / 2, fact_y - (36 if c.v else 30), a_)
    draw_hoot_corner(c, im, phase, t, pt)
    mc = c.spec.get("midcta")
    if mc and phase == "reveal" and idx == mc.get("idx"): cta_popup(c, im, pt)
    tm_i = c.spec.get("timing", {}).get(f"i{idx}", {})
    if idx == 0 and phase == "ask" and tm_i.get("hook") and c.spec.get("hook") and t < tm_i["hook"] + 0.3:
        hook_banner(c, im, c.spec["hook"], t, tm_i["hook"])
    elif idx > 0 and phase == "ask" and c.v and t < 1.9:  # long videos: hooks are SPOKEN (say.items[i].hook), never text banners
        tz = item.get("teaser")
        if tz is None:  # default cliff-hangers (varied) that keep people watching to the last puzzle
            rnd = random.Random(c.spec.get("hook", "") + str(idx))
            if idx == n_total - 1: tz = rnd.choice(TEASE_FINAL)
            elif levels and levels[idx] == "HARD" and levels[idx - 1] != "HARD": tz = rnd.choice(TEASE_HARD)
            elif levels and levels[idx] == "MEDIUM" and levels[idx - 1] == "EASY": tz = rnd.choice(TEASE_MED)
        if tz: hook_banner(c, im, tz, t, 1.6)
    progress_bar(c, im, f"i{idx}", {"ask": t, "count": tm_i.get("ask", 0) + pt, "reveal": tm_i.get("ask", 0) + c.spec["count_secs"] + pt}[phase])
    if phase == "reveal" and pt < 0.18:
        im.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, int(150 * (1 - pt / 0.18)))))
    if phase == "ask" and t < 0.55 and not (idx == 0 and tm_i.get("hook")):
        im = transition_in(c, im, t / 0.55, idx)
    return im.convert("RGB")

TEASE_MED = ["Warm-up done. Now it gets tricky!", "Too easy? Let's turn it up!", "Okay, now focus...",
             "Level up! Eyes open.", "Halfway there. Getting harder!", "Nice! But can you do this?"]
TEASE_HARD = ["HARD MODE! Only 1% get these", "Brain check: this is where most fail", "Now the real test begins...",
              "Hard level unlocked!", "Still with me? This one's sneaky", "Most people give up here"]
TEASE_FINAL = ["FINAL PUZZLE! Don't blink...", "Last one. The hardest of all!", "Boss level! Can you beat it?",
               "This one fools almost everyone", "Final round. Show me your eyes!", "Get this and you're a genius"]

TRANSITIONS = ["bands", "zoom", "slide", "split", "iris"]

def transition_in(c, im, u, idx):
    """Modern scene-in transitions (rotate per puzzle): brand-colour band sweep, zoom punch, whip slide,
    centre split, circle iris. u: 0 → 1 over the first 0.55 s of the scene."""
    W, H = im.size; seed = c.spec.get("music_seed", 0)
    kind = c.spec.get("transition") or TRANSITIONS[(idx + seed) % len(TRANSITIONS)]
    dark = tuple(int(v * 0.7) for v in c.pal[1]) + (255,)
    acc = tuple(c.accent) + (255,); pill_c = tuple(c.spec.get("style", {}).get("pill", [230, 60, 90])) + (255,)
    if kind == "iris":
        iris(c, im, u); return im
    if kind == "bands":  # three diagonal colour bands sweep off to the right
        out = im.copy(); d = ImageDraw.Draw(out)
        for k, col in enumerate([dark, pill_c, acc]):
            p_ = eo(max(0.0, min(1.0, (u - k * 0.12) / 0.7)))
            x = -0.3 * W + p_ * 1.9 * W
            d.polygon([(x, -10), (x + W * 1.2, -10), (x + W * 1.2 - H * 0.35, H + 10), (x - H * 0.35, H + 10)], fill=col)
        return out
    if kind == "zoom":  # punch-in: starts zoomed + blurred, snaps into focus
        z = 1 + 0.35 * (1 - eo(u)); b = 14 * (1 - eo(u))
        fr = im.resize((int(W * z), int(H * z)), Image.BILINEAR)
        fr = fr.crop(((fr.width - W) // 2, (fr.height - H) // 2, (fr.width - W) // 2 + W, (fr.height - H) // 2 + H))
        if b > 0.5: fr = fr.filter(ImageFilter.GaussianBlur(b))
        fl = Image.new("RGBA", (W, H), (255, 255, 255, int(160 * (1 - u)))); fr.alpha_composite(fl)
        return fr
    if kind == "slide":  # whip pan in from the right with motion blur
        off = int(W * (1 - eo(u)) ** 1.6 * 1.0)
        out = Image.new("RGBA", (W, H), dark); fr = im
        if off > 4: fr = im.filter(ImageFilter.BoxBlur(min(30, off // 12)))
        out.alpha_composite(fr, (off, 0)) if off < W else None
        return out
    if kind == "split":  # two panels slide apart from the middle
        out = im.copy(); d = ImageDraw.Draw(out); g = eo(u) * H / 2
        d.rectangle((0, 0, W, H / 2 - g), fill=dark); d.rectangle((0, H / 2 + g, W, H), fill=pill_c)
        if g < H / 2 - 4: d.rectangle((0, H / 2 - g - 8, W, H / 2 - g), fill=acc); d.rectangle((0, H / 2 + g, W, H / 2 + g + 8), fill=acc)
        return out
    return im

def cta_popup(c, im, pt):
    """Mid-video pop-up: LIKE + SUBSCRIBE buttons (with bell) slide in, the subscribe button gets 'clicked'."""
    a_in = eob((pt - 0.10) / 0.14); a_out = max(0.0, min(1.0, (0.96 - pt) / 0.08)); a = min(a_in, a_out)
    if a <= 0.02: return
    W, H = im.size; sc = 1.0 if not c.v else 1.25
    cw, chh = int(900 * sc), int(190 * sc)
    card_ = Image.new("RGBA", (cw + 60, chh + 60), (0, 0, 0, 0)); cd = ImageDraw.Draw(card_)
    cd.rounded_rectangle((30, 40, cw + 30, chh + 40), radius=50, fill=(15, 5, 40, 110)); card_ = card_.filter(ImageFilter.GaussianBlur(12)); cd = ImageDraw.Draw(card_)
    cd.rounded_rectangle((30, 30, cw + 30, chh + 30), radius=50, fill=(255, 255, 255))
    f = font(F_BOLD, int(62 * sc))
    cd.rounded_rectangle((60, 56, 60 + int(310 * sc), chh + 4), radius=40, fill=(30, 110, 235))
    cd.text((60 + int(310 * sc) / 2 + 40, 30 + chh / 2), "LIKE", font=f, fill=(255, 255, 255), anchor="mm")
    press = 0.9 if 0.45 < pt < 0.55 else 1.0
    bx0 = 60 + int(340 * sc); cd.rounded_rectangle((bx0, 56, cw, chh + 4), radius=40, fill=(225, 30, 45))
    cd.text(((bx0 + cw) / 2 + 36, 30 + chh / 2), "SUBSCRIBE", font=f, fill=(255, 255, 255), anchor="mm")
    card_.alpha_composite(emoji_img("👍", int(82 * sc)), (60 + 22, 30 + int(chh / 2 - 41 * sc)))
    card_.alpha_composite(emoji_img("🔔", int(82 * sc)), (bx0 + 22, 30 + int(chh / 2 - 41 * sc)))
    pulse = (1 + 0.04 * math.sin(pt * 40)) * press
    off = (1 - a_in) * 120
    if c.v: paste(im, card_, W / 2, H - (chh + 60) / 2 - 240 + off, pulse, a)
    else:  # landscape: compact, bottom-right corner (keeps the answer text and puzzle visible)
        k = 0.6; paste(im, card_, W - (cw + 60) * k / 2 - 30, H - (chh + 60) * k / 2 - 14 + off * k, pulse * k, a)

def hook_banner(c, im, text, t, hd):
    """Big tilted hook card shown over puzzle 1 for the first seconds (retention hook)."""
    W = im.width
    a = eob(t / 0.3) if t < hd else max(0.0, 1 - (t - hd) / 0.3)
    if a <= 0.02: return
    size = 84 if c.v else 70; lines = wrap(text, size, W - 220)
    h = int(len(lines) * size * 1.2 + 70); w = W - 120
    card_ = Image.new("RGBA", (w + 60, h + 60), (0, 0, 0, 0)); cd = ImageDraw.Draw(card_)
    cd.rounded_rectangle((30, 40, w + 30, h + 40), radius=40, fill=(15, 5, 40, 90))
    card_ = card_.filter(ImageFilter.GaussianBlur(12)); cd = ImageDraw.Draw(card_)
    cd.rounded_rectangle((30, 30, w + 30, h + 30), radius=40, fill=(255, 255, 255))
    cd.rounded_rectangle((30, 30, 60, h + 30), radius=14, fill=(235, 50, 80))
    for i, ln in enumerate(lines):
        f = font(F_BOLD, size); tw = cd.textlength(ln, font=f)
        cd.text(((w + 60 - tw) / 2 + 10, 30 + 35 + i * size * 1.2), ln, font=f, fill=(235, 50, 80) if i == len(lines) - 1 else (40, 30, 90))
    card_ = card_.rotate(-3, resample=Image.BICUBIC, expand=True)
    pulse = 1 + 0.03 * math.sin(t * 8)
    paste(im, card_, W / 2, im.height * (0.47 if c.v else 0.5), a * pulse, 1)

def progress_bar(c, im, seg, t_local):
    """Thin bar across the very top showing how much of the whole video is done (keeps viewers to the end)."""
    tm = c.spec.get("timing", {}); order = tm.get("order")
    if not order or not c.v: return
    tot = sum(tm[g]["dur"] for g in order); before = sum(tm[g]["dur"] for g in order[:order.index(seg)]) if seg in order else 0
    u = max(0.0, min(1.0, (before + t_local) / tot))
    d = ImageDraw.Draw(im); W = im.width
    d.rectangle((0, 0, W, 12), fill=(255, 255, 255, 70)); d.rectangle((0, 0, int(W * u), 12), fill=c.accent)

def iris(c, im, u):
    """Professional circle-wipe transition: a brand-coloured screen opens from the centre."""
    W, H = im.size; R = math.hypot(W, H) / 2 * eo(u)
    m = Image.new("L", (W, H), 255); ImageDraw.Draw(m).ellipse((W / 2 - R, H / 2 - R, W / 2 + R, H / 2 + R), fill=0)
    col = tuple(int(v * 0.75) for v in c.pal[1]) + (255,)
    im.paste(Image.new("RGBA", (W, H), col), (0, 0), m)
    if 0 < R:
        ImageDraw.Draw(im).ellipse((W / 2 - R, H / 2 - R, W / 2 + R, H / 2 + R), outline=c.accent, width=14)

def draw_intro(c, t):
    im = c.background(t); d = ImageDraw.Draw(im); W, H = c.W, c.H
    tc = c.spec["title_card"]
    if c.spec.get("mascot") is False:
        e = emoji_img(tc.get("emoji", "🧠"), 340 if c.v else 260)
        paste(im, e, W / 2, (560 if c.v else 250) + 18 * math.sin(t * 3), eob(t / 0.5))
    else:
        pose = "cheer" if t < 1.0 else "idle"
        hs = 520 if c.v else 380
        gl = _glow(900 if c.v else 700, (255, 240, 190)); paste(im, gl, W / 2, 520 if c.v else 250, eob(t / 0.6))
        paste(im, hoot_img(hs, pose, blink_at(t)), W / 2, (520 if c.v else 250) - abs(math.sin(t * 3)) * 18, eob(t / 0.5))
    ys = (860, 1030) if c.v else (470, 610)
    for i, (txt, col) in enumerate([(tc["line1"], (255, 255, 255)), (tc["line2"], c.accent)]):
        s = eob((t - 0.4 - i * 0.35) / 0.4)
        lay = Image.new("RGBA", (W, 200), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        text_center(ld, txt, W / 2, 10, 140 if c.v else 120, fill=col, stroke=8, maxw=W - 100)
        paste(im, lay, W / 2, ys[i] + 90, s)
    wl = Image.new("RGBA", (W, 80), (0, 0, 0, 0)); wd = ImageDraw.Draw(wl)
    text_center(wd, "W I T   W O N D E R L A N D", W / 2, 10, 34 if c.v else 30, fill=(255, 255, 255, 200), maxw=W - 100)
    paste(im, wl, W / 2, 130 if c.v else 70, eo(t / 0.6))
    if tc.get("tag"):
        s = eob((t - 1.4) / 0.5)
        p = pill(tc["tag"], tuple(c.spec.get("style", {}).get("pill", [230, 60, 90])), 72 if c.v else 60)
        paste(im, p, W / 2, 1400 if c.v else 900, s * (1 + 0.03 * math.sin(t * 6)))
    return im.convert("RGB")

def _rays(W, H, cx, cy, ang, col, n=16, alpha=46):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay); R = max(W, H) * 1.2
    for k in range(n):
        a0 = math.radians(ang + k * 360 / n); a1 = a0 + math.radians(360 / n / 2)
        d.polygon([(cx, cy), (cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=col + (alpha,))
    return lay

def _glow(size, col):
    g = Image.new("RGBA", (size, size), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for k in range(12, 0, -1):
        r = size / 2 * k / 12; gd.ellipse((size / 2 - r, size / 2 - r, size / 2 + r, size / 2 + r), fill=col + (int(110 * (1 - k / 12) + 8),))
    return g

def _icon_btn(emo, label, col, size):
    f = font(F_BOLD, int(size * 0.24)); lw = ImageDraw.Draw(Image.new("RGB", (1, 1))).textlength(label, font=f)
    Wb = int(max(size + 40, lw + 30)); im = Image.new("RGBA", (Wb, size + 110), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = Wb / 2; r = size / 2
    d.ellipse((cx - r + 6, 26, cx + r + 6, 26 + size), fill=(0, 0, 0, 90))
    d.ellipse((cx - r, 18, cx + r, 18 + size), fill=col, outline=(255, 255, 255), width=8)
    hl = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(hl).ellipse((cx - r * 0.62, 18 + size * 0.1, cx + r * 0.1, 18 + size * 0.36), fill=(255, 255, 255, 70))
    im.alpha_composite(hl)
    e = emoji_img(emo, size * 0.5); im.alpha_composite(e, (int(cx - e.width / 2), int(18 + size / 2 - e.height / 2)))
    d.text((cx - lw / 2, size + 34), label, font=f, fill=(255, 255, 255), stroke_width=2, stroke_fill=(20, 10, 40))
    return im

def _bubble(text, w, size, tail="left"):
    f = font(F_BOLD, size); lines = wrap(text, size, w - 70)
    h = int(len(lines) * size * 1.25 + 60)
    im = Image.new("RGBA", (w, h + 50), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h), radius=44, fill=(255, 255, 255), outline=(255, 210, 60), width=8)
    tx = 90 if tail == "left" else w - 90
    d.polygon([(tx - 30, h - 6), (tx + 30, h - 6), (tx - 50 if tail == "left" else tx + 50, h + 46)], fill=(255, 255, 255))
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=f); d.text(((w - tw) / 2, 28 + i * size * 1.25), ln, font=f, fill=(40, 30, 90))
    return im

def draw_outro(c, t):
    im = c.background(t); W, H = c.W, c.H; v = c.v
    oc = c.spec["outro"]
    hx, hy = (W / 2, 900) if v else (W * 0.27, 600)
    im.alpha_composite(_rays(W, H, hx, hy, t * 18, tuple(c.accent)))
    g = _glow(900 if v else 760, (255, 230, 140)); paste(im, g, hx, hy, 1)
    rnd = random.Random(7); sd = ImageDraw.Draw(im)
    for k in range(26):
        px = rnd.uniform(0, W); py = (rnd.uniform(0, H) - t * rnd.uniform(60, 160)) % H; sz = rnd.uniform(6, 14) * (0.6 + 0.4 * math.sin(t * 4 + k))
        col = [(255, 210, 60), (255, 110, 160), (110, 220, 255), (255, 255, 255)][k % 4]
        sd.polygon([(px, py - sz * 2), (px + sz * 0.5, py), (px, py + sz * 2), (px - sz * 0.5, py)], fill=col)
        sd.polygon([(px - sz * 2, py), (px, py + sz * 0.5), (px + sz * 2, py), (px, py - sz * 0.5)], fill=col)
    s = eob(t / 0.35)
    lay = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    if v:
        text_center(ld, oc["line1"], W / 2, 0, 116, stroke=10, maxw=W - 80)
        text_center(ld, oc["line2"], W / 2, 140, 132, fill=c.accent, stroke=10, maxw=W - 60)
        paste(im, lay, W / 2, 330, s * (1 + 0.03 * math.sin(t * 4)))
    else:
        text_center(ld, oc["line1"] + " " + oc["line2"], W / 2, 60, 118, fill=c.accent, stroke=10, maxw=W - 100)
        paste(im, lay, W * 0.62, 200, s * (1 + 0.03 * math.sin(t * 4)))
    if c.spec.get("mascot") is not False:
        paste(im, hoot_img(560 if v else 470, "cheer" if t > 0.4 else "idle", blink_at(t)), hx, hy - abs(math.sin(t * 2.6)) * 18, eob((t - 0.1) / 0.4))
    sub = oc.get("cta_sub", "")
    if sub:
        bub = _bubble(sub, 760 if v else 820, 64 if v else 66, "left")
        a_ = eob((t - 0.5) / 0.4)
        paste(im, bub, (W / 2 + 60) if v else W * 0.62, 1270 if v else 450, a_)
    btns = [("👍", "LIKE", (60, 130, 245)), ("🔔", "SUBSCRIBE", (240, 40, 70)), ("💬", "COMMENT", (40, 185, 100))]
    size = 200 if v else 170
    for k, (e, lab, col) in enumerate(btns):
        a_ = eob((t - 0.7 - 0.18 * k) / 0.35)
        if a_ < 0.03: continue
        tap = 1 + 0.12 * max(0, math.sin((t - 1.3 - 0.45 * k) * 6)) if t > 1.3 + 0.45 * k else 1
        bx = (W / 2 + (k - 1) * 330) if v else (W * 0.62 + (k - 1) * 300)
        paste(im, _icon_btn(e, lab, col, size), bx, (1640 if v else 790), a_ * tap)
    progress_bar(c, im, "outro", t)
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
