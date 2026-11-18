"""Custom eye & brain puzzle drawers. Each draw_X(c, im, item, phase, pt, t) draws the main area
and returns (x, y) for the confetti burst. min_ask(item) gives the minimum question phase length."""
import random
import math
from PIL import Image, ImageDraw, ImageFilter
from engine import emoji_img, eob, eo, cl, paste, font, F_BOLD, text_center

OPT = None  # when set (Shorts), option boxes are drawn on this separate layer instead of the puzzle layer

def area(c):
    # main puzzle box (x0, y0, x1, y1); Shorts: wide box so drawers draw near final size (engine fits the puzzle to ~90% width)
    return (40, 560, c.W - 40, 1500) if c.v else (140, 260, c.W - 140, 900)

def min_ask(item):
    t = item.get("type")
    if t == "changed": return 5.2
    if t == "cups": return 1.9 + 0.6 * len(item["swaps"]) + 0.3
    if t == "hidden": return 3.2
    return 0

def glow_box(im, box, color=(60, 255, 120), r=30):
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).rounded_rectangle(box, radius=r, outline=color + (255,), width=14)
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(6)))
    ImageDraw.Draw(im).rounded_rectangle(box, radius=r, outline=color, width=8)

# ---------------------------------------------------------------- What changed?
def draw_changed(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    cols, rows = 3, 2
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows
    if not c.v: ch = min(ch, 300)
    oy = y0 + ((y1 - y0) - rows * ch) / 2
    blink_t = 3.0
    after = phase != "ask" or t >= blink_t
    d = ImageDraw.Draw(im)
    centers = []
    for i in range(6):
        r_, k = divmod(i, cols)
        cx, cy = x0 + cw * (k + 0.5), oy + ch * (r_ + 0.5)
        centers.append((cx, cy))
        box = (cx - cw / 2 + 18, cy - ch / 2 + 18, cx + cw / 2 - 18, cy + ch / 2 - 18)
        d.rounded_rectangle(box, radius=36, fill=(255, 255, 255, 235))
        em = item["after_emoji"] if (after and i == item["changed"]) else item["before"][i]
        s = eob((t - 0.3 - 0.12 * i) / 0.4) if phase == "ask" and t < blink_t else 1
        paste(im, emoji_img(em, min(cw, ch) * 0.55), cx, cy + 6, s)
        nf = font(F_BOLD, 40); d.ellipse((box[0] + 10, box[1] + 10, box[0] + 66, box[1] + 66), fill=c.accent)
        tw = d.textlength(str(i + 1), font=nf); d.text((box[0] + 38 - tw / 2, box[1] + 12), str(i + 1), font=nf, fill=(30, 30, 60))
    if phase == "ask" and blink_t <= t < blink_t + 0.45:
        a = 1 - abs((t - blink_t) - 0.22) / 0.22
        im.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, int(255 * cl(a)))))
    if phase == "ask" and t < blink_t:
        # memorise timer ring
        frac = t / blink_t
        bx, by = (c.W / 2, y1 + 40) if c.v else (c.W - 120, 150)
        d.arc((bx - 40, by - 40, bx + 40, by + 40), -90, -90 + 360 * (1 - frac), fill=c.accent, width=10)
    if phase == "reveal":
        cx, cy = centers[item["changed"]]
        box = (cx - cw / 2 + 12, cy - ch / 2 + 12, cx + cw / 2 - 12, cy + ch / 2 - 12)
        glow_box(im, box)
        if pt > 0.5:
            was = emoji_img(item["before"][item["changed"]], min(cw, ch) * 0.24)
            paste(im, was, box[2] - 50, box[1] + 50, eob((pt - 0.5) / 0.4))
        return cx, cy
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Follow the ball
def _cup(w, h, col):
    im = Image.new("RGBA", (int(w) + 20, int(h) + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    top, bot = 10 + w * 0.22, 10
    d.polygon([(10 + w * 0.2, 10), (10 + w * 0.8, 10), (10 + w, 10 + h), (10, 10 + h)], fill=col)
    d.ellipse((10 + w * 0.2, 10 - h * 0.06, 10 + w * 0.8, 10 + h * 0.08), fill=tuple(min(255, v + 40) for v in col))
    d.rounded_rectangle((4, 10 + h - 22, 16 + w, 10 + h + 6), radius=12, fill=tuple(max(0, v - 50) for v in col))
    for k in range(3):
        yy = 10 + h * (0.3 + 0.2 * k)
        d.line((10 + w * (0.2 - 0.06 * k) + 20, yy, 10 + w * (0.8 + 0.06 * k) - 20, yy), fill=(255, 255, 255, 60), width=6)
    return im

def cups_state(item, t):
    """returns slot position (float) for each cup id at time t (ask phase)"""
    slot = [0.0, 1.0, 2.0]; lift = 0.0
    if t < 1.6:
        lift = math.sin(cl((t - 0.4) / 1.0) * math.pi)
        return slot, lift, None
    k = int((t - 1.6) / 0.6); frac = ((t - 1.6) % 0.6) / 0.6
    pos = [0, 1, 2]  # pos[cup] = slot
    for j, (a, b) in enumerate(item["swaps"]):
        if j < k:
            ca, cb = pos.index(a), pos.index(b)
            pos[ca], pos[cb] = b, a
    slot = [float(p) for p in pos]
    arc = None
    if k < len(item["swaps"]):
        a, b = item["swaps"][k]
        ca, cb = pos.index(a), pos.index(b)
        e = 0.5 - 0.5 * math.cos(frac * math.pi)
        slot[ca] = a + (b - a) * e; slot[cb] = b + (a - b) * e
        arc = (ca, cb, math.sin(frac * math.pi))
    return slot, 0.0, arc

def final_slot(item):
    pos = [0, 1, 2]
    for a, b in item["swaps"]:
        ca, cb = pos.index(a), pos.index(b)
        pos[ca], pos[cb] = b, a
    return pos[item["start"]]

def draw_cups(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    sw = (x1 - x0) / 3
    cw, chh = sw * 0.62, sw * 0.62 * 1.05
    if not c.v: cw, chh = 230, 230
    base_y = (y0 + y1) / 2 + chh * (0.35 if c.v else 0.75)
    d = ImageDraw.Draw(im)
    tt = t if phase == "ask" else 1e9
    if phase == "ask":
        slot, lift, arc = cups_state(item, t)
    else:
        n = len(item["swaps"]); slot, lift, arc = cups_state(item, 1.6 + 0.6 * n + 0.01)
        lift = eo(pt / 0.5) if phase == "reveal" else 0.0
    # table line
    d.rounded_rectangle((x0, base_y + 10, x1, base_y + 30), radius=10, fill=(255, 255, 255, 50))
    # ball
    ball_cup = item["start"]
    bx = x0 + sw * (slot[ball_cup] + 0.5)
    br = cw * 0.18
    show_ball = (phase == "ask" and t < 1.6) or phase == "reveal"
    if show_ball:
        d.ellipse((bx - br, base_y - 2 * br, bx + br, base_y), fill=(255, 80, 80), outline=(255, 255, 255), width=6)
    cols = [(230, 70, 70), (60, 140, 230), (250, 180, 40)]
    for cup in range(3):
        cx = x0 + sw * (slot[cup] + 0.5)
        dy = 0
        if arc and cup in (arc[0], arc[1]):
            dy = -arc[2] * chh * 0.35 * (1 if cup == arc[0] else -0.4)
        l = 0
        if phase == "ask" and t < 1.6 and cup == item["start"]: l = lift
        if phase == "reveal": l = lift
        cup_im = _cup(cw, chh, cols[cup] if item.get("colors") else (220, 60, 70))
        s = eob((t - 0.1 * cup) / 0.4) if phase == "ask" else 1
        paste(im, cup_im, cx, base_y - chh / 2 + dy - l * chh * 0.75, s)
    # slot letters
    for k in range(3):
        f = font(F_BOLD, 64 if c.v else 56)
        L = "ABC"[k]; cx = x0 + sw * (k + 0.5)
        d.ellipse((cx - 44, base_y + 60, cx + 44, base_y + 148), fill=c.accent)
        tw = d.textlength(L, font=f); d.text((cx - tw / 2, base_y + 66), L, font=f, fill=(30, 30, 60))
    if phase == "reveal":
        fx = x0 + sw * (final_slot(item) + 0.5)
        if pt > 0.4: glow_box(im, (fx - sw / 2 + 20, base_y - chh * 1.9, fx + sw / 2 - 20, base_y + 160))
        return fx, base_y - chh
    return c.W / 2, base_y

# ---------------------------------------------------------------- Complete the pattern
def draw_pattern(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    seq = item["seq"]; n = len(seq) + 1
    size = min(170 if c.v else 150, (x1 - x0) / n * 0.8)
    rowy = y0 + (180 if c.v else 120)
    gap = (x1 - x0) / n
    d = ImageDraw.Draw(im)
    for i in range(n):
        cx = x0 + gap * (i + 0.5)
        s = eob((t - 0.3 - 0.15 * i) / 0.4) if phase == "ask" else 1
        if i < len(seq):
            paste(im, emoji_img(seq[i], size), cx, rowy, s)
        else:
            box = (cx - size * 0.62, rowy - size * 0.62, cx + size * 0.62, rowy + size * 0.62)
            if phase == "reveal" and pt > 0.2:
                glow_box(im, box, r=24)
                paste(im, emoji_img(item["options"][item["right"]], size), cx, rowy, eob((pt - 0.2) / 0.4))
            else:
                d.rounded_rectangle(box, radius=24, outline=c.accent, width=8, fill=(255, 255, 255, 30))
                qf = font(F_BOLD, size * 0.8); tw = d.textlength("?", font=qf)
                d.text((cx - tw / 2, rowy - size * 0.55), "?", font=qf, fill=c.accent)
    # options row
    opts = item["options"]; oy = y0 + (560 if c.v else 430)
    ow = (x1 - x0) / len(opts)
    for k, o in enumerate(opts):
        cx = x0 + ow * (k + 0.5)
        bw, bh = min(ow - 50, 300), 260 if c.v else 220
        box = (cx - bw / 2, oy - bh / 2, cx + bw / 2, oy + bh / 2)
        s = eob((t - 1.4 - 0.25 * k) / 0.4) if phase == "ask" else 1
        if s <= 0.01: continue
        fill = (255, 255, 255)
        if phase == "reveal":
            fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        card = Image.new("RGBA", (int(bw) + 20, int(bh) + 20), (0, 0, 0, 0)); cd = ImageDraw.Draw(card)
        cd.rounded_rectangle((10, 10, bw + 10, bh + 10), radius=36, fill=fill, outline=c.accent, width=8)
        e = emoji_img(o, bh * 0.5); card.alpha_composite(e, (int(10 + bw / 2 - e.width / 2), int(10 + bh * 0.4 - e.height / 2)))
        lf = font(F_BOLD, 54); L = "ABC"[k]; tw = cd.textlength(L, font=lf)
        cd.text((10 + bw / 2 - tw / 2, 10 + bh * 0.72), L, font=lf, fill=(30, 30, 60) if phase != "reveal" else (255, 255, 255))
        paste(im, card, cx, oy, s, 0.55 if (phase == "reveal" and k != item["right"]) else 1)
    if phase == "reveal":
        return x0 + ow * (item["right"] + 0.5), oy
    return c.W / 2, oy

# ---------------------------------------------------------------- Find the hidden one
def draw_hidden(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    cols, rows = (6, 6) if c.v else (12, 5)
    if not c.v: y0 += 50
    cell = min((x1 - x0) / cols, (y1 - y0) / rows) * 0.94
    ox = x0 + ((x1 - x0) - cols * cell) / 2; oy = y0 + ((y1 - y0) - rows * cell) / 2
    orow, ocol = item["pos"]
    orow %= rows; ocol %= cols
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((ox - 20, oy - 20, ox + cols * cell + 20, oy + rows * cell + 20), radius=40, fill=(255, 255, 255, 230))
    a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
    for r_ in range(rows):
        for k in range(cols):
            em = item["odd"] if (r_ == orow and k == ocol) else item["base"]
            paste(im, emoji_img(em, cell * 0.78), ox + cell * (k + 0.5), oy + cell * (r_ + 0.5), 1, a)
    cx, cy = ox + cell * (ocol + 0.5), oy + cell * (orow + 0.5)
    if phase == "reveal":
        rr = cell * (0.75 + 0.1 * math.sin(pt * 6))
        im.alpha_composite(Image.new("RGBA", im.size, (0, 0, 0, int(90 * cl(pt / 0.4)))))
        paste(im, emoji_img(item["odd"], cell * 0.78 * (1 + 0.4 * eo(pt / 0.5))), cx, cy)
        d = ImageDraw.Draw(im)
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(60, 255, 120), width=12)
    return cx, cy

DRAW = {"changed": draw_changed, "cups": draw_cups, "pattern": draw_pattern, "hidden": draw_hidden}

# ================================================================ BATCH 2
def _key_img(teeth, scale, col=(250, 200, 60)):
    u = scale
    w, h = int(u * 9), int(u * 3.2)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = u * 1.3
    d.ellipse((0, h / 2 - r, 2 * r, h / 2 + r), fill=col)
    d.ellipse((r * 0.55, h / 2 - r * 0.45, r * 1.45, h / 2 + r * 0.45), fill=(0, 0, 0, 0))
    sx = 2 * r - 6; sy = h / 2 - u * 0.4
    d.rectangle((sx, sy, w - u * 0.3, sy + u * 0.8), fill=col)
    tw = (w - u * 0.6 - sx - u * 0.6) / len(teeth)
    for i, tv in enumerate(teeth):
        x = sx + u * 0.6 + i * tw
        d.rectangle((x + 3, sy + u * 0.8, x + tw - 3, sy + u * 0.8 + u * 0.38 * tv), fill=col)
    return im

def _lock_img(teeth, scale, open_=0.0, col=(120, 130, 150)):
    u = scale
    w, h = int(u * 11), int(u * 12)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    lift = open_ * u * 1.6
    d.arc((u * 2.5, u * 0.3 - lift, w - u * 2.5, u * 7 - lift), 180, 360, fill=(190, 195, 205), width=int(u * 1.1))
    d.line((u * 2.5 + u * 0.55, u * 3.65 - lift, u * 2.5 + u * 0.55, u * 5.5), fill=(190, 195, 205), width=int(u * 1.1))
    d.line((w - u * 2.5 - u * 0.55, u * 3.65 - lift, w - u * 2.5 - u * 0.55, u * 5.5), fill=(190, 195, 205), width=int(u * 1.1))
    d.rounded_rectangle((0, u * 5, w, h), radius=int(u * 1.2), fill=col)
    # keyway panel showing the tooth profile
    px0, py0 = u * 1.2, u * 7.2
    pw = w - u * 2.4
    d.rounded_rectangle((px0, py0, px0 + pw, py0 + u * 3), radius=int(u * 0.4), fill=(40, 44, 60))
    tw = (pw - u * 0.8) / len(teeth)
    pts = [(px0 + u * 0.4, py0 + u * 0.7)]
    for i, tv in enumerate(teeth):
        x = px0 + u * 0.4 + i * tw
        pts += [(x + 3, py0 + u * 0.7 + u * 0.5 * tv), (x + tw - 3, py0 + u * 0.7 + u * 0.5 * tv)]
    pts += [(px0 + pw - u * 0.4, py0 + u * 0.7)]
    d.line(pts, fill=(255, 210, 60), width=8, joint="curve")
    return im

def draw_keys(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    if c.v:
        lock_c = (c.W / 2, y0 + 170); u_l = 34
        key_cs = [(c.W / 2 + 60, y0 + 470 + i * 150) for i in range(3)]; u_k = 40
    else:
        lock_c = (x0 + 360, (y0 + y1) / 2 + 30); u_l = 40
        key_cs = [(x0 + 1100, y0 + 140 + i * 200) for i in range(3)]; u_k = 44
    op = 0.0
    if phase == "reveal": op = eo((pt - 0.9) / 0.4)
    paste(im, _lock_img(item["lock"], u_l, op), lock_c[0], lock_c[1], eob((t - 0.2) / 0.4) if phase == "ask" else 1)
    for k, teeth in enumerate(item["keys"]):
        kx, ky = key_cs[k]
        s = eob((t - 0.9 - 0.3 * k) / 0.4) if phase == "ask" else 1
        if phase == "reveal" and k == item["right"]:
            m = eo(pt / 0.8)
            tx, ty = lock_c[0], lock_c[1] + u_l * 2.7
            kx, ky = kx + (tx - kx) * m, ky + (ty - ky) * m
        a = 0.45 if (phase == "reveal" and k != item["right"]) else 1
        paste(im, _key_img(teeth, u_k), kx, ky, s, a)
        lx = key_cs[k][0] - u_k * 6.2
        f = font(F_BOLD, 56)
        d.ellipse((lx - 40, key_cs[k][1] - 40, lx + 40, key_cs[k][1] + 40), fill=c.accent)
        L = "ABC"[k]; tw = d.textlength(L, font=f); d.text((lx - tw / 2, key_cs[k][1] - 36), L, font=f, fill=(30, 30, 60))
    if phase == "reveal":
        return lock_c
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Which glass fills first
GL_POS_V = {1: (0.5, 0.05), 2: (0.27, 0.38), 3: (0.73, 0.38), 4: (0.13, 0.72), 5: (0.5, 0.72), 6: (0.87, 0.72)}
GL_POS_H = {1: (0.5, 0.0), 2: (0.3, 0.36), 3: (0.7, 0.36), 4: (0.12, 0.72), 5: (0.5, 0.72), 6: (0.88, 0.72)}

def glass_path(item):
    """follow lowest open outlet from glass 1; returns list of (glass, level_to_fill) ending with the glass that fills (level 1)"""
    g = 1; path = []
    pipes = item["pipes"]  # {"1": [[child, height, blocked], ...]}
    for _ in range(10):
        outs = [p for p in pipes.get(str(g), []) if not p[2]]
        if not outs:
            path.append((g, 1.0)); return path
        child, hgt, _ = min(outs, key=lambda p: p[1])
        path.append((g, hgt)); g = child
    return path

def draw_glasses(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    if not c.v: y0 += 70
    P = GL_POS_V if c.v else GL_POS_H
    gw, gh = (150, 200) if c.v else (130, 160)
    d = ImageDraw.Draw(im)
    def gbox(g):
        fx, fy = P[g]; cx = x0 + (x1 - x0) * fx; top = y0 + (y1 - y0 - gh) * fy + 60
        return (cx - gw / 2, top, cx + gw / 2, top + gh)
    path = glass_path(item)
    # fill animation in reveal
    levels = {g: 0.0 for g in P}
    if phase == "reveal":
        T = pt / 0.7
        for g, lvl in path:
            if T <= 0: break
            step = min(1.0, T); levels[g] = lvl * step; T -= 1.0
    # pipes
    for g, outs in item["pipes"].items():
        g = int(g); bx = gbox(g)
        for child, hgt, blocked in outs:
            cb = gbox(child)
            sx = bx[0] if (cb[0] + cb[2]) / 2 < (bx[0] + bx[2]) / 2 else bx[2]
            sy = bx[3] - (bx[3] - bx[1]) * hgt
            ex, ey = (cb[0] + cb[2]) / 2, cb[1] - 10
            mx = ex
            d.line((sx, sy, mx, sy, ex, ey), fill=(200, 210, 230), width=16, joint="curve")
            flowing = phase == "reveal" and any(pg == g for pg, _ in path) and levels[g] >= hgt - 1e-6 and not blocked and (g, hgt) in path
            if flowing:
                d.line((sx, sy, mx, sy, ex, ey), fill=(70, 160, 255), width=10, joint="curve")
            if blocked:
                bxm, bym = (sx + mx) / 2, sy
                d.rectangle((bxm - 14, bym - 22, bxm + 14, bym + 22), fill=(60, 60, 70))
                d.line((bxm - 22, bym - 22, bxm + 22, bym + 22), fill=(255, 70, 70), width=8)
                d.line((bxm + 22, bym - 22, bxm - 22, bym + 22), fill=(255, 70, 70), width=8)
    # tap
    b1 = gbox(1); tx = (b1[0] + b1[2]) / 2
    d.rounded_rectangle((tx - 70, b1[1] - 95, tx + 30, b1[1] - 60), radius=12, fill=(180, 185, 200))
    d.rectangle((tx - 10, b1[1] - 70, tx + 18, b1[1] - 40), fill=(180, 185, 200))
    if phase == "reveal" and pt < 0.7 * len(path) + 0.5:
        d.rectangle((tx - 2, b1[1] - 40, tx + 10, b1[1] + gh - levels[1] * gh), fill=(70, 160, 255))
    f = font(F_BOLD, 50)
    for g in P:
        bx = gbox(g)
        a = eob((t - 0.3 - 0.12 * g) / 0.4) if phase == "ask" else 1
        if a <= 0.05: continue
        lv = levels[g]
        if lv > 0:
            d.rectangle((bx[0] + 8, bx[3] - (gh - 8) * lv, bx[2] - 8, bx[3] - 6), fill=(70, 160, 255, 230))
        d.line((bx[0], bx[1], bx[0] + 8, bx[3], bx[2] - 8, bx[3], bx[2], bx[1]), fill=(255, 255, 255), width=8, joint="curve")
        L = str(g); tw = d.textlength(L, font=f)
        mx_, my_ = (bx[0] + bx[2]) / 2, bx[3] - 50
        d.ellipse((mx_ - 32, my_ - 32, mx_ + 32, my_ + 32), fill=c.accent)
        d.text((mx_ - tw / 2, my_ - 33), L, font=f, fill=(30, 30, 60))
    win = path[-1][0]
    if phase == "reveal" and pt > 0.7 * len(path):
        bx = gbox(win); glow_box(im, (bx[0] - 20, bx[1] - 20, bx[2] + 20, bx[3] + 20))
        return (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Which path gets the prize (ghost-leg)
def path_trace(item, lane, rows):
    """returns list of (lane_float, row_float) points and the end lane"""
    pts = [(lane, 0.0)]
    rungs = sorted(item["rungs"], key=lambda r: r[0])
    for r, left in rungs:
        if lane == left or lane == left + 1:
            other = left + 1 if lane == left else left
            pts.append((lane, r - 0.35)); pts.append((other, r + 0.35)); lane = other
    pts.append((lane, rows))
    return pts, lane

def draw_path(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    n = len(item["starters"]); rows = item.get("rows", 8)
    if not c.v: y0 += 70
    top, bot = y0 + (90 if c.v else 70), y1 - (110 if c.v else 80)
    lx = lambda l: x0 + (x1 - x0) * (l + 0.5) / n
    ry = lambda r: top + (bot - top) * r / rows
    d = ImageDraw.Draw(im)
    a = eo((t - 0.4) / 0.6) if phase == "ask" else 1
    col = (255, 255, 255, int(200 * a))
    def poly(pts):
        out = []
        for i in range(len(pts) - 1):
            (la, ra), (lb, rb) = pts[i], pts[i + 1]
            if la == lb:
                out += [(lx(la), ry(ra)), (lx(lb), ry(rb))]
            else:
                for s in range(13):
                    u = s / 12; e = 0.5 - 0.5 * math.cos(u * math.pi)
                    out.append((lx(la + (lb - la) * e), ry(ra + (rb - ra) * u)))
        return out
    for l in range(n):
        pts, _ = path_trace(item, l, rows)
        d.line(poly(pts), fill=col, width=12, joint="curve")
    right = None
    for l in range(n):
        _, end = path_trace(item, l, rows)
        if end == item["prize_slot"]: right = l
    for l, e in enumerate(item["starters"]):
        paste(im, emoji_img(e, 110 if c.v else 90), lx(l), top - 50, eob((t - 0.2 - 0.2 * l) / 0.4) if phase == "ask" else 1)
        f = font(F_BOLD, 44); L = "ABC"[l]; tw = d.textlength(L, font=f)
        d.text((lx(l) - 80 - tw / 2, top - 75), L, font=f, fill=c.accent)
    for l in range(n):
        if l == item["prize_slot"]:
            paste(im, emoji_img(item["prize"], 110 if c.v else 90), lx(l), bot + 55)
        else:
            paste(im, emoji_img("❌", 70), lx(l), bot + 55)
    if phase == "reveal":
        pts, _ = path_trace(item, right, rows)
        P = poly(pts); k = max(2, int(len(P) * cl(pt / 1.6)))
        d.line(P[:k], fill=(60, 255, 120), width=16, joint="curve")
        return lx(item["prize_slot"]), bot + 55
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Shadow match
def silhouette(em, size, flip=False, col=(20, 20, 35)):
    e = emoji_img(em, size)
    if flip: e = e.transpose(Image.FLIP_LEFT_RIGHT)
    sil = Image.new("RGBA", e.size, col + (0,)); sil.putalpha(e.split()[-1].point(lambda v: 255 if v > 60 else 0))
    return e, sil

def draw_shadow(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    big = 300 if c.v else 260
    oc = (c.W / 2, y0 + 180) if c.v else (x0 + 280, (y0 + y1) / 2)
    paste(im, emoji_img(item["object"], big), oc[0], oc[1], eob((t - 0.2) / 0.5) if phase == "ask" else 1)
    n = len(item["shadows"])
    for k, sh in enumerate(item["shadows"]):
        em, fl = (sh[:-5], True) if sh.endswith("|flip") else (sh, False)
        if c.v:
            cx, cy = x0 + (x1 - x0) * (k + 0.5) / n, y0 + 620; sz = 230
        else:
            cx, cy = x0 + 640 + k * 380, (y0 + y1) / 2; sz = 230
        box = (cx - sz * 0.72, cy - sz * 0.72, cx + sz * 0.72, cy + sz * 0.72)
        s = eob((t - 1.0 - 0.3 * k) / 0.4) if phase == "ask" else 1
        if s <= 0.02: continue
        d.rounded_rectangle(box, radius=30, fill=(255, 255, 255, 220))
        e, sil = silhouette(em, sz, fl)
        if phase == "reveal" and k == item["right"] and pt > 0.3:
            paste(im, e, cx, cy, 1)
            glow_box(im, box)
        else:
            paste(im, sil, cx, cy, s, 0.4 if phase == "reveal" else 1)
        f = font(F_BOLD, 50); L = "ABC"[k]; tw = d.textlength(L, font=f)
        d.ellipse((box[0] - 10, box[1] - 10, box[0] + 60, box[1] + 60), fill=c.accent)
        d.text((box[0] + 25 - tw / 2, box[1] - 8), L, font=f, fill=(30, 30, 60))
    if phase == "reveal":
        k = item["right"]
        return (x0 + (x1 - x0) * (k + 0.5) / n, y0 + 620) if c.v else (x0 + 640 + k * 380, (y0 + y1) / 2)
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Mirror match
def _content_img(item, size):
    if item.get("kind") == "text":
        f = font(F_BOLD, size); tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        w = int(tmp.textlength(item["content"], font=f)) + 40
        im = Image.new("RGBA", (w, int(size * 1.4)), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((20, 0), item["content"], font=f, fill=(30, 30, 60))
        return im.crop(im.getbbox())
    return emoji_img(item["content"], size)

def draw_mirror(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    base = _content_img(item, 150 if c.v else 130)
    oc = (c.W / 2, y0 + 120) if c.v else (c.W / 2, y0 + 170)
    bw = min(base.width + 80, c.W - 160)
    d.rounded_rectangle((oc[0] - bw / 2, oc[1] - base.height / 2 - 40, oc[0] + bw / 2, oc[1] + base.height / 2 + 40), radius=30, fill=(255, 255, 255))
    paste(im, base, oc[0], oc[1], min(1, (bw - 80) / base.width))
    tf = {"h": Image.FLIP_LEFT_RIGHT, "v": Image.FLIP_TOP_BOTTOM, "r": Image.ROTATE_180}
    n = len(item["opts"])
    for k, op in enumerate(item["opts"]):
        img = base.transpose(tf[op]) if op in tf else base
        if c.v:
            cx, cy = c.W / 2, y0 + 370 + k * 200; ow, oh = c.W - 220, 170
        else:
            cx, cy = x0 + (x1 - x0) * (k + 0.5) / n, y0 + 470; ow, oh = (x1 - x0) / n - 60, 230
        s = eob((t - 1.0 - 0.3 * k) / 0.4) if phase == "ask" else 1
        if s <= 0.02: continue
        fill = (255, 255, 255)
        if phase == "reveal": fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        d.rounded_rectangle((cx - ow / 2, cy - oh / 2, cx + ow / 2, cy + oh / 2), radius=30, fill=fill, outline=c.accent, width=6)
        sc = min((ow - 160) / img.width, (oh - 50) / img.height)
        paste(im, img, cx + 30, cy, sc * s, 0.5 if (phase == "reveal" and k != item["right"]) else 1)
        f = font(F_BOLD, 52); L = "ABC"[k]; tw = d.textlength(L, font=f)
        d.ellipse((cx - ow / 2 + 20, cy - 40, cx - ow / 2 + 100, cy + 40), fill=c.accent)
        d.text((cx - ow / 2 + 60 - tw / 2, cy - 36), L, font=f, fill=(30, 30, 60))
    if phase == "reveal":
        k = item["right"]
        return (c.W / 2, y0 + 370 + k * 200) if c.v else (x0 + (x1 - x0) * (k + 0.5) / n, y0 + 470)
    return c.W / 2, (y0 + y1) / 2

DRAW.update({"keys": draw_keys, "glasses": draw_glasses, "path": draw_path, "shadow": draw_shadow, "mirror": draw_mirror})

# ================================================================ BATCH 3 + 4
import random as _rnd

def _label(d, x, y, L, c, r=40, size=52):
    f = font(F_BOLD, size); d.ellipse((x - r, y - r, x + r, y + r), fill=c.accent)
    tw = d.textlength(L, font=f); d.text((x - tw / 2, y - size * 0.68), L, font=f, fill=(30, 30, 60))

# ---------------------------------------------------------------- Which jar has more
def _jar_points(n, w, h, size, seed):
    rnd = _rnd.Random(seed); pts = []
    cols = max(1, int(w / size)); rows_needed = math.ceil(n / cols)
    for i in range(n):
        r_, k = divmod(i, cols)
        x = (k + 0.5) * (w / cols) + rnd.uniform(-size * 0.12, size * 0.12)
        y = h - (r_ + 0.5) * size * 0.92 + rnd.uniform(-size * 0.1, size * 0.1)
        pts.append((x, y))
    return pts

CANDY = [(255, 90, 110), (255, 200, 60), (90, 200, 255), (120, 230, 120), (200, 120, 255), (255, 150, 60)]

def draw_jar(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    jw, jh = (380, 620) if c.v else (420, 520)
    cy = (y0 + y1) / 2 + (0 if c.v else 40)
    win = 0 if item["counts"][0] > item["counts"][1] else 1
    for k in range(2):
        cx = x0 + (x1 - x0) * (0.27 + 0.46 * k)
        bx = (cx - jw / 2, cy - jh / 2, cx + jw / 2, cy + jh / 2)
        s = eob((t - 0.3 - 0.3 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        n = item["counts"][k]; size = 52 * item["sizes"][k] * (1 if c.v else 0.95)
        pts = _jar_points(n, jw - 40, jh - 80, size, item.get("seed", 1) + k)
        shown = n
        if phase == "reveal": shown = n
        cnt = int(n * cl(pt / 1.6)) if phase == "reveal" else 0
        for i, (px, py) in enumerate(pts[:shown]):
            col = CANDY[(i * 7 + k) % 6]
            X, Y = bx[0] + 20 + px, bx[1] + 60 + py
            hl = phase == "reveal" and i < cnt
            d.ellipse((X - size / 2, Y - size / 2, X + size / 2, Y + size / 2), fill=col, outline=(255, 255, 255) if hl else (0, 0, 0, 60), width=4 if hl else 2)
        d.rounded_rectangle(bx, radius=60, outline=(220, 240, 255), width=10)
        d.rounded_rectangle((bx[0] + 40, bx[1] - 40, bx[2] - 40, bx[1] + 10), radius=16, fill=(200, 160, 110))
        _label(d, cx, bx[3] + 70, "AB"[k], c)
        if phase == "reveal":
            f = font(F_BOLD, 90); txt = str(cnt); tw = d.textlength(txt, font=f)
            d.text((cx - tw / 2, bx[1] + jh / 2 - 60), txt, font=f, fill=(255, 255, 255), stroke_width=8, stroke_fill=(20, 10, 40))
            if pt > 1.7 and k == win: glow_box(im, (bx[0] - 20, bx[1] - 60, bx[2] + 20, bx[3] + 20), r=60)
    if phase == "reveal":
        return x0 + (x1 - x0) * (0.27 + 0.46 * win), cy
    return c.W / 2, cy

# ---------------------------------------------------------------- How many fit
def draw_fit(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    cols, rows = item["grid"]  # container holds cols x rows items exactly
    cell = (140 if c.v else 105) * item.get("scale", 1)
    bw, bh = cols * cell + 40, rows * cell + 40
    cx = c.W / 2 if c.v else x0 + 420
    cy = y0 + (60 + bh / 2 if c.v else (y1 - y0) / 2 + 30)
    bx = (cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
    d.rounded_rectangle(bx, radius=30, fill=(150, 100, 60), outline=(90, 60, 30), width=10)
    d.rounded_rectangle((bx[0] + 14, bx[1] + 14, bx[2] - 14, bx[3] - 14), radius=20, fill=(255, 245, 225))
    n = cols * rows
    # sample item for scale
    sx, sy = (bx[2] + 100, bx[1] + 70) if not c.v else (bx[2] + 60, bx[1] + 40)
    if phase != "reveal":
        paste(im, emoji_img(item["item"], cell * 0.85), sx, sy, eob((t - 0.6) / 0.4) if phase == "ask" else 1)
    if phase == "reveal":
        k = int(n * cl(pt / 1.8))
        for i in range(k):
            r_, q = divmod(i, cols)
            paste(im, emoji_img(item["item"], cell * 0.85), bx[0] + 20 + cell * (q + 0.5), bx[3] - 20 - cell * (r_ + 0.5))
        f = font(F_BOLD, 80); txt = str(k); tw = d.textlength(txt, font=f)
        d.text((cx - tw / 2, bx[3] + 20), txt, font=f, fill=c.accent, stroke_width=6, stroke_fill=(20, 10, 40))
    # options
    opts = item["options"]
    for k, o in enumerate(opts):
        if c.v:
            ox, oy = x0 + (x1 - x0) * (k + 0.5) / len(opts), bx[3] + 200; ow, oh = 270, 150
        else:
            ox, oy = x0 + 880 + k * 290, (y0 + y1) / 2 + 30; ow, oh = 250, 190
        s = eob((t - 1.2 - 0.25 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 1.9: fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox - ow / 2, oy - oh / 2, ox + ow / 2, oy + oh / 2), radius=30, fill=fill, outline=c.accent, width=6)
        f = font(F_BOLD, 80); tw = d.textlength(o, font=f)
        d.text((ox - tw / 2 + 25, oy - 56), o, font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
        _label(d, ox - ow / 2 + 45, oy, "ABC"[k], c, r=32, size=42)
    if phase == "reveal":
        return cx, cy
    return c.W / 2, cy

# ---------------------------------------------------------------- Find the twins (procedural creatures)
def twins_set(seed):
    rnd = _rnd.Random(seed)
    base = dict(body=rnd.randrange(6), eyes=rnd.choice([1, 2, 3]), mouth=rnd.choice(["smile", "o", "flat"]),
                spots=rnd.randrange(4), horns=rnd.choice([0, 1]), cheeks=rnd.choice([0, 1]))
    alts = {"body": [i for i in range(6)], "eyes": [1, 2, 3], "mouth": ["smile", "o", "flat"], "spots": [0, 1, 2, 3], "horns": [0, 1], "cheeks": [0, 1]}
    feats = list(alts.keys())
    creatures = []
    used = set()
    for i in range(5):
        while True:
            f = rnd.choice(feats); v = rnd.choice([x for x in alts[f] if x != base[f]])
            if (f, v) not in used: used.add((f, v)); break
        cr = dict(base); cr[f] = v; creatures.append(cr)
    pair = rnd.sample(range(6), 2)
    order = []; ci = 0
    for i in range(6):
        if i in pair: order.append(dict(base))
        else: order.append(creatures[ci]); ci += 1
    return order, sorted(pair)

def _creature(cr, size):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = CANDY[cr["body"]]
    s = size
    if cr["horns"]:
        d.polygon([(s * 0.3, s * 0.28), (s * 0.24, s * 0.08), (s * 0.4, s * 0.22)], fill=(255, 240, 200))
        d.polygon([(s * 0.7, s * 0.28), (s * 0.76, s * 0.08), (s * 0.6, s * 0.22)], fill=(255, 240, 200))
    d.ellipse((s * 0.12, s * 0.18, s * 0.88, s * 0.92), fill=col, outline=(30, 30, 60), width=5)
    for k in range(cr["spots"]):
        sx, sy = [(0.3, 0.72), (0.7, 0.7), (0.5, 0.82)][k]
        d.ellipse((s * (sx - 0.05), s * (sy - 0.04), s * (sx + 0.05), s * (sy + 0.04)), fill=tuple(max(0, v - 60) for v in col))
    ex = {1: [0.5], 2: [0.38, 0.62], 3: [0.32, 0.5, 0.68]}[cr["eyes"]]
    for x in ex:
        d.ellipse((s * (x - 0.07), s * 0.36, s * (x + 0.07), s * 0.5), fill=(255, 255, 255), outline=(30, 30, 60), width=3)
        d.ellipse((s * (x - 0.03), s * 0.41, s * (x + 0.03), s * 0.47), fill=(30, 30, 60))
    if cr["mouth"] == "smile":
        d.arc((s * 0.36, s * 0.48, s * 0.64, s * 0.68), 20, 160, fill=(30, 30, 60), width=6)
    elif cr["mouth"] == "o":
        d.ellipse((s * 0.45, s * 0.56, s * 0.55, s * 0.66), fill=(30, 30, 60))
    else:
        d.line((s * 0.4, s * 0.62, s * 0.6, s * 0.62), fill=(30, 30, 60), width=6)
    if cr["cheeks"]:
        d.ellipse((s * 0.2, s * 0.52, s * 0.3, s * 0.6), fill=(255, 150, 170))
        d.ellipse((s * 0.7, s * 0.52, s * 0.8, s * 0.6), fill=(255, 150, 170))
    return im

def draw_twins(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    order, pair = twins_set(item["seed"])
    cols, rows = (2, 3) if c.v else (3, 2)
    if not c.v: y0 += 40
    cw, ch = (x1 - x0) / cols, (y1 - y0) / rows
    sz = int(min(cw, ch) * 0.82)
    centers = []
    for i, cr in enumerate(order):
        r_, k = divmod(i, cols)
        cx, cy = x0 + cw * (k + 0.5), y0 + ch * (r_ + 0.5)
        centers.append((cx, cy))
        s = eob((t - 0.3 - 0.12 * i) / 0.4) if phase == "ask" else 1
        a = 0.35 if (phase == "reveal" and i not in pair and pt > 0.3) else 1
        paste(im, _creature(cr, sz), cx, cy, s, a)
        _label(d, cx - sz * 0.45, cy - sz * 0.4, str(i + 1), c, r=34, size=44)
    if phase == "reveal":
        for i in pair:
            cx, cy = centers[i]; glow_box(im, (cx - sz / 2, cy - sz / 2, cx + sz / 2, cy + sz / 2), r=40)
        return centers[pair[0]]
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Gears
def _gear(r, teeth, col, ang):
    size = int(r * 2.5); im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = cy = size / 2; pts = []
    for i in range(teeth * 2):
        a = ang + i * math.pi / teeth
        rr = r * (1.18 if i % 2 == 0 else 0.95)
        for da in (-0.32, 0.32):
            aa = a + da * math.pi / teeth
            pts.append((cx + rr * math.cos(aa), cy + rr * math.sin(aa)))
    d.polygon(pts, fill=col, outline=(30, 30, 60))
    d.ellipse((cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35), fill=(40, 40, 60))
    d.line((cx, cy, cx + r * 0.8 * math.cos(ang), cy + r * 0.8 * math.sin(ang)), fill=(255, 255, 255), width=6)
    return im

def gears_answer(item):
    same = item["n"] % 2 == 1
    first_cw = item["first"] == "cw"
    last_cw = first_cw if same else not first_cw
    return 0 if last_cw else 1

def _arrow_arc(d, cx, cy, r, cw, col, width=10):
    if cw:
        d.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=col, width=width)
        a = math.radians(340); hx, hy = cx + r * math.cos(a), cy + r * math.sin(a)
        d.polygon([(hx + 22, hy - 4), (hx - 12, hy - 20), (hx - 4, hy + 18)], fill=col)
    else:
        d.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=col, width=width)
        a = math.radians(200); hx, hy = cx + r * math.cos(a), cy + r * math.sin(a)
        d.polygon([(hx - 22, hy - 4), (hx + 12, hy - 20), (hx + 4, hy + 18)], fill=col)

def draw_gears(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    n = item["n"]
    r = 105 if c.v else 85
    pitch = r * 2.12
    if c.v:
        cols = 3; pos = []
        for i in range(n):
            row, k = divmod(i, cols)
            k = k if row % 2 == 0 else cols - 1 - k
            pos.append((c.W / 2 - pitch + k * pitch, y0 + 150 + row * pitch))
    else:
        pos = [(x0 + 200 + i * pitch, y0 + 220 + (60 if i % 2 else 0)) for i in range(n)]
    spin = (pt * 2.2) if phase == "reveal" else 0
    first_cw = item["first"] == "cw"
    cols_ = [(250, 180, 60), (90, 180, 240), (240, 110, 110), (120, 210, 120), (200, 140, 240), (250, 150, 80)]
    for i, (gx, gy) in enumerate(pos):
        dirn = (1 if first_cw else -1) * (1 if i % 2 == 0 else -1)
        g = _gear(r, 10, cols_[i % 6], dirn * spin + (math.pi / 10 if i % 2 else 0))
        s = eob((t - 0.2 - 0.15 * i) / 0.4) if phase == "ask" else 1
        paste(im, g, gx, gy, s)
    fx, fy = pos[0]
    _arrow_arc(d, fx, fy, r * 1.45, first_cw, c.accent)
    lx, ly = pos[-1]
    f = font(F_BOLD, 70); tw = d.textlength("?", font=f)
    if phase != "reveal": d.text((lx - tw / 2, ly - r * 1.75 - 30), "?", font=f, fill=c.accent, stroke_width=6, stroke_fill=(20, 10, 40))
    # options
    labels = ["Clockwise", "Anticlockwise"]
    for k in range(2):
        if c.v:
            ox, oy, ow, oh = x0 + (x1 - x0) * (k + 0.5) / 2, y1 - 40, 440, 170
        else:
            ox, oy, ow, oh = x0 + 1400, y0 + 160 + k * 230, 400, 180
        s = eob((t - 1.4 - 0.3 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255)
        right = gears_answer(item)
        if phase == "reveal" and pt > 1.0: fill = (40, 190, 90) if k == right else (150, 40, 55)
        d.rounded_rectangle((ox - ow / 2, oy - oh / 2, ox + ow / 2, oy + oh / 2), radius=30, fill=fill, outline=c.accent, width=6)
        _arrow_arc(d, ox, oy + 10, 50, k == 0, (30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255), 9)
        f = font(F_BOLD, 40); tw = d.textlength(labels[k], font=f)
        d.text((ox - tw / 2, oy + 30), labels[k], font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
        _label(d, ox - ow / 2 + 40, oy - oh / 2 + 40, "AB"[k], c, r=30, size=40)
    if phase == "reveal":
        _arrow_arc(d, lx, ly, r * 1.45, gears_answer(item) == 0, (60, 255, 120))
        return lx, ly
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Which piece fits
def _tile(src, idx, n, size, rot=False):
    w = src.width / n; r_, k = divmod(idx, n)
    t_ = src.crop((int(k * w), int(r_ * w), int((k + 1) * w), int((r_ + 1) * w))).resize((size, size), Image.LANCZOS)
    return t_.transpose(Image.ROTATE_180) if rot else t_

def draw_piece(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    n = 3; S = 540 if c.v else 520
    src = Image.new("RGBA", (S, S), (255, 255, 255, 255))
    e = emoji_img(item["emoji"], S * 0.92); src.alpha_composite(e, (int(S / 2 - e.width / 2), int(S / 2 - e.height / 2)))
    if item.get("bg"):
        bgc = Image.new("RGBA", (S, S), tuple(item["bg"]) + (255,)); bgc.alpha_composite(src.copy()); src = bgc
    cx, cy = (c.W / 2, y0 + S / 2 - 30) if c.v else (x0 + 380, (y0 + y1) / 2 + 30)
    pic = src.copy(); pd = ImageDraw.Draw(pic)
    w = S / n; mi = item["missing"]; r_, k = divmod(mi, n)
    hole = (k * w, r_ * w, (k + 1) * w, (r_ + 1) * w)
    pd.rectangle(hole, fill=(40, 40, 60, 255))
    pd.text((hole[0] + w / 2 - 25, hole[1] + w / 2 - 50), "?", font=font(F_BOLD, 90), fill=c.accent)
    frame = Image.new("RGBA", (S + 24, S + 24), (255, 255, 255, 255)); frame.alpha_composite(pic, (12, 12))
    paste(im, frame, cx, cy, eob((t - 0.2) / 0.5) if phase == "ask" else 1)
    opts = item["options"]
    for q, o in enumerate(opts):
        rot = isinstance(o, str) and o.endswith("r"); idx = int(str(o).rstrip("r"))
        ts = 200 if c.v else 190
        tile = _tile(src, idx, n, ts, rot)
        if c.v:
            ox, oy = x0 + (x1 - x0) * (q + 0.5) / len(opts), cy + S / 2 + 200
        else:
            ox, oy = x0 + 1000 + q * 300, (y0 + y1) / 2 + 30
        if phase == "reveal" and q == item["right"]:
            m = eo(pt / 0.8); tx, ty = cx - S / 2 + w * (k + 0.5), cy - S / 2 + w * (r_ + 0.5)
            ox, oy = ox + (tx - ox) * m, oy + (ty - oy) * m
            tile = tile.resize((int(ts + (w - ts) * m), int(ts + (w - ts) * m)))
        s = eob((t - 1.2 - 0.25 * q) / 0.4) if phase == "ask" else 1
        a = 0.4 if (phase == "reveal" and q != item["right"]) else 1
        fr = Image.new("RGBA", (tile.width + 12, tile.height + 12), c.accent + (255,)); fr.alpha_composite(tile, (6, 6))
        paste(im, fr, ox, oy, s, a)
        if not (phase == "reveal" and q == item["right"]):
            _label(d, ox - ts / 2, oy - ts / 2, "ABC"[q], c, r=30, size=40)
    if phase == "reveal":
        return cx, cy
    return c.W / 2, cy

# ---------------------------------------------------------------- Illusion check
def illusion_answer(item):
    dlt = item.get("diff", 0)
    return 2 if dlt == 0 else (0 if dlt > 0 else 1)

def draw_illusion(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    kind = item["kind"]; dlt = item.get("diff", 0)
    a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
    col = (255, 255, 255, int(255 * a))
    cx = c.W / 2 if c.v else x0 + 520
    centers = []
    if kind == "lines":
        L = 420 if c.v else 440
        for k in range(2):
            ln = L * (1 + (dlt * 0.06 if k == 0 else -dlt * 0.06))
            yy = y0 + 70 + k * 240 if c.v else y0 + 200 + k * 260
            xa, xb = cx - ln / 2, cx + ln / 2
            d.line((xa, yy, xb, yy), fill=col, width=12)
            fin = 70
            if k == 0:
                for sx, sgn in ((xa, 1), (xb, -1)):
                    d.line((sx, yy, sx + sgn * fin, yy - fin), fill=col, width=10); d.line((sx, yy, sx + sgn * fin, yy + fin), fill=col, width=10)
            else:
                for sx, sgn in ((xa, -1), (xb, 1)):
                    d.line((sx, yy, sx + sgn * fin, yy - fin), fill=col, width=10); d.line((sx, yy, sx + sgn * fin, yy + fin), fill=col, width=10)
            centers.append((xa, xb, yy))
            _label(d, cx - 330 if c.v else cx - 380, yy, "AB"[k], c)
        if phase == "reveal":
            for k, (xa, xb, yy) in enumerate(centers):
                m = eo(pt / 0.6)
                d.line((xa, yy - 6, xa, yy + 6 + (centers[1][2] - yy if k == 0 else 0) * m), fill=(60, 255, 120), width=6)
                d.line((xb, yy - 6, xb, yy + 6 + (centers[1][2] - yy if k == 0 else 0) * m), fill=(60, 255, 120), width=6)
    else:  # circles (Ebbinghaus)
        R = 55 if c.v else 58
        for k in range(2):
            rr = R * (1 + (dlt * 0.07 if k == 0 else -dlt * 0.07))
            px = (cx - 230 + k * 460) if c.v else (cx - 260 + k * 520)
            py = y0 + 230 if c.v else (y0 + y1) / 2 + 30
            ring_r, ring_n, ring_d = ((rr * 1.5, 6, rr * 2.9) if k == 0 else (rr * 0.38, 8, rr * 1.65))
            for j in range(ring_n):
                an = j * 2 * math.pi / ring_n
                qx, qy = px + ring_d * math.cos(an), py + ring_d * math.sin(an)
                d.ellipse((qx - ring_r, qy - ring_r, qx + ring_r, qy + ring_r), fill=(160, 170, 200, int(255 * a)))
            d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=(255, 150, 60, int(255 * a)))
            centers.append((px, py, rr))
            _label(d, px, py + (265 if c.v else 270), "AB"[k], c)
        if phase == "reveal":
            m = eo(pt / 0.8)
            px, py, rr = centers[0]
            tx, ty, tr = centers[1]
            gx = px + (tx - px) * m
            d.ellipse((gx - rr, py - rr, gx + rr, py + rr), outline=(60, 255, 120), width=8)
    # options
    labels = ["A is bigger", "B is bigger", "Same size"] if kind == "circles" else ["A is longer", "B is longer", "Same length"]
    for k in range(3):
        if c.v:
            ox, oy, ow, oh = c.W / 2, y1 - 250 + k * 122 + (40 if kind == "circles" else 0), 640, 105
        else:
            ox, oy, ow, oh = x0 + 1360, y0 + 140 + k * 170, 460, 130
        s = eob((t - 1.3 - 0.25 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 0.9: fill = (40, 190, 90) if k == illusion_answer(item) else (150, 40, 55)
        d.rounded_rectangle((ox - ow / 2, oy - oh / 2, ox + ow / 2, oy + oh / 2), radius=26, fill=fill, outline=c.accent, width=6)
        f = font(F_BOLD, 50 if c.v else 46); tw = d.textlength(labels[k], font=f)
        d.text((ox - tw / 2 + 20, oy - 34), labels[k], font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
    if phase == "reveal":
        return cx, (y0 + y1) / 2
    return cx, (y0 + y1) / 2

# ---------------------------------------------------------------- Rotate match
def _shape_img(cells, color, cell=60):
    n = 4; im = Image.new("RGBA", (n * cell + 8, n * cell + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for (r_, k) in cells:
        d.rounded_rectangle((4 + k * cell, 4 + r_ * cell, 4 + (k + 1) * cell - 4, 4 + (r_ + 1) * cell - 4), radius=10, fill=color)
    d.ellipse((4 + cells[0][1] * cell + cell * 0.3, 4 + cells[0][0] * cell + cell * 0.3, 4 + cells[0][1] * cell + cell * 0.66, 4 + cells[0][0] * cell + cell * 0.66), fill=(255, 255, 255))
    return im

def draw_rotate(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    col = tuple(item.get("color", [255, 120, 80]))
    base = _shape_img([tuple(x) for x in item["cells"]], col, 70 if c.v else 62)
    oc = (c.W / 2, y0 + 200) if c.v else (x0 + 300, (y0 + y1) / 2 + 30)
    d.rounded_rectangle((oc[0] - base.width / 2 - 30, oc[1] - base.height / 2 - 30, oc[0] + base.width / 2 + 30, oc[1] + base.height / 2 + 30), radius=30, fill=(255, 255, 255, 230))
    rot_now = 0
    if phase == "reveal":
        target = item["opts"][item["right"]][0]
        rot_now = target * eo(pt / 1.0)
    paste(im, base.rotate(-rot_now, expand=True, resample=Image.BICUBIC), oc[0], oc[1], eob((t - 0.2) / 0.5) if phase == "ask" else 1)
    for k, (ang, mirror) in enumerate(item["opts"]):
        img = base.transpose(Image.FLIP_LEFT_RIGHT) if mirror else base
        img = img.rotate(-ang, expand=True, resample=Image.BICUBIC)
        if c.v:
            ox, oy = x0 + (x1 - x0) * (k + 0.5) / 3, y0 + 680
        else:
            ox, oy = x0 + 780 + k * 330, (y0 + y1) / 2 + 30
        bw = 290 if c.v else 290
        s = eob((t - 1.0 - 0.25 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255, 230)
        if phase == "reveal" and pt > 1.0: fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox - bw / 2, oy - bw / 2, ox + bw / 2, oy + bw / 2), radius=30, fill=fill, outline=c.accent, width=6)
        paste(im, img, ox, oy, s * 0.82, 0.5 if (phase == "reveal" and pt > 1.0 and k != item["right"]) else 1)
        _label(d, ox - bw / 2 + 10, oy - bw / 2 + 10, "ABC"[k], c, r=30, size=40)
    if phase == "reveal":
        k = item["right"]
        return (x0 + (x1 - x0) * (k + 0.5) / 3, y0 + 680) if c.v else (x0 + 780 + k * 330, (y0 + y1) / 2 + 30)
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- What's at the bottom (stack)
SHAPE_COLS = {"red": (235, 70, 80), "blue": (70, 140, 240), "green": (70, 200, 110), "yellow": (250, 200, 50), "purple": (170, 100, 230), "orange": (250, 140, 50)}

def _draw_shape(d, kind, color, cx, cy, s, outline=(30, 30, 60)):
    if kind == "circle": d.ellipse((cx - s, cy - s, cx + s, cy + s), fill=color, outline=outline, width=6)
    elif kind == "square": d.rounded_rectangle((cx - s, cy - s, cx + s, cy + s), radius=16, fill=color, outline=outline, width=6)
    elif kind == "triangle": d.polygon([(cx, cy - s * 1.1), (cx + s * 1.1, cy + s * 0.8), (cx - s * 1.1, cy + s * 0.8)], fill=color, outline=outline)
    elif kind == "star":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5; rr = s * (1.15 if i % 2 == 0 else 0.5)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=color, outline=outline)

def draw_stack(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    shapes = item["shapes"]  # bottom -> top: [kind, color, dx, dy, size]
    cx, cy = (c.W / 2, y0 + 300) if c.v else (x0 + 420, (y0 + y1) / 2 + 30)
    sc = 1.0 if c.v else 0.9
    n = len(shapes)
    for i, (kind, colname, dx, dy, s) in enumerate(shapes):
        lift = 0
        if phase == "reveal":
            order_from_top = n - 1 - i
            if i != 0: lift = eo((pt - order_from_top * 0.35) / 0.35)
        ap = eob((t - 0.2 - 0.25 * i) / 0.35) if phase == "ask" else 1
        if ap < 0.05: continue
        if lift > 0.6: continue
        px, py = cx + dx * sc, cy + dy * sc - lift * 500
        _draw_shape(d, kind, SHAPE_COLS[colname], px, py, s * sc * ap)
    opts = item["options"]
    for k, (kind, colname) in enumerate(opts):
        if c.v:
            ox, oy = x0 + (x1 - x0) * (k + 0.5) / len(opts), y0 + 720
        else:
            ox, oy = x0 + 950 + k * 300, (y0 + y1) / 2 + 30
        bw = 250
        s = eob((t - 1.6 - 0.25 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255, 230)
        if phase == "reveal" and pt > 0.35 * n: fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox - bw / 2, oy - bw / 2, ox + bw / 2, oy + bw / 2), radius=30, fill=fill, outline=c.accent, width=6)
        _draw_shape(d, kind, SHAPE_COLS[colname], ox, oy + 10, 70 * s)
        _label(d, ox - bw / 2 + 10, oy - bw / 2 + 10, "ABC"[k], c, r=30, size=40)
    if phase == "reveal":
        return cx, cy
    return cx, cy

# ---------------------------------------------------------------- Quick count
def draw_count(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    rnd = _rnd.Random(item.get("seed", 1))
    objs = [item["target"]] * item["n"] + [rnd.choice(item["others"]) for _ in range(item["m"])]
    rnd.shuffle(objs)
    bx = (x0 + 20, y0 - 20, x1 - 20, y0 + 470) if c.v else (x0 + 40, y0 + 40, x0 + 940, y1 - 20)
    cols, rows = (5, 4) if c.v else (6, 4)
    cells = [(r_, k) for r_ in range(rows) for k in range(cols)]; rnd.shuffle(cells)
    cw, ch = (bx[2] - bx[0]) / cols, (bx[3] - bx[1]) / rows
    show = phase == "ask" and 0.5 < t < 2.7 or phase == "reveal"
    d.rounded_rectangle(bx, radius=40, fill=(255, 255, 255, 230))
    hl = 0
    for i, em in enumerate(objs[:len(cells)]):
        r_, k = cells[i]
        px = bx[0] + cw * (k + 0.5) + rnd.uniform(-cw * 0.15, cw * 0.15); py = bx[1] + ch * (r_ + 0.5) + rnd.uniform(-ch * 0.12, ch * 0.12)
        if show:
            a = 0.3 if (phase == "reveal" and em != item["target"]) else 1
            paste(im, emoji_img(em, min(cw, ch) * 0.7), px, py, 1, a)
            if phase == "reveal" and em == item["target"]:
                hl += 1
                if hl <= int(item["n"] * cl(pt / 1.4)):
                    d.ellipse((px - 50, py - 50, px + 50, py + 50), outline=(60, 255, 120), width=7)
    if not show:
        mx, my = (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2
        if phase == "ask" and t <= 0.5:
            f = font(F_BOLD, 80); txt = "READY?"; tw = d.textlength(txt, font=f); d.text((mx - tw / 2, my - 50), txt, font=f, fill=(30, 30, 60))
        else:
            f = font(F_BOLD, 200); tw = d.textlength("?", font=f); d.text((mx - tw / 2, my - 130), "?", font=f, fill=(30, 30, 60))
    # target hint
    hx, hy = (c.W / 2, bx[3] + 75) if c.v else (x0 + 1250, y0 + 90)
    paste(im, emoji_img(item["target"], 110), hx, hy)
    opts = item["options"]
    for k, o in enumerate(opts):
        if c.v:
            ox, oy, ow, oh = x0 + (x1 - x0) * (k + 0.5) / 3, bx[3] + 240, 260, 150
        else:
            ox, oy, ow, oh = x0 + 1250, y0 + 260 + k * 190, 340, 150
        s = eob((t - 2.8 - 0.2 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 1.5: fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox - ow / 2, oy - oh / 2, ox + ow / 2, oy + oh / 2), radius=30, fill=fill, outline=c.accent, width=6)
        f = font(F_BOLD, 90); tw = d.textlength(o, font=f)
        d.text((ox - tw / 2 + 20, oy - 62), o, font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
        _label(d, ox - ow / 2 + 40, oy, "ABC"[k], c, r=30, size=40)
    return ((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2)

# ---------------------------------------------------------------- Remember the order
def draw_order(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    seq = item["seq"]; n = len(seq)
    rowy = y0 + 140 if c.v else y0 + 160
    gap = (x1 - x0) / n
    sz = min(170, gap * 0.75)
    for i, em in enumerate(seq):
        cx = x0 + gap * (i + 0.5)
        box = (cx - sz * 0.65, rowy - sz * 0.65, cx + sz * 0.65, rowy + sz * 0.65)
        d.rounded_rectangle(box, radius=26, fill=(255, 255, 255, 230))
        f = font(F_BOLD, 40); L = str(i + 1); tw = d.textlength(L, font=f)
        d.text((cx - tw / 2, box[3] + 10), L, font=f, fill=c.accent)
        if phase == "ask":
            ti = 0.5 + i * 0.75
            if ti <= t < 0.5 + n * 0.75 + 0.6:
                paste(im, emoji_img(em, sz), cx, rowy, eob((t - ti) / 0.3))
            elif t >= 0.5 + n * 0.75 + 0.6:
                qf = font(F_BOLD, sz * 0.7); tw = d.textlength("?", font=qf); d.text((cx - tw / 2, rowy - sz * 0.5), "?", font=qf, fill=(30, 30, 60))
        elif phase == "count":
            qf = font(F_BOLD, sz * 0.7); tw = d.textlength("?", font=qf); d.text((cx - tw / 2, rowy - sz * 0.5), "?", font=qf, fill=(30, 30, 60))
        else:
            paste(im, emoji_img(em, sz), cx, rowy, 1, 1 if i + 1 == item["ask_pos"] else 0.35)
            if i + 1 == item["ask_pos"]: glow_box(im, box, r=26)
    opts = item["options"]
    for k, o in enumerate(opts):
        if c.v:
            ox, oy = x0 + (x1 - x0) * (k + 0.5) / 3, y0 + 560
        else:
            ox, oy = x0 + (x1 - x0) * (k + 0.5) / 3, y0 + 480
        bw = 250 if c.v else 230
        s = eob((t - (0.5 + n * 0.75 + 0.8) - 0.2 * k) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255, 230)
        if phase == "reveal" and pt > 0.5: fill = (40, 190, 90) if k == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox - bw / 2, oy - bw / 2, ox + bw / 2, oy + bw / 2), radius=30, fill=fill, outline=c.accent, width=6)
        paste(im, emoji_img(o, bw * 0.55), ox, oy + 10, s)
        _label(d, ox - bw / 2 + 10, oy - bw / 2 + 10, "ABC"[k], c, r=30, size=40)
    if phase == "reveal":
        return x0 + gap * (item["ask_pos"] - 0.5), rowy
    return c.W / 2, (y0 + y1) / 2

DRAW.update({"jar": draw_jar, "fit": draw_fit, "twins": draw_twins, "gears": draw_gears, "piece": draw_piece,
             "illusion": draw_illusion, "rotate": draw_rotate, "stack": draw_stack, "count": draw_count, "order": draw_order})

_old_min_ask = min_ask
def min_ask(item):
    t_ = item.get("type")
    if t_ == "count": return 3.4
    if t_ == "order": return 0.5 + 0.75 * len(item["seq"]) + 1.4
    return _old_min_ask(item)

# ================================================================ REPLACEMENTS (v2)
# ---------------------------------------------------------------- Count the blocks (isometric)
def blocks_total(item): return sum(sum(r) for r in item["heights"])

def draw_blocks(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    H = item["heights"]; R, C = len(H), len(H[0])
    s = 95 if c.v else 85
    ox = c.W / 2 if c.v else x0 + 420
    oy = y0 + (330 if c.v else 330)
    def iso(gx, gy, gz):
        return ox + (gx - gy) * s * 0.87, oy + (gx + gy) * s * 0.5 - gz * s
    cols = [(250, 190, 70), (240, 120, 90), (110, 180, 240), (130, 210, 130)]
    k = 0
    order = sorted([(r_, q) for r_ in range(R) for q in range(C)], key=lambda p: p[0] + p[1])
    for (r_, q) in order:
        for z in range(H[r_][q]):
            a = eob((t - 0.3 - 0.08 * k) / 0.3) if phase == "ask" else 1
            k += 1
            if a < 0.05: continue
            base = cols[(r_ + q + z) % 4]
            top = [iso(q, r_, z + 1), iso(q + 1, r_, z + 1), iso(q + 1, r_ + 1, z + 1), iso(q, r_ + 1, z + 1)]
            left = [iso(q, r_ + 1, z + 1), iso(q + 1, r_ + 1, z + 1), iso(q + 1, r_ + 1, z), iso(q, r_ + 1, z)]
            right = [iso(q + 1, r_, z + 1), iso(q + 1, r_ + 1, z + 1), iso(q + 1, r_ + 1, z), iso(q + 1, r_, z)]
            dy = (1 - a) * -200
            sh = lambda P: [(x, y + dy) for x, y in P]
            d.polygon(sh(left), fill=tuple(int(v * 0.75) for v in base), outline=(30, 30, 60))
            d.polygon(sh(right), fill=tuple(int(v * 0.6) for v in base), outline=(30, 30, 60))
            d.polygon(sh(top), fill=base, outline=(30, 30, 60))
            if phase == "reveal" and z == H[r_][q] - 1 and pt > 0.3:
                cx_ = sum(p[0] for p in top) / 4; cy_ = sum(p[1] for p in top) / 4
                f = font(F_BOLD, 46); L = str(H[r_][q]); tw = d.textlength(L, font=f)
                d.ellipse((cx_ - 30, cy_ - 30, cx_ + 30, cy_ + 30), fill=(255, 255, 255))
                d.text((cx_ - tw / 2, cy_ - 32), L, font=f, fill=(30, 30, 60))
    opts = item["options"]
    for q, o in enumerate(opts):
        if c.v: ox_, oy_, ow, oh = x0 + (x1 - x0) * (q + 0.5) / 3, y1 - 60, 260, 150
        else: ox_, oy_, ow, oh = x0 + 1250, y0 + 170 + q * 190, 330, 150
        sc = eob((t - 1.4 - 0.2 * q) / 0.4) if phase == "ask" else 1
        if sc < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 0.9: fill = (40, 190, 90) if q == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox_ - ow / 2, oy_ - oh / 2, ox_ + ow / 2, oy_ + oh / 2), radius=30, fill=fill, outline=c.accent, width=6)
        f = font(F_BOLD, 90); tw = d.textlength(o, font=f)
        d.text((ox_ - tw / 2 + 20, oy_ - 62), o, font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
        _label(d, ox_ - ow / 2 + 40, oy_, "ABC"[q], c, r=30, size=40)
    return ox, oy

# ---------------------------------------------------------------- Connect the dots
DOT_SHAPES = {
 "star": [(0.5, 0.0), (0.62, 0.36), (1.0, 0.38), (0.7, 0.6), (0.81, 1.0), (0.5, 0.76), (0.19, 1.0), (0.3, 0.6), (0.0, 0.38), (0.38, 0.36)],
 "house": [(0.1, 1.0), (0.1, 0.45), (0.0, 0.45), (0.5, 0.0), (1.0, 0.45), (0.9, 0.45), (0.9, 1.0), (0.6, 1.0), (0.6, 0.7), (0.4, 0.7), (0.4, 1.0)],
 "fish": [(0.0, 0.5), (0.2, 0.25), (0.5, 0.15), (0.75, 0.3), (1.0, 0.1), (0.92, 0.5), (1.0, 0.9), (0.75, 0.7), (0.5, 0.85), (0.2, 0.75)],
 "heart": [(0.5, 0.25), (0.65, 0.05), (0.88, 0.05), (1.0, 0.25), (0.95, 0.5), (0.5, 1.0), (0.05, 0.5), (0.0, 0.25), (0.12, 0.05), (0.35, 0.05)],
 "boat": [(0.0, 0.62), (1.0, 0.62), (0.82, 0.95), (0.18, 0.95), (0.0, 0.62), (0.48, 0.62), (0.48, 0.0), (0.9, 0.5), (0.48, 0.5)],
 "arrow": [(0.0, 0.38), (0.6, 0.38), (0.6, 0.12), (1.0, 0.5), (0.6, 0.88), (0.6, 0.62), (0.0, 0.62)],
 "tree": [(0.5, 0.0), (0.8, 0.35), (0.65, 0.35), (0.92, 0.7), (0.58, 0.7), (0.58, 1.0), (0.42, 1.0), (0.42, 0.7), (0.08, 0.7), (0.35, 0.35), (0.2, 0.35)],
 "rocket": [(0.5, 0.0), (0.68, 0.25), (0.68, 0.7), (0.88, 0.95), (0.62, 0.85), (0.38, 0.85), (0.12, 0.95), (0.32, 0.7), (0.32, 0.25)],
 "crown": [(0.0, 1.0), (0.0, 0.2), (0.25, 0.55), (0.5, 0.05), (0.75, 0.55), (1.0, 0.2), (1.0, 1.0)],
 "cat": [(0.15, 0.0), (0.38, 0.28), (0.62, 0.28), (0.85, 0.0), (0.92, 0.45), (0.8, 0.85), (0.5, 1.0), (0.2, 0.85), (0.08, 0.45)],
 "kite": [(0.5, 0.0), (0.9, 0.4), (0.5, 0.75), (0.1, 0.4), (0.5, 0.0), (0.5, 0.75), (0.45, 0.85), (0.55, 0.92), (0.48, 1.0)],
 "umbrella": [(0.0, 0.45), (0.15, 0.18), (0.5, 0.0), (0.85, 0.18), (1.0, 0.45), (0.52, 0.45), (0.52, 0.9), (0.42, 1.0), (0.34, 0.9)],
}
def draw_dots(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    pts = DOT_SHAPES[item["shape"]]
    S = 520 if c.v else 480
    ox, oy = (c.W / 2 - S / 2, y0 + 20) if c.v else (x0 + 120, y0 + 60)
    P = [(ox + x * S, oy + y * S) for x, y in pts]
    closed = item["shape"] not in ("boat", "kite", "umbrella")
    seq = P + ([P[0]] if closed else [])
    if phase == "reveal":
        n = len(seq) - 1; prog = cl(pt / 1.6) * n
        k = int(prog); fr = prog - k
        line = seq[:k + 1]
        if k < n: line = line + [(seq[k][0] + (seq[k + 1][0] - seq[k][0]) * fr, seq[k][1] + (seq[k + 1][1] - seq[k][1]) * fr)]
        if pt > 1.7 and closed:
            ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(ov).polygon(P, fill=c.accent + (120,)); im.alpha_composite(ov); d = ImageDraw.Draw(im)
        if len(line) > 1: d.line(line, fill=(60, 255, 120), width=12, joint="curve")
    f = font(F_BOLD, 34)
    for i, (x, y) in enumerate(P):
        a = eob((t - 0.3 - 0.1 * i) / 0.3) if phase == "ask" else 1
        if a < 0.05: continue
        r = 14 * a
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255))
        d.text((x + 16, y - 40), str(i + 1), font=f, fill=c.accent)
    opts = item["options"]
    for q, o in enumerate(opts):
        if c.v: ox_, oy_, ow, oh = x0 + (x1 - x0) * (q + 0.5) / 3, y1 - 60, 300, 140
        else: ox_, oy_, ow, oh = x0 + 1250, y0 + 170 + q * 190, 380, 150
        sc = eob((t - 1.6 - 0.2 * q) / 0.4) if phase == "ask" else 1
        if sc < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 1.0: fill = (40, 190, 90) if q == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox_ - ow / 2, oy_ - oh / 2, ox_ + ow / 2, oy_ + oh / 2), radius=30, fill=fill, outline=c.accent, width=6)
        f2 = font(F_BOLD, 52)
        sz = 52
        while d.textlength(o, font=f2) > ow - 100: sz -= 4; f2 = font(F_BOLD, sz)
        tw = d.textlength(o, font=f2)
        d.text((ox_ - tw / 2 + 25, oy_ - sz * 0.68), o, font=f2, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
        _label(d, ox_ - ow / 2 + 40, oy_, "ABC"[q], c, r=30, size=40)
    return ox + S / 2, oy + S / 2

# ---------------------------------------------------------------- Colour trap
INKS = {"red": (240, 60, 70), "blue": (60, 130, 245), "green": (60, 200, 100), "yellow": (250, 210, 40), "purple": (170, 90, 240), "orange": (250, 140, 40), "pink": (255, 110, 180)}
def draw_colortrap(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    cx, cy = (c.W / 2, y0 + 200) if c.v else (x0 + 460, (y0 + y1) / 2 - 20)
    box = (cx - (440 if c.v else 420), cy - 150, cx + (440 if c.v else 420), cy + 150)
    d.rounded_rectangle(box, radius=40, fill=(250, 250, 250))
    a = eob((t - 0.3) / 0.4) if phase == "ask" else 1
    lay = Image.new("RGBA", (int(box[2] - box[0]), 300), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    text_center(ld, item["word"].upper(), lay.width / 2, 40, 190, fill=INKS[item["ink"]], maxw=lay.width - 60)
    paste(im, lay, cx, cy, a)
    opts = item["options"]
    for q, o in enumerate(opts):
        if c.v: ox_, oy_, ow, oh = c.W / 2, y0 + 470 + q * 160, 640, 130
        else: ox_, oy_, ow, oh = x0 + 1250, y0 + 160 + q * 190, 420, 150
        sc = eob((t - 1.0 - 0.2 * q) / 0.4) if phase == "ask" else 1
        if sc < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal": fill = (40, 190, 90) if q == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox_ - ow / 2, oy_ - oh / 2, ox_ + ow / 2, oy_ + oh / 2), radius=30, fill=fill, outline=c.accent, width=6)
        f = font(F_BOLD, 60); tw = d.textlength(o.upper(), font=f)
        d.text((ox_ - tw / 2 + 20, oy_ - 42), o.upper(), font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
        _label(d, ox_ - ow / 2 + 45, oy_, "ABC"[q], c, r=32, size=42)
    if phase == "reveal":
        glow_box(im, box, color=INKS[item["ink"]], r=40)
    return cx, cy

# ---------------------------------------------------------------- Balance the scale
def balance_answer(item):
    (a_e, a_n), (b_e, b_n) = item["rule"]          # a_n of A == b_n of B
    q_n = item["q_n"]                              # q_n of B on the left
    return q_n * a_n / b_n                         # how many A balance it

def _scale(d, im, cx, cy, w, left, right, tilt, c, qmark=False):
    ang = math.radians(tilt)
    dx, dy = math.cos(ang) * w / 2, math.sin(ang) * w / 2
    d.polygon([(cx - 55, cy + 200), (cx + 55, cy + 200), (cx, cy)], fill=(150, 160, 180))
    d.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=(200, 210, 230), width=16)
    for side, items, sx, sy in ((-1, left, cx - dx, cy - dy), (1, right, cx + dx, cy + dy)):
        d.rounded_rectangle((sx - 160, sy - 16, sx + 160, sy + 8), radius=8, fill=(230, 200, 140))
        if qmark and side == 1:
            f = font(F_BOLD, 90); tw = d.textlength("?", font=f)
            d.rounded_rectangle((sx - 60, sy - 140, sx + 60, sy - 18), radius=20, fill=(255, 255, 255, 60), outline=c.accent, width=6)
            d.text((sx - tw / 2, sy - 140), "?", font=f, fill=c.accent)
            continue
        em, n = items
        size = 100 if n <= 3 else 80
        per_row = 3
        for i in range(n):
            r_, k = divmod(i, per_row)
            cnt = min(per_row, n - r_ * per_row)
            px = sx + (k - (cnt - 1) / 2) * size * 1.0
            py = sy - size / 2 - 14 - r_ * size * 0.9
            paste(im, emoji_img(em, size), px, py)

def draw_balance(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    (a_e, a_n), (b_e, b_n) = item["rule"]
    w = 680 if c.v else 520
    if c.v: c1, c2 = (c.W / 2, y0 + 190), (c.W / 2, y0 + 560)
    else: c1, c2 = (x0 + 330, y0 + 330), (x0 + 900, y0 + 330)
    a = eob((t - 0.2) / 0.4) if phase == "ask" else 1
    if a > 0.05:
        _scale(d, im, c1[0], c1[1], w, (a_e, a_n), (b_e, b_n), 0, c)
        f = font(F_BOLD, 90); tw = d.textlength("=", font=f)
        d.text((c1[0] - tw / 2, c1[1] - 150), "=", font=f, fill=c.accent, stroke_width=5, stroke_fill=(20, 10, 40))
    a2 = eob((t - 1.2) / 0.4) if phase == "ask" else 1
    if a2 > 0.05:
        ans = int(balance_answer(item))
        if phase == "reveal" and pt > 0.3:
            tilt = -8 * (1 - eo((pt - 0.3) / 0.6))
            _scale(d, im, c2[0], c2[1], w, (b_e, item["q_n"]), (a_e, ans), tilt, c)
        else:
            _scale(d, im, c2[0], c2[1], w, (b_e, item["q_n"]), None, -8, c, qmark=True)
    opts = item["options"]
    for q, o in enumerate(opts):
        if c.v: ox_, oy_, ow, oh = x0 + (x1 - x0) * (q + 0.5) / 3, y1 - 30, 260, 140
        else: ox_, oy_, ow, oh = x0 + 1380, y0 + 170 + q * 190, 300, 150
        sc = eob((t - 2.0 - 0.2 * q) / 0.4) if phase == "ask" else 1
        if sc < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 0.9: fill = (40, 190, 90) if q == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox_ - ow / 2, oy_ - oh / 2, ox_ + ow / 2, oy_ + oh / 2), radius=30, fill=fill, outline=c.accent, width=6)
        e = emoji_img(a_e, 70)
        f = font(F_BOLD, 80); tw = d.textlength(o, font=f)
        d.text((ox_ - tw / 2 - 10, oy_ - 56), o, font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
        paste(im, e, ox_ + 70, oy_)
        _label(d, ox_ - ow / 2 + 40, oy_ - oh / 2 + 36, "ABC"[q], c, r=28, size=38)
    return c2

# ---------------------------------------------------------------- Mini maze (3 separate regions)
def maze_build(item, Wc=7, Hc=8):
    rnd = _rnd.Random(item["seed"])
    seeds = [(0, 1), (0, Wc // 2), (0, Wc - 2)]
    region = [[-1] * Wc for _ in range(Hc)]
    fronts = []
    for k, (r_, q) in enumerate(seeds):
        region[r_][q] = k; fronts.append([(r_, q)])
    left = Wc * Hc - 3
    while left:
        k = rnd.randrange(3)
        if not fronts[k]: continue
        r_, q = rnd.choice(fronts[k])
        nb = [(r_ + a, q + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)) if 0 <= r_ + a < Hc and 0 <= q + b < Wc and region[r_ + a][q + b] < 0]
        if not nb:
            fronts[k].remove((r_, q)); continue
        n = rnd.choice(nb); region[n[0]][n[1]] = k; fronts[k].append(n); left -= 1
    # spanning tree per region
    opened = set(); visited = set()
    for k, s in enumerate(seeds):
        stack = [s]; visited.add(s)
        while stack:
            cur = stack[-1]
            nb = [(cur[0] + a, cur[1] + b) for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= cur[0] + a < Hc and 0 <= cur[1] + b < Wc and (cur[0] + a, cur[1] + b) not in visited and region[cur[0] + a][cur[1] + b] == k]
            if not nb: stack.pop(); continue
            n = rnd.choice(nb); opened.add(frozenset((cur, n))); visited.add(n); stack.append(n)
    goal = (Hc - 1, item.get("goal_col", Wc // 2))
    win = region[goal[0]][goal[1]]
    # path from seed to goal
    prev = {seeds[win]: None}; queue = [seeds[win]]
    while queue:
        cur = queue.pop(0)
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (cur[0] + a, cur[1] + b)
            if n not in prev and frozenset((cur, n)) in opened: prev[n] = cur; queue.append(n)
    path = []; cur = goal
    while cur: path.append(cur); cur = prev.get(cur)
    return region, opened, seeds, goal, win, path[::-1]

def maze_answer(item): return maze_build(item)[4]

def draw_maze(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    Wc, Hc = 7, 8
    region, opened, seeds, goal, win, path = maze_build(item, Wc, Hc)
    cell = 100 if c.v else 72
    ox = c.W / 2 - Wc * cell / 2 if c.v else x0 + 120
    oy = y0 + 70 if c.v else y0 + 60
    d.rectangle((ox, oy, ox + Wc * cell, oy + Hc * cell), fill=(255, 255, 255, 235))
    a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
    wc = (30, 30, 60, int(255 * a))
    for r_ in range(Hc):
        for q in range(Wc):
            X, Y = ox + q * cell, oy + r_ * cell
            if q + 1 < Wc and frozenset(((r_, q), (r_, q + 1))) not in opened:
                d.line((X + cell, Y, X + cell, Y + cell), fill=wc, width=8)
            if r_ + 1 < Hc and frozenset(((r_, q), (r_ + 1, q))) not in opened:
                d.line((X, Y + cell, X + cell, Y + cell), fill=wc, width=8)
    # outer walls with entrances at seed tops
    for q in range(Wc):
        if (0, q) not in seeds: d.line((ox + q * cell, oy, ox + (q + 1) * cell, oy), fill=(30, 30, 60), width=10)
        d.line((ox + q * cell, oy + Hc * cell, ox + (q + 1) * cell, oy + Hc * cell), fill=(30, 30, 60), width=10)
    d.line((ox, oy, ox, oy + Hc * cell), fill=(30, 30, 60), width=10); d.line((ox + Wc * cell, oy, ox + Wc * cell, oy + Hc * cell), fill=(30, 30, 60), width=10)
    for k, (r_, q) in enumerate(seeds):
        sx = ox + (q + 0.5) * cell
        paste(im, emoji_img(item["starters"][k], cell * 0.8), sx, oy - cell * 0.55)
        f = font(F_BOLD, 40); L = "ABC"[k]; tw = d.textlength(L, font=f)
        d.text((sx - cell * 0.55 - tw, oy - cell * 0.9), L, font=f, fill=c.accent)
    gx, gy = ox + (goal[1] + 0.5) * cell, oy + (goal[0] + 0.5) * cell
    paste(im, emoji_img(item["prize"], cell * 0.7), gx, gy)
    if phase == "reveal":
        P = [(ox + (q + 0.5) * cell, oy + (r_ + 0.5) * cell) for r_, q in path]
        P = [(P[0][0], oy - 10)] + P
        k = max(2, int(len(P) * cl(pt / 1.8)))
        d.line(P[:k], fill=(60, 220, 120), width=14, joint="curve")
        return gx, gy
    return c.W / 2, (y0 + y1) / 2

DRAW.update({"blocks": draw_blocks, "dots": draw_dots, "colortrap": draw_colortrap, "balance": draw_balance, "maze": draw_maze})

# ================================================================ CANDIDATES (v3)
def _opt_row(c, d, item, phase, pt, t, labels, y_v, start=1.4, h_x=None, emojis=None):
    """generic 3-4 option boxes with text labels. returns rects"""
    if OPT is not None and c.v: d = ImageDraw.Draw(OPT)
    x0, y0, x1, y1 = area(c)
    n = len(labels); rects = []
    for q, o in enumerate(labels):
        if c.v: ox_, oy_, ow, oh = x0 + (x1 - x0) * (q + 0.5) / n, y_v, (x1 - x0) / n - 40, 140
        else: ox_, oy_, ow, oh = (h_x or x0 + 1300), y0 + 150 + q * 180, 360, 140
        rects.append((ox_, oy_))
        sc = eob((t - start - 0.2 * q) / 0.4) if phase == "ask" else 1
        if sc < 0.05: continue
        fill = (255, 255, 255)
        if phase == "reveal" and pt > 0.6: fill = (40, 190, 90) if q == item["right"] else (150, 40, 55)
        from engine import soft_shadow
        try: soft_shadow(d._image, (ox_ - ow / 2, oy_ - oh / 2, ox_ + ow / 2, oy_ + oh / 2), 28, off=8, blur=10, alpha=60)
        except Exception: pass
        d.rounded_rectangle((ox_ - ow / 2, oy_ - oh / 2, ox_ + ow / 2, oy_ + oh / 2), radius=28, fill=fill, outline=(255, 255, 255) if fill != (255, 255, 255) else (230, 232, 245), width=3)
        sz = 70; f = font(F_BOLD, sz)
        while d.textlength(o, font=f) > ow - 90 and sz > 30: sz -= 4; f = font(F_BOLD, sz)
        tw = d.textlength(o, font=f)
        d.text((ox_ - tw / 2 + 20, oy_ - sz * 0.68), o, font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
        _label(d, ox_ - ow / 2 + 38, oy_, "ABCD"[q], c, r=28, size=38)
    return rects

# ---------------------------------------------------------------- Spot the difference
def draw_spotdiff(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    sc = item["scene"]; n = 4 if len(sc) >= 16 else 3
    cell = (95 if n == 4 else 120) if c.v else (88 if n == 4 else 110)
    pw = cell * n + 40
    gap = pw + (40 if c.v else 60)
    if c.v: cell = (c.W - 120) / (2 * n) - 12; pw = cell * n + 24; gap = pw + 24
    panels = [(c.W / 2 - gap / 2, y0 + 300), (c.W / 2 + gap / 2, y0 + 300)] if c.v else [(c.W / 2 - gap / 2, (y0 + y1) / 2 + 30), (c.W / 2 + gap / 2, (y0 + y1) / 2 + 30)]
    hit = None
    for p, (px, py) in enumerate(panels):
        a = eob((t - 0.2 - 0.3 * p) / 0.4) if phase == "ask" else 1
        if a < 0.05: continue
        d.rounded_rectangle((px - pw / 2, py - pw / 2, px + pw / 2, py + pw / 2), radius=30, fill=(255, 255, 255))
        f = font(F_BOLD, 40); L = "AB"[p]; d.text((px - pw / 2 + 14, py - pw / 2 + 4), L, font=f, fill=c.accent)
        for i, e in enumerate(sc):
            r_, k = divmod(i, n)
            em = item["alt"] if (p == 1 and i == item["diff"]) else e
            cx, cy = px - (n - 1) * cell / 2 + k * cell, py - (n - 1) * cell / 2 + r_ * cell
            paste(im, emoji_img(em, cell * 0.72), cx, cy, a)
            if phase == "reveal" and i == item["diff"]:
                rr = cell * 0.55; d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(60, 255, 120), width=10); hit = (cx, cy)
    return hit or (c.W / 2, (y0 + y1) / 2)

# ---------------------------------------------------------------- Odd colour out
def draw_oddcolor(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    cols, rows = (5, 6) if c.v else (9, 4)
    cell = min((x1 - x0) / cols, (y1 - y0 - 40) / rows) * 0.92
    ox = c.W / 2 - cols * cell / 2; oy = y0 + 20 if c.v else y0 + 70
    base = tuple(item["color"]); dl = item.get("delta", 22)
    odd = tuple(max(0, min(255, v + dl)) for v in base)
    pr, pc = item["pos"]; pr %= rows; pc %= cols
    a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
    for r_ in range(rows):
        for k in range(cols):
            col = odd if (r_, k) == (pr, pc) else base
            g = 10
            d.rounded_rectangle((ox + k * cell + g, oy + r_ * cell + g, ox + (k + 1) * cell - g, oy + (r_ + 1) * cell - g), radius=18, fill=col + (int(255 * a),))
    cx, cy = ox + (pc + 0.5) * cell, oy + (pr + 0.5) * cell
    if phase == "reveal":
        rr = cell * (0.62 + 0.06 * math.sin(pt * 6))
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(255, 255, 255), width=12)
    return cx, cy

# ---------------------------------------------------------------- Which clock is different
def _clock(size, h, m, col=(255, 255, 255)):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    r = size / 2 - 6; cx = cy = size / 2
    d.ellipse((6, 6, size - 6, size - 6), fill=col, outline=(30, 30, 60), width=8)
    for i in range(12):
        a = i * math.pi / 6; r1 = r * (0.8 if i % 3 else 0.72)
        d.line((cx + r1 * math.sin(a), cy - r1 * math.cos(a), cx + r * 0.9 * math.sin(a), cy - r * 0.9 * math.cos(a)), fill=(30, 30, 60), width=5)
    am = m * math.pi / 30; ah = (h % 12 + m / 60) * math.pi / 6
    d.line((cx, cy, cx + r * 0.5 * math.sin(ah), cy - r * 0.5 * math.cos(ah)), fill=(30, 30, 60), width=12)
    d.line((cx, cy, cx + r * 0.75 * math.sin(am), cy - r * 0.75 * math.cos(am)), fill=(230, 60, 80), width=8)
    d.ellipse((cx - 10, cy - 10, cx + 10, cy + 10), fill=(30, 30, 60))
    return im

def draw_clocks(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    n = 4; size = 330 if c.v else 300
    pos = [(c.W / 2 - 220, y0 + 200), (c.W / 2 + 220, y0 + 200), (c.W / 2 - 220, y0 + 600), (c.W / 2 + 220, y0 + 600)] if c.v else \
          [(x0 + 220 + i * 420, (y0 + y1) / 2 + 40) for i in range(4)]
    for i, (px, py) in enumerate(pos):
        hh, mm = item["odd_time"] if i == item["odd"] else item["time"]
        s = eob((t - 0.3 - 0.2 * i) / 0.4) if phase == "ask" else 1
        a = 0.4 if (phase == "reveal" and i != item["odd"]) else 1
        paste(im, _clock(size, hh, mm), px, py, s, a)
        _label(d, px - size * 0.45, py - size * 0.45, "ABCD"[i], c, r=32, size=42)
    if phase == "reveal":
        px, py = pos[item["odd"]]; glow_box(im, (px - size / 2 - 10, py - size / 2 - 10, px + size / 2 + 10, py + size / 2 + 10), r=size // 2)
        return px, py
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Missing number
def draw_missingnum(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    rnd = _rnd.Random(item.get("seed", 1)); n = item["n"]
    nums = [k for k in range(1, n + 1)]; rnd.shuffle(nums)
    cols, rows = (4, 5) if c.v else (5, 4)
    cell = 132 if c.v else 120
    ox = c.W / 2 - cols * cell / 2 if c.v else x0 + 80; oy = y0 if c.v else y0 + 80
    d.rounded_rectangle((ox - 20, oy - 20, ox + cols * cell + 20, oy + rows * cell + 20), radius=30, fill=(255, 255, 255, 235))
    f = font(F_BOLD, 58 if c.v else 54)
    a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
    for i, k in enumerate(nums):
        r_, q = divmod(i, cols)
        cx, cy = ox + (q + 0.5) * cell, oy + (r_ + 0.5) * cell
        if k == item["missing"]:
            if phase == "reveal":
                d.ellipse((cx - 55, cy - 55, cx + 55, cy + 55), fill=(40, 190, 90))
                tw = d.textlength(str(k), font=f); d.text((cx - tw / 2, cy - 44), str(k), font=f, fill=(255, 255, 255))
            else:
                tw = d.textlength("?", font=f); d.text((cx - tw / 2, cy - 44), "?", font=f, fill=c.accent)
            continue
        col = CANDY[k % 6]
        tw = d.textlength(str(k), font=f); d.text((cx - tw / 2, cy - 44), str(k), font=f, fill=tuple(int(v * 0.75) for v in col) + (int(255 * a),))
    _opt_row(c, d, item, phase, pt, t, item["options"], y1 - 20, 1.4)
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Memory grid
def draw_memgrid(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    n = int(item.get("n", 3))
    cell = (230 if c.v else 190) * 3 / n
    ox = c.W / 2 - n * cell / 2 if c.v else x0 + 120; oy = y0 + 20 if c.v else y0 + 70
    seq = item["seq"]; step = 0.65
    lit = None
    if phase == "ask":
        k = int((t - 0.6) / step)
        if 0 <= k < len(seq) and ((t - 0.6) % step) < step * 0.75: lit = seq[k]
    f = font(F_BOLD, 60 if n == 3 else 48)
    for i in range(n * n):
        r_, q = divmod(i, n)
        box = (ox + q * cell + 10, oy + r_ * cell + 10, ox + (q + 1) * cell - 10, oy + (r_ + 1) * cell - 10)
        fill = (255, 255, 255, 220)
        if lit == i: fill = c.accent + (255,)
        if phase == "reveal" and i == seq[-1]: fill = (40, 190, 90, 255)
        d.rounded_rectangle(box, radius=24, fill=fill)
        L = str(i + 1); tw = d.textlength(L, font=f)
        d.text(((box[0] + box[2]) / 2 - tw / 2, (box[1] + box[3]) / 2 - f.size * 0.72), L, font=f, fill=(30, 30, 60) if fill[:3] != (40, 190, 90) else (255, 255, 255))
    if phase == "reveal":
        r_, q = divmod(seq[-1], n); return ox + (q + 0.5) * cell, oy + (r_ + 0.5) * cell
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Count the triangles
def triangles_total(item): return (item.get("h", 0) + 1) * (item["k"] + 1) * (item["k"] + 2) // 2

def draw_triangles(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    S = 560 if c.v else 520
    ax, ay = (c.W / 2, y0 + 30) if c.v else (x0 + 400, y0 + 80)
    bl, br = (ax - S / 2, ay + S * 0.87), (ax + S / 2, ay + S * 0.87)
    a = eo((t - 0.3) / 0.6) if phase == "ask" else 1
    col = (255, 255, 255, int(255 * a))
    lc = (60, 255, 120) if phase == "reveal" and pt > 0.3 else col
    d.polygon([(ax, ay), bl, br], outline=lc, width=10)
    k = item["k"]
    for i in range(1, k + 1):
        fx = bl[0] + (br[0] - bl[0]) * i / (k + 1)
        d.line((ax, ay, fx, bl[1]), fill=lc, width=8)
    for j in range(1, item.get("h", 0) + 1):
        fy = ay + (bl[1] - ay) * (0.45 + 0.25 * (j - 1))
        lx = ax + (bl[0] - ax) * (fy - ay) / (bl[1] - ay); rx = ax + (br[0] - ax) * (fy - ay) / (bl[1] - ay)
        d.line((lx, fy, rx, fy), fill=lc, width=8)
    _opt_row(c, d, item, phase, pt, t, item["options"], y1 - 60, 1.4)
    return ax, ay + S * 0.5

# ---------------------------------------------------------------- Paper fold
def _paper(size, holes, folded=None, fold="v"):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    if folded:
        w = size / 2 if fold == "v" else size; h = size if fold == "v" else size / 2
        d.rectangle((size / 2 - w / 2, size / 2 - h / 2, size / 2 + w / 2, size / 2 + h / 2), fill=(255, 250, 235), outline=(30, 30, 60), width=6)
        ox, oy = size / 2 - w / 2, size / 2 - h / 2
        for hx, hy in holes:
            d.ellipse((ox + hx * w - 18, oy + hy * h - 18, ox + hx * w + 18, oy + hy * h + 18), fill=(40, 40, 60))
        return im
    d.rectangle((6, 6, size - 6, size - 6), fill=(255, 250, 235), outline=(30, 30, 60), width=6)
    if fold == "v": d.line((size / 2, 10, size / 2, size - 10), fill=(180, 170, 150), width=3)
    else: d.line((10, size / 2, size - 10, size / 2), fill=(180, 170, 150), width=3)
    for hx, hy in holes:
        d.ellipse((hx * size - 18, hy * size - 18, hx * size + 18, hy * size + 18), fill=(40, 40, 60))
    return im

def paper_options(item):
    hx, hy = item["hole"]; fold = item.get("fold", "v")
    if fold == "v":
        right = [(hx / 2, hy), (1 - hx / 2, hy)]; single = [(hx / 2, hy)]; shift = [(hx / 2, hy), (1 - hx / 2, 1 - hy)]
    else:
        right = [(hx, hy / 2), (hx, 1 - hy / 2)]; single = [(hx, hy / 2)]; shift = [(hx, hy / 2), (1 - hx, 1 - hy / 2)]
    return {"right": right, "single": single, "shift": shift}

def draw_paperfold(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    fold = item.get("fold", "v")
    big = 340 if c.v else 320
    fx, fy = (c.W / 2, y0 + 180) if c.v else (x0 + 260, (y0 + y1) / 2 + 30)
    paste(im, _paper(big, [tuple(item["hole"])], folded=True, fold=fold), fx, fy, eob((t - 0.2) / 0.4) if phase == "ask" else 1)
    f = font(F_BOLD, 40); txt = "folded + punched"; tw = d.textlength(txt, font=f)
    d.text((fx - tw / 2, fy + big / 2 + 4), txt, font=f, fill=(255, 255, 255))
    opts = paper_options(item); order = item["options"]
    sz = 280 if c.v else 260
    for q, key in enumerate(order):
        ox, oy = (x0 + (x1 - x0) * (q + 0.5) / 3, y0 + 640) if c.v else (x0 + 760 + q * 320, (y0 + y1) / 2 + 30)
        s = eob((t - 1.2 - 0.25 * q) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        p = _paper(sz, opts[key], fold=fold)
        if phase == "reveal" and pt > 0.5:
            fr = Image.new("RGBA", (sz + 20, sz + 20), ((40, 190, 90) if q == item["right"] else (150, 40, 55)) + (255,)); fr.alpha_composite(p, (10, 10)); p = fr
        paste(im, p, ox, oy, s, 0.5 if (phase == "reveal" and pt > 0.5 and q != item["right"]) else 1)
        _label(d, ox - sz / 2, oy - sz / 2, "ABC"[q], c, r=30, size=40)
    if phase == "reveal":
        q = item["right"]; return (x0 + (x1 - x0) * (q + 0.5) / 3, y0 + 640) if c.v else (x0 + 760 + q * 320, (y0 + y1) / 2 + 30)
    return c.W / 2, (y0 + y1) / 2

# ---------------------------------------------------------------- Tangled balloons
BALLOON_COLS = {"red": (235, 60, 70), "blue": (60, 130, 240), "yellow": (250, 200, 40)}
def balloons_answer(item):
    names = ["red", "blue", "yellow"]
    return item["map"].index(names.index(item["ask"]))

def draw_balloons(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c)
    d = ImageDraw.Draw(im)
    names = ["red", "blue", "yellow"]
    top, bot = (y0 + 60, y0 + 760) if c.v else (y0 + 60, y1 - 60)
    xs = [x0 + (x1 - x0) * (i + 0.5) / 3 for i in range(3)] if c.v else [x0 + 300 + i * 360 for i in range(3)]
    rnd = _rnd.Random(item.get("seed", 2))
    ans = balloons_answer(item)
    for kid, b in enumerate(item["map"]):
        bx, by = xs[b], top + 70
        kx, ky = xs[kid], bot - 70
        w1 = rnd.uniform(-260, 260); w2 = rnd.uniform(-260, 260)
        pts = []
        for s in range(41):
            u = s / 40
            x = (1 - u) ** 3 * kx + 3 * (1 - u) ** 2 * u * (kx + w1) + 3 * (1 - u) * u ** 2 * (bx + w2) + u ** 3 * bx
            y = (1 - u) ** 3 * ky + 3 * (1 - u) ** 2 * u * (ky - 200) + 3 * (1 - u) * u ** 2 * (by + 200) + u ** 3 * (by + 70)
            pts.append((x, y))
        hl = phase == "reveal" and kid == ans
        d.line(pts, fill=(60, 255, 120) if hl else (230, 230, 240), width=10 if hl else 6, joint="curve")
    for i, nme in enumerate(names):
        bx, by = xs[i], top + 70
        a = eob((t - 0.2 - 0.15 * i) / 0.4) if phase == "ask" else 1
        r = 62 * a
        d.ellipse((bx - r, by - r * 1.15, bx + r, by + r * 1.15), fill=BALLOON_COLS[nme], outline=(30, 30, 60), width=4)
        d.polygon([(bx - 10, by + r * 1.15), (bx + 10, by + r * 1.15), (bx, by + r * 1.15 + 14)], fill=BALLOON_COLS[nme])
    for kid in range(3):
        paste(im, emoji_img(item["kids"][kid], 130 if c.v else 110), xs[kid], bot - 40)
        _label(d, xs[kid] - 90, bot - 90, "ABC"[kid], c, r=30, size=40)
    if phase == "reveal":
        return xs[ans], bot - 40
    return c.W / 2, (y0 + y1) / 2

DRAW.update({"spotdiff": draw_spotdiff, "oddcolor": draw_oddcolor, "clocks": draw_clocks, "missingnum": draw_missingnum,
             "memgrid": draw_memgrid, "triangles": draw_triangles, "paperfold": draw_paperfold, "balloons": draw_balloons})
_old_min_ask2 = min_ask
def min_ask(item):
    if item.get("type") == "memgrid": return 0.6 + 0.65 * len(item["seq"]) + 1.0
    return _old_min_ask2(item)

# ================================================================ CANDIDATES (v4) — eyes & memory
def _grid_geom(c, cols, rows, top_pad=20, size_cap=None, box=None):
    x0, y0, x1, y1 = box or area(c)
    cell = min((x1 - x0) / cols, (y1 - y0 - top_pad) / rows)
    if size_cap: cell = min(cell, size_cap)
    ox = c.W / 2 - cols * cell / 2; oy = y0 + top_pad
    return cell, ox, oy

def _panel(d, ox, oy, w, h, r=36):
    from engine import soft_shadow
    try: soft_shadow(d._image, (ox - 20, oy - 20, ox + w + 20, oy + h + 20), r)
    except Exception: pass
    d.rounded_rectangle((ox - 20, oy - 20, ox + w + 20, oy + h + 20), radius=r, fill=(255, 255, 255, 235))

def _circle_hit(d, cx, cy, rr, pt):
    rr = rr * (1 + 0.06 * math.sin(pt * 6))
    d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=(60, 255, 120), width=12)

def _emoji_opts(c, im, d, item, phase, pt, t, start, y_v, x_h=None):
    if OPT is not None and c.v: im = OPT; d = ImageDraw.Draw(OPT)
    x0, y0, x1, y1 = area(c); opts = item["options"]; n = len(opts)
    for q, o in enumerate(opts):
        ox, oy = (x0 + (x1 - x0) * (q + 0.5) / n, y_v) if c.v else ((x_h or x0 + 1300), y0 + 140 + q * 200)
        bw = 220 if c.v else 180
        s = eob((t - start - 0.2 * q) / 0.4) if phase == "ask" else 1
        if s < 0.05: continue
        fill = (255, 255, 255, 230)
        if phase == "reveal" and pt > 0.5: fill = (40, 190, 90) if q == item["right"] else (150, 40, 55)
        d.rounded_rectangle((ox - bw / 2, oy - bw / 2, ox + bw / 2, oy + bw / 2), radius=30, fill=fill, outline=c.accent, width=6)
        paste(im, emoji_img(o, bw * 0.55), ox, oy + 8, s)
        _label(d, ox - bw / 2 + 12, oy - bw / 2 + 12, "ABC"[q], c, r=28, size=38)

def missing_hold(item):
    return 3.0 if len(item["before"]) <= 6 else 4.6

# 34 What's missing
def draw_missing(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cols = 3; cw = (x1 - x0) / cols; big = len(item["before"]) > 6
    ch = (190 if big else 230) if c.v else (200 if big else 220)
    oy = y0 + 10 if c.v else y0 + 40
    hold = missing_hold(item)
    after = phase != "ask" or t >= hold
    for i, e in enumerate(item["before"]):
        r_, k = divmod(i, cols)
        cx, cy = (x0 + cw * (k + 0.5), oy + ch * (r_ + 0.5)) if c.v else (x0 + 120 + k * 270, oy + ch * (r_ + 0.5) + 60)
        box = (cx - 110, cy - 100, cx + 110, cy + 100)
        gone = after and i == item["gone"]
        d.rounded_rectangle(box, radius=30, fill=(255, 255, 255, 60 if gone else 235), outline=c.accent if gone else None, width=6)
        if not gone or (phase == "reveal" and pt > 0.3):
            s = eob((t - 0.3 - 0.1 * i) / 0.4) if (phase == "ask" and t < hold) else 1
            paste(im, emoji_img(e, 130), cx, cy, s)
            if phase == "reveal" and i == item["gone"]: glow_box(im, box, r=30)
    if phase == "ask" and hold <= t < hold + 0.45:
        im.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, int(255 * cl(1 - abs(t - hold - 0.22) / 0.22)))))
    if after: _emoji_opts(c, im, d, item, phase, pt, t, hold + 0.6, y0 + (700 if big else 720), x0 + 1250)
    return c.W / 2, (y0 + y1) / 2

# 35 Find the letter
LH_COLS = [(230, 60, 80), (40, 130, 230), (30, 170, 90), (245, 150, 20), (150, 70, 210), (20, 170, 180), (230, 80, 170), (90, 90, 110)]
def draw_letterhunt(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im)
    cols, rows = (8, 10) if c.v else (16, 6)
    cell, ox, oy = _grid_geom(c, cols, rows, 40 if c.v else 80, 120)
    _panel(d, ox, oy, cols * cell, rows * cell)
    f = font(F_BOLD, cell * 0.66)
    pr, pc = item["pos"]; pr %= rows; pc %= cols
    a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
    for r_ in range(rows):
        for k in range(cols):
            ch_ = item["odd"] if (r_, k) == (pr, pc) else item["base"]
            cx, cy = ox + (k + 0.5) * cell, oy + (r_ + 0.5) * cell
            col = LH_COLS[random.Random(item.get("seed", 0) * 100003 + r_ * 997 + k * 31).randrange(len(LH_COLS))]
            short_q = ch_ == "Q" and item["base"] == "O"
            dc = "O" if short_q else ch_
            tw = d.textlength(dc, font=f); d.text((cx - tw / 2, cy - cell * 0.5), dc, font=f, fill=col + (int(255 * a),))
            if short_q:  # tiny tail so the Q hides among the Os
                bx0, by0, bx1, by1 = d.textbbox((cx - tw / 2, cy - cell * 0.5), "O", font=f)
                rx, ry = (bx1 - bx0) / 2, (by1 - by0) / 2; mx, my = bx0 + rx, by0 + ry
                px, py = mx + rx * 0.6, my + ry * 0.6; L = ry * 0.62
                d.line((px - L * 0.35, py - L * 0.35, px + L * 0.65, py + L * 0.65), fill=col + (int(255 * a),), width=max(4, int(rx * 0.3)))
    cx, cy = ox + (pc + 0.5) * cell, oy + (pr + 0.5) * cell
    if phase == "reveal": _circle_hit(d, cx, cy, cell * 0.6, pt)
    return cx, cy

# 36 Upside-down one
def draw_flipped(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im)
    cols, rows = tuple(item.get("grid") or ((7, 9) if c.v else (12, 6)))
    cell, ox, oy = _grid_geom(c, cols, rows, 40 if c.v else 60, 150)
    _panel(d, ox, oy, cols * cell, rows * cell)
    e = emoji_img(item["emoji"], cell * 0.62)
    odd = e.transpose(Image.ROTATE_180) if item.get("mode", "mirror") == "rot" else e.transpose(Image.FLIP_LEFT_RIGHT)
    pr, pc = item["pos"]; pr %= rows; pc %= cols
    a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
    for r_ in range(rows):
        for k in range(cols):
            paste(im, odd if (r_, k) == (pr, pc) else e, ox + (k + 0.5) * cell, oy + (r_ + 0.5) * cell, 1, a)
    cx, cy = ox + (pc + 0.5) * cell, oy + (pr + 0.5) * cell
    if phase == "reveal": _circle_hit(d, cx, cy, cell * 0.6, pt)
    return cx, cy

# 37 Count the flashes
def flash_times(item):
    rnd = _rnd.Random(item.get("seed", 1)); n = item["n"]; t = 0.9; out = []
    for i in range(n):
        out.append(t); t += 0.16 + rnd.uniform(0.14, 0.42)
    return out

def draw_blinks(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cx, cy = (c.W / 2, y0 + 300) if c.v else (x0 + 420, (y0 + y1) / 2 + 20)
    on = phase == "ask" and any(ft <= t < ft + 0.13 for ft in flash_times(item))
    R = 190 if c.v else 170
    if on:
        g = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((cx - R * 1.5, cy - R * 1.5, cx + R * 1.5, cy + R * 1.5), fill=(255, 230, 90, 160))
        im.alpha_composite(g.filter(ImageFilter.GaussianBlur(40))); d = ImageDraw.Draw(im)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(255, 225, 70) if on else (90, 90, 120), outline=(255, 255, 255), width=10)
    if phase == "reveal":
        f = font(F_BOLD, 160); txt = str(item["n"]); tw = d.textlength(txt, font=f)
        d.text((cx - tw / 2, cy - 110), txt, font=f, fill=(255, 255, 255))
    _opt_row(c, d, item, phase, pt, t, item["options"], y1 - 60, max(flash_times(item)) + 0.4)
    return cx, cy

# 38 Number flash (5 look-alike options)
def numflash_end(item):
    return 2.2 + 0.35 * max(0, len(item["number"]) - 5)

def draw_numflash(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cx, cy = (c.W / 2, y0 + 110) if c.v else (x0 + 480, (y0 + y1) / 2 + 30)
    box = (cx - 380, cy - 120, cx + 380, cy + 120)
    d.rounded_rectangle(box, radius=40, fill=(255, 255, 255))
    show = (phase == "ask" and 0.6 <= t < numflash_end(item)) or phase == "reveal"
    txt = item["number"] if show else ("READY?" if phase == "ask" and t < 0.6 else " ".join("?" * len(item["number"])))
    ff = font(F_BOLD, 170 if show else 100)
    while d.textlength(txt, font=ff) > 700: ff = font(F_BOLD, ff.size - 8)
    tw = d.textlength(txt, font=ff); d.text((cx - tw / 2, cy - ff.size * 0.72), txt, font=ff, fill=(40, 40, 70))
    if phase != "ask" or t > numflash_end(item) + 0.1:
        opts = item["options"]; n = len(opts)
        for q, o in enumerate(opts):
            if c.v: ox, oy, ow, oh = c.W / 2, y0 + 330 + q * 116, 540, 98
            else: ox, oy, ow, oh = x0 + 1300, y0 + 90 + q * 125, 400, 108
            sc = eob((t - numflash_end(item) - 0.2 - 0.12 * q) / 0.35) if phase == "ask" else 1
            if sc < 0.05: continue
            fill = (255, 255, 255)
            if phase == "reveal" and pt > 0.5: fill = (40, 190, 90) if q == item["right"] else (150, 40, 55)
            d.rounded_rectangle((ox - ow / 2, oy - oh / 2, ox + ow / 2, oy + oh / 2), radius=26, fill=fill, outline=c.accent, width=5)
            f = font(F_BOLD, 64); tw = d.textlength(o, font=f)
            d.text((ox - tw / 2 + 25, oy - 44), o, font=f, fill=(30, 30, 60) if fill == (255, 255, 255) else (255, 255, 255))
            _label(d, ox - ow / 2 + 42, oy, "ABCDE"[q], c, r=28, size=38)
    if phase == "reveal": glow_box(im, box, r=40)
    return cx, cy

# 39 Where was the star
def draw_whereflash(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cell = 230 if c.v else 200
    ox = c.W / 2 - 1.5 * cell; oy = y0 + 20 if c.v else y0 + 60
    show = (phase == "ask" and 0.4 <= t < 3.0)
    f = font(F_BOLD, 64)
    for i, e in enumerate(item["grid"]):
        r_, q = divmod(i, 3)
        box = (ox + q * cell + 12, oy + r_ * cell + 12, ox + (q + 1) * cell - 12, oy + (r_ + 1) * cell - 12)
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        if show or (phase == "reveal" and i == item["target_idx"]):
            d.rounded_rectangle(box, radius=28, fill=(255, 255, 255, 235)); paste(im, emoji_img(e, cell * 0.55), cx, cy)
            if phase == "reveal": glow_box(im, box, r=28)
        else:
            d.rounded_rectangle(box, radius=28, fill=c.accent)
            L = str(i + 1); tw = d.textlength(L, font=f); d.text((cx - tw / 2, cy - 46), L, font=f, fill=(30, 30, 60))
    if phase != "ask" or t >= 3.0:
        tx, ty = (c.W / 2, oy + 3 * cell + 110) if c.v else (x0 + 1350, (y0 + y1) / 2)
        f2 = font(F_BOLD, 60); txt = "Where was"; tw = d.textlength(txt, font=f2)
        d.text((tx - tw / 2 - 70, ty - 40), txt, font=f2, fill=(255, 255, 255))
        paste(im, emoji_img(item["grid"][item["target_idx"]], 110), tx + tw / 2, ty)
    r_, q = divmod(item["target_idx"], 3)
    return ox + (q + 0.5) * cell, oy + (r_ + 0.5) * cell

# 40 Bug arrows
def bug_path(item, n=4):
    r_, q = item["start"]; path = [(r_, q)]
    for m in item["moves"]:
        dr, dq = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}[m]
        r_, q = r_ + dr, q + dq
        if not (0 <= r_ < n and 0 <= q < n): return None
        path.append((r_, q))
    return path

def draw_bug(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    n = 4; cell = 170 if c.v else 150
    ox = c.W / 2 - n * cell / 2 if c.v else x0 + 100; oy = y0 + 20 if c.v else y0 + 60
    path = bug_path(item)
    f = font(F_BOLD, 50)
    for i in range(n * n):
        r_, q = divmod(i, n)
        box = (ox + q * cell + 8, oy + r_ * cell + 8, ox + (q + 1) * cell - 8, oy + (r_ + 1) * cell - 8)
        end = phase == "reveal" and (r_, q) == path[-1] and pt > 0.5 * len(item["moves"]) * 0.35
        d.rounded_rectangle(box, radius=22, fill=(40, 190, 90) if end else (255, 255, 255, 225))
        L = str(i + 1); tw = d.textlength(L, font=f); d.text((box[2] - tw - 12, box[1] + 4), L, font=f, fill=(150, 150, 180))
    if phase == "reveal":
        k = min(len(path) - 1, int(pt / 0.35)); fr = (pt / 0.35) - k
        a, b = path[k], path[min(k + 1, len(path) - 1)]
        pos = (a[0] + (b[0] - a[0]) * min(1, fr), a[1] + (b[1] - a[1]) * min(1, fr))
    else:
        pos = tuple(path[0])
    paste(im, emoji_img("🐞", cell * 0.6), ox + (pos[1] + 0.5) * cell, oy + (pos[0] + 0.5) * cell)
    # arrows strip
    arr = {"U": "⬆", "D": "⬇", "L": "⬅", "R": "➡"}
    ms = item["moves"] if item.get("show_arrows") else []
    if not ms:  # voice-driven: ring the start square and show a LISTEN badge
        sr, sq = path[0]
        pulse = 1 + 0.08 * math.sin(t * 7)
        d.rounded_rectangle((ox + sq * cell + 4, oy + sr * cell + 4, ox + (sq + 1) * cell - 4, oy + (sr + 1) * cell - 4), radius=24, outline=(255, 210, 60), width=10)
        f3 = font(F_BOLD, 50); lab = "LISTEN to Hoot!"; tw = d.textlength(lab, font=f3)
        lx, ly = (c.W / 2, oy + n * cell + 70) if c.v else (x0 + 1250, y0 + 200)
        d.rounded_rectangle((lx - tw / 2 - 40, ly - 42 * pulse, lx + tw / 2 + 80, ly + 42 * pulse), radius=40, fill=(255, 210, 60))
        d.text((lx - tw / 2 + 40, ly - 36), lab, font=f3, fill=(40, 30, 90))
        paste(im, emoji_img("🔊", 56), lx - tw / 2 + 2, ly)
    ms = ms or []; ax = c.W / 2 - (len(ms) - 1) * 60 if c.v else x0 + 1250 - (len(ms) - 1) * 50
    ay = oy + n * cell + 90 if c.v else y0 + 200
    for i, m in enumerate(ms):
        s = eob((t - 0.8 - 0.2 * i) / 0.3) if phase == "ask" else 1
        paste(im, emoji_img(arr[m], 96), ax + i * (120 if c.v else 100), ay, s)
    er, eq = path[-1]
    return ox + (eq + 0.5) * cell, oy + (er + 0.5) * cell

# 41 Which colour appeared most
def draw_colormost(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    rnd = _rnd.Random(item.get("seed", 1))
    dots = [nm for nm, k in item["counts"].items() for _ in range(k)]; rnd.shuffle(dots)
    bx = (x0 + 20, y0, x1 - 20, y0 + 560) if c.v else (x0 + 40, y0 + 60, x0 + 940, y1 - 20)
    d.rounded_rectangle(bx, radius=40, fill=(255, 255, 255, 235))
    show = (phase == "ask" and 0.5 <= t < 2.6) or phase == "reveal"
    cols, rows = 6, 4; cells = [(r_, q) for r_ in range(rows) for q in range(cols)]; rnd.shuffle(cells)
    cw, ch = (bx[2] - bx[0]) / cols, (bx[3] - bx[1]) / rows
    win = max(item["counts"], key=item["counts"].get)
    if show:
        for i, nm in enumerate(dots[:len(cells)]):
            r_, q = cells[i]
            px = bx[0] + cw * (q + 0.5) + rnd.uniform(-cw * 0.15, cw * 0.15); py = bx[1] + ch * (r_ + 0.5) + rnd.uniform(-ch * 0.12, ch * 0.12)
            rr = min(cw, ch) * 0.3
            a = 255 if (phase != "reveal" or nm == win) else 70
            d.ellipse((px - rr, py - rr, px + rr, py + rr), fill=INKS[nm] + (a,))
    else:
        f = font(F_BOLD, 180); tw = d.textlength("?", font=f); d.text(((bx[0] + bx[2]) / 2 - tw / 2, (bx[1] + bx[3]) / 2 - 120), "?", font=f, fill=(30, 30, 60))
    if phase != "ask" or t > 2.7:
        _opt_row(c, d, item, phase, pt, t, item["options"], bx[3] + 160 if c.v else 0, 2.8)
    return (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2

# 42 Find the pair
def pair_answer(item):
    em = item["emojis"]
    for i in range(len(em)):
        for j in range(i + 1, len(em)):
            if em[i] == em[j]: return i, j
    return None

def draw_pair(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im)
    em = item["emojis"]; cols = 3 if c.v else 6; rows = math.ceil(len(em) / cols)
    cell, ox, oy = _grid_geom(c, cols, rows, 30 if c.v else 80, 230)
    _panel(d, ox, oy, cols * cell, rows * cell)
    pr = pair_answer(item)
    for i, e in enumerate(em):
        r_, q = divmod(i, cols); cx, cy = ox + (q + 0.5) * cell, oy + (r_ + 0.5) * cell
        s = eob((t - 0.3 - 0.06 * i) / 0.4) if phase == "ask" else 1
        a = 0.3 if (phase == "reveal" and pt > 0.3 and i not in pr) else 1
        paste(im, emoji_img(e, cell * 0.62), cx, cy, s, a)
        if phase == "reveal" and i in pr: _circle_hit(d, cx, cy, cell * 0.48, pt)
    i = pr[0]; r_, q = divmod(i, cols)
    return ox + (q + 0.5) * cell, oy + (r_ + 0.5) * cell

# 43 Odd size out
def draw_oddsize(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im)
    cols, rows = (5, 6) if c.v else (10, 4)
    cell, ox, oy = _grid_geom(c, cols, rows, 40 if c.v else 80, 160)
    _panel(d, ox, oy, cols * cell, rows * cell)
    pr, pc = item["pos"]; pr %= rows; pc %= cols
    a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
    for r_ in range(rows):
        for k in range(cols):
            sc = item.get("scale", 1.15) if (r_, k) == (pr, pc) else 1.0
            paste(im, emoji_img(item["emoji"], cell * 0.66 * sc), ox + (k + 0.5) * cell, oy + (r_ + 0.5) * cell, 1, a)
    cx, cy = ox + (pc + 0.5) * cell, oy + (pr + 0.5) * cell
    if phase == "reveal": _circle_hit(d, cx, cy, cell * 0.62, pt)
    return cx, cy

# 44 Which row is different (harder: longer rows, look-alike emojis, adjacent swap, up to 5 rows)
def draw_rowdiff(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    seq = item["seq"]; n = len(seq); rows = item.get("rows", 4)
    cell = min(170 if c.v else 140, ((x1 - x0) - 160) / n)
    gap = 22 if rows > 4 else 30
    if c.v: cell = min(cell, (y1 - y0 - 40 - gap * (rows - 1)) / rows)
    else: cell = min(cell, (y1 - y0 - 100 - gap * (rows - 1)) / rows)
    ox = c.W / 2 - n * cell / 2 + 40; oy = y0 + 20 if c.v else y0 + 70
    for r_ in range(rows):
        row = list(seq)
        if r_ == item["odd_row"]:
            a, b = item["swap"]; row[a], row[b] = row[b], row[a]
        y = oy + r_ * (cell + gap)
        hl = phase == "reveal" and r_ == item["odd_row"]
        d.rounded_rectangle((ox - 20, y, ox + n * cell + 20, y + cell), radius=26, fill=(40, 190, 90) if hl else (255, 255, 255, 230))
        _label(d, ox - 80, y + cell / 2, "ABCDE"[r_], c, r=34, size=44)
        for k, e in enumerate(row):
            s = eob((t - 0.3 - 0.12 * r_) / 0.4) if phase == "ask" else 1
            paste(im, emoji_img(e, cell * 0.7), ox + (k + 0.5) * cell, y + cell / 2, s)
            if hl and k in item["swap"] and pt > 0.4:
                d.rounded_rectangle((ox + k * cell + 4, y + 4, ox + (k + 1) * cell - 4, y + cell - 4), radius=20, outline=(255, 255, 255), width=6)
    return c.W / 2, oy + item["odd_row"] * (cell + gap) + cell / 2

# 45 How many differences
def draw_countdiff(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    sc = item["scene"]; diffs = {i: e for i, e in item["diffs"]}
    cell = 115 if c.v else 105; pw = cell * 3 + 40
    panels = [(c.W / 2, y0 + 200), (c.W / 2, y0 + 610)] if c.v else [(c.W / 2 - 520, (y0 + y1) / 2 + 30), (c.W / 2 - 80, (y0 + y1) / 2 + 30)]
    for p, (px, py) in enumerate(panels):
        a = eob((t - 0.2 - 0.3 * p) / 0.4) if phase == "ask" else 1
        if a < 0.05: continue
        d.rounded_rectangle((px - pw / 2, py - pw / 2, px + pw / 2, py + pw / 2), radius=30, fill=(255, 255, 255))
        for i, e in enumerate(sc):
            r_, k = divmod(i, 3)
            em = diffs.get(i, e) if p == 1 else e
            cx, cy = px - cell + k * cell, py - cell + r_ * cell
            paste(im, emoji_img(em, cell * 0.7), cx, cy, a)
            if phase == "reveal" and i in diffs: _circle_hit(d, cx, cy, cell * 0.5, pt)
    _opt_row(c, d, item, phase, pt, t, item["options"], y1 + 40 if c.v else 0, 1.4, h_x=x0 + 1380)
    return panels[1]

# 46 Which spins the other way
def draw_spinner(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cols, rows = (3, 3) if c.v else (5, 2)
    cell = 240 if c.v else 220
    ox = c.W / 2 - cols * cell / 2; oy = y0 + 20 if c.v else y0 + 120
    f = font(F_BOLD, 40)
    for i in range(cols * rows):
        r_, q = divmod(i, cols); cx, cy = ox + (q + 0.5) * cell, oy + (r_ + 0.5) * cell
        dirn = -1 if i == item["pos"] else 1
        ang = dirn * t * 3.2 + i * 0.3
        R = cell * 0.36
        for b in range(4):
            a = ang + b * math.pi / 2
            p1 = (cx + R * math.cos(a), cy + R * math.sin(a))
            p2 = (cx + R * 0.55 * math.cos(a + 0.9), cy + R * 0.55 * math.sin(a + 0.9))
            d.polygon([(cx, cy), p1, p2], fill=CANDY[(b + i) % 6], outline=(30, 30, 60))
        d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=(255, 255, 255))
        L = str(i + 1); d.text((cx - cell * 0.45, cy - cell * 0.45), L, font=f, fill=c.accent)
        if phase == "reveal" and i == item["pos"]: _circle_hit(d, cx, cy, cell * 0.46, pt)
    r_, q = divmod(item["pos"], cols)
    return ox + (q + 0.5) * cell, oy + (r_ + 0.5) * cell

# 47 Which eye blinked
def draw_blinkeye(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cols, rows = (3, 4) if c.v else (6, 2)
    cell = 220 if c.v else 210
    ox = c.W / 2 - cols * cell / 2; oy = y0 + 10 if c.v else y0 + 120
    at = item.get("at", 2.0)
    f = font(F_BOLD, 40)
    for i in range(cols * rows):
        r_, q = divmod(i, cols); cx, cy = ox + (q + 0.5) * cell, oy + (r_ + 0.5) * cell
        R = cell * 0.36
        closed = 0.0
        if i == item["pos"]:
            tt = t if phase == "ask" else (pt - 0.4 if phase == "reveal" else -9)
            if at <= tt < at + 0.22 or (phase == "reveal" and 0 <= pt - 0.4 < 0.22): closed = 1.0
        d.ellipse((cx - R, cy - R * 0.75, cx + R, cy + R * 0.75), fill=(255, 255, 255), outline=(30, 30, 60), width=6)
        if closed:
            d.ellipse((cx - R, cy - R * 0.75, cx + R, cy + R * 0.75), fill=(240, 200, 170), outline=(30, 30, 60), width=6)
            d.arc((cx - R * 0.8, cy - R * 0.4, cx + R * 0.8, cy + R * 0.4), 20, 160, fill=(30, 30, 60), width=6)
        else:
            d.ellipse((cx - R * 0.42, cy - R * 0.42, cx + R * 0.42, cy + R * 0.42), fill=(80, 150, 230))
            d.ellipse((cx - R * 0.2, cy - R * 0.2, cx + R * 0.2, cy + R * 0.2), fill=(30, 30, 60))
            d.ellipse((cx - R * 0.08 + 8, cy - R * 0.2, cx + R * 0.08 + 8, cy - R * 0.05), fill=(255, 255, 255))
        L = str(i + 1); d.text((cx - cell * 0.46, cy - cell * 0.46), L, font=f, fill=c.accent)
        if phase == "reveal" and i == item["pos"] and pt > 0.7: _circle_hit(d, cx, cy, cell * 0.46, pt)
    r_, q = divmod(item["pos"], cols)
    return ox + (q + 0.5) * cell, oy + (r_ + 0.5) * cell

DRAW.update({"missing": draw_missing, "letterhunt": draw_letterhunt, "flipped": draw_flipped, "blinks": draw_blinks,
             "numflash": draw_numflash, "whereflash": draw_whereflash, "bug": draw_bug, "colormost": draw_colormost,
             "pair": draw_pair, "oddsize": draw_oddsize, "rowdiff": draw_rowdiff, "countdiff": draw_countdiff,
             "spinner": draw_spinner, "blinkeye": draw_blinkeye})
_old_min_ask3 = min_ask
def min_ask(item):
    t_ = item.get("type")
    if t_ == "missing": return missing_hold(item) + 2.4
    if t_ == "blinks": return max(flash_times(item)) + 1.4
    if t_ == "numflash": return numflash_end(item) + 1.4
    if t_ == "colormost": return 3.6
    if t_ == "whereflash": return 4.2
    if t_ == "blinkeye": return item.get("at", 2.0) + 1.5
    return _old_min_ask3(item)

# ================================================================ CANDIDATES (v5)
def _arrow(size, angle, col=(255, 120, 60)):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    s = size
    d.polygon([(s * 0.12, s * 0.4), (s * 0.55, s * 0.4), (s * 0.55, s * 0.2), (s * 0.9, s * 0.5), (s * 0.55, s * 0.8), (s * 0.55, s * 0.6), (s * 0.12, s * 0.6)], fill=col, outline=(30, 30, 60))
    return im.rotate(-angle, resample=Image.BICUBIC)

# 48 Arrow out
def draw_arrowout(c, im, item, phase, pt, t):
    d = ImageDraw.Draw(im)
    cols, rows = (7, 9) if c.v else (14, 6)
    cell, ox, oy = _grid_geom(c, cols, rows, 40 if c.v else 80, 160)
    _panel(d, ox, oy, cols * cell, rows * cell)
    pr, pc = item["pos"]; pr %= rows; pc %= cols
    base = _arrow(int(cell * 0.8), item["angle"]); odd = _arrow(int(cell * 0.8), item["odd_angle"])
    a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
    for r_ in range(rows):
        for k in range(cols):
            paste(im, odd if (r_, k) == (pr, pc) else base, ox + (k + 0.5) * cell, oy + (r_ + 0.5) * cell, 1, a)
    cx, cy = ox + (pc + 0.5) * cell, oy + (pr + 0.5) * cell
    if phase == "reveal": _circle_hit(d, cx, cy, cell * 0.6, pt)
    return cx, cy

# 49 Card flip memory
def cardflip_pair(item):
    return [i + 1 for i, e in enumerate(item["cards"]) if e == item["target"]]

def cardflip_end(item):
    return 3.0 if len(item["cards"]) < 16 else 5.5

def draw_cardflip(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cards = item["cards"]; big = len(cards) >= 16
    cols, rows = (4, 4) if big else ((3, 3) if c.v else (5, 2))
    cw, ch = ((190, 165) if big else (230, 200)) if c.v else ((165, 165) if big else (230, 230))
    ox = c.W / 2 - cols * cw / 2 if c.v else x0 + 40; oy = y0 + 10 if c.v else y0 + (20 if big else 80)
    ask_end = cardflip_end(item)
    show = phase == "ask" and 0.4 <= t < ask_end
    pair = cardflip_pair(item)
    f = font(F_BOLD, 64)
    for i, e in enumerate(cards):
        r_, q = divmod(i, cols)
        box = (ox + q * cw + 12, oy + r_ * ch + 12, ox + (q + 1) * cw - 12, oy + (r_ + 1) * ch - 12)
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        if show or (phase == "reveal" and (i + 1) in pair and pt > 0.3):
            d.rounded_rectangle(box, radius=26, fill=(255, 255, 255, 240)); paste(im, emoji_img(e, ch * 0.55), cx, cy)
            if phase == "reveal": glow_box(im, box, r=26)
        else:
            d.rounded_rectangle(box, radius=26, fill=(230, 80, 120), outline=(255, 255, 255), width=6)
            L = str(i + 1); tw = d.textlength(L, font=f); d.text((cx - tw / 2, cy - 46), L, font=f, fill=(255, 255, 255))
    if phase != "ask" or t >= ask_end:
        f2 = font(F_BOLD, 56); txt = "Where are the two"; tw = d.textlength(txt, font=f2)
        tx, ty = (c.W / 2, oy + rows * ch + 50) if c.v else (x0 + 1430, y0 + (10 if big else 60))
        d.text((tx - tw / 2 - 60, ty - 36), txt, font=f2, fill=(255, 255, 255))
        paste(im, emoji_img(item["target"], 90), tx + tw / 2 + 10, ty)
        _opt_row(c, d, item, phase, pt, t, item["options"], ty + 140 if c.v else 0, ask_end + 0.2, h_x=x0 + 1430)
    return c.W / 2, (y0 + y1) / 2

# 50 Quick swap
def draw_quickswap(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    its = item["items"]; n = len(its); cols = 3
    cw = (x1 - x0) / cols if c.v else 230; ch = 230
    ox = x0 if c.v else x0 + 60; oy = y0 + 20 if c.v else y0 + 80
    a, b = item["swap"]
    def center(i):
        r_, q = divmod(i, cols); return ox + cw * (q + 0.5), oy + ch * (r_ + 0.5)
    m = 0.0
    if phase == "ask": m = cl((t - 2.0) / 0.35)
    else: m = 1.0
    for i, e in enumerate(its):
        cx, cy = center(i)
        d.rounded_rectangle((cx - 100, cy - 95, cx + 100, cy + 95), radius=28, fill=(255, 255, 255, 220))
    for i, e in enumerate(its):
        cx, cy = center(i)
        if i in (a, b):
            tx, ty = center(b if i == a else a)
            arc = math.sin(m * math.pi) * 90 * (1 if i == a else -1)
            cx, cy = cx + (tx - cx) * m, cy + (ty - cy) * m - arc
        paste(im, emoji_img(e, 130), cx, cy)
    if phase == "reveal":
        for i in (a, b):
            cx, cy = center(i); glow_box(im, (cx - 100, cy - 95, cx + 100, cy + 95), r=28)
    if phase != "ask" or t >= 2.6:
        opts = item["options"]
        for q, (e1, e2) in enumerate(opts):
            bx, by = (x0 + (x1 - x0) * (q + 0.5) / 3, oy + 2 * ch + 160) if c.v else (x0 + 1350, y0 + 140 + q * 200)
            fill = (255, 255, 255)
            if phase == "reveal" and pt > 0.5: fill = (40, 190, 90) if q == item["right"] else (150, 40, 55)
            d.rounded_rectangle((bx - 140, by - 75, bx + 140, by + 75), radius=28, fill=fill, outline=c.accent, width=6)
            paste(im, emoji_img(e1, 80), bx - 45, by); paste(im, emoji_img(e2, 80), bx + 55, by)
            _label(d, bx - 140 + 30, by - 75 + 30, "ABC"[q], c, r=24, size=32)
    return c.W / 2, (y0 + y1) / 2

# 51 Dice flash
def _die(size, n):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, size - 6, size - 6), radius=size // 6, fill=(255, 255, 255), outline=(30, 30, 60), width=8)
    P = {1: [(0.5, 0.5)], 2: [(0.27, 0.27), (0.73, 0.73)], 3: [(0.27, 0.27), (0.5, 0.5), (0.73, 0.73)],
         4: [(0.27, 0.27), (0.73, 0.27), (0.27, 0.73), (0.73, 0.73)], 5: [(0.27, 0.27), (0.73, 0.27), (0.5, 0.5), (0.27, 0.73), (0.73, 0.73)],
         6: [(0.27, 0.25), (0.73, 0.25), (0.27, 0.5), (0.73, 0.5), (0.27, 0.75), (0.73, 0.75)]}[n]
    r = size * 0.08
    for x, y in P: d.ellipse((x * size - r, y * size - r, x * size + r, y * size + r), fill=(230, 50, 70))
    return im

def draw_diceflash(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    show = (phase == "ask" and 0.6 <= t < 2.0) or phase == "reveal"
    cy = y0 + 230 if c.v else (y0 + y1) / 2 + 30
    for k, v in enumerate(item["dice"]):
        cx = (c.W / 2 if c.v else x0 + 480) + (k - (len(item["dice"]) - 1) / 2) * 340
        if show: paste(im, _die(280, v), cx, cy)
        else:
            d.rounded_rectangle((cx - 140, cy - 140, cx + 140, cy + 140), radius=46, fill=(90, 90, 130), outline=(255, 255, 255), width=8)
            f = font(F_BOLD, 150); tw = d.textlength("?", font=f); d.text((cx - tw / 2, cy - 105), "?", font=f, fill=(255, 255, 255))
    if phase != "ask" or t >= 2.1:
        _opt_row(c, d, item, phase, pt, t, item["options"], y0 + 620 if c.v else 0, 2.2, h_x=x0 + 1300)
    return c.W / 2, cy

# 52 Who's hiding
def draw_peek(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    S = 480 if c.v else 420
    cx, cy = (c.W / 2, y0 + 300) if c.v else (x0 + 420, (y0 + y1) / 2 + 30)
    e = emoji_img(item["emoji"], S)
    show = item.get("show", 0.3)
    wall_top = cy - S / 2 + S * show
    if phase == "reveal": wall_top += eo(pt / 0.7) * S
    paste(im, e, cx, cy)
    if wall_top < cy + S / 2 + 40:
        d.rectangle((cx - S * 0.75, wall_top, cx + S * 0.75, cy + S / 2 + 40), fill=(170, 90, 60))
    for k in range(6):
        yy = wall_top + k * 50
        if yy < cy + S / 2 + 40: d.line((cx - S * 0.75, yy, cx + S * 0.75, yy), fill=(120, 60, 40), width=5)
    _opt_row(c, d, item, phase, pt, t, item["options"], y1 - 40 if c.v else 0, 1.2)
    return cx, cy

# 53 Zoom out
def draw_zoom(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    win = 520 if c.v else 460
    cx, cy = (c.W / 2, y0 + 280) if c.v else (x0 + 420, (y0 + y1) / 2 + 30)
    z0, z1 = item.get("zoom", [4.5, 2.4])
    if phase == "ask": z = z0 - (z0 - z1) * cl(t / 4.0)
    elif phase == "count": z = z1
    else: z = z1 - (z1 - 1.0) * eo(pt / 0.8)
    big = emoji_img(item["emoji"], int(win * z * 0.8))
    fx, fy = item.get("focus", [0.5, 0.5])
    canvas = Image.new("RGBA", (win, win), (255, 255, 255, 255))
    px = int(win / 2 - big.width * (fx if z > 1.05 else 0.5)); py = int(win / 2 - big.height * (fy if z > 1.05 else 0.5))
    canvas.alpha_composite(big, (max(-big.width, min(win, px)), max(-big.height, min(win, py)))) if False else canvas.paste(big, (px, py), big)
    mask = Image.new("L", (win, win), 0); ImageDraw.Draw(mask).ellipse((0, 0, win, win), fill=255)
    canvas.putalpha(mask)
    im.paste(canvas, (int(cx - win / 2), int(cy - win / 2)), canvas)
    d.ellipse((cx - win / 2, cy - win / 2, cx + win / 2, cy + win / 2), outline=c.accent, width=12)
    _opt_row(c, d, item, phase, pt, t, item["options"], y1 - 40 if c.v else 0, 1.5)
    return cx, cy

# 54 Moving count
def draw_movingcount(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    rnd = _rnd.Random(item.get("seed", 1))
    objs = [item["target"]] * item["n"] + [rnd.choice(item["others"]) for _ in range(item["m"])]
    rnd.shuffle(objs)
    band = (x0, y0 + 40, x1, y0 + 520) if c.v else (x0, y0 + 60, x1, y0 + 440)
    d.rounded_rectangle(band, radius=30, fill=(40, 120, 200, 140))
    span = 3.2; start = 0.4
    if phase == "ask":
        for i, e in enumerate(objs):
            t0 = start + i * span / len(objs)
            u = (t - t0) / 1.4
            if 0 <= u <= 1:
                x = band[2] + 80 - u * (band[2] - band[0] + 160)
                y = band[1] + 60 + ((i * 137) % int(band[3] - band[1] - 120))
                paste(im, emoji_img(e, 110), x, y)
    else:
        f = font(F_BOLD, 120)
        txt = str(item["n"]) if phase == "reveal" else "?"
        tw = d.textlength(txt, font=f); d.text(((band[0] + band[2]) / 2 - tw / 2, (band[1] + band[3]) / 2 - 85), txt, font=f, fill=(255, 255, 255))
    hx, hy = (c.W / 2 - 200, band[3] + 90) if c.v else (x0 + 300, band[3] + 90)
    paste(im, emoji_img(item["target"], 100), hx, hy)
    f2 = font(F_BOLD, 54); d.text((hx + 70, hy - 36), "How many?", font=f2, fill=(255, 255, 255))
    if phase != "ask" or t >= start + span + 1.0:
        _opt_row(c, d, item, phase, pt, t, item["options"], band[3] + 280 if c.v else 0, start + span + 1.1, h_x=x0 + 1300)
    return (band[0] + band[2]) / 2, (band[1] + band[3]) / 2

# 55 Light order
LIGHTS = ["red", "blue", "green", "yellow"]
def draw_lightorder(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    R = 110 if c.v else 100
    pos = {"red": (c.W / 2 - 160, y0 + 160), "blue": (c.W / 2 + 160, y0 + 160), "green": (c.W / 2 - 160, y0 + 480), "yellow": (c.W / 2 + 160, y0 + 480)} if c.v else \
          {"red": (x0 + 250, y0 + 200), "blue": (x0 + 560, y0 + 200), "green": (x0 + 250, y0 + 510), "yellow": (x0 + 560, y0 + 510)}
    seq = item["seq"]; step = 0.7
    lit = None
    if phase == "ask":
        k = int((t - 0.6) / step)
        if 0 <= k < len(seq) and ((t - 0.6) % step) < step * 0.7: lit = seq[k]
    for nm, (px, py) in pos.items():
        col = INKS[nm]
        on = lit == nm or (phase == "reveal" and nm == seq[item["ask_pos"] - 1])
        if on:
            g = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(g).ellipse((px - R * 1.5, py - R * 1.5, px + R * 1.5, py + R * 1.5), fill=col + (170,))
            im.alpha_composite(g.filter(ImageFilter.GaussianBlur(30))); d = ImageDraw.Draw(im)
        d.ellipse((px - R, py - R, px + R, py + R), fill=col if on else tuple(int(v * 0.35) for v in col), outline=(255, 255, 255), width=8)
    if phase != "ask" or t >= 0.6 + step * len(seq) + 0.3:
        _opt_row(c, d, item, phase, pt, t, item["options"], y0 + 760 if c.v else 0, 0.6 + step * len(seq) + 0.4, h_x=x0 + 1250)
    return pos[seq[item["ask_pos"] - 1]]

# 56 Split picture
def split_answer(item): return item["order"].index(item["ask"])

def draw_split(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    S = 230 if c.v else 210
    em = item["emojis"]; n = len(em)
    xs = [x0 + (x1 - x0) * (i + 0.5) / n for i in range(n)] if c.v else [x0 + 300 + i * 330 for i in range(n)]
    ty, by = (y0 + 140, y0 + 560) if c.v else (y0 + 150, y0 + 500)
    f = font(F_BOLD, 46)
    for i, e in enumerate(em):
        img = emoji_img(e, S); top = img.crop((0, 0, img.width, img.height // 2))
        d.rounded_rectangle((xs[i] - S * 0.6, ty - S * 0.35, xs[i] + S * 0.6, ty + S * 0.35), radius=20, fill=(255, 255, 255, 230))
        paste(im, top, xs[i], ty + S * 0.05)
        d.text((xs[i] - S * 0.55, ty - S * 0.35), "ABC"[i], font=f, fill=c.accent)
    ans = split_answer(item)
    for j, src in enumerate(item["order"]):
        img = emoji_img(em[src], S); bot = img.crop((0, img.height // 2, img.width, img.height))
        bx, byy = xs[j], by
        if phase == "reveal" and j == ans:
            m = eo(pt / 0.7); tx, tyy = xs[item["ask"]], ty + S * 0.05 + bot.height
            bx, byy = bx + (tx - bx) * m, byy + (tyy - byy) * m
        else:
            d.rounded_rectangle((xs[j] - S * 0.6, by - S * 0.35, xs[j] + S * 0.6, by + S * 0.35), radius=20, fill=(255, 255, 255, 230))
        paste(im, bot, bx, byy, 1, 0.4 if (phase == "reveal" and j != ans) else 1)
        if not (phase == "reveal" and j == ans): d.text((xs[j] - S * 0.55, by - S * 0.35), str(j + 1), font=f, fill=c.accent)
    if phase != "reveal":
        f2 = font(F_BOLD, 56); txt = f"Which bottom fits top {'ABC'[item['ask']]}?"; tw = d.textlength(txt, font=f2)
        d.text((c.W / 2 - tw / 2, by + S * 0.55), txt, font=f2, fill=(255, 255, 255))
    return xs[item["ask"]], ty

# 57 How many circles
def draw_circles(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    rnd = _rnd.Random(item.get("seed", 1))
    S = 560 if c.v else 520
    ox, oy = (c.W / 2 - S / 2, y0 + 20) if c.v else (x0 + 140, y0 + 80)
    d.rounded_rectangle((ox - 20, oy - 20, ox + S + 20, oy + S + 20), radius=30, fill=(255, 255, 255, 235))
    circ = []
    for i in range(item["n"]):
        r = rnd.uniform(S * 0.12, S * 0.3)
        cx = rnd.uniform(ox + r, ox + S - r); cy = rnd.uniform(oy + r, oy + S - r); circ.append((cx, cy, r))
    k = item["n"] if phase != "reveal" else int(item["n"] * cl(pt / 1.2))
    for i, (cx, cy, r) in enumerate(circ):
        hl = phase == "reveal" and i < k
        a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=CANDY[i % 6] if hl else (40, 40, 70, int(255 * a)), width=8 if hl else 6)
    _opt_row(c, d, item, phase, pt, t, item["options"], y1 - 40 if c.v else 0, 1.4)
    return ox + S / 2, oy + S / 2

DRAW.update({"arrowout": draw_arrowout, "cardflip": draw_cardflip, "quickswap": draw_quickswap, "diceflash": draw_diceflash,
             "peek": draw_peek, "zoom": draw_zoom, "movingcount": draw_movingcount, "lightorder": draw_lightorder,
             "split": draw_split, "circles": draw_circles})
_old_min_ask4 = min_ask
def min_ask(item):
    t_ = item.get("type")
    if t_ == "cardflip": return 4.4
    if t_ == "quickswap": return 3.6
    if t_ == "diceflash": return 3.2
    if t_ == "zoom": return 4.2
    if t_ == "movingcount": return 5.2
    if t_ == "lightorder": return 0.6 + 0.7 * len(item["seq"]) + 1.4
    return _old_min_ask4(item)

# ================================================================ CANDIDATES (v6) — 20 more
def _seq_show(t, n, step=0.7, t0=0.5):
    k = int((t - t0) / step)
    return k if 0 <= k < n and ((t - t0) % step) < step * 0.8 else None

# 58 Which one did NOT appear
def draw_shapemiss(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cx, cy = (c.W / 2, y0 + 260) if c.v else (x0 + 420, (y0 + y1) / 2 + 20)
    d.rounded_rectangle((cx - 220, cy - 220, cx + 220, cy + 220), radius=40, fill=(255, 255, 255, 235))
    seq = item["seq"]
    if phase == "ask":
        k = _seq_show(t, len(seq))
        if k is not None: paste(im, emoji_img(seq[k], 300), cx, cy, eob(((t - 0.5) % 0.7) / 0.2))
        elif t > 0.5 + 0.7 * len(seq):
            f = font(F_BOLD, 200); tw = d.textlength("?", font=f); d.text((cx - tw / 2, cy - 140), "?", font=f, fill=(30, 30, 60))
    else:
        f = font(F_BOLD, 200); tw = d.textlength("?", font=f); d.text((cx - tw / 2, cy - 140), "?", font=f, fill=(30, 30, 60))
    if phase != "ask" or t > 0.5 + 0.7 * len(seq):
        _emoji_opts(c, im, d, item, phase, pt, t, 0.6 + 0.7 * len(seq), y0 + 680, x0 + 1250)
    return cx, cy

# 59 Spotlight
def draw_spotlight(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    S = 900 if c.v else 460   # Shorts: drawn big (engine fits it to ~90% width) so the picture stays sharp
    cx, cy = (c.W / 2, y0 + S / 2) if c.v else (x0 + 420, (y0 + y1) / 2 + 30)
    pic = Image.new("RGBA", (S, S), (250, 245, 230, 255)); e = emoji_img(item["emoji"], int(S * 0.9)); pic.paste(e, (int(S / 2 - e.width / 2), int(S / 2 - e.height / 2)), e)
    dark = Image.new("L", (S, S), 255)
    if phase == "reveal": dark = Image.new("L", (S, S), int(255 * (1 - eo(pt / 0.6))))
    else:
        tt = t if phase == "ask" else 4.0
        ang = tt * 1.6; r = S * 0.17
        sx, sy = S / 2 + math.cos(ang) * S * 0.28, S / 2 + math.sin(ang * 1.3) * S * 0.28
        ImageDraw.Draw(dark).ellipse((sx - r, sy - r, sx + r, sy + r), fill=0)
        dark = dark.filter(ImageFilter.GaussianBlur(10))
    shade = Image.new("RGBA", (S, S), (15, 15, 30, 255)); shade.putalpha(dark)
    pic.alpha_composite(shade)
    m = Image.new("L", (S, S), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, S, S), radius=40, fill=255); pic.putalpha(m)
    im.paste(pic, (int(cx - S / 2), int(cy - S / 2)), pic)
    _opt_row(c, d, item, phase, pt, t, item["options"], y1 - 30 if c.v else 0, 1.2)
    return cx, cy

# 60 Pixelated
def draw_pixel(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    S = 900 if c.v else 460   # Shorts: drawn big (engine fits it to ~90% width) so the picture stays sharp
    cx, cy = (c.W / 2, y0 + S / 2) if c.v else (x0 + 420, (y0 + y1) / 2 + 30)
    pic = Image.new("RGBA", (S, S), (250, 245, 230, 255)); e = emoji_img(item["emoji"], int(S * 0.9)); pic.paste(e, (int(S / 2 - e.width / 2), int(S / 2 - e.height / 2)), e)
    if phase == "reveal" and pt > 0.3: n = S
    else:
        tt = t if phase == "ask" else 4.5
        n = int(5 + 7 * cl(tt / 4.5))
    if n < S: pic = pic.resize((n, n), Image.BILINEAR).resize((S, S), Image.NEAREST)
    m = Image.new("L", (S, S), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, S, S), radius=40, fill=255); pic.putalpha(m)
    im.paste(pic, (int(cx - S / 2), int(cy - S / 2)), pic)
    _opt_row(c, d, item, phase, pt, t, item["options"], y1 - 30 if c.v else 0, 1.2)
    return cx, cy

# 61 Find it in the crowd
def draw_crowd(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cols, rows = (8, 9) if c.v else (16, 6)
    cell, ox, oy = _grid_geom(c, cols, rows, 150 if c.v else 110, 150)
    rnd = _rnd.Random(item.get("seed", 1))
    _panel(d, ox, oy, cols * cell, rows * cell)
    pr, pc = item["pos"]; pr %= rows; pc %= cols
    a = eo((t - 0.3) / 0.5) if phase == "ask" else 1
    for r_ in range(rows):
        for k in range(cols):
            e = item["target"] if (r_, k) == (pr, pc) else rnd.choice(item["pool"])
            sc = 0.3 if (phase == "reveal" and (r_, k) != (pr, pc) and pt > 0.3) else 1
            paste(im, emoji_img(e, cell * 0.78), ox + (k + 0.5) * cell, oy + (r_ + 0.5) * cell, 1, a * sc)
    hx = c.W / 2
    f = font(F_BOLD, 56); txt = "Find:"; tw = d.textlength(txt, font=f)
    d.text((hx - tw - 10, oy - 130), txt, font=f, fill=(255, 255, 255)); paste(im, emoji_img(item["target"], 100), hx + 60, oy - 95)
    cx, cy = ox + (pc + 0.5) * cell, oy + (pr + 0.5) * cell
    if phase == "reveal": _circle_hit(d, cx, cy, cell * 0.6, pt)
    return cx, cy

# 62 Pattern memory
def _mini_grid(size, cells, n=4, on=(255, 210, 60)):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im); g = size / n
    for i in range(n * n):
        r_, q = divmod(i, n)
        d.rounded_rectangle((q * g + 4, r_ * g + 4, (q + 1) * g - 4, (r_ + 1) * g - 4), radius=int(g * 0.18), fill=on if i in cells else (255, 255, 255, 200))
    return im

def draw_patmem(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    S = 440 if c.v else 420
    cx, cy = (c.W / 2, y0 + 240) if c.v else (x0 + 380, (y0 + y1) / 2 + 30)
    show = (phase == "ask" and 0.4 <= t < 2.6)
    paste(im, _mini_grid(S, item["patterns"][item["right"]] if show else [], on=c.accent), cx, cy)
    if phase != "ask" or t >= 2.6:
        n = len(item["patterns"])
        for q, pat in enumerate(item["patterns"]):
            ox, oy = (x0 + (x1 - x0) * (q + 0.5) / n, y0 + 680) if c.v else (x0 + 820 + q * 300, (y0 + y1) / 2 + 30)
            sz = 250 if c.v else 240
            fill = (255, 255, 255, 40)
            if phase == "reveal" and pt > 0.4: fill = (40, 190, 90, 255) if q == item["right"] else (150, 40, 55, 255)
            d.rounded_rectangle((ox - sz / 2 - 14, oy - sz / 2 - 14, ox + sz / 2 + 14, oy + sz / 2 + 14), radius=24, fill=fill, outline=c.accent, width=5)
            paste(im, _mini_grid(sz, pat, on=c.accent), ox, oy, eob((t - 2.7 - 0.2 * q) / 0.4) if phase == "ask" else 1)
            _label(d, ox - sz / 2, oy - sz / 2, "ABC"[q], c, r=28, size=38)
    return cx, cy

# 63 Odd pattern out (rotations vs mirror)
def _rot_cells(cells, k, n=3):
    out = set(cells)
    for _ in range(k % 4): out = {(q) * n + (n - 1 - r_) for r_, q in (divmod(i, n) for i in out)}
    return out

def draw_oddpattern(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    base = item["cells"]; n = 3
    pats = []
    for i, k in enumerate(item["rots"]):
        cells = _rot_cells(base, k)
        if i == item["odd"]: cells = {r_ * n + (n - 1 - q) for r_, q in (divmod(x, n) for x in cells)}
        pats.append(cells)
    sz = 300 if c.v else 280
    pos = [(c.W / 2 - 190, y0 + 190), (c.W / 2 + 190, y0 + 190), (c.W / 2 - 190, y0 + 590), (c.W / 2 + 190, y0 + 590)] if c.v else [(x0 + 200 + i * 410, (y0 + y1) / 2 + 30) for i in range(4)]
    for i, (px, py) in enumerate(pos):
        fill = (255, 255, 255, 40)
        if phase == "reveal" and pt > 0.4 and i == item["odd"]: fill = (40, 190, 90, 255)
        d.rounded_rectangle((px - sz / 2 - 14, py - sz / 2 - 14, px + sz / 2 + 14, py + sz / 2 + 14), radius=24, fill=fill, outline=c.accent, width=5)
        paste(im, _mini_grid(sz, pats[i], n=3, on=(255, 120, 80)), px, py, eob((t - 0.3 - 0.2 * i) / 0.4) if phase == "ask" else 1)
        _label(d, px - sz / 2, py - sz / 2, "ABCD"[i], c, r=28, size=38)
    return pos[item["odd"]]

# 64 Colour count
def draw_colorcount(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    rnd = _rnd.Random(item.get("seed", 1))
    shapes = [nm for nm, k in item["counts"].items() for _ in range(k)]; rnd.shuffle(shapes)
    bx = (x0 + 20, y0, x1 - 20, y0 + 600) if c.v else (x0 + 40, y0 + 60, x0 + 940, y1 - 20)
    d.rounded_rectangle(bx, radius=40, fill=(255, 255, 255, 235))
    cols, rows = 6, 5; cells = [(r_, q) for r_ in range(rows) for q in range(cols)]; rnd.shuffle(cells)
    cw, ch = (bx[2] - bx[0]) / cols, (bx[3] - bx[1]) / rows
    kinds = ["circle", "square", "triangle", "star"]
    for i, nm in enumerate(shapes[:len(cells)]):
        r_, q = cells[i]
        px = bx[0] + cw * (q + 0.5) + rnd.uniform(-cw * 0.12, cw * 0.12); py = bx[1] + ch * (r_ + 0.5) + rnd.uniform(-ch * 0.1, ch * 0.1)
        a = eob((t - 0.3 - 0.03 * i) / 0.3) if phase == "ask" else 1
        col = INKS[nm]
        if phase == "reveal" and nm != item["ask"]: col = tuple(int(v * 0.35 + 160) for v in col)
        _draw_shape(d, rnd.choice(kinds), col, px, py, min(cw, ch) * 0.3 * a)
    _opt_row(c, d, item, phase, pt, t, item["options"], bx[3] + 120 if c.v else 0, 1.6)
    return (bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2

# 65 What moved
def draw_moved(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    slots = list(item["slots"]); cols = 4
    a_, b_ = item["move"]
    after = phase != "ask" or t >= 3.0
    if after: slots[b_], slots[a_] = slots[a_], ""
    cw, ch = ((x1 - x0) / cols, 230) if c.v else (230, 230)
    ox = x0 if c.v else x0 + 40; oy = y0 + 20 if c.v else y0 + 80
    for i, e in enumerate(slots):
        r_, q = divmod(i, cols); cx, cy = ox + cw * (q + 0.5), oy + ch * (r_ + 0.5)
        box = (cx - 100, cy - 100, cx + 100, cy + 100)
        d.rounded_rectangle(box, radius=26, fill=(255, 255, 255, 220 if e else 50))
        if e: paste(im, emoji_img(e, 130), cx, cy)
        if phase == "reveal" and i == b_: glow_box(im, box, r=26)
    if phase == "ask" and 3.0 <= t < 3.45:
        im.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, int(255 * cl(1 - abs(t - 3.22) / 0.22)))))
    if after: _emoji_opts(c, im, d, item, phase, pt, t, 3.6, y0 + 660, x0 + 1300)
    return c.W / 2, (y0 + y1) / 2

# 66 Same or different
def draw_samediff(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    sc = item["scene"]; diff = item.get("diff")
    cell = 115 if c.v else 110; pw = cell * 3 + 40
    panels = [(c.W / 2, y0 + 200), (c.W / 2, y0 + 610)] if c.v else [(c.W / 2 - 520, (y0 + y1) / 2 + 30), (c.W / 2 - 80, (y0 + y1) / 2 + 30)]
    for p, (px, py) in enumerate(panels):
        d.rounded_rectangle((px - pw / 2, py - pw / 2, px + pw / 2, py + pw / 2), radius=30, fill=(255, 255, 255))
        for i, e in enumerate(sc):
            r_, k = divmod(i, 3)
            em = diff[1] if (p == 1 and diff and i == diff[0]) else e
            ex, ey = px - cell + k * cell, py - cell + r_ * cell
            paste(im, emoji_img(em, cell * 0.7), ex, ey, eob((t - 0.2 - 0.3 * p) / 0.4) if phase == "ask" else 1)
            if phase == "reveal" and diff and i == diff[0]: _circle_hit(d, ex, ey, cell * 0.5, pt)
    _opt_row(c, d, item, phase, pt, t, ["Same", "Different"], y1 + 40 if c.v else 0, 1.4, h_x=x0 + 1380)
    return panels[1]

# 67 Bigger group
def draw_biggroup(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    rnd = _rnd.Random(item.get("seed", 1))
    show = (phase == "ask" and 0.5 <= t < 1.8) or phase == "reveal"
    boxes = [(x0 + 10, y0 + 40, c.W / 2 - 20, y0 + 560), (c.W / 2 + 20, y0 + 40, x1 - 10, y0 + 560)] if c.v else [(x0 + 60, y0 + 80, x0 + 760, y1 - 40), (x0 + 820, y0 + 80, x0 + 1520, y1 - 40)]
    win = 0 if item["counts"][0] > item["counts"][1] else 1
    for k, bx in enumerate(boxes):
        fill = (255, 255, 255, 230)
        if phase == "reveal" and pt > 0.5: fill = (40, 190, 90, 255) if k == win else (150, 40, 55, 255)
        d.rounded_rectangle(bx, radius=30, fill=fill)
        _label(d, bx[0] + 40, bx[1] + 40, "AB"[k], c, r=30, size=40)
        if show:
            for _ in range(item["counts"][k]):
                px = rnd.uniform(bx[0] + 40, bx[2] - 40); py = rnd.uniform(bx[1] + 80, bx[3] - 40); r = 18
                d.ellipse((px - r, py - r, px + r, py + r), fill=(60, 120, 230))
        else:
            f = font(F_BOLD, 150); tw = d.textlength("?", font=f); d.text(((bx[0] + bx[2]) / 2 - tw / 2, (bx[1] + bx[3]) / 2 - 100), "?", font=f, fill=(30, 30, 60))
        if phase == "reveal":
            f2 = font(F_BOLD, 80); txt = str(item["counts"][k]); tw = d.textlength(txt, font=f2)
            d.text(((bx[0] + bx[2]) / 2 - tw / 2, bx[3] + 10), txt, font=f2, fill=(255, 255, 255))
    return ((boxes[win][0] + boxes[win][2]) / 2, (boxes[win][1] + boxes[win][3]) / 2)

# 68 Speed read
def draw_speedread(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cx, cy = (c.W / 2, y0 + 250) if c.v else (x0 + 480, (y0 + y1) / 2 + 30)
    box = (cx - 400, cy - 130, cx + 400, cy + 130)
    d.rounded_rectangle(box, radius=40, fill=(255, 255, 255))
    show = (phase == "ask" and 1.0 <= t < 1.35) or phase == "reveal"
    if show:
        f = font(F_BOLD, 150); tw = d.textlength(item["word"], font=f); d.text((cx - tw / 2, cy - 110), item["word"], font=f, fill=(40, 40, 70))
    else:
        f = font(F_BOLD, 90); txt = "READY?" if (phase == "ask" and t < 1.0) else "???"; tw = d.textlength(txt, font=f); d.text((cx - tw / 2, cy - 65), txt, font=f, fill=(150, 150, 180))
    if phase != "ask" or t > 1.5:
        _opt_row(c, d, item, phase, pt, t, item["options"], y0 + 620 if c.v else 0, 1.6, h_x=x0 + 1300)
    return cx, cy

# 69 Number that appears twice
def dupnum_answer(item):
    seen = {}
    for i, n in enumerate(item["nums"]):
        if n in seen: return n, seen[n], i
        seen[n] = i
    return None

def draw_dupnum(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    nums = item["nums"]; cols = (5 if len(nums) > 16 else 4) if c.v else (10 if len(nums) > 16 else 8); rows = math.ceil(len(nums) / cols)
    cell, ox, oy = _grid_geom(c, cols, rows, 30 if c.v else 80, 170)
    _panel(d, ox, oy, cols * cell, rows * cell)
    ans = dupnum_answer(item); f = font(F_BOLD, cell * 0.42)
    for i, n in enumerate(nums):
        r_, q = divmod(i, cols); cx, cy = ox + (q + 0.5) * cell, oy + (r_ + 0.5) * cell
        txt = str(n); tw = d.textlength(txt, font=f)
        col = CANDY[(n * 7) % 6]; col = tuple(int(v * 0.7) for v in col)
        d.text((cx - tw / 2, cy - cell * 0.3), txt, font=f, fill=col)
        if phase == "reveal" and i in ans[1:]: _circle_hit(d, cx, cy, cell * 0.45, pt)
    i = ans[1]; r_, q = divmod(i, cols)
    return ox + (q + 0.5) * cell, oy + (r_ + 0.5) * cell

# 70 Which glass has the most water
def fill_answer(item):
    v = [w * l for w, l in item["glasses"]]; return v.index(max(v))

def draw_fill(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    gl = item["glasses"]; n = len(gl)
    H = 460 if c.v else 420
    base = y0 + 600 if c.v else y1 - 80
    for k, (w, l) in enumerate(gl):
        cx = x0 + (x1 - x0) * (k + 0.5) / n if c.v else x0 + 250 + k * 380
        W = 120 + w * 140
        top = base - H
        lvl = l * (cl(t / 1.0) if phase == "ask" else 1)
        d.rectangle((cx - W / 2 + 8, base - H * lvl, cx + W / 2 - 8, base - 6), fill=(70, 160, 255))
        d.line((cx - W / 2, top, cx - W / 2, base, cx + W / 2, base, cx + W / 2, top), fill=(255, 255, 255), width=10, joint="curve")
        _label(d, cx, base + 60, "ABC"[k], c)
        if phase == "reveal" and k == fill_answer(item) and pt > 0.5: glow_box(im, (cx - W / 2 - 20, top - 20, cx + W / 2 + 20, base + 20), r=20)
    k = fill_answer(item)
    return (x0 + (x1 - x0) * (k + 0.5) / n if c.v else x0 + 250 + k * 380), base - H / 2

# 71 Longest snake
def _snake_pts(x0, x1, y, amp, freq, steps=120):
    return [(x0 + (x1 - x0) * i / steps, y + amp * math.sin(i / steps * math.pi * 2 * freq)) for i in range(steps + 1)]

def snakes_answer(item):
    L = []
    for amp, freq in item["waves"]:
        p = _snake_pts(0, 800, 0, amp, freq, 400); L.append(sum(math.dist(p[i], p[i + 1]) for i in range(len(p) - 1)))
    return L.index(max(L))

def draw_snakes(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cols = [(240, 80, 90), (70, 150, 240), (80, 200, 110)]
    win = snakes_answer(item)
    for k, (amp, freq) in enumerate(item["waves"]):
        y = y0 + 120 + k * 260 if c.v else y0 + 120 + k * 220
        xa, xb = (x0 + 120, x1 - 40) if c.v else (x0 + 160, x0 + 1100)
        P = _snake_pts(xa, xb, y, amp, freq)
        a = eo((t - 0.3 - 0.2 * k) / 0.6) if phase == "ask" else 1
        kk = max(2, int(len(P) * a))
        wdt = 22 if (phase == "reveal" and k == win and pt > 0.4) else 14
        d.line(P[:kk], fill=cols[k], width=wdt, joint="curve")
        _label(d, xa - 70, y, "ABC"[k], c)
    if c.v:
        _opt_row(c, d, dict(item, right=win), phase, pt, t, ["A", "B", "C"], y1 - 30, 1.4)
    return x0 + 500, y0 + 120 + win * (260 if c.v else 220)

# 72 Count the squares
def squares_total(item): return sum(k * k for k in range(1, item["n"] + 1))

def draw_squares(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    n = item["n"]; S = 480 if c.v else 440
    ox, oy = (c.W / 2 - S / 2, y0 + 40) if c.v else (x0 + 180, y0 + 90)
    a = eo((t - 0.3) / 0.6) if phase == "ask" else 1
    col = (255, 255, 255, int(255 * a))
    for i in range(n + 1):
        d.line((ox + S * i / n, oy, ox + S * i / n, oy + S), fill=col, width=10)
        d.line((ox, oy + S * i / n, ox + S, oy + S * i / n), fill=col, width=10)
    if phase == "reveal" and pt > 0.3:
        k = int(cl((pt - 0.3) / 1.5) * n) + 1
        k = min(k, n); g = S / n
        d.rectangle((ox, oy, ox + g * k, oy + g * k), outline=(60, 255, 120), width=12)
    _opt_row(c, d, item, phase, pt, t, item["options"], y1 - 40 if c.v else 0, 1.4)
    return ox + S / 2, oy + S / 2

# 73 Colour memory
def draw_colormem(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cx, cy = (c.W / 2, y0 + 260) if c.v else (x0 + 420, (y0 + y1) / 2 + 30)
    show = (phase == "ask" and 0.5 <= t < 2.3) or (phase == "reveal" and pt > 0.3)
    e = emoji_img(item["shape"], 380)
    mask = e.split()[-1].point(lambda v: 255 if v > 60 else 0)
    col = INKS[item["color"]] if show else (150, 150, 165)
    sil = Image.new("RGBA", e.size, col + (255,)); sil.putalpha(mask)
    d.rounded_rectangle((cx - 240, cy - 240, cx + 240, cy + 240), radius=40, fill=(255, 255, 255, 230))
    paste(im, sil, cx, cy)
    if phase != "ask" or t >= 2.3:
        _opt_row(c, d, item, phase, pt, t, item["options"], y0 + 680 if c.v else 0, 2.4)
    return cx, cy

# 74 Silhouette guess
def draw_silhouette(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cx, cy = (c.W / 2, y0 + 270) if c.v else (x0 + 420, (y0 + y1) / 2 + 30)
    e = emoji_img(item["emoji"], 420)
    d.rounded_rectangle((cx - 260, cy - 260, cx + 260, cy + 260), radius=40, fill=(255, 255, 255, 230))
    if phase == "reveal" and pt > 0.3: paste(im, e, cx, cy)
    else:
        sil = Image.new("RGBA", e.size, (25, 25, 40, 255)); sil.putalpha(e.split()[-1].point(lambda v: 255 if v > 60 else 0))
        paste(im, sil, cx, cy, eob((t - 0.2) / 0.4) if phase == "ask" else 1)
    _opt_row(c, d, item, phase, pt, t, item["options"], y1 - 30 if c.v else 0, 1.2)
    return cx, cy

# 75 Upside-down word
def draw_upsideword(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cx, cy = (c.W / 2, y0 + 250) if c.v else (x0 + 480, (y0 + y1) / 2 + 30)
    f = font(F_BOLD, 170); tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    w = int(tmp.textlength(item["word"], font=f)) + 60
    lay = Image.new("RGBA", (w, 230), (0, 0, 0, 0)); ImageDraw.Draw(lay).text((30, 0), item["word"], font=f, fill=(40, 40, 70))
    rot = 180 if phase != "reveal" else 180 * (1 - eo(pt / 0.7))
    lay = lay.rotate(rot, expand=True, resample=Image.BICUBIC)
    d.rounded_rectangle((cx - 420, cy - 150, cx + 420, cy + 150), radius=40, fill=(255, 255, 255))
    sc = min(1, 780 / lay.width)
    paste(im, lay, cx, cy, sc)
    _opt_row(c, d, item, phase, pt, t, item["options"], y0 + 620 if c.v else 0, 1.2, h_x=x0 + 1300)
    return cx, cy

# 76 Colour change
def draw_colorchange(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    cols = item["colors"]; n = len(cols); per = 3
    after = phase != "ask" or t >= 3.0
    f = font(F_BOLD, 44)
    for i, nm in enumerate(cols):
        r_, q = divmod(i, per)
        cx = x0 + (x1 - x0) * (q + 0.5) / per if c.v else x0 + 200 + q * 330
        cy = y0 + 200 + r_ * 380 if c.v else y0 + 200 + r_ * 330
        col = INKS[item["new"] if (after and i == item["changed"]) else nm]
        R = 85
        d.line((cx, cy + R * 1.2, cx + 10, cy + R * 2.6), fill=(230, 230, 240), width=5)
        d.ellipse((cx - R, cy - R * 1.2, cx + R, cy + R * 1.2), fill=col, outline=(30, 30, 60), width=5)
        d.text((cx - R - 30, cy - R * 1.2 - 20), str(i + 1), font=f, fill=c.accent)
        if phase == "reveal" and i == item["changed"]: _circle_hit(d, cx, cy, R * 1.5, pt)
    if phase == "ask" and 3.0 <= t < 3.45:
        im.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, int(255 * cl(1 - abs(t - 3.22) / 0.22)))))
    return c.W / 2, (y0 + y1) / 2

# 77 Hidden number (dot plate)
def draw_hiddennum(c, im, item, phase, pt, t):
    x0, y0, x1, y1 = area(c); d = ImageDraw.Draw(im)
    S = 560 if c.v else 520
    cx, cy = (c.W / 2, y0 + 300) if c.v else (x0 + 420, (y0 + y1) / 2 + 30)
    mask = Image.new("L", (S, S), 0); md = ImageDraw.Draw(mask)
    f = font(F_BOLD, int(S * 0.75)); tw = md.textlength(item["digit"], font=f)
    md.text((S / 2 - tw / 2, S * 0.02), item["digit"], font=f, fill=255)
    rnd = _rnd.Random(item.get("seed", 1)); fg, bg = tuple(item["fg"]), tuple(item["bg"])
    plate = Image.new("RGBA", (S, S), (0, 0, 0, 0)); pd = ImageDraw.Draw(plate)
    pd.ellipse((0, 0, S, S), fill=(250, 248, 240))
    step = S / 26
    for gy in range(27):
        for gx in range(27):
            x = gx * step + rnd.uniform(-3, 3); y = gy * step + rnd.uniform(-3, 3)
            if math.hypot(x - S / 2, y - S / 2) > S / 2 - 12: continue
            r = rnd.uniform(step * 0.32, step * 0.48)
            inside = mask.getpixel((int(min(S - 1, max(0, x))), int(min(S - 1, max(0, y))))) > 128
            base = fg if inside else bg
            jit = rnd.randint(-18, 18)
            col = tuple(max(0, min(255, v + jit)) for v in base)
            if phase == "reveal" and pt > 0.4 and inside: col = (30, 30, 60)
            pd.ellipse((x - r, y - r, x + r, y + r), fill=col)
    paste(im, plate, cx, cy, eob((t - 0.2) / 0.4) if phase == "ask" else 1)
    _opt_row(c, d, item, phase, pt, t, item["options"], y1 - 20 if c.v else 0, 1.2)
    return cx, cy

DRAW.update({"shapemiss": draw_shapemiss, "spotlight": draw_spotlight, "pixel": draw_pixel, "crowd": draw_crowd,
             "patmem": draw_patmem, "oddpattern": draw_oddpattern, "colorcount": draw_colorcount, "moved": draw_moved,
             "samediff": draw_samediff, "biggroup": draw_biggroup, "speedread": draw_speedread, "dupnum": draw_dupnum,
             "fill": draw_fill, "snakes": draw_snakes, "squares": draw_squares, "colormem": draw_colormem,
             "silhouette": draw_silhouette, "upsideword": draw_upsideword, "colorchange": draw_colorchange, "hiddennum": draw_hiddennum})
_old_min_ask5 = min_ask
def min_ask(item):
    t_ = item.get("type")
    if t_ == "shapemiss": return 0.5 + 0.7 * len(item["seq"]) + 1.4
    if t_ in ("spotlight", "pixel"): return 4.6
    if t_ == "patmem": return 3.8
    if t_ in ("moved", "colorchange"): return 5.4
    if t_ == "biggroup": return 2.6
    if t_ == "speedread": return 2.6
    if t_ == "colormem": return 3.6
    if t_ == "cardflip": return cardflip_end(item) + 1.6
    return _old_min_ask5(item)
import eyebrain3  # noqa: E402,F401  (candidate formats 78-97)
