"""Multi-format quiz/puzzle video engine (frames drawn in code, piped to ffmpeg).

usage:
  python3 engine.py SPEC.json still SEGMENT T OUT.jpg     # one frame
  python3 engine.py SPEC.json video SEGMENT OUT.mp4       # one scene file
SEGMENT is "intro", "i0".."iN", or "outro". SPEC must already contain timings (see build.py).
"""
import sys, os, math, json, subprocess, random
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter

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
    sz = min(96, h * 0.42); f = font(F_BOLD, sz)
    if not label: maxw = 10**6
    while d.textlength(label, font=f) > maxw and sz > 26: sz -= 3; f = font(F_BOLD, sz)
    words = label.split()
    if sz < h * 0.3 and len(words) > 1:   # long answer: two lines at a readable size instead of tiny text
        best = None
        for k_ in range(1, len(words)):
            l1, l2 = " ".join(words[:k_]), " ".join(words[k_:])
            s2 = min(96, h * 0.3); f2 = font(F_BOLD, s2)
            while max(d.textlength(l1, font=f2), d.textlength(l2, font=f2)) > maxw and s2 > 26: s2 -= 2; f2 = font(F_BOLD, s2)
            if not best or s2 > best[0]: best = (s2, l1, l2)
        s2, l1, l2 = best; f2 = font(F_BOLD, s2)
        if s2 > sz:
            for j_, ln in enumerate((l1, l2)):
                xx = x if (letter or emo) else pad + (w - d.textlength(ln, font=f2)) / 2
                d.text((xx, cy - s2 * 1.15 + j_ * s2 * 1.1), ln, font=f2, fill=lt)
            label = None
    if label is not None and not letter and not emo:
        tw = d.textlength(label, font=f); x = pad + (w - tw) / 2
    if label is not None: d.text((x, cy - sz * 0.66), label, font=f, fill=lt)
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
        # Shorts (Aman, 18 Nov): compact header; puzzle ~80% of the width; bottom content kept above the title overlay
        L = dict(head=150, prompt=226, prompt_size=84, prompt_w=W - 90,
                 disp=(W / 2, 880), disp_h=260, disp_w=W - 120,
                 opt_box=(W * 0.1, 1060 if has_disp else 560, W * 0.9, 1460),
                 bottom=1555, count=(W / 2, 1660), bar=(160, 1790, W - 160, 1816), opt_y=1415)
    else:
        L = dict(head=80, prompt=140, prompt_size=86, prompt_w=W - 300,
                 disp=(W / 2, 540), disp_h=200, disp_w=W - 300,
                 opt_box=(160, 690 if has_disp else 400, W - 160, 900 if has_disp else 880),
                 bottom=930, count=(W - 140, 140), bar=(560, 1040, W - 560, 1062))
    if not has_disp and c.v and nopt == 0:
        L["disp"] = (W / 2, 900)
    if c.v and nopt and item.get("type") not in __import__("eyebrain").DRAW:
        center_stack(c, item, L)
    elif not c.v and nopt and item.get("type") not in __import__("eyebrain").DRAW:
        center_stack_h(c, item, L)
    return L

def center_stack_h(c, item, L):
    """MASTER STYLE, landscape (Aman, 18 Nov): question, picture/graphic panel, one row of option cards and the
    ANSWER + fact line form one block centred top-to-bottom with the SAME gap between every part."""
    W = c.W
    size = L["prompt_size"]; stack = bool(item.get("stack") and item.get("prompt2"))
    def _lines(sz):
        if stack: return wrap(item["prompt"], sz, L["prompt_w"]) + wrap(item["prompt2"], sz, L["prompt_w"])
        return wrap(item["prompt"], sz, L["prompt_w"])
    lines = _lines(size)
    while len(lines) > (3 if stack else 2) and size > 56:
        size -= 6; lines = _lines(size)
    hp = len(lines) * size * 1.22 + 10
    hd = 300 if item.get("panel") else (240 if item.get("display") else 0)
    n = len(item["options"]); oh = 190; hf = 150
    top, bot = 185, 1015
    k = 3 + (1 if hd else 0)
    G = max(28, min(80, (bot - top - (hp + hd + oh + hf)) / (k + 1)))
    total = hp + hd + oh + hf + G * (k - 1)
    y = top + (bot - top - total) / 2
    L["prompt"] = y - 10; y += hp + G
    if hd:
        L["disp"] = (W / 2, y + hd / 2); L["disp_h"] = hd; L["panel_box"] = (W / 2 - 520, y, W / 2 + 520, y + hd); y += hd + G
    ow = min(560, (W - 320 - (n - 1) * G) / n)
    x0 = W / 2 - (n * ow + (n - 1) * G) / 2
    L["rects"] = [(x0 + ow / 2 + i * (ow + G), y + oh / 2, ow, oh) for i in range(n)]
    L["opt_box"] = (x0, y, x0 + n * ow + (n - 1) * G, y + oh)
    y += oh + G
    L["bottom"] = int(y + 28)          # fact text; ANSWER pill sits just above it (fact_y - 30)
    L["prompt_size_fixed"] = size

def anim_sink(c, im, L, item, pt):
    """Reveal graphic (Aman, 18 Nov): all options drop into a water tank, only the right one sinks."""
    W = c.W; x0, x1 = W * 0.12, W * 0.88; top = L["pill_y"] - 14; h = 300; bot = top + h; surf = top + 70
    a0 = eo(pt / 0.35)
    if a0 <= 0: return
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((x0, top, x1, bot), 34, fill=(255, 255, 255, 40), outline=(255, 255, 255, 230), width=8)
    n = len(item["options"]); cw = (x1 - x0) / n
    for k, op in enumerate(item["options"]):
        emo = op[1] if len(op) > 1 else None
        if not emo: continue
        e = emoji_img(emo, 120)
        cx = x0 + cw * (k + 0.5)
        drop = eo((pt - 0.3 - k * 0.12) / 0.45)
        y = (top - 160) + (surf - 55 - (top - 160)) * drop
        if k == item["right"] and pt > 1.0:
            y = surf - 55 + (bot - 140 - (surf - 55)) * eo((pt - 1.0) / 1.6)
        elif drop >= 1:
            y += math.sin(pt * 4 + k) * 6
        if drop > 0: lay.alpha_composite(e, (int(cx - e.width / 2), int(y)))
    wl = Image.new("RGBA", im.size, (0, 0, 0, 0)); wd = ImageDraw.Draw(wl)
    pts = [(x0 + 8, bot - 8)] + [(x0 + 8 + i * (x1 - x0 - 16) / 40, surf + math.sin(pt * 3 + i * 0.6) * 5) for i in range(41)] + [(x1 - 8, bot - 8)]
    wd.polygon(pts, fill=(70, 170, 255, 120))
    lay.alpha_composite(wl)
    if a0 < 1: lay.putalpha(lay.split()[-1].point(lambda v: int(v * a0)))
    im.alpha_composite(lay)

def anim_spider(c, im, L, item, pt):
    """Reveal graphic (Aman, 18 Nov): a spider whose 8 legs light up and get counted 1..8."""
    W = c.W; top = L["pill_y"] - 14; cx, cy = W / 2, top + 150
    a0 = eo(pt / 0.35)
    if a0 <= 0: return
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    order = []
    for side in (-1, 1):
        for j in range(4):
            ang = math.radians([-50, -18, 18, 50][j]); order.append((side, j, ang))
    order = [o for o in order if o[0] == -1] + [o for o in order if o[0] == 1]
    f = font(F_BOLD, 40)
    for n_, (side, j, ang) in enumerate(order):
        lit = pt > 0.6 + n_ * 0.25
        col = c.accent if lit else (70, 60, 90)
        hx, hy = cx + side * 40, cy + (j - 1.5) * 16
        kx, ky = cx + side * (40 + 110 * math.cos(ang)), cy - 70 + 110 * math.sin(ang) + j * 6
        fx, fy = cx + side * (40 + 230 * math.cos(ang * 0.6)), cy + 20 + 120 * math.sin(ang) + j * 20
        d.line([(hx, hy), (kx, ky), (fx, fy)], fill=(20, 15, 40), width=24, joint="curve")
        d.line([(hx, hy), (kx, ky), (fx, fy)], fill=col, width=14, joint="curve")
        if lit:
            t_ = str(n_ + 1); tw = d.textlength(t_, font=f)
            d.ellipse((fx - 30, fy - 30, fx + 30, fy + 30), fill=(255, 255, 255), outline=(20, 15, 40), width=4)
            d.text((fx - tw / 2, fy - 26), t_, font=f, fill=(40, 30, 90))
    d.ellipse((cx - 75, cy - 55, cx + 75, cy + 70), fill=(50, 40, 70), outline=(20, 15, 40), width=6)
    d.ellipse((cx - 45, cy - 105, cx + 45, cy - 30), fill=(60, 50, 85), outline=(20, 15, 40), width=6)
    for ex in (-18, 18):
        d.ellipse((cx + ex - 13, cy - 85, cx + ex + 13, cy - 59), fill=(255, 255, 255))
        d.ellipse((cx + ex - 6, cy - 78, cx + ex + 6, cy - 66), fill=(20, 15, 40))
    if a0 < 1: lay.putalpha(lay.split()[-1].point(lambda v: int(v * a0)))
    im.alpha_composite(lay)

ANIMS = {"sink": anim_sink, "spider": anim_spider}

# ---------------------------------------------------------------- landscape answer panels (Aman, 18 Nov: premium reveal graphics)
def _clip(lay, box):
    m = Image.new("L", lay.size, 0); ImageDraw.Draw(m).rounded_rectangle(box, 36, fill=255)
    a = lay.split()[-1]; from PIL import ImageChops; lay.putalpha(ImageChops.multiply(a, m)); return lay

def _glass(d, box, r=36):
    d.rounded_rectangle(box, r, fill=(255, 255, 255, 34), outline=(255, 255, 255, 150), width=5)

def panel_flag(c, im, box, item, phase, pt):
    cols = item["flag"]; x0, y0, x1, y1 = box; h = y1 - y0 - 30; w = h * 1.5; cx = (x0 + x1) / 2; cy = (y0 + y1) / 2
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((cx - w / 2 + 8, cy - h / 2 + 14, cx + w / 2 + 8, cy + h / 2 + 14), 18, fill=(0, 0, 0, 90))
    for i, col in enumerate(cols):
        d.rectangle((cx - w / 2 + i * w / len(cols), cy - h / 2, cx - w / 2 + (i + 1) * w / len(cols), cy + h / 2), fill=tuple(col))
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), 14, outline=(255, 255, 255), width=8)
    im.alpha_composite(lay.filter(ImageFilter.GaussianBlur(0)))

def panel_banana(c, im, box, item, phase, pt):
    x0, y0, x1, y1 = box; cx = (x0 + x1) / 2
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); _glass(d, box)
    g = eo(pt / 1.0); gy = y1 - 30; top = gy - (y1 - y0 - 70) * g
    d.rounded_rectangle((cx - 26, top, cx + 26, gy), 20, fill=(120, 160, 60))
    d.rectangle((cx - 360, gy, cx + 360, gy + 10), fill=(130, 90, 50))
    if g > 0.6:
        lg = eo((pt - 0.6) / 0.6)
        for k, ang in enumerate((-150, -110, -60, -20)):
            a_ = math.radians(ang); L_ = 210 * lg
            ex, ey = cx + math.cos(a_) * L_, top + 20 + math.sin(a_) * L_ * 0.6
            d.polygon([(cx, top + 30), (ex - 30, ey), (ex + 30, ey - 20)], fill=(70, 170, 70))
            d.line([(cx, top + 30), (ex, ey - 10)], fill=(40, 120, 40), width=6)
    if pt > 1.2:
        e = emoji_img("🍌", 110); lay.alpha_composite(e, (int(cx + 18), int(top + 70)))
        e2 = emoji_img("🍌", 90); lay.alpha_composite(e2, (int(cx + 30), int(top + 140)))
    if pt > 1.5:
        f = font(F_BOLD, 50); t_ = "Giant HERB!"
        d.text((cx - 470, y0 + 30), t_, font=f, fill=c.accent, stroke_width=5, stroke_fill=(20, 10, 50))
    im.alpha_composite(_clip(lay, box))

def panel_sizes(c, im, box, item, phase, pt):
    x0, y0, x1, y1 = box; sz = item["sizes"]; n = len(sz)
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); _glass(d, box)
    mx = max(s_[2] for s_ in sz); H_ = (y1 - y0) - 90; f = font(F_BOLD, 40)
    cw = (x1 - x0) / n
    for k, (col, label, rel) in enumerate(sz):
        a_ = eob((pt - 0.2 - k * 0.45) / 0.45)
        if a_ <= 0: continue
        r = max(10, H_ / 2 * rel / mx) * a_; cx = x0 + cw * (k + 0.5); cy = y0 + 20 + H_ / 2
        if r > 60:
            glow = Image.new("RGBA", im.size, (0, 0, 0, 0))
            ImageDraw.Draw(glow).ellipse((cx - r - 18, cy - r - 18, cx + r + 18, cy + r + 18), fill=tuple(col) + (120,))
            lay.alpha_composite(glow.filter(ImageFilter.GaussianBlur(16)))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=tuple(col), outline=(255, 255, 255), width=4)
        tw = d.textlength(label, font=f)
        d.text((cx - tw / 2, y1 - 62), label, font=f, fill=(255, 255, 255), stroke_width=4, stroke_fill=(20, 10, 50))
    if item.get("size_note") and pt > 0.3 + n * 0.45:
        f2 = font(F_BOLD, 54); t_ = item["size_note"]; tw = d.textlength(t_, font=f2)
        d.text((x1 - tw - 40, y0 + 26), t_, font=f2, fill=c.accent, stroke_width=5, stroke_fill=(20, 10, 50))
    im.alpha_composite(_clip(lay, box))

def panel_tank(c, im, box, item, phase, pt):
    x0, y0, x1, y1 = box; surf = y0 + 80
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(box, 34, fill=(255, 255, 255, 30), outline=(255, 255, 255, 220), width=7)
    n = len(item["options"]); cw = (x1 - x0) / n; fl = set(item.get("floats", [item["right"]]))
    for k, op in enumerate(item["options"]):
        if len(op) < 2: continue
        e = emoji_img(op[1], 110); cx = x0 + cw * (k + 0.5)
        drop = eo((pt - 0.2 - k * 0.12) / 0.45)
        y = (y0 - 150) + (surf - 55 - (y0 - 150)) * drop
        if k not in fl and pt > 0.9: y = surf - 55 + (y1 - 125 - (surf - 55)) * eo((pt - 0.9) / 1.5)
        elif drop >= 1: y += math.sin(pt * 4 + k) * 6
        if drop > 0: lay.alpha_composite(e, (int(cx - e.width / 2), int(y)))
    wl = Image.new("RGBA", im.size, (0, 0, 0, 0)); wd = ImageDraw.Draw(wl)
    pts = [(x0 + 8, y1 - 8)] + [(x0 + 8 + i * (x1 - x0 - 16) / 50, surf + math.sin(pt * 3 + i * 0.6) * 5) for i in range(51)] + [(x1 - 8, y1 - 8)]
    wd.polygon(pts, fill=(70, 170, 255, 115)); lay.alpha_composite(wl)
    im.alpha_composite(_clip(lay, box))

def panel_scale(c, im, box, item, phase, pt):
    x0, y0, x1, y1 = box; cx = (x0 + x1) / 2; L_, Lb, R_, Rb, heavy = item["scale"]
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); _glass(d, box)
    piv = (cx, y0 + 95); tilt = math.radians(12) * eo((pt - 0.4) / 1.0) * (1 if heavy == 1 else -1)
    d.polygon([(cx - 60, y1 - 25), (cx + 60, y1 - 25), (cx, piv[1])], fill=(230, 200, 120))
    arm = 330; lx, ly = cx - arm * math.cos(tilt), piv[1] - arm * math.sin(tilt); rx, ry = cx + arm * math.cos(tilt), piv[1] + arm * math.sin(tilt)
    d.line([(lx, ly), (rx, ry)], fill=(240, 210, 130), width=14); d.ellipse((cx - 16, piv[1] - 16, cx + 16, piv[1] + 16), fill=(255, 230, 150))
    f = font(F_BOLD, 40)
    for (px, py, emo, lab) in ((lx, ly, L_, Lb), (rx, ry, R_, Rb)):
        d.line([(px, py), (px - 70, py + 70)], fill=(240, 210, 130), width=5); d.line([(px, py), (px + 70, py + 70)], fill=(240, 210, 130), width=5)
        d.chord((px - 95, py + 30, px + 95, py + 130), 0, 180, fill=(240, 210, 130))
        e = emoji_img(emo, 100); lay.alpha_composite(e, (int(px - e.width / 2), int(py - 15)))
        tw = d.textlength(lab, font=f); d.text((px - tw / 2, py + 136), lab, font=f, fill=(255, 255, 255), stroke_width=4, stroke_fill=(20, 10, 50))
    im.alpha_composite(_clip(lay, box))

def panel_shark(c, im, box, item, phase, pt):
    x0, y0, x1, y1 = box; cy = (y0 + y1) / 2 + 10
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(box, 34, fill=(20, 60, 120, 150), outline=(255, 255, 255, 170), width=5)
    for k in range(9):
        bx = x0 + 60 + (k * 113 + pt * 40) % (x1 - x0 - 120); by = y1 - 30 - ((k * 37 + pt * 90) % (y1 - y0 - 60))
        d.ellipse((bx - 7, by - 7, bx + 7, by + 7), outline=(200, 230, 255, 160), width=2)
    sx = x0 + 120 + (x1 - x0 - 520) * eo(pt / 2.6); s = 1.0; wig = math.sin(pt * 6) * 8
    body = [(sx, cy), (sx + 80, cy - 52), (sx + 260, cy - 62), (sx + 360, cy - 30), (sx + 400, cy + wig * 0.3), (sx + 360, cy + 34), (sx + 220, cy + 56), (sx + 70, cy + 40)]
    d.polygon(body, fill=(120, 135, 150), outline=(40, 50, 70), width=4)
    d.polygon([(sx + 30, cy - 10), (sx - 70, cy - 70 + wig), (sx - 40, cy), (sx - 70, cy + 60 + wig), (sx + 30, cy + 15)], fill=(110, 125, 140), outline=(40, 50, 70), width=4)
    d.polygon([(sx + 180, cy - 58), (sx + 230, cy - 120), (sx + 250, cy - 60)], fill=(110, 125, 140), outline=(40, 50, 70), width=4)
    d.polygon([(sx + 200, cy + 40), (sx + 230, cy + 95), (sx + 260, cy + 46)], fill=(110, 125, 140), outline=(40, 50, 70), width=4)
    d.ellipse((sx + 330, cy - 22, sx + 346, cy - 6), fill=(20, 25, 35))
    d.polygon([(sx + 150, cy + 30), (sx + 380, cy + 10), (sx + 360, cy + 34), (sx + 220, cy + 54)], fill=(200, 210, 215))
    yrs = int(250 * eo(pt / 2.4)); f = font(F_BOLD, 64); t_ = f"{yrs}+ years!" if pt > 2.4 else f"{yrs} years"
    d.text((x0 + 40, y0 + 22), "🦈" if False else "Greenland shark", font=font(F_BOLD, 40), fill=(255, 255, 255), stroke_width=4, stroke_fill=(20, 10, 50))
    tw = d.textlength(t_, font=f); d.text((x1 - tw - 40, y0 + 18), t_, font=f, fill=c.accent, stroke_width=5, stroke_fill=(20, 10, 50))
    im.alpha_composite(_clip(lay, box))

def _lab(d, x, y, t_, sz, fill=(255, 255, 255), anchor="la"):
    f = font(F_BOLD, sz); d.text((x, y), t_, font=f, fill=fill, stroke_width=max(3, sz // 12), stroke_fill=(20, 10, 50), anchor=anchor)

def panel_sushi(c, im, box, item, phase, t):
    x0, y0, x1, y1 = box; lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(box, 36, fill=(60, 30, 25, 200), outline=(255, 255, 255, 150), width=5)
    by = y1 - 95; d.rounded_rectangle((x0 + 20, by, x1 - 20, by + 50), 20, fill=(150, 150, 165))
    for k in range(24):
        xx = x0 + 20 + ((k * 46 - t * 120) % (x1 - x0 - 40)); d.line([(xx, by + 4), (xx, by + 46)], fill=(110, 110, 125), width=3)
    foods = ["🍣", "🍙", "🍤", "🍣", "🥟", "🍣", "🍱"]
    for k, e in enumerate(foods):
        xx = x0 + 40 + ((k * 170 + t * 120) % (x1 - x0 - 120)); im_e = emoji_img(e, 96); lay.alpha_composite(im_e, (int(xx), int(by - 88)))
    ch = emoji_img("🥢", 120); lay.alpha_composite(ch, (int(x0 + 420 + math.sin(t * 2) * 30), int(y0 + 20 + abs(math.sin(t * 2)) * 30)))
    lay.alpha_composite(emoji_img("🍵", 80), (int(x1 - 130), int(y0 + 30)))
    im.alpha_composite(_clip(lay, box))

def panel_lions(c, im, box, item, phase, t):
    x0, y0, x1, y1 = box; lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for yy in range(int(y0), int(y1)):   # savanna sunset
        k = (yy - y0) / (y1 - y0); d.line([(x0, yy), (x1, yy)], fill=(int(255 - 60 * k), int(170 - 40 * k), int(80 - 30 * k), 255))
    d.ellipse((x1 - 260, y0 + 30, x1 - 120, y0 + 170), fill=(255, 230, 120))
    d.rectangle((x0, y1 - 70, x1, y1), fill=(170, 120, 50))
    tr = (x0 + 140, y1 - 70); d.rectangle((tr[0] - 10, tr[1] - 120, tr[0] + 10, tr[1]), fill=(80, 50, 30)); d.ellipse((tr[0] - 110, tr[1] - 170, tr[0] + 110, tr[1] - 100), fill=(60, 110, 50))
    for k, (sz, off) in enumerate([(120, 0), (100, 150), (90, 270), (70, 380), (65, 470)]):
        xx = x0 + 300 + ((off + t * 70) % (x1 - x0 - 380)); bob = abs(math.sin(t * 6 + k)) * 8
        lay.alpha_composite(emoji_img("🦁", sz), (int(xx), int(y1 - 60 - sz - bob)))
    im.alpha_composite(_clip(lay, box))

def panel_fragile(c, im, box, item, phase, t):
    x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle((cx - 420, y0 + 20, cx + 420, y1 - 20), 24, fill=(200, 150, 90), outline=(120, 80, 40), width=6)   # cardboard box
    d.rectangle((cx - 420, cy - 18, cx + 420, cy + 18), fill=(225, 190, 130))
    st = Image.new("RGBA", (620, 220), (0, 0, 0, 0)); sd = ImageDraw.Draw(st)
    sd.rounded_rectangle((6, 6, 614, 214), 20, fill=(255, 250, 240), outline=(210, 30, 40), width=12)
    f = font(F_BOLD, 110); sd.text((310, 70), "FRAGILE", font=f, fill=(210, 30, 40), anchor="mm")
    f2 = font(F_BOLD, 38); sd.text((310, 160), "HANDLE WITH CARE", font=f2, fill=(210, 30, 40), anchor="mm")
    g = emoji_img("🍷", 70); st.alpha_composite(g, (24, 70)); st.alpha_composite(g, (526, 70))
    k = eob(min(1, t / 0.5)); ang = -6 + math.sin(t * 3) * 2
    st = st.rotate(ang, expand=True, resample=Image.BICUBIC); st = st.resize((max(1, int(st.width * k)), max(1, int(st.height * k))), Image.LANCZOS)
    lay.alpha_composite(st, (int(cx - st.width / 2), int(cy - st.height / 2)))
    im.alpha_composite(_clip(lay, box))

def panel_ancient(c, im, box, item, phase, t):
    x0, y0, x1, y1 = box; lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for yy in range(int(y0), int(y1)):
        k = (yy - y0) / (y1 - y0); d.line([(x0, yy), (x1, yy)], fill=(int(255 - 30 * k), int(200 - 60 * k), int(120 - 60 * k), 255))
    d.ellipse((x0 + 90, y0 + 30, x0 + 210, y0 + 150), fill=(255, 245, 190))
    gy = y1 - 60
    for (px, w, h) in ((x0 + 380, 330, 210), (x0 + 640, 260, 160), (x0 + 820, 180, 110)):
        d.polygon([(px - w / 2, gy), (px + w / 2, gy), (px, gy - h)], fill=(215, 170, 95), outline=(150, 105, 50))
        d.polygon([(px, gy - h), (px + w / 2, gy), (px + w * 0.12, gy)], fill=(185, 140, 75))
    d.rectangle((x0, gy, x1, y1), fill=(230, 185, 110))
    cam = emoji_img("🐪", 110); lay.alpha_composite(cam, (int(x1 - 160 - (t * 60) % (x1 - x0 - 200)), int(gy - 100 + abs(math.sin(t * 5)) * -6)))
    _lab(d, x1 - 40, y0 + 22, "4,500 years old!", 44, c.accent, "ra")
    im.alpha_composite(_clip(lay, box))

def panel_orbit(c, im, box, item, phase, t):
    x0, y0, x1, y1 = box; cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(box, 36, fill=(8, 8, 30, 230), outline=(255, 255, 255, 120), width=4)
    for k in range(40): sx = x0 + (k * 97) % (x1 - x0); sy = y0 + (k * 53) % (y1 - y0); d.ellipse((sx, sy, sx + 3, sy + 3), fill=(255, 255, 255, 180))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((cx - 60, cy - 60, cx + 60, cy + 60), fill=(255, 190, 40, 200))
    lay.alpha_composite(glow.filter(ImageFilter.GaussianBlur(18))); d = ImageDraw.Draw(lay)
    d.ellipse((cx - 40, cy - 40, cx + 40, cy + 40), fill=(255, 205, 60))
    pl = [((170, 160, 150), 6, 4.1), ((230, 190, 120), 9, 1.6), ((70, 140, 230), 10, 1.0), ((215, 100, 60), 8, 0.53),
          ((210, 170, 130), 20, 0.084), ((230, 210, 150), 17, 0.034), ((150, 210, 230), 13, 0.012), ((80, 110, 220), 13, 0.006)]
    for k, (col, r, sp) in enumerate(pl):
        rx = 75 + k * 58; ry = rx * 0.25; d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=(255, 255, 255, 60), width=2)
        a = t * sp * 1.2 + k * 1.3; px, py = cx + rx * math.cos(a), cy + ry * math.sin(a)
        d.ellipse((px - r, py - r, px + r, py + r), fill=col)
        if k == 5: d.ellipse((px - r * 1.8, py - r * 0.5, px + r * 1.8, py + r * 0.5), outline=(240, 220, 170), width=3)
    im.alpha_composite(_clip(lay, box))

def panel_organs(c, im, box, item, phase, t):
    x0, y0, x1, y1 = box; lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); _glass(d, box)
    cw = (x1 - x0) / 3; rv = phase == "reveal"
    for k, lab in enumerate(("Liver", "Skin", "Lungs")):
        cx = x0 + cw * (k + 0.5); cy = y0 + 125; s = 1 + 0.06 * math.sin(t * 3 + k)
        if rv and k == item["right"]: s *= 1 + 0.25 * eob(min(1, t / 0.5))
        if k == 0:
            d.ellipse((cx - 95 * s, cy - 55 * s, cx + 70 * s, cy + 50 * s), fill=(150, 50, 40), outline=(90, 20, 20), width=5)
            d.ellipse((cx + 20 * s, cy - 40 * s, cx + 95 * s, cy + 25 * s), fill=(160, 60, 45), outline=(90, 20, 20), width=5)
        elif k == 1:
            e = emoji_img("🖐️", int(150 * s)); lay.alpha_composite(e, (int(cx - e.width / 2), int(cy - e.height / 2)))
        else:
            br = 1 + 0.08 * math.sin(t * 2.5); e = emoji_img("🫁", int(150 * s * br)); lay.alpha_composite(e, (int(cx - e.width / 2), int(cy - e.height / 2)))
        _lab(d, cx, y1 - 40, lab, 44, c.accent if (rv and k == item["right"]) else (255, 255, 255), "mm")
    if rv: _lab(d, x0 + cw * 1.5, y0 + 18, "≈ 2 m²!", 40, c.accent, "ma")
    im.alpha_composite(_clip(lay, box))

def panel_basket(c, im, box, item, phase, t):
    x0, y0, x1, y1 = box; lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(box, 36, fill=(205, 140, 70), outline=(255, 255, 255, 160), width=5)
    for k in range(12): d.line([(x0 + k * 90, y0), (x0 + k * 90, y1)], fill=(190, 125, 60), width=3)
    d.arc((x1 - 330, y0 + 40, x1 + 30, y1 + 200), 90, 270, fill=(255, 255, 255), width=5)
    hx, hy = x1 - 110, y0 + 95
    d.rectangle((hx + 40, y0 + 20, hx + 50, y1 - 20), fill=(90, 90, 100)); d.rectangle((hx + 20, hy - 70, hx + 46, hy + 10), fill=(250, 250, 250), outline=(60, 60, 70), width=3)
    d.ellipse((hx - 50, hy - 8, hx + 20, hy + 8), outline=(235, 90, 30), width=6)
    for k, px in enumerate((x0 + 120, x0 + 300, x0 + 470, x0 + 620, x0 + 760)):
        bob = abs(math.sin(t * 5 + k)) * 14; lay.alpha_composite(emoji_img("⛹️", 110), (int(px + math.sin(t * 1.5 + k) * 25), int(y1 - 140 - bob)))
    ph = (t % 1.8) / 1.8; sx, sy = x0 + 790, y1 - 150; ex, ey = hx - 25, hy - 20
    bx = sx + (ex - sx) * ph; byy = sy + (ey - sy) * ph - math.sin(ph * math.pi) * 170
    lay.alpha_composite(emoji_img("🏀", 54), (int(bx - 27), int(byy - 27)))
    _lab(d, x0 + 30, y0 + 22, "5 vs 5", 46, (255, 255, 255))
    im.alpha_composite(_clip(lay, box))

def panel_turkey(c, im, box, item, phase, t):
    x0, y0, x1, y1 = box; lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for yy in range(int(y0), int(y1)):
        k = (yy - y0) / (y1 - y0); d.line([(x0, yy), (x1, yy)], fill=(int(250 - 120 * k), int(150 - 60 * k), int(120 + 40 * k), 255))
    wy = y1 - 70
    for (mx, s) in ((x0 + 230, 1.0), (x0 + 560, 1.3), (x0 + 860, 0.9)):
        d.rectangle((mx - 110 * s, wy - 70 * s, mx + 110 * s, wy), fill=(70, 50, 90)); d.pieslice((mx - 80 * s, wy - 150 * s, mx + 80 * s, wy - 10 * s), 180, 360, fill=(70, 50, 90))
        for dx in (-140, 140):
            d.rectangle((mx + dx * s - 7, wy - 190 * s, mx + dx * s + 7, wy), fill=(70, 50, 90)); d.polygon([(mx + dx * s - 10, wy - 190 * s), (mx + dx * s + 10, wy - 190 * s), (mx + dx * s, wy - 225 * s)], fill=(70, 50, 90))
    d.rectangle((x0, wy, x1, y1), fill=(40, 90, 150))
    for k in range(6): xx = x0 + (k * 180 + t * 40) % (x1 - x0); d.line([(xx, wy + 20 + k % 3 * 15), (xx + 60, wy + 20 + k % 3 * 15)], fill=(150, 200, 240), width=3)
    lay.alpha_composite(emoji_img("⛵", 80), (int(x0 + 80 + (t * 50) % (x1 - x0 - 200)), int(wy - 40)))
    lay.alpha_composite(emoji_img("🐦", 40), (int(x0 + 300 + t * 30 % 400), int(y0 + 40 + math.sin(t * 3) * 10)))
    im.alpha_composite(_clip(lay, box))

def _shark(d, sx, cy, s, wig, flip=False):
    def P(x, y): return (sx - x * s, cy + y * s) if flip else (sx + x * s, cy + y * s)
    d.polygon([P(0, 0), P(80, -52), P(260, -62), P(360, -30), P(400, 0), P(360, 34), P(220, 56), P(70, 40)], fill=(120, 135, 150), outline=(40, 50, 70), width=4)
    d.polygon([P(30, -10), P(-70, -70 + wig), P(-40, 0), P(-70, 60 + wig), P(30, 15)], fill=(110, 125, 140), outline=(40, 50, 70), width=4)
    d.polygon([P(180, -58), P(230, -120), P(250, -60)], fill=(110, 125, 140), outline=(40, 50, 70), width=4)
    d.polygon([P(150, 30), P(380, 10), P(360, 34), P(220, 54)], fill=(200, 210, 215))
    ex, ey = P(338, -14); d.ellipse((ex - 8, ey - 8, ex + 8, ey + 8), fill=(20, 25, 35))
    mx, my = P(392, 10); d.polygon([P(330, 12), P(395, 4), P(370, 24)], fill=(80, 20, 30))

def panel_sharkhunt(c, im, box, item, phase, t):
    x0, y0, x1, y1 = box; cy = (y0 + y1) / 2 + 10
    lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(box, 34, fill=(15, 55, 115, 220), outline=(255, 255, 255, 160), width=5)
    cyc = (t % 4.0) / 4.0
    sx = x0 - 300 + (x1 - x0 + 350) * cyc
    for k in range(7):   # fish school, scatters when the shark gets close
        fx0 = x0 + 520 + (k % 4) * 60; fy0 = cy - 70 + (k // 4) * 70 + (k % 2) * 20
        dist = (sx + 400) - fx0; sc = max(0.0, min(1.0, (dist + 120) / 200))
        fx = fx0 + sc * (180 + k * 25); fy = fy0 + sc * ((k % 3) - 1) * 120 + math.sin(t * 6 + k) * 5
        lay.alpha_composite(emoji_img("🐟", 62), (int(fx), int(fy)))
    _shark(d, sx, cy, 0.9, math.sin(t * 8) * 10)
    for k in range(10):
        bx = x0 + 40 + (k * 107) % (x1 - x0 - 80); by = y1 - 20 - ((k * 41 + t * 80) % (y1 - y0 - 40)); d.ellipse((bx - 6, by - 6, bx + 6, by + 6), outline=(200, 230, 255, 150), width=2)
    _lab(d, x0 + 30, y0 + 20, "No bones — just cartilage!", 40, c.accent) if phase == "reveal" else None
    im.alpha_composite(_clip(lay, box))

def panel_trio(c, im, box, item, phase, t):
    x0, y0, x1, y1 = box; lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); _glass(d, box)
    cw = (x1 - x0) / 3; rv = phase == "reveal"
    # honey jar
    cx = x0 + cw * 0.5; lay.alpha_composite(emoji_img("🍯", 140), (int(cx - 70), int(y0 + 40 + math.sin(t * 2) * 6)))
    # goldfish bowl
    cx = x0 + cw * 1.5; cy = y0 + 125
    d.ellipse((cx - 110, cy - 95, cx + 110, cy + 95), fill=(120, 190, 255, 110), outline=(255, 255, 255, 220), width=5)
    fx = cx + math.sin(t * 1.7) * 55; e = emoji_img("🐠", 70)
    if math.cos(t * 1.7) < 0: e = e.transpose(Image.FLIP_LEFT_RIGHT)
    lay.alpha_composite(e, (int(fx - 35), int(cy - 20 + math.sin(t * 3) * 10)))
    for k in range(4): by = cy + 70 - ((t * 60 + k * 35) % 150); d.ellipse((cx - 30 + k * 18, by, cx - 20 + k * 18, by + 10), outline=(255, 255, 255, 200), width=2)
    # octopus + 3 hearts
    cx = x0 + cw * 2.5; lay.alpha_composite(emoji_img("🐙", 130), (int(cx - 65), int(y0 + 45 + math.sin(t * 2.5) * 8)))
    for k in range(3): lay.alpha_composite(emoji_img("❤️", 34), (int(cx - 60 + k * 45), int(y0 + 10 + abs(math.sin(t * 4 + k)) * -6 + 6)))
    for k, lab in enumerate(("Honey", "Goldfish", "Octopus")):
        _lab(d, x0 + cw * (k + 0.5), y1 - 40, lab, 42, (255, 90, 90) if (rv and k == item["right"]) else (255, 255, 255), "mm")
    if rv:
        cx = x0 + cw * 1.5; d.line([(cx - 120, y0 + 40), (cx + 120, y1 - 70)], fill=(255, 70, 70), width=12); d.line([(cx + 120, y0 + 40), (cx - 120, y1 - 70)], fill=(255, 70, 70), width=12)
    im.alpha_composite(_clip(lay, box))

def panel_planets3(c, im, box, item, phase, t):
    x0, y0, x1, y1 = box; lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    d.rounded_rectangle(box, 36, fill=(8, 8, 30, 230), outline=(255, 255, 255, 120), width=4)
    for k in range(40): sx = x0 + (k * 97) % (x1 - x0); sy = y0 + (k * 53) % (y1 - y0); d.ellipse((sx, sy, sx + 3, sy + 3), fill=(255, 255, 255, 180))
    cw = (x1 - x0) / 3; rv = phase == "reveal"
    data = [("Mercury", (170, 160, 150), 55, "59 days"), ("Venus", (230, 190, 120), 80, "243 days"), ("Jupiter", (210, 170, 130), 110, "10 hours")]
    for k, (nm, col, r, day) in enumerate(data):
        cx = x0 + cw * (k + 0.5); cy = y0 + 125
        if rv and k == item["right"]:
            glow = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((cx - r - 25, cy - r - 25, cx + r + 25, cy + r + 25), fill=(255, 210, 80, 160))
            lay.alpha_composite(glow.filter(ImageFilter.GaussianBlur(14))); d = ImageDraw.Draw(lay)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)
        spd = {0: 0.3, 1: 0.05, 2: 2.5}[k]   # spin speed ~ how short the day is
        for j in range(3):
            off = ((t * spd * r + j * r * 0.7) % (2 * r)) - r
            if k == 2: d.line([(cx - math.sqrt(max(0, r * r - (off * 0.5) ** 2)), cy + off * 0.5), (cx + math.sqrt(max(0, r * r - (off * 0.5) ** 2)), cy + off * 0.5)], fill=(180, 120, 90), width=8)
            else:
                xx = cx + off; hh = math.sqrt(max(0, r * r - off * off)) * 0.4; d.ellipse((xx - 8, cy - hh * 0.3 - 8, xx + 8, cy - hh * 0.3 + 8), fill=tuple(max(0, v - 40) for v in col))
        _lab(d, cx, y1 - 52, nm, 40, (255, 255, 255), "mm")
        if rv: _lab(d, cx, y1 - 14, "1 day = " + day, 36, c.accent if k == item["right"] else (220, 220, 230), "mm")
    im.alpha_composite(_clip(lay, box))

# ---------------------------------------------------------------- photo puzzles (Aman, 18 Nov): cinematic zoom-out + torch spotlight
_PHOTOS = {}
def _photo(path):
    if path not in _PHOTOS: _PHOTOS[path] = Image.open(path).convert("RGB")
    return _PHOTOS[path]

def zoom_steps(ask, cs):
    """item-time of each zoom-out step (shared with build.py for the whoosh sounds)"""
    return [round(ask * 0.5, 3), round(ask + 0.6, 3), round(ask + 2.2, 3), round(ask + cs, 3)]

def _item_timing(c, item):
    idx = c.spec["items"].index(item); tm = c.spec.get("timing", {}).get(f"i{idx}", {})
    return idx, tm.get("ask", 4.0), c.spec["count_secs"]

def _card_photo(c, im, box, ph, t, idx, blur=0.0, extra=None):
    x0, y0, x1, y1 = [int(v) for v in box]; bw, bh = x1 - x0, y1 - y0
    k = 1.0 if idx == 0 else eo(min(1.0, t / 0.4))           # slide-in from the right with a blur (transition)
    dx = int((1 - k) * 160); blur += (1 - k) * 10
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle((x0 + dx + 10, y0 + 18, x1 + dx + 10, y1 + 18), 46, fill=(0, 0, 0, 150))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    glow = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(glow).rounded_rectangle((x0 + dx - 10, y0 - 10, x1 + dx + 10, y1 + 10), 52, fill=tuple(c.accent) + (90,))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(18)))
    if ph.size != (bw, bh): ph = ph.resize((bw, bh), Image.BILINEAR)
    if blur > 0.4: ph = ph.filter(ImageFilter.GaussianBlur(blur))
    m = Image.new("L", (bw, bh), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, bw - 1, bh - 1), 44, fill=255)
    if k < 1: m = m.point(lambda v: int(v * k))
    im.paste(ph.convert("RGB"), (x0 + dx, y0), m)
    if extra: extra(im, x0 + dx, y0, bw, bh)
    ImageDraw.Draw(im).rounded_rectangle((x0 + dx, y0, x1 + dx, y1), 44, outline=(255, 255, 255), width=6)

def panel_photozoom(c, im, box, item, phase, t):
    idx, A, cs = _item_timing(c, item); img = _photo(item["photo"])
    x0, y0, x1, y1 = box; bw, bh = int(x1 - x0), int(y1 - y0)
    Z = item.get("zooms", [8.0, 5.5, 3.8, 2.6, 1.0]); st = zoom_steps(A, cs)
    z = Z[0]; blur = 0.0
    for k_, s_ in enumerate(st):
        if t >= s_:
            p = min(1.0, (t - s_) / 0.65); e = eo(p)
            z = math.exp(math.log(Z[k_]) + (math.log(Z[k_ + 1]) - math.log(Z[k_])) * e); blur = math.sin(math.pi * p) * 7
    z *= 1 + 0.015 * math.sin(t * 0.8)                       # tiny breathing drift = "camera" feel
    fx, fy = item.get("focus", [0.5, 0.5]); iw, ih = img.size
    zz = max(1.0, z)
    cw = iw / zz; ch = cw * bh / bw
    if ch > ih: ch = ih; cw = ch * bw / bh
    cx = min(max(fx * iw, cw / 2), iw - cw / 2); cy = min(max(fy * ih, ch / 2), ih - ch / 2)
    ph = img.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((bw, bh), Image.BILINEAR)
    if z < 1.0:   # zoom out past the photo edge: whole photo shrinks onto a blurred backdrop of itself
        full = img.resize((int(bw * z), int(bw * z * ih / iw)), Image.BILINEAR) if iw / ih >= bw / bh else img.resize((int(bh * z * iw / ih), int(bh * z)), Image.BILINEAR)
        bg = ph.filter(ImageFilter.GaussianBlur(22)).point(lambda v: int(v * 0.55))
        mk = Image.new("L", full.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, full.width - 1, full.height - 1), 28, fill=255)
        bg.paste(full, ((bw - full.width) // 2, (bh - full.height) // 2), mk); ph = bg
    def extra(im_, X, Y, w_, h_):
        if phase == "reveal": return
        d = ImageDraw.Draw(im_); f = font(F_BOLD, 44); t_ = f"ZOOM  {max(1.0, z):.0f}×"
        tw = d.textlength(t_, font=f); d.rounded_rectangle((X + 26, Y + 26, X + 70 + tw, Y + 92), 30, fill=(15, 10, 40, 200))
        d.text((X + 48, Y + 34), t_, font=f, fill=c.accent)
    _card_photo(c, im, box, ph, t, idx, blur, extra)

_BEAM = {}
def _beam(r):
    """soft torch beam: 255 (full light) in the middle, fading to 0 at the edge"""
    r = int(r)
    if r not in _BEAM:
        g = Image.radial_gradient("L").resize((2 * r, 2 * r), Image.BILINEAR)   # 0 centre -> 255 edge (at 0.5*size*sqrt2)
        _BEAM[r] = g.point(lambda v: 255 if v < 90 else max(0, int(255 - (v - 90) * 255 / 75)))
    return _BEAM[r]

def panel_photospot(c, im, box, item, phase, t):
    idx, A, cs = _item_timing(c, item); img = _photo(item["photo"])
    x0, y0, x1, y1 = box; bw, bh = int(x1 - x0), int(y1 - y0)
    iw, ih = img.size; sc = max(bw / iw, bh / ih) * item.get("crop", 1.0); cw, ch = bw / sc, bh / sc   # crop>1 = zoomed in closer
    fx, fy = item.get("focus", [0.5, 0.5])
    cx = min(max(fx * iw, cw / 2), iw - cw / 2); cy = min(max(fy * ih, ch / 2), ih - ch / 2)
    ph = img.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize((bw, bh), Image.BILINEAR)
    R = A + cs
    if t < R:
        r = bw * item.get("beam", 0.13)
        bx = bw * (0.5 + 0.36 * math.sin(t * 0.95 + 0.4)); by = bh * (0.5 + 0.33 * math.sin(t * 1.37 + 1.2))
        dark = Image.new("L", (bw, bh), 255)   # pitch black outside the torch beam (Aman, 18 Nov)
        m = Image.new("L", (bw, bh), 0); m.paste(_beam(r), (int(bx - r), int(by - r)))   # light amount
        dark = ImageChops.subtract(dark, m)
        blackL = Image.new("RGB", (bw, bh), (0, 0, 0))
        lit = ph.point(lambda v: min(255, int(v * 1.12)))
        ph = Image.composite(blackL, lit, dark)
        gd = ImageDraw.Draw(ph, "RGBA"); gd.ellipse((bx - r * 0.82, by - r * 0.82, bx + r * 0.82, by + r * 0.82), outline=(255, 240, 180, 40), width=4)
        for k in range(14):
            a_ = k * 2.4 + t * 0.6; rr = r * (0.2 + 0.6 * ((k * 37) % 100) / 100)
            px, py = bx + math.cos(a_) * rr, by + math.sin(a_ * 1.3) * rr * 0.8
            gd.ellipse((px - 2, py - 2, px + 2, py + 2), fill=(255, 245, 210, 150))
        def extra(im_, X, Y, w_, h_):
            d = ImageDraw.Draw(im_); f = font(F_BOLD, 44); t_ = "SPOTLIGHT"
            tw = d.textlength(t_, font=f); d.rounded_rectangle((X + 26, Y + 26, X + 70 + tw, Y + 92), 30, fill=(15, 10, 40, 200))
            d.text((X + 48, Y + 34), t_, font=f, fill=c.accent)
        _card_photo(c, im, box, ph, t, idx, 0.0, extra)
    else:
        p = (t - R) / 0.45
        _card_photo(c, im, box, ph, t, idx, 0.0)
        if p < 1:
            fl = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(fl).rounded_rectangle(box, 44, fill=(255, 255, 255, int(230 * (1 - eo(p)))))
            im.alpha_composite(fl)

PANELS_ALWAYS = {"photozoom", "photospot", "flag", "sushi", "lions", "fragile", "ancient", "orbit", "organs", "basket", "turkey", "sharkhunt", "trio", "planets3"}

PANELS = {"photozoom": panel_photozoom, "photospot": panel_photospot, "sushi": panel_sushi, "lions": panel_lions, "fragile": panel_fragile, "ancient": panel_ancient, "orbit": panel_orbit,
          "organs": panel_organs, "basket": panel_basket, "turkey": panel_turkey, "sharkhunt": panel_sharkhunt, "trio": panel_trio,
          "planets3": panel_planets3,
          "flag": panel_flag, "banana": panel_banana, "sizes": panel_sizes, "tank": panel_tank, "scale": panel_scale, "shark": panel_shark}

def center_stack(c, item, L):
    """MASTER STYLE for Shorts quiz/option questions (Aman, 18 Nov): question text, icon, option boxes and the
    timer/answer area are one block, centred horizontally and vertically, with the SAME gap between every part."""
    W = c.W
    size = L["prompt_size"]; stack = bool(item.get("stack") and item.get("prompt2"))
    def _lines(sz):
        if stack: return wrap(item["prompt"], sz, L["prompt_w"]) + wrap(item["prompt2"], sz, L["prompt_w"])
        return wrap(item["prompt"], sz, L["prompt_w"])
    lines = _lines(size)
    while len(lines) > (3 if stack else 2) and size > 56:
        size -= 6; lines = _lines(size)
    hp = len(lines) * size * 1.22 + 10
    disp = item.get("display")
    hd = 0
    if disp: hd = {"emoji": 230, "big": 170}.get(disp["kind"], 260)
    if item.get("panel"): hd = item.get("panel_h", 560)
    n = len(item["options"])
    oh = {2: 210, 3: 190, 4: 220}.get(n, 170)
    if item.get("panel"): oh = 132
    rows = 2 if n == 4 else n
    blocks = [hp] + ([hd] if hd else []) + [None, 300]   # None = options (height depends on the gap)
    top, bot = 215, 1825
    fixed = hp + hd + rows * oh + 300
    k = len(blocks)
    G = max(40, min(100, (bot - top - fixed) / (k + 1 + (rows - 1))))
    total = fixed + G * (k - 1) + G * (rows - 1)
    y = top + (bot - top - total) / 2
    L["prompt"] = y - 10; y += hp + G
    if hd:
        L["disp"] = (W / 2, y + hd / 2)
        if item.get("panel"): L["panel_box"] = (W * 0.07, y, W * 0.93, y + hd)
        y += hd + G
    rects = []
    bw = W * 0.8
    if n == 4:
        w = (bw - G) / 2
        for i in range(4):
            r, kk = divmod(i, 2)
            rects.append((W / 2 - bw / 2 + w / 2 + kk * (w + G), y + oh / 2 + r * (oh + G), w, oh))
    else:
        for i in range(n):
            rects.append((W / 2, y + oh / 2 + i * (oh + G), bw, oh))
    y += rows * oh + (rows - 1) * G + G
    L["rects"] = rects
    L["opt_box"] = (W / 2 - bw / 2, rects[0][1] - oh / 2, W / 2 + bw / 2, rects[-1][1] + oh / 2)
    L["count"] = (W / 2, y + 120); L["bar"] = (160, y + 262, W - 160, y + 288)
    L["bottom"] = int(y + 45)
    L["pill_y"] = y + 24                     # ANSWER pill (≈48 px tall) sits one gap below the options
    L["fact_top"] = y + 48 + G * 0.5         # fact lines start a half-gap below the pill (tight pair)
    # progress dots: centred between the level pill (head) and the question text
    L["dots_y"] = (L["head"] + 28 + L["prompt"] + 10 + size * 0.22) / 2
    L["prompt_size_fixed"] = size

def option_rects(c, L, n):
    if L.get("rects") and len(L["rects"]) == n: return L["rects"]
    x0, y0, x1, y1 = L["opt_box"]; bw, bh = x1 - x0, y1 - y0
    rects = []
    if n == 2:
        if c.v:
            h = min(420, (bh - 60) / 2)
            for i in range(2):
                cy = y0 + bh / 4 + i * bh / 2
                rects.append((W2(c), cy, bw - 40, h))
        else:
            w = (bw - 80) / 2; h = min(300, bh - 40)
            for i in range(2):
                rects.append((x0 + w / 2 + i * (w + 80), y0 + bh / 2, w, h))
    elif n == 4:
        if c.v:
            w = (bw - 50) / 2; h = min(420, (bh - 50) / 2)
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
            h = min(300, (bh - 60) / 3)
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

def draw_hoot_corner(c, im, phase, t, pt, idx=None):
    if c.spec.get("mascot") is False: return
    size = 160 if c.v else 230
    x, y = (112, 112) if c.v else (150, 945)   # Shorts: small, top-left, clear of the question text
    tm = c.spec.get("timing", {}).get(f"i{idx}", {}) if idx is not None else {}
    if not c.v and tm.get("hook_at") and t >= tm["hook_at"] - 0.2:
        # Hoot jumps up big and talks while he says the hook (Aman, 18 Nov: show the character wherever possible)
        k = eob((t - tm["hook_at"] + 0.2) / 0.4); big = 230 + 90 * k     # grows into the free bottom-left corner
        bob = abs(math.sin(t * 9)) * 16
        paste(im, hoot_img(int(big), "cheer", blink_at(t + 0.7)), 165, 955 - 10 * k - bob, 1)
        return
    pose, bob = "idle", 0.0
    if phase == "count": pose = "think"
    elif phase == "reveal":
        pose = "cheer"; bob = abs(math.sin(pt * 7)) * 24 * max(0.0, 1 - pt / 2.5)
    else:
        bob = math.sin(t * 2.4) * 5
    s = eob(t / 0.5) if (phase == "ask" and not c.v) else 1
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
    first = c.v and idx == 0 and phase == "ask"   # Shorts: frame 0 is already complete (no fade-in)
    paste(im, p, W / 2, L["head"], eob(t / 0.4) if (phase == "ask" and not first) else 1)
    if n_total > 1:  # progress dots
        gap = 26 if c.v else 22; r0 = 7 if c.v else 6
        if n_total > 8: gap, r0 = gap * 0.7, r0 * 0.8
        dx0 = W / 2 - (n_total - 1) * gap / 2; dy = L.get("dots_y", L["head"] + (66 if c.v else 56))
        for k in range(n_total):
            rr = r0 * (1.5 if k == idx else 1)
            col = c.accent + (255,) if k == idx else ((255, 255, 255, 230) if k < idx else (255, 255, 255, 90))
            d.ellipse((dx0 + k * gap - rr, dy - rr, dx0 + k * gap + rr, dy + rr), fill=col)
    # prompt
    qa = eo(t / 0.4) if (phase == "ask" and not first) else 1
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
        if c.v and item.get("autofit", True): bb = True   # Shorts: drawn below with the options on their own layer
        else:
            custom_origin = eyebrain.DRAW[item["type"]](c, lay, item, phase, pt, t)
            bb = lay.getbbox()
        # fill the empty space: scale the whole puzzle up to the free area (same scale every frame of the scene)
        fit = bb and item.get("autofit", True)
        if fit and c.v:
            # Shorts (Aman, 18 Nov): the puzzle itself fills ~80% of the width; option boxes go on their own row below it
            lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); opt = Image.new("RGBA", im.size, (0, 0, 0, 0))
            # first frame already shows the whole puzzle (entrance animations skipped); puzzles with a timed watch phase
            # only skip the first 0.5 s so no flash/step is lost
            t_d = max(t, 0.5 if item["type"] in TIMED else 1.8) if (idx == 0 and phase == "ask") else t
            eyebrain.OPT = opt
            try: custom_origin = eyebrain.DRAW[item["type"]](c, lay, item, phase, pt, t_d)
            finally: eyebrain.OPT = None
            ref = getattr(c, "_fit", {}).get(idx)
            if ref is None:
                lay0 = Image.new("RGBA", im.size, (0, 0, 0, 0)); opt0 = Image.new("RGBA", im.size, (0, 0, 0, 0))
                tm0 = c.spec.get("timing", {}).get(f"i{idx}", {})
                eyebrain.OPT = opt0
                try: eyebrain.DRAW[item["type"]](c, lay0, item, "reveal", 1.5, tm0.get("ask", 6) + c.spec["count_secs"] + 1.5)
                finally: eyebrain.OPT = None
                b0 = lay0.getbbox() or lay.getbbox() or (0, 0, W, 10); ob0 = opt0.getbbox()
                fx0, fx1 = W * 0.1, W * 0.9   # puzzle + options cover ~80% of the width (Aman: like/comment buttons and title overlay the edges)
                if ob0:
                    osc = min((fx1 - fx0) / (ob0[2] - ob0[0]), 180 / (ob0[3] - ob0[1]), 1.6)
                    oc = (W / 2, L["opt_y"]); fy1 = L["opt_y"] - (ob0[3] - ob0[1]) * osc / 2 - 28
                else:
                    osc, oc, fy1 = 1, None, L["bottom"] - 30
                fy0 = prompt_bottom + 22
                sc = min((fx1 - fx0) / (b0[2] - b0[0]), (fy1 - fy0) / (b0[3] - b0[1]), 3.0)
                ref = (b0, sc, (W / 2, (fy0 + fy1) / 2), ob0, osc, oc)
                if not hasattr(c, "_fit"): c._fit = {}
                c._fit[idx] = ref
            b0, sc, (tcx, tcy), ob0, osc, oc = ref
            crop = lay.crop(b0); crop = crop.resize((max(1, int(crop.width * sc)), max(1, int(crop.height * sc))), Image.LANCZOS)
            im.paste(crop, (int(tcx - crop.width / 2), int(tcy - crop.height / 2)), crop)
            if custom_origin:
                custom_origin = (tcx + (custom_origin[0] - (b0[0] + b0[2]) / 2) * sc, tcy + (custom_origin[1] - (b0[1] + b0[3]) / 2) * sc)
            if ob0:
                oc_ = opt.crop(ob0); oc_ = oc_.resize((max(1, int(oc_.width * osc)), max(1, int(oc_.height * osc))), Image.LANCZOS)
                im.paste(oc_, (int(oc[0] - oc_.width / 2), int(oc[1] - oc_.height / 2)), oc_)
        elif fit:
            ref = getattr(c, "_fit", {}).get(idx)
            if ref is None:
                lay0 = Image.new("RGBA", im.size, (0, 0, 0, 0))
                tm0 = c.spec.get("timing", {}).get(f"i{idx}", {})
                eyebrain.DRAW[item["type"]](c, lay0, item, "reveal", 1.5, tm0.get("ask", 6) + c.spec["count_secs"] + 1.5)
                b0 = lay0.getbbox() or bb
                fx0, fy0, fx1, fy1 = (60, prompt_bottom + 20, W - 60, L["bottom"] - 45)
                sc = min((fx1 - fx0) / (b0[2] - b0[0]), (fy1 - fy0) / (b0[3] - b0[1]), 1.45)
                ref = (b0, max(0.75, sc), ((fx0 + fx1) / 2, (fy0 + fy1) / 2))
                if not hasattr(c, "_fit"): c._fit = {}
                c._fit[idx] = ref
            b0, sc, (tcx, tcy) = ref
            crop = lay.crop(b0); crop = crop.resize((int(crop.width * sc), int(crop.height * sc)), Image.LANCZOS)
            ox_ = int(tcx - crop.width / 2); oy_ = int(tcy - crop.height / 2)
            im.alpha_composite(crop, (max(0, ox_), max(0, oy_))) if ox_ >= 0 and oy_ >= 0 else im.paste(crop, (ox_, oy_), crop)
            if custom_origin:
                custom_origin = (tcx + (custom_origin[0] - (b0[0] + b0[2]) / 2) * sc, tcy + (custom_origin[1] - (b0[1] + b0[3]) / 2) * sc)
        else:
            im.alpha_composite(lay)
        d = ImageDraw.Draw(im)
    pnl = item.get("panel")
    if pnl in PANELS and L.get("panel_box") and pnl in PANELS_ALWAYS:
        PANELS[pnl](c, im, L["panel_box"], item, phase, t if pnl != "flag" else pt)
    elif pnl in PANELS and L.get("panel_box") and phase == "reveal" and pt > 0.25:
        PANELS[pnl](c, im, L["panel_box"], item, phase, pt - 0.25)
    elif item.get("display"):
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
        s = eob((t - delay) / 0.45) if (phase == "ask" and not first) else 1.0
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
        R = 100 if c.v else 80; S = int(R * 2 + 60)
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
        if c.v and L.get("fact_top") is not None and item.get("anim") in ANIMS:
            ANIMS[item["anim"]](c, im, L, item, pt)
        elif c.v and L.get("fact_top") is not None and item.get("fact"):
            fl = []
            for k_, ln in enumerate(item["fact"]): fl += [(k_, x_) for x_ in wrap(ln, 66 if k_ == 0 else 54, W - 140)]
            yy = L["fact_top"]
            for j, (k_, ln) in enumerate(fl):
                a_ = eo((pt - 0.6 - k_ * 0.9) / 0.4)
                sz = 66 if k_ == 0 else 54
                if a_ > 0:
                    lay = Image.new("RGBA", (W, int(sz * 1.6)), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
                    text_center(ld, ln, W / 2, 6, sz, fill=c.accent if k_ == 0 else (255, 255, 255), stroke=5, maxw=W - 120)
                    lay.putalpha(lay.split()[-1].point(lambda v: int(v * a_)))
                    im.alpha_composite(lay, (0, int(yy + (1 - a_) * 20)))
                yy += sz * 1.25
        for i, ln in enumerate([] if (c.v and L.get("fact_top") is not None) else item.get("fact", [])):
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
    if phase == "reveal" and fact_y is not None and pt > 0.35 and item.get("anim") not in ANIMS:
        a_ = eob((pt - 0.35) / 0.35)
        chip = pill("ANSWER", (40, 190, 90), 38 if c.v else 32)
        paste(im, chip, W / 2, L.get("pill_y", fact_y - (36 if c.v else 30)), a_)
    draw_hoot_corner(c, im, phase, t, pt, idx)
    mc = c.spec.get("midcta")
    if mc and phase == "reveal" and idx == mc.get("idx"): cta_popup(c, im, pt)
    tm_i = c.spec.get("timing", {}).get(f"i{idx}", {})
    if idx == 0 and phase == "ask" and tm_i.get("hook") and c.spec.get("hook") and t < tm_i["hook"] + 0.3 and c.spec.get("hook_banner", False):
        hook_banner(c, im, c.spec["hook"], t, tm_i["hook"])  # off by default: the hook is voice-over only (Aman, 18 Nov)
    elif idx > 0 and phase == "ask" and c.v and t < 1.9:  # long videos: hooks are SPOKEN (say.items[i].hook), never text banners
        tz = item.get("teaser")
        if any(si.get("hook") for si in c.spec.get("say", {}).get("items", [])): tz = ""  # spoken hooks -> no text cards (Aman, 18 Nov)
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

TIMED = {"memgrid", "missing", "numflash", "cardflip", "diceflash", "shapemiss", "bug", "whereflash", "lightorder", "quickswap",
         "cups", "changed", "blinks", "moved", "movingcount", "patmem", "order", "split", "zoom", "spinner", "blinkeye", "hidden"}

TEASE_MED = ["Great start! Now it gets tricky!", "Nice! Ready for a twist?", "You're on a roll — keep going!",
             "Level up! You've got this!", "Sharp eyes! Try this one!", "Love it! Next one's sneakier!"]
TEASE_HARD = ["Hard mode! You've got this!", "You're doing great — stay sharp!", "Big brain time! Let's go!",
              "Hard level unlocked — show me!", "Almost there! Keep it up!", "Sharp eyes only — you in?"]
TEASE_FINAL = ["Final one! Go get all six!", "Last one — save your best!", "Boss level! You can beat it!",
               "The best one is last — go!", "Final round! Finish strong!", "One more! Can you get them all?"]

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
